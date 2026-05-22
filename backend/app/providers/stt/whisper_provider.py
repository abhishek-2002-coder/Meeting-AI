"""OpenAI Whisper Speech-to-Text Provider"""
import os
from pathlib import Path
from typing import Optional
from openai import AsyncOpenAI

from app.core.config import settings
from app.core.exceptions import HealthSetuException
from app.providers.base import SpeechToTextProvider, TranscriptSegmentData, TranscriptionResult


class WhisperSTTProvider(SpeechToTextProvider):
    def __init__(self, api_key: Optional[str] = None, model: str = settings.OPENAI_STT_MODEL):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        if not self.api_key:
            raise HealthSetuException(
                message="OpenAI API key is missing. Please set OPENAI_API_KEY in environment.",
                code="AI_PROVIDER_ERROR",
                status_code=500,
            )
        self.client = AsyncOpenAI(api_key=self.api_key)

    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = "en",
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        if not os.path.exists(audio_file_path):
            raise HealthSetuException(message=f"Audio file not found at path: {audio_file_path}")

        try:
            with open(audio_file_path, "rb") as audio_file:
                # Request verbose_json format from Whisper API to obtain timestamps
                response = await self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    language=language if language and language != "auto" else None,
                    prompt=prompt,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )

            segments_data = []
            raw_segments = getattr(response, "segments", []) or []
            for idx, seg in enumerate(raw_segments):
                segments_data.append(
                    TranscriptSegmentData(
                        start=float(seg.get("start", 0.0) if isinstance(seg, dict) else getattr(seg, "start", 0.0)),
                        end=float(seg.get("end", 0.0) if isinstance(seg, dict) else getattr(seg, "end", 0.0)),
                        text=str(seg.get("text", "") if isinstance(seg, dict) else getattr(seg, "text", "")).strip(),
                        speaker=f"Speaker {1 + (idx % 2)}",  # Basic alternating speaker heuristic if external diarization omitted
                    )
                )

            duration = getattr(response, "duration", 0.0) or (segments_data[-1].end if segments_data else 0.0)
            full_text = getattr(response, "text", "") or " ".join([s.text for s in segments_data])

            return TranscriptionResult(
                text=full_text,
                language=language or getattr(response, "language", "en"),
                duration=float(duration),
                segments=segments_data,
            )
        except Exception as e:
            raise HealthSetuException(
                message=f"Whisper transcription failed: {str(e)}",
                code="TRANSCRIPTION_ERROR",
                status_code=502,
            )
