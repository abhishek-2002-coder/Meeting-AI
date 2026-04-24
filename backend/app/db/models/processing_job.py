"""Processing Jobs Database Model"""
from datetime import datetime, timezone
from typing import Optional
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class JobType:
    AUDIO_PROCESSING = "AUDIO_PROCESSING"
    TRANSCRIPTION = "TRANSCRIPTION"
    DIARIZATION = "DIARIZATION"
    SUMMARY = "SUMMARY"
    ACTION_EXTRACTION = "ACTION_EXTRACTION"
    TOPIC_EXTRACTION = "TOPIC_EXTRACTION"
    FINALIZATION = "FINALIZATION"

    ALL_TYPES = [
        AUDIO_PROCESSING,
        TRANSCRIPTION,
        DIARIZATION,
        SUMMARY,
        ACTION_EXTRACTION,
        TOPIC_EXTRACTION,
        FINALIZATION,
    ]


class JobStatus:
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class ProcessingJob(Base):
    __tablename__ = "processing_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    meeting_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=JobStatus.PENDING, nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    meeting = relationship("Meeting", back_populates="processing_jobs")

    __table_args__ = (
        Index("ix_processing_meeting_type", "meeting_id", "job_type"),
    )
