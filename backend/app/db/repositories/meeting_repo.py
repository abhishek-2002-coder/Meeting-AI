"""Meeting Repository"""
from datetime import datetime, timezone
from typing import Dict, Optional, Sequence, Tuple
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.action_item import ActionItem, ActionItemStatus
from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.meeting_decision import MeetingDecision
from app.db.models.meeting_file import MeetingFile
from app.db.models.meeting_question import MeetingQuestion
from app.db.models.meeting_risk import MeetingRisk
from app.db.models.meeting_summary import MeetingSummary
from app.db.models.meeting_topic import MeetingTopic
from app.db.models.speaker import Speaker
from app.db.models.transcript_segment import TranscriptSegment
from app.db.repositories.base import BaseUserRepository


class MeetingRepository(BaseUserRepository[Meeting]):
    def __init__(self, session: AsyncSession):
        super().__init__(Meeting, session)

    async def get_with_details(self, user_id: uuid.UUID, meeting_id: uuid.UUID) -> Optional[Meeting]:
        """Fetch meeting with all related intelligence models loaded"""
        stmt = (
            select(Meeting)
            .where(Meeting.user_id == user_id, Meeting.id == meeting_id)
            .options(
                selectinload(Meeting.file),
                selectinload(Meeting.speakers),
                selectinload(Meeting.summary),
                selectinload(Meeting.topics),
                selectinload(Meeting.decisions),
                selectinload(Meeting.action_items),
                selectinload(Meeting.questions),
                selectinload(Meeting.risks),
                selectinload(Meeting.processing_jobs),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def search_and_paginate(
        self,
        user_id: uuid.UUID,
        status: Optional[str] = None,
        search: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> Tuple[Sequence[Meeting], int]:
        base_query = select(Meeting).where(Meeting.user_id == user_id).options(selectinload(Meeting.file))
        count_query = select(func.count(Meeting.id)).where(Meeting.user_id == user_id)

        if status:
            base_query = base_query.where(Meeting.status == status)
            count_query = count_query.where(Meeting.status == status)

        if search:
            pattern = f"%{search.strip()}%"
            filter_cond = or_(Meeting.title.ilike(pattern), Meeting.description.ilike(pattern))
            base_query = base_query.where(filter_cond)
            count_query = count_query.where(filter_cond)

        count_res = await self.session.execute(count_query)
        total = count_res.scalar_one() or 0

        base_query = base_query.order_by(Meeting.created_at.desc()).offset(offset).limit(limit)
        items_res = await self.session.execute(base_query)
        items = items_res.scalars().all()

        return items, total

    async def save_file(
        self,
        meeting_id: uuid.UUID,
        original_filename: str,
        storage_path: str,
        mime_type: str,
        file_size: int,
        checksum: str,
        duration_seconds: Optional[float] = None,
    ) -> MeetingFile:
        file_obj = MeetingFile(
            meeting_id=meeting_id,
            original_filename=original_filename,
            storage_path=storage_path,
            mime_type=mime_type,
            file_size=file_size,
            checksum=checksum,
            duration_seconds=duration_seconds,
        )
        self.session.add(file_obj)
        await self.session.flush()
        return file_obj

    async def get_dashboard_metrics(self, user_id: uuid.UUID) -> Dict[str, int]:
        """Aggregate meeting and action item counts for user dashboard"""
        stmt_meetings = select(
            func.count(Meeting.id).label("total"),
            func.count(Meeting.id).filter(Meeting.status == MeetingStatus.COMPLETED).label("completed"),
            func.count(Meeting.id).filter(
                Meeting.status.in_([MeetingStatus.PROCESSING, MeetingStatus.TRANSCRIBING, MeetingStatus.ANALYZING])
            ).label("processing"),
            func.count(Meeting.id).filter(Meeting.status == MeetingStatus.FAILED).label("failed"),
        ).where(Meeting.user_id == user_id)

        res_meetings = await self.session.execute(stmt_meetings)
        m_row = res_meetings.one()

        # Count action items
        stmt_actions = select(
            func.count(ActionItem.id).label("total_actions"),
            func.count(ActionItem.id).filter(ActionItem.status == ActionItemStatus.OPEN).label("open_actions"),
        ).join(Meeting, ActionItem.meeting_id == Meeting.id).where(Meeting.user_id == user_id)

        res_actions = await self.session.execute(stmt_actions)
        a_row = res_actions.one()

        return {
            "total_meetings": m_row.total or 0,
            "completed_meetings": m_row.completed or 0,
            "processing_meetings": m_row.processing or 0,
            "failed_meetings": m_row.failed or 0,
            "total_action_items": a_row.total_actions or 0,
            "open_action_items": a_row.open_actions or 0,
        }
