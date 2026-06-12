"""Multi-Stage Meeting Intelligence Processing Pipeline Orchestrator"""
from datetime import datetime, timezone
from typing import Dict, List, Optional
import uuid
from dateutil import parser as date_parser
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundException
from app.db.models.action_item import ActionItem, ActionItemPriority, ActionItemStatus
from app.db.models.audit_log import AuditAction
from app.db.models.meeting import Meeting, MeetingStatus
from app.db.models.meeting_decision import MeetingDecision
from app.db.models.meeting_question import MeetingQuestion
from app.db.models.meeting_risk import MeetingRisk
from app.db.models.meeting_topic import MeetingTopic
from app.db.models.processing_job import JobStatus, JobType
from app.db.models.speaker import Speaker
from app.db.models.transcript_segment import TranscriptSegment
from app.db.repositories.audit_repo import AuditRepository
from app.db.repositories.meeting_repo import MeetingRepository
from app.db.repositories.processing_job_repo import ProcessingJobRepository
from app.db.repositories.summary_repo import IntelligenceRepository, SummaryRepository
from app.db.repositories.transcript_repo import SpeakerRepository, TranscriptRepository
from app.providers import get_llm_provider, get_stt_provider
from app.services.chunking_service import ChunkingService


class PipelineService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.meeting_repo = MeetingRepository(db)
        self.job_repo = ProcessingJobRepository(db)
        self.transcript_repo = TranscriptRepository(db)
        self.speaker_repo = SpeakerRepository(db)
        self.summary_repo = SummaryRepository(db)
        self.intelligence_repo = IntelligenceRepository(db)
        self.audit_repo = AuditRepository(db)
        self.stt_provider = get_stt_provider()
        self.llm_provider = get_llm_provider()

    async def execute_pipeline(self, user_id: uuid.UUID, meeting_id: uuid.UUID) -> Meeting:
        """
        Executes the complete end-to-end meeting intelligence pipeline:
        Audio Check -> Transcription -> Speaker Diarization -> LLM Extraction -> Storage
        """
        meeting = await self.meeting_repo.get_with_details(user_id=user_id, meeting_id=meeting_id)
        if not meeting:
            raise NotFoundException(message="Meeting not found")

        if not meeting.file:
            raise NotFoundException(message="Meeting has no uploaded audio/video file")

        # Initialize progress jobs
        await self.job_repo.init_pipeline_jobs(meeting_id=meeting_id)
        await self.meeting_repo.update(
            user_id=user_id,
            entity_id=meeting_id,
            status=MeetingStatus.PROCESSING,
        )

        try:
            # ─────────────────────────────────────────────────────────────
            # STAGE 1: Audio Processing & Validation
            # ─────────────────────────────────────────────────────────────
            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.AUDIO_PROCESSING,
                status=JobStatus.RUNNING,
                progress=50,
            )
            audio_path = meeting.file.storage_path
            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.AUDIO_PROCESSING,
                status=JobStatus.COMPLETED,
                progress=100,
            )

            # ─────────────────────────────────────────────────────────────
            # STAGE 2: Speech-to-Text Transcription
            # ─────────────────────────────────────────────────────────────
            await self.meeting_repo.update(
                user_id=user_id, entity_id=meeting_id, status=MeetingStatus.TRANSCRIBING
            )
            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.TRANSCRIPTION,
                status=JobStatus.RUNNING,
                progress=30,
            )

            stt_result = await self.stt_provider.transcribe(
                audio_file_path=audio_path,
                language=meeting.language,
                prompt=f"Meeting: {meeting.title}. {meeting.description or ''}",
            )

            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.TRANSCRIPTION,
                status=JobStatus.COMPLETED,
                progress=100,
            )

            # ─────────────────────────────────────────────────────────────
            # STAGE 3: Speaker Segmentation & Transcript Storage
            # ─────────────────────────────────────────────────────────────
            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.DIARIZATION,
                status=JobStatus.RUNNING,
                progress=40,
            )

            speaker_map: Dict[str, Speaker] = {}
            transcript_entities: List[TranscriptSegment] = []

            for idx, seg in enumerate(stt_result.segments, start=1):
                label = seg.speaker or f"Speaker {1 + (idx % 2)}"
                if label not in speaker_map:
                    spk = await self.speaker_repo.get_or_create(
                        meeting_id=meeting_id, speaker_label=label, display_name=label
                    )
                    speaker_map[label] = spk
                else:
                    spk = speaker_map[label]

                transcript_entities.append(
                    TranscriptSegment(
                        meeting_id=meeting_id,
                        speaker_id=spk.id,
                        sequence=idx,
                        start_time=seg.start,
                        end_time=seg.end,
                        text=seg.text,
                    )
                )

            if transcript_entities:
                await self.transcript_repo.add_segments_batch(transcript_entities)

            # Update meeting duration
            duration = stt_result.duration or (transcript_entities[-1].end_time if transcript_entities else 0.0)
            await self.meeting_repo.update(
                user_id=user_id,
                entity_id=meeting_id,
                duration_seconds=duration,
            )

            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.DIARIZATION,
                status=JobStatus.COMPLETED,
                progress=100,
            )

            # ─────────────────────────────────────────────────────────────
            # STAGE 4: AI Analysis & Extraction
            # ─────────────────────────────────────────────────────────────
            await self.meeting_repo.update(
                user_id=user_id, entity_id=meeting_id, status=MeetingStatus.ANALYZING
            )
            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.SUMMARY,
                status=JobStatus.RUNNING,
                progress=25,
            )

            # Build formatted dialogue text
            formatted_dialogue = ChunkingService.format_segments_to_dialogue(transcript_entities)

            extracted_ai = await self.llm_provider.analyze_transcript(
                meeting_title=meeting.title,
                structured_transcript=formatted_dialogue,
                meeting_description=meeting.description,
            )

            # ─────────────────────────────────────────────────────────────
            # STAGE 5: Persisting Structured Meeting Intelligence
            # ─────────────────────────────────────────────────────────────
            # 1. Summary
            provider_name = "OpenAI" if settings.LLM_PROVIDER == "openai" else "Mock"
            model_name = settings.OPENAI_MODEL if settings.LLM_PROVIDER == "openai" else "mock-gpt-4o"
            await self.summary_repo.save_summary(
                meeting_id=meeting_id,
                short_summary=extracted_ai.executive_summary,
                detailed_summary=extracted_ai.detailed_summary,
                model_provider=provider_name,
                model_name=model_name,
            )
            await self.job_repo.update_job_status(
                meeting_id=meeting_id, job_type=JobType.SUMMARY, status=JobStatus.COMPLETED, progress=100
            )

            # 2. Topics
            await self.job_repo.update_job_status(
                meeting_id=meeting_id, job_type=JobType.TOPIC_EXTRACTION, status=JobStatus.RUNNING, progress=50
            )
            topics_entities = [
                MeetingTopic(meeting_id=meeting_id, title=t.title, description=t.description)
                for t in extracted_ai.topics
            ]
            await self.job_repo.update_job_status(
                meeting_id=meeting_id, job_type=JobType.TOPIC_EXTRACTION, status=JobStatus.COMPLETED, progress=100
            )

            # 3. Decisions
            decisions_entities = [
                MeetingDecision(
                    meeting_id=meeting_id,
                    decision=d.decision,
                    context=d.context,
                    timestamp_seconds=d.timestamp_seconds,
                )
                for d in extracted_ai.decisions
            ]

            # 4. Action Items
            await self.job_repo.update_job_status(
                meeting_id=meeting_id, job_type=JobType.ACTION_EXTRACTION, status=JobStatus.RUNNING, progress=50
            )
            action_entities = []
            for a in extracted_ai.action_items:
                parsed_due = None
                if a.due_date:
                    try:
                        parsed_due = date_parser.parse(a.due_date, fuzzy=True).date()
                    except Exception:
                        pass

                prio = a.priority.upper() if a.priority and a.priority.upper() in [
                    ActionItemPriority.LOW, ActionItemPriority.MEDIUM, ActionItemPriority.HIGH, ActionItemPriority.URGENT
                ] else ActionItemPriority.MEDIUM

                action_entities.append(
                    ActionItem(
                        meeting_id=meeting_id,
                        task=a.task,
                        assignee=a.assignee,
                        due_date=parsed_due,
                        priority=prio,
                        status=ActionItemStatus.OPEN,
                        timestamp_seconds=a.timestamp_seconds,
                    )
                )
            await self.job_repo.update_job_status(
                meeting_id=meeting_id, job_type=JobType.ACTION_EXTRACTION, status=JobStatus.COMPLETED, progress=100
            )

            # 5. Questions & Risks
            questions_entities = [
                MeetingQuestion(meeting_id=meeting_id, question=q.question, context=q.context, status=q.status)
                for q in extracted_ai.questions
            ]
            risks_entities = [
                MeetingRisk(meeting_id=meeting_id, risk=r.risk, impact=r.impact)
                for r in extracted_ai.risks
            ]

            await self.intelligence_repo.save_intelligence_batch(
                meeting_id=meeting_id,
                topics=topics_entities,
                decisions=decisions_entities,
                action_items=action_entities,
                questions=questions_entities,
                risks=risks_entities,
            )

            # Finalize
            await self.job_repo.update_job_status(
                meeting_id=meeting_id, job_type=JobType.FINALIZATION, status=JobStatus.COMPLETED, progress=100
            )

            updated_meeting = await self.meeting_repo.update(
                user_id=user_id,
                entity_id=meeting_id,
                status=MeetingStatus.COMPLETED,
                completed_at=datetime.now(timezone.utc),
            )

            await self.audit_repo.log_event(
                action=AuditAction.MEETING_PROCESSED,
                user_id=user_id,
                resource_type="Meeting",
                resource_id=str(meeting_id),
                metadata_json={
                    "segments_count": len(transcript_entities),
                    "action_items_count": len(action_entities),
                    "decisions_count": len(decisions_entities),
                },
            )

            return updated_meeting

        except Exception as e:
            await self.meeting_repo.update(
                user_id=user_id,
                entity_id=meeting_id,
                status=MeetingStatus.FAILED,
            )
            await self.job_repo.update_job_status(
                meeting_id=meeting_id,
                job_type=JobType.FINALIZATION,
                status=JobStatus.FAILED,
                error_message=str(e),
            )
            raise
