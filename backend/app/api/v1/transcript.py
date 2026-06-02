"""Transcript and Speaker API Endpoints"""
from typing import Optional
import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.database import get_db
from app.db.models.user import User
from app.schemas.common import ApiResponse
from app.schemas.speaker import SpeakerRead, SpeakerUpdate
from app.schemas.transcript import TranscriptResponse, TranscriptSearchResponse
from app.services.meeting_service import MeetingService

router = APIRouter(prefix="/meetings", tags=["Transcript & Speakers"])


@router.get(
    "/{meeting_id}/transcript",
    response_model=ApiResponse[TranscriptResponse],
    summary="Get complete structured transcript with speaker mappings",
)
async def get_transcript(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MeetingService(db)
    transcript = await service.get_transcript(user_id=current_user.id, meeting_id=meeting_id)
    return ApiResponse.ok(data=transcript)


@router.get(
    "/{meeting_id}/transcript/search",
    response_model=ApiResponse[TranscriptSearchResponse],
    summary="Search within the transcript of a specific meeting",
)
async def search_transcript(
    meeting_id: uuid.UUID,
    q: str = Query(..., min_length=1, description="Search query"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MeetingService(db)
    results = await service.search_transcript(user_id=current_user.id, meeting_id=meeting_id, query=q)
    return ApiResponse.ok(data=results)


@router.put(
    "/{meeting_id}/speakers/{speaker_id}",
    response_model=ApiResponse[SpeakerRead],
    summary="Rename a speaker label (e.g. Speaker 1 -> Abhishek)",
)
async def rename_speaker(
    meeting_id: uuid.UUID,
    speaker_id: uuid.UUID,
    req: SpeakerUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = MeetingService(db)
    speaker = await service.rename_speaker(
        user_id=current_user.id,
        meeting_id=meeting_id,
        speaker_id=speaker_id,
        new_name=req.display_name,
    )
    return ApiResponse.ok(data=SpeakerRead.model_validate(speaker), message="Speaker updated successfully")
