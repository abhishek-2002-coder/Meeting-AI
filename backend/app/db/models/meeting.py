"""Meeting Database Model"""
from datetime import datetime
from typing import Optional
import uuid
from sqlalchemy import DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class MeetingStatus:
    UPLOADED = "UPLOADED"
    PROCESSING = "PROCESSING"
    TRANSCRIBING = "TRANSCRIBING"
    ANALYZING = "ANALYZING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"

    ALL_STATUSES = [UPLOADED, PROCESSING, TRANSCRIBING, ANALYZING, COMPLETED, FAILED]


class Meeting(Base, TimestampMixin):
    __tablename__ = "meetings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(50), default=MeetingStatus.UPLOADED, nullable=False, index=True
    )
    language: Mapped[str] = mapped_column(String(20), default="en", nullable=False)
    duration_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True, default=0.0)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", back_populates="meetings")
    file = relationship("MeetingFile", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    speakers = relationship("Speaker", back_populates="meeting", cascade="all, delete-orphan")
    transcript_segments = relationship("TranscriptSegment", back_populates="meeting", cascade="all, delete-orphan", order_by="TranscriptSegment.sequence")
    summary = relationship("MeetingSummary", back_populates="meeting", uselist=False, cascade="all, delete-orphan")
    topics = relationship("MeetingTopic", back_populates="meeting", cascade="all, delete-orphan")
    decisions = relationship("MeetingDecision", back_populates="meeting", cascade="all, delete-orphan")
    action_items = relationship("ActionItem", back_populates="meeting", cascade="all, delete-orphan")
    questions = relationship("MeetingQuestion", back_populates="meeting", cascade="all, delete-orphan")
    risks = relationship("MeetingRisk", back_populates="meeting", cascade="all, delete-orphan")
    processing_jobs = relationship("ProcessingJob", back_populates="meeting", cascade="all, delete-orphan", order_by="ProcessingJob.created_at")

    __table_args__ = (
        Index("ix_meetings_user_created", "user_id", "created_at"),
    )
