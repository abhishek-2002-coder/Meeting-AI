"""Audio & Video File Storage Service with Byte-Range Streaming Support"""
import hashlib
import os
from pathlib import Path
from typing import BinaryIO, Generator, Optional, Tuple
import uuid
import aiofiles
from fastapi import UploadFile

from app.core.config import settings
from app.core.exceptions import HealthSetuException

ALLOWED_AUDIO_EXTENSIONS = {".mp3", ".wav", ".m4a", ".mp4", ".webm", ".aac", ".ogg", ".flac"}
MAX_FILE_SIZE_BYTES = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024


class StorageService:
    def __init__(self, storage_dir: str = settings.STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, file: UploadFile) -> Tuple[str, str]:
        """Validates file extension and returns sanitized unique storage filename"""
        filename = file.filename or "recording.mp3"
        ext = os.path.splitext(filename)[1].lower()
        if ext not in ALLOWED_AUDIO_EXTENSIONS:
            raise HealthSetuException(
                message=f"Unsupported media format '{ext}'. Allowed formats: MP3, WAV, M4A, MP4, WEBM, AAC, OGG, FLAC.",
                code="UNSUPPORTED_MEDIA_TYPE",
                status_code=415,
            )
        safe_name = f"{uuid.uuid4()}{ext}"
        return ext.lstrip("."), safe_name

    async def save_recording(
        self, user_id: uuid.UUID, file: UploadFile
    ) -> Tuple[str, int, str, str, str]:
        """
        Saves uploaded audio file into user-scoped directory and calculates SHA256 checksum.
        Returns (storage_path, file_size_bytes, checksum, mime_type, original_filename).
        """
        ext, safe_filename = self.validate_file(file)
        user_dir = self.storage_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)
        target_path = user_dir / safe_filename

        total_bytes = 0
        hasher = hashlib.sha256()

        async with aiofiles.open(target_path, "wb") as out_file:
            while chunk := await file.read(1024 * 1024):  # 1MB buffer
                total_bytes += len(chunk)
                if total_bytes > MAX_FILE_SIZE_BYTES:
                    await out_file.close()
                    if target_path.exists():
                        target_path.unlink()
                    raise HealthSetuException(
                        message=f"Recording file exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB}MB.",
                        code="FILE_TOO_LARGE",
                        status_code=413,
                    )
                hasher.update(chunk)
                await out_file.write(chunk)

        checksum = hasher.hexdigest()
        mime_type = file.content_type or f"audio/{ext}"
        await file.seek(0)

        return str(target_path), total_bytes, checksum, mime_type, file.filename or "recording.mp3"

    @staticmethod
    def get_range_stream(file_path: str, start: int, end: int, chunk_size: int = 64 * 1024) -> Generator[bytes, None, None]:
        """Yields chunks of a file for HTTP 206 Partial Content range requests"""
        with open(file_path, "rb") as f:
            f.seek(start)
            bytes_left = end - start + 1
            while bytes_left > 0:
                read_len = min(chunk_size, bytes_left)
                data = f.read(read_len)
                if not data:
                    break
                bytes_left -= len(data)
                yield data

    def delete_file(self, file_path: str) -> None:
        """Safely delete file from disk"""
        p = Path(file_path)
        if p.exists() and p.is_file():
            try:
                p.unlink()
            except Exception:
                pass
