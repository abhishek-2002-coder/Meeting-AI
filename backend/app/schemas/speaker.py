"""Meeting File and Speaker Schemas"""
from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class MeetingFileRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    original_filename: str
    mime_type: str
    file_size: int
    checksum: str
    duration_seconds: Optional[float] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpeakerRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    speaker_label: str
    display_name: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SpeakerUpdate(BaseModel):
    display_name: str = Field(..., min_length=1, max_length=255)
