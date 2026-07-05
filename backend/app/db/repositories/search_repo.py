"""Search and Audit Repositories"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.action_item import ActionItem
from app.db.models.audit_log import AuditLog
from app.db.models.meeting import Meeting
from app.db.models.meeting_decision import MeetingDecision
from app.db.models.meeting_summary import MeetingSummary
from app.db.models.meeting_topic import MeetingTopic
from app.db.models.transcript_segment import TranscriptSegment
from app.schemas.search import SearchMeetingResult


class SearchRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def search_meetings(self, user_id: uuid.UUID, query: str, limit: int = 50) -> List[SearchMeetingResult]:
        pattern = f"%{query.strip()}%"
        results: List[SearchMeetingResult] = []
        seen_keys = set()

        # 1. Search in Meeting Title / Description
        stmt_meetings = select(Meeting).where(
            Meeting.user_id == user_id,
            (Meeting.title.ilike(pattern) | Meeting.description.ilike(pattern)),
        ).limit(limit)
        res_meetings = await self.session.execute(stmt_meetings)
        for m in res_meetings.scalars().all():
            k = (m.id, "title")
            if k not in seen_keys:
                seen_keys.add(k)
                results.append(
                    SearchMeetingResult(
                        meeting_id=m.id,
                        title=m.title,
                        description=m.description,
                        created_at=m.created_at,
                        match_type="title",
                        snippet=m.title if query.lower() in m.title.lower() else (m.description or m.title),
                    )
                )

        # 2. Search in Transcript Segments
        stmt_segments = (
            select(TranscriptSegment, Meeting)
            .join(Meeting, TranscriptSegment.meeting_id == Meeting.id)
            .where(Meeting.user_id == user_id, TranscriptSegment.text.ilike(pattern))
            .limit(limit)
        )
        res_segments = await self.session.execute(stmt_segments)
        for seg, m in res_segments.all():
            results.append(
                SearchMeetingResult(
                    meeting_id=m.id,
                    title=m.title,
                    description=m.description,
                    created_at=m.created_at,
                    match_type="transcript",
                    snippet=seg.text,
                    timestamp_seconds=seg.start_time,
                )
            )

        # 3. Search in Summaries
        stmt_summaries = (
            select(MeetingSummary, Meeting)
            .join(Meeting, MeetingSummary.meeting_id == Meeting.id)
            .where(
                Meeting.user_id == user_id,
                (MeetingSummary.short_summary.ilike(pattern) | MeetingSummary.detailed_summary.ilike(pattern)),
            )
            .limit(limit)
        )
        res_summaries = await self.session.execute(stmt_summaries)
        for summ, m in res_summaries.all():
            results.append(
                SearchMeetingResult(
                    meeting_id=m.id,
                    title=m.title,
                    description=m.description,
                    created_at=m.created_at,
                    match_type="summary",
                    snippet=summ.short_summary,
                )
            )

        # 4. Search in Decisions & Action Items
        stmt_decisions = (
            select(MeetingDecision, Meeting)
            .join(Meeting, MeetingDecision.meeting_id == Meeting.id)
            .where(
                Meeting.user_id == user_id,
                (MeetingDecision.decision.ilike(pattern) | MeetingDecision.context.ilike(pattern)),
            )
            .limit(limit)
        )
        res_decisions = await self.session.execute(stmt_decisions)
        for dec, m in res_decisions.all():
            results.append(
                SearchMeetingResult(
                    meeting_id=m.id,
                    title=m.title,
                    description=m.description,
                    created_at=m.created_at,
                    match_type="decision",
                    snippet=dec.decision,
                    timestamp_seconds=dec.timestamp_seconds,
                )
            )

        stmt_actions = (
            select(ActionItem, Meeting)
            .join(Meeting, ActionItem.meeting_id == Meeting.id)
            .where(
                Meeting.user_id == user_id,
                (ActionItem.task.ilike(pattern) | ActionItem.assignee.ilike(pattern)),
            )
            .limit(limit)
        )
        res_actions = await self.session.execute(stmt_actions)
        for act, m in res_actions.all():
            results.append(
                SearchMeetingResult(
                    meeting_id=m.id,
                    title=m.title,
                    description=m.description,
                    created_at=m.created_at,
                    match_type="action_item",
                    snippet=f"{act.task} ({act.assignee or 'Unassigned'})",
                    timestamp_seconds=act.timestamp_seconds,
                )
            )

        return results


class AuditRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def log_event(
        self,
        action: str,
        user_id: Optional[uuid.UUID] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> AuditLog:
        audit = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            metadata_json=metadata_json or {},
            ip_address=ip_address,
        )
        self.session.add(audit)
        await self.session.flush()
        return audit
