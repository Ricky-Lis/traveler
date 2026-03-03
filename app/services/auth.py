from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as redis

from app.models.user import User
from app.utils.security import hash_password, verify_password, create_access_token
from app.utils.email_utils import (
    generate_code,
    send_verification_email,
    VERIFY_CODE_TTL,
    VERIFY_CODE_INTERVAL,
)

REDIS_CODE_PREFIX = "email_code:"
REDIS_CODE_LIMIT_PREFIX = "email_code_limit:"


class AuthService:

    def __init__(self, db: AsyncSession, rds: redis.Redis):
        self.db = db
        self.rds = rds

    # ---------- 发送验证码 ----------

    async def send_code(self, email: str) -> None:
        limit_key = f"{REDIS_CODE_LIMIT_PREFIX}{email}"
        if await self.rds.exists(limit_key):
            raise ValueError("发送过于频繁，请稍后再试")

        code = generate_code()
        ok = await send_verification_email(email, code)
        if not ok:
            raise RuntimeError("验证码发送失败，请稍后重试")

        code_key = f"{REDIS_CODE_PREFIX}{email}"
        await self.rds.set(code_key, code, ex=VERIFY_CODE_TTL)
        await self.rds.set(limit_key, "1", ex=VERIFY_CODE_INTERVAL)

    # ---------- 验证码校验 (内部) ----------

    async def _verify_code(self, email: str, code: str) -> None:
        code_key = f"{REDIS_CODE_PREFIX}{email}"
        cached = await self.rds.get(code_key)
        if not cached:
            raise ValueError("验证码已过期或未发送")
        if cached != code:
            raise ValueError("验证码错误")
        await self.rds.delete(code_key)

    # ---------- 注册 ----------

    async def register(
        self, email: str, code: str, password: str, nickname: str
    ) -> tuple[str, User]:
        await self._verify_code(email, code)

        exists = await self.db.scalar(select(User).where(User.email == email))
        if exists:
            raise ValueError("该邮箱已注册")

        user = User(
            email=email,
            password_hash=hash_password(password),
            nickname=nickname or email.split("@")[0],
            email_verified=True,
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)

        token = create_access_token(user.id)
        return token, user

    # ---------- 登录 ----------

    async def login(self, email: str, password: str) -> tuple[str, User]:
        user = await self.db.scalar(select(User).where(User.email == email))
        if not user:
            raise ValueError("邮箱或密码错误")
        if not verify_password(password, user.password_hash):
            raise ValueError("邮箱或密码错误")
        if not user.is_active:
            raise ValueError("该账号已被禁用")

        user.last_login_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(user)

        token = create_access_token(user.id)
        return token, user

    # ---------- 重置密码 ----------

    async def reset_password(self, email: str, code: str, new_password: str) -> None:
        await self._verify_code(email, code)

        user = await self.db.scalar(select(User).where(User.email == email))
        if not user:
            raise ValueError("该邮箱尚未注册")

        user.password_hash = hash_password(new_password)
        await self.db.flush()

    # ---------- 根据 id 获取用户 ----------

    async def get_user_by_id(self, user_id: int) -> User | None:
        return await self.db.get(User, user_id)
