"""Authentication API Endpoints"""
from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_client_ip, get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.auth import (
    AuthResponseData,
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenData,
    UserRead,
)
from app.schemas.common import ApiResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=ApiResponse[AuthResponseData],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account",
)
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request)
    service = AuthService(db)
    result = await service.register(req, ip_address=ip)
    return ApiResponse.ok(data=result, message="User registered successfully")


@router.post(
    "/login",
    response_model=ApiResponse[AuthResponseData],
    summary="Authenticate user and issue JWT tokens",
)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    ip = get_client_ip(request)
    service = AuthService(db)
    result = await service.login(email=req.email, password=req.password, ip_address=ip)
    return ApiResponse.ok(data=result, message="Login successful")


@router.post(
    "/refresh",
    response_model=ApiResponse[TokenData],
    summary="Refresh access token",
)
async def refresh_token(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    service = AuthService(db)
    tokens = await service.refresh_tokens(req.refresh_token)
    return ApiResponse.ok(data=tokens, message="Token refreshed successfully")


@router.post(
    "/logout",
    response_model=ApiResponse[dict],
    summary="Logout active session",
)
async def logout(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse.ok(data={"logged_out": True}, message="Logged out successfully")


@router.get(
    "/me",
    response_model=ApiResponse[UserRead],
    summary="Get current authenticated user profile",
)
async def get_me(
    current_user: User = Depends(get_current_user),
):
    return ApiResponse.ok(data=UserRead.model_validate(current_user))
