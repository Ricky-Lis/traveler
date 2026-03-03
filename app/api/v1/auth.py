from fastapi import APIRouter, Depends, HTTPException, status

from app.dependencies import get_auth_service, get_current_user
from app.services.auth import AuthService
from app.models.user import User
from app.schemas.user import (
    SendCodeRequest,
    RegisterRequest,
    LoginRequest,
    ResetPasswordRequest,
    TokenResponse,
    UserInfo,
    MessageResponse,
)

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/send-code", response_model=MessageResponse, summary="发送邮箱验证码")
async def send_code(
    body: SendCodeRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.send_code(body.email)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    return MessageResponse(message="验证码已发送，请查收邮箱")


@router.post("/register", response_model=TokenResponse, summary="邮箱注册")
async def register(
    body: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token, user = await auth_service.register(
            email=body.email,
            code=body.code,
            password=body.password,
            nickname=body.nickname,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


@router.post("/login", response_model=TokenResponse, summary="密码登录")
async def login(
    body: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        token, user = await auth_service.login(email=body.email, password=body.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    return TokenResponse(access_token=token, user=UserInfo.model_validate(user))


@router.post("/reset-password", response_model=MessageResponse, summary="重置密码")
async def reset_password(
    body: ResetPasswordRequest,
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        await auth_service.reset_password(
            email=body.email, code=body.code, new_password=body.new_password
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return MessageResponse(message="密码重置成功，请使用新密码登录")


@router.get("/me", response_model=UserInfo, summary="获取当前用户信息")
async def get_me(current_user: User = Depends(get_current_user)):
    return UserInfo.model_validate(current_user)
