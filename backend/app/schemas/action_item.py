"""Action Item Schemas"""
from datetime import date, datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.db.models.action_item import ActionItemPriority, ActionItemStatus


class ActionItemBase(BaseModel):
    task: str = Field(..., min_length=1)
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    priority: str = Field(default=ActionItemPriority.MEDIUM)
    status: str = Field(default=ActionItemStatus.OPEN)
    timestamp_seconds: Optional[float] = None


class ActionItemCreate(ActionItemBase):
    pass


class ActionItemUpdate(BaseModel):
    task: Optional[str] = None
    assignee: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    timestamp_seconds: Optional[float] = None


class ActionItemRead(ActionItemBase):
    id: uuid.UUID
    meeting_id: uuid.UUID
    source_segment_id: Optional[uuid.UUID] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
