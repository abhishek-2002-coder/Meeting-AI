"""Meeting Summary, Topics, Decisions, Questions, and Risks Schemas"""
from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


class MeetingSummaryRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    short_summary: str
    detailed_summary: str
    model_provider: str
    model_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingTopicRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    title: str
    description: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingDecisionRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    source_segment_id: Optional[uuid.UUID] = None
    decision: str
    context: Optional[str] = None
    timestamp_seconds: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingQuestionRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    question: str
    context: Optional[str] = None
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MeetingRiskRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    risk: str
    impact: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
