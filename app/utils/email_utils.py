import random
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib

from app.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

VERIFY_CODE_TTL = 300  # 验证码有效期 5 分钟
VERIFY_CODE_INTERVAL = 60  # 同一邮箱最短发送间隔 60 秒


def generate_code(length: int = 6) -> str:
    return "".join(str(random.randint(0, 9)) for _ in range(length))


async def send_verification_email(to_email: str, code: str) -> bool:
    """通过 SMTP 发送验证码邮件，成功返回 True"""
    msg = MIMEMultipart("alternative")
    msg["From"] = settings.SMTP_FROM
    msg["To"] = to_email
    msg["Subject"] = "【旅行计划】邮箱验证码"

    html = f"""\
    <div style="font-family:sans-serif;max-width:480px;margin:auto;padding:24px;border:1px solid #e0e0e0;border-radius:8px;">
        <h2 style="color:#1a73e8;">旅行计划</h2>
        <p>您好，您的验证码为：</p>
        <p style="font-size:32px;font-weight:bold;letter-spacing:8px;color:#333;">{code}</p>
        <p style="color:#888;font-size:13px;">验证码 {VERIFY_CODE_TTL // 60} 分钟内有效，请勿泄露给他人。</p>
    </div>
    """
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        await aiosmtplib.send(
            msg,
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            username=settings.SMTP_USER,
            password=settings.SMTP_PASSWORD,
            use_tls=True,
        )
        return True
    except Exception:
        logger.exception("发送验证码邮件失败: %s", to_email)
        return False
