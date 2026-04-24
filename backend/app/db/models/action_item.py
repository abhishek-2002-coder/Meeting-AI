"""Meeting Action Items Database Model"""
from datetime import date, datetime
from typing import Optional
import uuid
from sqlalchemy import Date, DateTime, Float, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ActionItemStatus:
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

    ALL_STATUSES = [OPEN, IN_PROGRESS, COMPLETED, CANCELLED]


class ActionItemPriority:
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ActionItem(Base, TimestampMixin):
    __tablename__ = "action_items"

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
    source_segment_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transcript_segments.id", ondelete="SET NULL"),
        nullable=True,
    )
    task: Mapped[str] = mapped_column(Text, nullable=False)
    assignee: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    due_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    priority: Mapped[str] = mapped_column(String(50), default=ActionItemPriority.MEDIUM, nullable=False)
    status: Mapped[str] = mapped_column(String(50), default=ActionItemStatus.OPEN, nullable=False, index=True)
    timestamp_seconds: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    meeting = relationship("Meeting", back_populates="action_items")

    __table_args__ = (
        Index("ix_action_items_meeting_status", "meeting_id", "status"),
    )
