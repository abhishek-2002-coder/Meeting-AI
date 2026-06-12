"""Processing Job Repository"""
from datetime import datetime, timezone
from typing import Optional, Sequence
import uuid
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.processing_job import JobStatus, JobType, ProcessingJob


class ProcessingJobRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_meeting(self, meeting_id: uuid.UUID) -> Sequence[ProcessingJob]:
        stmt = (
            select(ProcessingJob)
            .where(ProcessingJob.meeting_id == meeting_id)
            .order_by(ProcessingJob.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def init_pipeline_jobs(self, meeting_id: uuid.UUID) -> Sequence[ProcessingJob]:
        """Initializes all standard pipeline stages in PENDING state"""
        # Remove any previous jobs for meeting
        await self.session.execute(delete(ProcessingJob).where(ProcessingJob.meeting_id == meeting_id))
        
        stages = [
            JobType.AUDIO_PROCESSING,
            JobType.TRANSCRIPTION,
            JobType.DIARIZATION,
            JobType.SUMMARY,
            JobType.ACTION_EXTRACTION,
            JobType.TOPIC_EXTRACTION,
            JobType.FINALIZATION,
        ]
        jobs = [
            ProcessingJob(
                meeting_id=meeting_id,
                job_type=stage,
                status=JobStatus.PENDING,
                progress=0,
            )
            for stage in stages
        ]
        self.session.add_all(jobs)
        await self.session.flush()
        return jobs

    async def update_job_status(
        self,
        meeting_id: uuid.UUID,
        job_type: str,
        status: str,
        progress: int = 0,
        error_message: Optional[str] = None,
    ) -> Optional[ProcessingJob]:
        stmt = select(ProcessingJob).where(
            ProcessingJob.meeting_id == meeting_id,
            ProcessingJob.job_type == job_type,
        )
        result = await self.session.execute(stmt)
        job = result.scalar_one_or_none()
        if not job:
            return None

        job.status = status
        job.progress = progress
        job.error_message = error_message
        if status == JobStatus.RUNNING and not job.started_at:
            job.started_at = datetime.now(timezone.utc)
        elif status in (JobStatus.COMPLETED, JobStatus.FAILED):
            job.completed_at = datetime.now(timezone.utc)

        await self.session.flush()
        return job
