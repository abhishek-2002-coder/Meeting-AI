"""Meeting Summary, Topics, and Decisions API Endpoints"""
from typing import List
import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.db.database import get_db
from app.db.models.user import User
from app.db.repositories.meeting_repo import MeetingRepository
from app.db.repositories.summary_repo import IntelligenceRepository, SummaryRepository
from app.schemas.common import ApiResponse
from app.schemas.summary import MeetingDecisionRead, MeetingSummaryRead, MeetingTopicRead

router = APIRouter(prefix="/meetings", tags=["Meeting Intelligence"])


@router.get(
    "/{meeting_id}/summary",
    response_model=ApiResponse[MeetingSummaryRead],
    summary="Get executive and detailed AI summary for meeting",
)
async def get_summary(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(user_id=current_user.id, entity_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    summary_repo = SummaryRepository(db)
    summary = await summary_repo.get_by_meeting(meeting_id)
    if not summary:
        raise NotFoundException(message="Summary not generated yet for this meeting")

    return ApiResponse.ok(data=MeetingSummaryRead.model_validate(summary))


@router.get(
    "/{meeting_id}/topics",
    response_model=ApiResponse[List[MeetingTopicRead]],
    summary="Get key discussion topics",
)
async def get_topics(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(user_id=current_user.id, entity_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    intel_repo = IntelligenceRepository(db)
    topics = await intel_repo.get_topics(meeting_id)
    return ApiResponse.ok(data=[MeetingTopicRead.model_validate(t) for t in topics])


@router.get(
    "/{meeting_id}/decisions",
    response_model=ApiResponse[List[MeetingDecisionRead]],
    summary="Get explicit decisions reached in the meeting",
)
async def get_decisions(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(user_id=current_user.id, entity_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    intel_repo = IntelligenceRepository(db)
    decisions = await intel_repo.get_decisions(meeting_id)
    return ApiResponse.ok(data=[MeetingDecisionRead.model_validate(d) for d in decisions])
