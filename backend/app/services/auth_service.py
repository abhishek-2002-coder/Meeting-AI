"""Authentication Service for Meeting AI"""
from typing import Optional
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ConflictException, UnauthorizedException
from app.core.security import create_access_token, create_refresh_token, decode_token, get_password_hash, verify_password
from app.db.models.audit_log import AuditAction
from app.db.models.user import User, UserStatus
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.user_repo import UserRepository
from app.schemas.auth import AuthResponseData, LoginRequest, RegisterRequest, TokenData, UserRead


class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.audit_repo = AuditRepository(db)

    async def register(self, req: RegisterRequest, ip_address: Optional[str] = None) -> AuthResponseData:
        existing = await self.user_repo.get_by_email(req.email)
        if existing:
            raise ConflictException(message=f"Account with email '{req.email}' already exists.")

        pw_hash = get_password_hash(req.password)
        user = await self.user_repo.create(name=req.name, email=req.email, password_hash=pw_hash)

        access_token = create_access_token(subject=user.id, organization_id=user.id, role="USER")
        refresh_token = create_refresh_token(subject=user.id, organization_id=user.id)

        await self.audit_repo.log_event(
            action=AuditAction.USER_REGISTER,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            metadata_json={"email": user.email},
            ip_address=ip_address,
        )

        return AuthResponseData(
            user=UserRead.model_validate(user),
            tokens=TokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
        )

    async def login(self, email: str, password: str, ip_address: Optional[str] = None) -> AuthResponseData:
        user = await self.user_repo.get_by_email(email)
        if not user or not verify_password(password, user.password_hash):
            raise UnauthorizedException(message="Incorrect email or password")

        if user.status != UserStatus.ACTIVE:
            raise UnauthorizedException(message="Account has been deactivated")

        access_token = create_access_token(subject=user.id, organization_id=user.id, role="USER")
        refresh_token = create_refresh_token(subject=user.id, organization_id=user.id)

        await self.audit_repo.log_event(
            action=AuditAction.USER_LOGIN,
            user_id=user.id,
            resource_type="User",
            resource_id=str(user.id),
            ip_address=ip_address,
        )

        return AuthResponseData(
            user=UserRead.model_validate(user),
            tokens=TokenData(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            ),
        )

    async def refresh_tokens(self, refresh_token_str: str) -> TokenData:
        payload = decode_token(refresh_token_str)
        if payload.get("type") != "refresh":
            raise UnauthorizedException(message="Invalid token type, expected refresh token")

        user_id = uuid.UUID(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise UnauthorizedException(message="User account is no longer active")

        access_token = create_access_token(subject=user.id, organization_id=user.id, role="USER")
        refresh_token = create_refresh_token(subject=user.id, organization_id=user.id)

        return TokenData(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )
