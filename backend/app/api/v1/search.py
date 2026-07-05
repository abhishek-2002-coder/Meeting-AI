"""Search & Dashboard API Endpoints"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.db.repositories.meeting_repo import MeetingRepository
from app.schemas.common import ApiResponse
from app.schemas.meeting import DashboardStats, MeetingRead
from app.schemas.search import SearchResponse
from app.services.search_service import SearchService

router = APIRouter(tags=["Search & Dashboard"])


@router.get(
    "/search/meetings",
    response_model=ApiResponse[SearchResponse],
    summary="Search across all meeting titles, transcripts, summaries, decisions, and action items",
)
async def search_meetings(
    q: str = Query(..., min_length=1, description="Keyword search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = SearchService(db)
    results = await service.search(user_id=current_user.id, query=q)
    return ApiResponse.ok(data=results)


@router.get(
    "/dashboard/stats",
    response_model=ApiResponse[DashboardStats],
    summary="Get aggregated statistics and recent meetings for dashboard overview",
)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    metrics = await repo.get_dashboard_metrics(user_id=current_user.id)
    recent_meetings_raw, _ = await repo.search_and_paginate(user_id=current_user.id, limit=5)

    recent_reads = [
        MeetingRead(
            id=m.id,
            user_id=m.user_id,
            title=m.title,
            description=m.description,
            status=m.status,
            language=m.language,
            duration_seconds=m.duration_seconds,
            completed_at=m.completed_at,
            created_at=m.created_at,
            updated_at=m.updated_at,
            has_recording=m.file is not None,
        )
        for m in recent_meetings_raw
    ]

    stats = DashboardStats(
        total_meetings=metrics["total_meetings"],
        completed_meetings=metrics["completed_meetings"],
        processing_meetings=metrics["processing_meetings"],
        failed_meetings=metrics["failed_meetings"],
        total_action_items=metrics["total_action_items"],
        open_action_items=metrics["open_action_items"],
        recent_meetings=recent_reads,
    )

    return ApiResponse.ok(data=stats)
