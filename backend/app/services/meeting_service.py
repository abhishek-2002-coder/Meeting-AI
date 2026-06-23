"""Meeting Service for CRUD and Intelligence Lookups"""
from typing import List, Optional, Tuple
import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.db.models.action_item import ActionItem
from app.db.models.audit_log import AuditAction
from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.speaker import Speaker
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.meeting_repo import MeetingRepository
from app.db.repositories.processing_job_repo import ProcessingJobRepository
from app.db.repositories.summary_repo import IntelligenceRepository, SummaryRepository
from app.db.repositories.transcript_repo import SpeakerRepository, TranscriptRepository
from app.schemas.action_item import ActionItemCreate, ActionItemUpdate
from app.schemas.meeting import MeetingCounts, MeetingCreate, MeetingDetailRead, MeetingRead, MeetingUpdate
from app.schemas.meeting_file import MeetingFileRead
from app.schemas.speaker import SpeakerRead
from app.schemas.summary import MeetingDecisionRead, MeetingQuestionRead, MeetingRiskRead, MeetingSummaryRead, MeetingTopicRead
from app.schemas.transcript import SegmentMatch, TranscriptResponse, TranscriptSearchResponse, TranscriptSegmentRead
from app.services.storage_service import StorageService


class MeetingService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.meeting_repo = MeetingRepository(db)
        self.transcript_repo = TranscriptRepository(db)
        self.speaker_repo = SpeakerRepository(db)
        self.summary_repo = SummaryRepository(db)
        self.intelligence_repo = IntelligenceRepository(db)
        self.job_repo = ProcessingJobRepository(db)
        self.audit_repo = AuditRepository(db)
        self.storage = StorageService()

    async def create_meeting(self, user_id: uuid.UUID, req: MeetingCreate) -> Meeting:
        meeting = await self.meeting_repo.create(
            user_id=user_id,
            title=req.title,
            description=req.description,
            language=req.language or "en",
            status=MeetingStatus.UPLOADED,
        )
        await self.audit_repo.log_event(
            action=AuditAction.MEETING_CREATED,
            user_id=user_id,
            resource_type="Meeting",
            resource_id=str(meeting.id),
        )
        return meeting

    async def get_meeting_detail(self, user_id: uuid.UUID, meeting_id: uuid.UUID) -> MeetingDetailRead:
        meeting = await self.meeting_repo.get_with_details(user_id=user_id, meeting_id=meeting_id)
        if not meeting:
            raise NotFoundException(message="Meeting not found")

        counts = MeetingCounts(
            transcript_segments_count=len(meeting.transcript_segments) if meeting.transcript_segments else 0,
            action_items_count=len(meeting.action_items) if meeting.action_items else 0,
            decisions_count=len(meeting.decisions) if meeting.decisions else 0,
            topics_count=len(meeting.topics) if meeting.topics else 0,
            questions_count=len(meeting.questions) if meeting.questions else 0,
            risks_count=len(meeting.risks) if meeting.risks else 0,
        )

        return MeetingDetailRead(
            id=meeting.id,
            user_id=meeting.user_id,
            title=meeting.title,
            description=meeting.description,
            status=meeting.status,
            language=meeting.language,
            duration_seconds=meeting.duration_seconds,
            completed_at=meeting.completed_at,
            created_at=meeting.created_at,
            updated_at=meeting.updated_at,
            has_recording=meeting.file is not None,
            counts=counts,
            file=MeetingFileRead.model_validate(meeting.file) if meeting.file else None,
            speakers=[SpeakerRead.model_validate(s) for s in meeting.speakers],
            summary=MeetingSummaryRead.model_validate(meeting.summary) if meeting.summary else None,
            topics=[MeetingTopicRead.model_validate(t) for t in meeting.topics],
            decisions=[MeetingDecisionRead.model_validate(d) for d in meeting.decisions],
            action_items=[ActionItemRead.model_validate(a) for a in meeting.action_items],
            questions=[MeetingQuestionRead.model_validate(q) for q in meeting.questions],
            risks=[MeetingRiskRead.model_validate(r) for r in meeting.risks],
        )

    async def get_transcript(self, user_id: uuid.UUID, meeting_id: uuid.UUID) -> TranscriptResponse:
        meeting = await self.meeting_repo.get_by_id(user_id=user_id, entity_id=meeting_id)
        if not meeting:
            raise NotFoundException(message="Meeting not found")

        segments = await self.transcript_repo.get_segments_by_meeting(meeting_id)
        speakers = await self.speaker_repo.get_speakers_by_meeting(meeting_id)

        segment_reads = []
        for s in segments:
            spk_label = s.speaker.speaker_label if s.speaker else None
            spk_name = s.speaker.display_name if s.speaker else None
            segment_reads.append(
                TranscriptSegmentRead(
                    id=s.id,
                    meeting_id=s.meeting_id,
                    speaker_id=s.speaker_id,
                    speaker_label=spk_label,
                    speaker_name=spk_name,
                    sequence=s.sequence,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    text=s.text,
                    created_at=s.created_at,
                )
            )

        return TranscriptResponse(
            meeting_id=meeting_id,
            segments=segment_reads,
            speakers=[SpeakerRead.model_validate(spk) for spk in speakers],
        )

    async def search_transcript(self, user_id: uuid.UUID, meeting_id: uuid.UUID, query: str) -> TranscriptSearchResponse:
        meeting = await self.meeting_repo.get_by_id(user_id=user_id, entity_id=meeting_id)
        if not meeting:
            raise NotFoundException(message="Meeting not found")

        segments = await self.transcript_repo.search_in_meeting(meeting_id, query)
        matches = []
        for s in segments:
            speaker_name = s.speaker.display_name if s.speaker else "Speaker"
            highlight = s.text.replace(query, f"**{query}**")
            matches.append(
                SegmentMatch(
                    segment_id=s.id,
                    start_time=s.start_time,
                    end_time=s.end_time,
                    speaker_name=speaker_name,
                    text=s.text,
                    highlight=highlight,
                )
            )

        return TranscriptSearchResponse(
            meeting_id=meeting_id,
            query=query,
            matches=matches,
            total_matches=len(matches),
        )

    async def rename_speaker(self, user_id: uuid.UUID, meeting_id: uuid.UUID, speaker_id: uuid.UUID, new_name: str) -> Speaker:
        meeting = await self.meeting_repo.get_by_id(user_id=user_id, entity_id=meeting_id)
        if not meeting:
            raise NotFoundException(message="Meeting not found")

        spk = await self.speaker_repo.update_display_name(speaker_id=speaker_id, display_name=new_name)
        if not spk:
            raise NotFoundException(message="Speaker not found")

        await self.audit_repo.log_event(
            action=AuditAction.SPEAKER_RENAMED,
            user_id=user_id,
            resource_type="Speaker",
            resource_id=str(speaker_id),
            metadata_json={"new_name": new_name},
        )
        return spk

    async def delete_meeting(self, user_id: uuid.UUID, meeting_id: uuid.UUID) -> bool:
        meeting = await self.meeting_repo.get_with_details(user_id=user_id, meeting_id=meeting_id)
        if not meeting:
            raise NotFoundException(message="Meeting not found")

        # Delete physical file
        if meeting.file:
            self.storage.delete_file(meeting.file.storage_path)

        deleted = await self.meeting_repo.delete(user_id=user_id, entity_id=meeting_id)
        if deleted:
            await self.audit_repo.log_event(
                action=AuditAction.MEETING_DELETED,
                user_id=user_id,
                resource_type="Meeting",
                resource_id=str(meeting_id),
            )
        return deleted
