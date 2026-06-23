"""Intelligence Repositories: Summaries, Topics, Decisions, Action Items, Questions, Risks"""
from typing import List, Optional, Sequence
import uuid
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.action_item import ActionItem
from app.db.models.meeting_decision import MeetingDecision
from app.db.models.meeting_question import MeetingQuestion
from app.db.models.meeting_risk import MeetingRisk
from app.db.models.meeting_summary import MeetingSummary
from app.db.models.meeting_topic import MeetingTopic


class SummaryRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_meeting(self, meeting_id: uuid.UUID) -> Optional[MeetingSummary]:
        stmt = select(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def save_summary(
        self,
        meeting_id: uuid.UUID,
        short_summary: str,
        detailed_summary: str,
        model_provider: str,
        model_name: str,
    ) -> MeetingSummary:
        # Delete existing if updating
        await self.session.execute(delete(MeetingSummary).where(MeetingSummary.meeting_id == meeting_id))
        summary = MeetingSummary(
            meeting_id=meeting_id,
            short_summary=short_summary,
            detailed_summary=detailed_summary,
            model_provider=model_provider,
            model_name=model_name,
        )
        self.session.add(summary)
        await self.session.flush()
        return summary


class IntelligenceRepository:
    """Repository handling Topics, Decisions, Questions, and Risks"""
    def __init__(self, session: AsyncSession):
        self.session = session

    async def save_intelligence_batch(
        self,
        meeting_id: uuid.UUID,
        topics: List[MeetingTopic],
        decisions: List[MeetingDecision],
        action_items: List[ActionItem],
        questions: List[MeetingQuestion],
        risks: List[MeetingRisk],
    ) -> None:
        # Clear previous extractions for idempotency
        await self.session.execute(delete(MeetingTopic).where(MeetingTopic.meeting_id == meeting_id))
        await self.session.execute(delete(MeetingDecision).where(MeetingDecision.meeting_id == meeting_id))
        await self.session.execute(delete(ActionItem).where(ActionItem.meeting_id == meeting_id))
        await self.session.execute(delete(MeetingQuestion).where(MeetingQuestion.meeting_id == meeting_id))
        await self.session.execute(delete(MeetingRisk).where(MeetingRisk.meeting_id == meeting_id))

        self.session.add_all(topics)
        self.session.add_all(decisions)
        self.session.add_all(action_items)
        self.session.add_all(questions)
        self.session.add_all(risks)
        await self.session.flush()

    async def get_topics(self, meeting_id: uuid.UUID) -> Sequence[MeetingTopic]:
        stmt = select(MeetingTopic).where(MeetingTopic.meeting_id == meeting_id)
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_decisions(self, meeting_id: uuid.UUID) -> Sequence[MeetingDecision]:
        stmt = select(MeetingDecision).where(MeetingDecision.meeting_id == meeting_id).order_by(MeetingDecision.timestamp_seconds.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def get_action_items(
        self,
        meeting_id: uuid.UUID,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
    ) -> Sequence[ActionItem]:
        stmt = select(ActionItem).where(ActionItem.meeting_id == meeting_id)
        if status:
            stmt = stmt.where(ActionItem.status == status)
        if assignee:
            stmt = stmt.where(ActionItem.assignee.ilike(f"%{assignee.strip()}%"))
        stmt = stmt.order_by(ActionItem.created_at.asc())
        res = await self.session.execute(stmt)
        return res.scalars().all()

    async def create_action_item(self, meeting_id: uuid.UUID, **kwargs) -> ActionItem:
        item = ActionItem(meeting_id=meeting_id, **kwargs)
        self.session.add(item)
        await self.session.flush()
        await self.session.refresh(item)
        return item

    async def update_action_item(self, action_item_id: uuid.UUID, **kwargs) -> Optional[ActionItem]:
        stmt = (
            update(ActionItem)
            .where(ActionItem.id == action_item_id)
            .values(**kwargs)
            .returning(ActionItem)
        )
        res = await self.session.execute(stmt)
        return res.scalar_one_or_none()

    async def delete_action_item(self, action_item_id: uuid.UUID) -> bool:
        stmt = delete(ActionItem).where(ActionItem.id == action_item_id)
        res = await self.session.execute(stmt)
        return (res.rowcount or 0) > 0
