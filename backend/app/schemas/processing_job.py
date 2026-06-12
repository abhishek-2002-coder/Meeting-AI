"""Processing Job and Pipeline Status Schemas"""
from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict


class ProcessingJobRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    job_type: str
    status: str
    progress: int
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ProcessingStatusResponse(BaseModel):
    meeting_id: uuid.UUID
    status: str
    overall_progress: int
    jobs: List[ProcessingJobRead]
