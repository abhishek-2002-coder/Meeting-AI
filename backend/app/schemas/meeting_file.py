"""Meeting File Schemas"""
from datetime import datetime
from typing import Optional
import uuid
from pydantic import BaseModel, ConfigDict


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


class UploadResponse(BaseModel):
    meeting_id: uuid.UUID
    file: MeetingFileRead
    status: str
