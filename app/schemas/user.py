from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


# ---------- 请求体 ----------

class SendCodeRequest(BaseModel):
    """发送邮箱验证码"""
    email: EmailStr


class RegisterRequest(BaseModel):
    """注册"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码")
    password: str = Field(..., min_length=6, max_length=64, description="密码")
    nickname: str = Field(default="", max_length=50, description="昵称")


class LoginRequest(BaseModel):
    """登录"""
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=64)


class ResetPasswordRequest(BaseModel):
    """重置密码"""
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, max_length=64)


# ---------- 响应体 ----------

class UserInfo(BaseModel):
    """对外暴露的用户信息"""
    id: int
    nickname: str
    avatar: str
    email: str
    bio: str
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserInfo


class MessageResponse(BaseModel):
    message: str
