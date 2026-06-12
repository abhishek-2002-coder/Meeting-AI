"""Meeting Processing Pipeline API Endpoints"""
import uuid
from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.db.database import async_session_maker, get_db
from app.db.models.user import User
from app.db.repositories.meeting_repo import MeetingRepository
from app.db.repositories.processing_job_repo import ProcessingJobRepository
from app.schemas.common import ApiResponse
from app.schemas.processing_job import ProcessingJobRead, ProcessingStatusResponse
from app.services.pipeline_service import PipelineService

router = APIRouter(prefix="/meetings", tags=["Processing Pipeline"])


async def run_background_pipeline(user_id: uuid.UUID, meeting_id: uuid.UUID):
    """Background task runner providing isolated DB session"""
    async with async_session_maker() as session:
        try:
            pipeline = PipelineService(session)
            await pipeline.execute_pipeline(user_id=user_id, meeting_id=meeting_id)
            await session.commit()
        except Exception:
            await session.rollback()


@router.post(
    "/{meeting_id}/process",
    response_model=ApiResponse[dict],
    summary="Trigger the multi-stage AI intelligence processing pipeline",
)
async def start_processing(
    meeting_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_with_details(user_id=current_user.id, meeting_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    if not meeting.file:
        raise NotFoundException(message="Please upload a recording file before processing.")

    # Enqueue background task
    background_tasks.add_task(run_background_pipeline, current_user.id, meeting_id)

    return ApiResponse.ok(
        data={"meeting_id": meeting_id, "status": "PROCESSING"},
        message="Meeting processing pipeline started in background.",
    )


@router.get(
    "/{meeting_id}/processing-status",
    response_model=ApiResponse[ProcessingStatusResponse],
    summary="Get real-time status of pipeline jobs and progress percentage",
)
async def get_processing_status(
    meeting_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(user_id=current_user.id, entity_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    job_repo = ProcessingJobRepository(db)
    jobs = await job_repo.get_by_meeting(meeting_id)

    job_reads = [ProcessingJobRead.model_validate(j) for j in jobs]
    total_progress = sum([j.progress for j in jobs]) // len(jobs) if jobs else (100 if meeting.status == "COMPLETED" else 0)

    data = ProcessingStatusResponse(
        meeting_id=meeting_id,
        status=meeting.status,
        overall_progress=total_progress,
        jobs=job_reads,
    )
    return ApiResponse.ok(data=data)
