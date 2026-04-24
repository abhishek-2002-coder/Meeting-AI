"""Meeting Speaker Database Model"""
from datetime import datetime, timezone
import uuid
from sqlalchemy import DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Speaker(Base):
    __tablename__ = "meeting_speakers"

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
    speaker_label: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g. "Speaker 1"
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)   # e.g. "Abhishek"
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    meeting = relationship("Meeting", back_populates="speakers")
    segments = relationship("TranscriptSegment", back_populates="speaker")

    __table_args__ = (
        Index("ix_meeting_speaker_label", "meeting_id", "speaker_label", unique=True),
    )
