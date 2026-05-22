"""Abstract Interfaces for Pluggable AI Providers (Speech-to-Text & LLM)"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.schemas.ai_output import AIExtractedMeeting


class TranscriptSegmentData(BaseModel):
    start: float = Field(..., description="Start time in seconds")
    end: float = Field(..., description="End time in seconds")
    text: str = Field(..., description="Transcribed text segment")
    speaker: Optional[str] = Field(None, description="Speaker identifier if diarized, e.g. 'Speaker 1'")


class TranscriptionResult(BaseModel):
    text: str
    language: str = "en"
    duration: float = 0.0
    segments: List[TranscriptSegmentData] = Field(default_factory=list)


class SpeechToTextProvider(ABC):
    """Abstract interface for Speech-to-Text / Audio transcription engines"""
    @abstractmethod
    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = "en",
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        """Transcribe audio file and return structured segments"""
        pass


class LLMProvider(ABC):
    """Abstract interface for LLM meeting intelligence extraction"""
    @abstractmethod
    async def analyze_transcript(
        self,
        meeting_title: str,
        structured_transcript: str,
        meeting_description: Optional[str] = None,
    ) -> AIExtractedMeeting:
        """Analyze full transcript text and return validated structured meeting insights"""
        pass
