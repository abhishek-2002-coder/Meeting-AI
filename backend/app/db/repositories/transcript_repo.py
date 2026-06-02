"""Transcript Segment and Speaker Repositories"""
from typing import List, Optional, Sequence
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.speaker import Speaker
from app.db.models.transcript_segment import TranscriptSegment


class TranscriptRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_segments_by_meeting(self, meeting_id: uuid.UUID) -> Sequence[TranscriptSegment]:
        stmt = (
            select(TranscriptSegment)
            .where(TranscriptSegment.meeting_id == meeting_id)
            .options(selectinload(TranscriptSegment.speaker))
            .order_by(TranscriptSegment.sequence.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def add_segments_batch(self, segments: List[TranscriptSegment]) -> None:
        self.session.add_all(segments)
        await self.session.flush()

    async def search_in_meeting(self, meeting_id: uuid.UUID, query: str) -> Sequence[TranscriptSegment]:
        pattern = f"%{query.strip()}%"
        stmt = (
            select(TranscriptSegment)
            .where(
                TranscriptSegment.meeting_id == meeting_id,
                TranscriptSegment.text.ilike(pattern),
            )
            .options(selectinload(TranscriptSegment.speaker))
            .order_by(TranscriptSegment.start_time.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class SpeakerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, speaker_id: uuid.UUID) -> Optional[Speaker]:
        stmt = select(Speaker).where(Speaker.id == speaker_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_speakers_by_meeting(self, meeting_id: uuid.UUID) -> Sequence[Speaker]:
        stmt = select(Speaker).where(Speaker.id == meeting_id).order_by(Speaker.speaker_label.asc())
        result = await self.session.execute(select(Speaker).where(Speaker.meeting_id == meeting_id))
        return result.scalars().all()

    async def get_or_create(self, meeting_id: uuid.UUID, speaker_label: str, display_name: Optional[str] = None) -> Speaker:
        stmt = select(Speaker).where(
            Speaker.meeting_id == meeting_id,
            Speaker.speaker_label == speaker_label,
        )
        result = await self.session.execute(stmt)
        existing = result.scalar_one_or_none()
        if existing:
            return existing

        name = display_name or speaker_label
        speaker = Speaker(
            meeting_id=meeting_id,
            speaker_label=speaker_label,
            display_name=name,
        )
        self.session.add(speaker)
        await self.session.flush()
        await self.session.refresh(speaker)
        return speaker

    async def update_display_name(self, speaker_id: uuid.UUID, display_name: str) -> Optional[Speaker]:
        speaker = await self.get_by_id(speaker_id)
        if not speaker:
            return None
        speaker.display_name = display_name.strip()
        await self.session.flush()
        return speaker
