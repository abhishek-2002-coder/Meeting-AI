"""Meeting Management and Upload Tests"""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_meeting_crud_and_upload(client: AsyncClient, auth_headers: dict):
    # 1. Create Meeting
    create_payload = {
        "title": "Weekly Backend Sync",
        "description": "Sprint planning and architectural review",
        "language": "en",
    }
    create_res = await client.post("/api/v1/meetings", json=create_payload, headers=auth_headers)
    assert create_res.status_code == 201
    meeting_data = create_res.json()["data"]
    meeting_id = meeting_data["id"]
    assert meeting_data["title"] == "Weekly Backend Sync"

    # 2. Upload Audio
    fake_audio_content = b"ID3\x03\x00\x00\x00\x00\x00#TSSE\x00\x00\x00\x0f\x00\x00\x03Lavf58.29.100" + b"\x00" * 1024
    upload_res = await client.post(
        f"/api/v1/meetings/{meeting_id}/upload",
        files={"file": ("meeting-sync.mp3", io.BytesIO(fake_audio_content), "audio/mpeg")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201
    upload_data = upload_res.json()["data"]
    assert upload_data["file"]["original_filename"] == "meeting-sync.mp3"

    # 3. Get Meeting Detail
    detail_res = await client.get(f"/api/v1/meetings/{meeting_id}", headers=auth_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["data"]["has_recording"] is True

    # 4. Update Meeting
    update_res = await client.put(
        f"/api/v1/meetings/{meeting_id}",
        json={"title": "Updated Backend Sync"},
        headers=auth_headers,
    )
    assert update_res.status_code == 200
    assert update_res.json()["data"]["title"] == "Updated Backend Sync"

    # 5. List Meetings
    list_res = await client.get("/api/v1/meetings", headers=auth_headers)
    assert list_res.status_code == 200
    assert list_res.json()["data"]["total"] >= 1
