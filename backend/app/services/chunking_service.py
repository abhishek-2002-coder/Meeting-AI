"""Transcript Formatting and Chunking Service"""
from typing import List
from app.db.models.transcript_segment import TranscriptSegment


class ChunkingService:
    @staticmethod
    def format_segments_to_dialogue(segments: List[TranscriptSegment]) -> str:
        """
        Formats a list of transcript segments into a clean, human-readable dialogue:
        [00:01:12] Speaker 1 (Abhishek):
        We need to complete the backend API by Friday.
        """
        lines = []
        for seg in segments:
            m, s = divmod(int(seg.start_time), 60)
            h, m = divmod(m, 60)
            time_str = f"{h:02d}:{m:02d}:{s:02d}" if h > 0 else f"{m:02d}:{s:02d}"
            
            speaker_name = seg.speaker.display_name if seg.speaker else "Speaker"
            lines.append(f"[{time_str}] {speaker_name}:\n{seg.text}\n")

        return "\n".join(lines)

    @staticmethod
    def chunk_transcript(text: str, max_chars_per_chunk: int = 15000, overlap_chars: int = 1000) -> List[str]:
        """
        Splits long multi-hour transcripts into overlapping chunks to fit LLM context windows.
        """
        if len(text) <= max_chars_per_chunk:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = min(start + max_chars_per_chunk, len(text))
            chunk = text[start:end]
            chunks.append(chunk)
            if end == len(text):
                break
            start += max_chars_per_chunk - overlap_chars

        return chunks
