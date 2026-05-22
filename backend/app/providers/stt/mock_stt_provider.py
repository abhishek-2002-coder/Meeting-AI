"""Realistic Mock Speech-to-Text Provider for Local Development & Testing"""
from pathlib import Path
from typing import Optional
from app.providers.base import SpeechToTextProvider, TranscriptSegmentData, TranscriptionResult


class MockSTTProvider(SpeechToTextProvider):
    """
    Mock STT provider that generates realistic engineering/business sync transcripts
    with multiple speakers, precise timestamps, and explicit action items & decisions.
    """
    async def transcribe(
        self,
        audio_file_path: str,
        language: Optional[str] = "en",
        prompt: Optional[str] = None,
    ) -> TranscriptionResult:
        filename = Path(audio_file_path).name.lower()

        # Generate realistic dialog segments
        segments = [
            TranscriptSegmentData(
                start=0.0,
                end=8.5,
                speaker="Speaker 1",
                text="Good morning everyone. Let's start our weekly engineering sync. Today we need to review backend progress, Docker deployment, and the API delivery deadline.",
            ),
            TranscriptSegmentData(
                start=9.0,
                end=22.4,
                speaker="Speaker 2",
                text="On the backend side, we completed the core database schema and user authentication models. The remaining task is finalizing the meeting transcription pipeline.",
            ),
            TranscriptSegmentData(
                start=23.0,
                end=34.8,
                speaker="Speaker 1",
                text="Great. Abhishek, can you complete the authentication API and the meeting processing worker by Friday?",
            ),
            TranscriptSegmentData(
                start=35.2,
                end=46.0,
                speaker="Speaker 2",
                text="Yes, I will finish the authentication API and the background worker by Friday. I'll also add comprehensive unit tests.",
            ),
            TranscriptSegmentData(
                start=46.5,
                end=61.2,
                speaker="Speaker 3",
                text="Regarding production deployment, we faced container startup issues with the old configuration. I recommend we standardize on Docker Compose for all production and staging environments.",
            ),
            TranscriptSegmentData(
                start=62.0,
                end=75.5,
                speaker="Speaker 1",
                text="Agreed, that is a clear decision: production deployment will use Docker. Rahul, please prepare the deployment server and configuration by Thursday.",
            ),
            TranscriptSegmentData(
                start=76.0,
                end=84.2,
                speaker="Speaker 3",
                text="Got it. I'll have the deployment server ready by Thursday.",
            ),
            TranscriptSegmentData(
                start=85.0,
                end=98.6,
                speaker="Speaker 2",
                text="One unresolved point: which cloud provider will host the production PostgreSQL database? We still need server access credentials from DevOps.",
            ),
            TranscriptSegmentData(
                start=99.0,
                end=110.0,
                speaker="Speaker 1",
                text="That's a potential risk for the timeline if server access is delayed. Let's follow up with DevOps today. Thanks everyone!",
            ),
        ]

        full_text = " ".join([s.text for s in segments])
        total_duration = segments[-1].end

        return TranscriptionResult(
            text=full_text,
            language=language or "en",
            duration=total_duration,
            segments=segments,
        )
