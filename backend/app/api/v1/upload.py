"""Audio / Video Upload & Streaming API Endpoints"""
import os
import uuid
from fastapi import APIRouter, Depends, File, Header, HTTPException, Request, Response, UploadFile, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.exceptions import NotFoundException
from app.db.database import get_db
from app.db.models.meeting import MeetingStatus
from app.db.models.user import User
from app.db.repositories.meeting_repo import MeetingRepository
from app.schemas.common import ApiResponse
from app.schemas.meeting_file import MeetingFileRead, UploadResponse
from app.services.storage_service import StorageService

router = APIRouter(prefix="/meetings", tags=["Upload & Audio"])


@router.post(
    "/{meeting_id}/upload",
    response_model=ApiResponse[UploadResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload audio/video recording for a meeting",
)
async def upload_meeting_file(
    meeting_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_by_id(user_id=current_user.id, entity_id=meeting_id)
    if not meeting:
        raise NotFoundException(message="Meeting not found")

    storage = StorageService()
    storage_path, file_size, checksum, mime_type, orig_name = await storage.save_recording(
        user_id=current_user.id, file=file
    )

    file_obj = await meeting_repo.save_file(
        meeting_id=meeting_id,
        original_filename=orig_name,
        storage_path=storage_path,
        mime_type=mime_type,
        file_size=file_size,
        checksum=checksum,
    )

    await meeting_repo.update(
        user_id=current_user.id,
        entity_id=meeting_id,
        status=MeetingStatus.UPLOADED,
    )

    resp = UploadResponse(
        meeting_id=meeting_id,
        file=MeetingFileRead.model_validate(file_obj),
        status=MeetingStatus.UPLOADED,
    )

    return ApiResponse.ok(data=resp, message="Recording uploaded successfully")


@router.get(
    "/{meeting_id}/audio",
    summary="Stream meeting audio recording with HTTP Byte-Range support",
)
async def stream_audio(
    meeting_id: uuid.UUID,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    meeting_repo = MeetingRepository(db)
    meeting = await meeting_repo.get_with_details(user_id=current_user.id, meeting_id=meeting_id)
    if not meeting or not meeting.file:
        raise NotFoundException(message="Meeting recording not found")

    file_path = meeting.file.storage_path
    if not os.path.exists(file_path):
        raise NotFoundException(message="Audio file is missing on storage")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range")

    if range_header:
        # Parse "bytes=start-end"
        range_str = range_header.replace("bytes=", "").strip()
        parts = range_str.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1

        if start >= file_size or end >= file_size or start > end:
            raise HTTPException(status_code=416, detail="Requested Range Not Satisfiable")

        content_length = end - start + 1
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": meeting.file.mime_type,
        }
        return StreamingResponse(
            StorageService.get_range_stream(file_path, start, end),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers=headers,
        )

    # Standard complete stream
    headers = {
        "Accept-Ranges": "bytes",
        "Content-Length": str(file_size),
        "Content-Type": meeting.file.mime_type,
    }
    return StreamingResponse(
        StorageService.get_range_stream(file_path, 0, file_size - 1),
        status_code=status.HTTP_200_OK,
        headers=headers,
    )
