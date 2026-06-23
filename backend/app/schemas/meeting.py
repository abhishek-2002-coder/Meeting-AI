"""Meeting Management Schemas"""
from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.schemas.action_item import ActionItemRead
from app.schemas.meeting_file import MeetingFileRead
from app.schemas.speaker import SpeakerRead
from app.schemas.summary import MeetingDecisionRead, MeetingQuestionRead, MeetingRiskRead, MeetingSummaryRead, MeetingTopicRead


class MeetingBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    language: str = Field(default="en", max_length=20)


class MeetingCreate(MeetingBase):
    pass


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    language: Optional[str] = None


class MeetingCounts(BaseModel):
    transcript_segments_count: int = 0
    action_items_count: int = 0
    decisions_count: int = 0
    topics_count: int = 0
    questions_count: int = 0
    risks_count: int = 0


class MeetingRead(MeetingBase):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str
    duration_seconds: Optional[float] = 0.0
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    has_recording: bool = False
    counts: Optional[MeetingCounts] = None

    model_config = ConfigDict(from_attributes=True)


class MeetingDetailRead(MeetingRead):
    file: Optional[MeetingFileRead] = None
    speakers: List[SpeakerRead] = Field(default_factory=list)
    summary: Optional[MeetingSummaryRead] = None
    topics: List[MeetingTopicRead] = Field(default_factory=list)
    decisions: List[MeetingDecisionRead] = Field(default_factory=list)
    action_items: List[ActionItemRead] = Field(default_factory=list)
    questions: List[MeetingQuestionRead] = Field(default_factory=list)
    risks: List[MeetingRiskRead] = Field(default_factory=list)


class DashboardStats(BaseModel):
    total_meetings: int
    completed_meetings: int
    processing_meetings: int
    failed_meetings: int
    total_action_items: int
    open_action_items: int
    recent_meetings: List[MeetingRead] = Field(default_factory=list)
