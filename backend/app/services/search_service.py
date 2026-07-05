"""Search Service for Meeting AI"""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.repositories.search_repo import SearchRepository
from app.schemas.search import SearchResponse


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = SearchRepository(db)

    async def search(self, user_id: uuid.UUID, query: str, limit: int = 50) -> SearchResponse:
        results = await self.repo.search_meetings(user_id=user_id, query=query, limit=limit)
        return SearchResponse(
            query=query,
            total_results=len(results),
            results=results,
        )
