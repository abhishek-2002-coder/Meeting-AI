"""Meeting Management API Endpoints"""
import math
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.db.database import get_db
from app.db.models.user import User
from app.db.repositories.meeting_repo import MeetingRepository
from app.schemas.common import ApiResponse, PaginatedData
from app.schemas.meeting import MeetingCreate, MeetingDetailRead, MeetingRead, MeetingUpdate
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["Meetings"])


@router.get(
    "",
    response_model=ApiResponse[PaginatedData[MeetingRead]],
    summary="List user meetings with search, status filtering, and pagination",
)
async def list_meetings(
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status: UPLOADED | PROCESSING | COMPLETED | FAILED"),
    search: Optional[str] = Query(None, description="Search by title or description"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    offset = (page - 1) * limit
    repo = MeetingRepository(db)
    items, total = await repo.search_and_paginate(
        user_id=current_user.id,
        status=status,
        search=search,
        offset=offset,
        limit=limit,
    )
    pages = math.ceil(total / limit) if limit > 0 else 1

    item_reads = [
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
        for m in items
    ]

    return ApiResponse.ok(
        data=PaginatedData[MeetingRead](
            items=item_reads,
            total=total,
            page=page,
            limit=limit,
            pages=pages,
        )
    )


@router.post(
    "",
    response_model=ApiResponse[MeetingRead],
    status_code=status.HTTP_201_CREATED,
    summary="Create a new meeting draft",
)
async def create_meeting(
    req: MeetingCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MeetingService(db)
    meeting = await service.create_meeting(user_id=current_user.id, req=req)
    return ApiResponse.ok(data=MeetingRead.model_validate(meeting), message="Meeting created successfully")


@router.get(
    "/{meeting_id}",
    response_model=ApiResponse[MeetingDetailRead],
    summary="Get comprehensive meeting details, summary, topics, decisions, and action items",
)
async def get_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MeetingService(db)
    detail = await service.get_meeting_detail(user_id=current_user.id, meeting_id=meeting_id)
    return ApiResponse.ok(data=detail)


@router.put(
    "/{meeting_id}",
    response_model=ApiResponse[MeetingRead],
    summary="Update meeting title, description, or language",
)
async def update_meeting(
    meeting_id: uuid.UUID,
    req: MeetingUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    repo = MeetingRepository(db)
    update_data = req.model_dump(exclude_unset=True)
    meeting = await repo.update(user_id=current_user.id, entity_id=meeting_id, **update_data)
    if not meeting:
        raise NotFoundException(message="Meeting not found")
    return ApiResponse.ok(data=MeetingRead.model_validate(meeting), message="Meeting updated successfully")


@router.delete(
    "/{meeting_id}",
    response_model=ApiResponse[dict],
    summary="Delete a meeting and its uploaded recording",
)
async def delete_meeting(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MeetingService(db)
    deleted = await service.delete_meeting(user_id=current_user.id, meeting_id=meeting_id)
    return ApiResponse.ok(data={"deleted": deleted}, message="Meeting deleted successfully")
