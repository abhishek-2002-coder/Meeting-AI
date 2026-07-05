"""Meeting and Cross-Meeting Search Schemas"""
from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel


class SearchMeetingResult(BaseModel):
    meeting_id: uuid.UUID
    title: str
    description: Optional[str] = None
    created_at: datetime
    match_type: str  # "title" | "transcript" | "summary" | "topic" | "decision" | "action_item"
    snippet: str
    timestamp_seconds: Optional[float] = None
    match_count: int = 1


class SearchResponse(BaseModel):
    query: str
    total_results: int
    results: List[SearchMeetingResult]
