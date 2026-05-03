"""FastAPI Dependencies for Meeting AI: Auth, Database Sessions, and User Context"""
from typing import Optional
import uuid
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import UnauthorizedException
from app.core.security import decode_token
from app.db.database import get_db
from app.db.models.user import User, UserStatus
from app.db.repositories.user_repo import UserRepository

bearer_scheme = HTTPBearer(auto_error=True)


async def get_token_payload(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
) -> dict:
    """Extract and validate JWT token payload from Authorization header"""
    token = credentials.credentials
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise UnauthorizedException(message="Invalid token type, access token expected")
    return payload


async def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Fetch current authenticated user from database"""
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException(message="Token missing subject identifier")

    try:
        user_id = uuid.UUID(user_id_str)
    except ValueError:
        raise UnauthorizedException(message="Invalid user identifier in token")

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)
    if not user:
        raise UnauthorizedException(message="User not found or deleted")

    if user.status != UserStatus.ACTIVE:
        raise UnauthorizedException(message="User account is deactivated")

    return user


def get_client_ip(request: Optional[Request]) -> Optional[str]:
    """Extract client IP address"""
    if not request:
        return None
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else None
