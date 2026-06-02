"""Transcript Segment and Search Schemas"""
from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict
from app.schemas.speaker import SpeakerRead


class TranscriptSegmentRead(BaseModel):
    id: uuid.UUID
    meeting_id: uuid.UUID
    speaker_id: Optional[uuid.UUID] = None
    speaker_label: Optional[str] = None
    speaker_name: Optional[str] = None
    sequence: int
    start_time: float
    end_time: float
    text: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TranscriptResponse(BaseModel):
    meeting_id: uuid.UUID
    segments: List[TranscriptSegmentRead]
    speakers: List[SpeakerRead]


class SegmentMatch(BaseModel):
    segment_id: uuid.UUID
    start_time: float
    end_time: float
    speaker_name: Optional[str] = None
    text: str
    highlight: str


class TranscriptSearchResponse(BaseModel):
    meeting_id: uuid.UUID
    query: str
    matches: List[SegmentMatch]
    total_matches: int
