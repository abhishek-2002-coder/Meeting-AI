"""Base User-Scoped Generic Repository"""
from typing import Any, Generic, List, Optional, Sequence, Type, TypeVar
import uuid
from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseUserRepository(Generic[ModelType]):
    """Generic repository enforcing user boundary for models containing user_id"""
    def __init__(self, model: Type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, user_id: uuid.UUID, entity_id: uuid.UUID) -> Optional[ModelType]:
        stmt = select(self.model).where(
            self.model.user_id == user_id,
            self.model.id == entity_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_user(
        self,
        user_id: uuid.UUID,
        offset: int = 0,
        limit: int = 50,
    ) -> Sequence[ModelType]:
        stmt = select(self.model).where(self.model.user_id == user_id)
        if hasattr(self.model, "created_at"):
            stmt = stmt.order_by(self.model.created_at.desc())
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(self, user_id: uuid.UUID) -> int:
        stmt = select(func.count(self.model.id)).where(self.model.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one() or 0

    async def create(self, user_id: uuid.UUID, **kwargs: Any) -> ModelType:
        entity = self.model(user_id=user_id, **kwargs)
        self.session.add(entity)
        await self.session.flush()
        await self.session.refresh(entity)
        return entity

    async def update(self, user_id: uuid.UUID, entity_id: uuid.UUID, **kwargs: Any) -> Optional[ModelType]:
        stmt = (
            update(self.model)
            .where(self.model.user_id == user_id, self.model.id == entity_id)
            .values(**kwargs)
            .returning(self.model)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, user_id: uuid.UUID, entity_id: uuid.UUID) -> bool:
        stmt = delete(self.model).where(
            self.model.user_id == user_id,
            self.model.id == entity_id,
        )
        result = await self.session.execute(stmt)
        return (result.rowcount or 0) > 0
