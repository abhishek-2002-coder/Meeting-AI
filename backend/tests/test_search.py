"""Speaker Renaming and In-Transcript Search Tests"""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_speaker_renaming_and_transcript_search(client: AsyncClient, auth_headers: dict):
    # 1. Create meeting and upload recording
    create_res = await client.post(
        "/api/v1/meetings",
        json={"title": "Sprint Review Sync"},
        headers=auth_headers,
    )
    meeting_id = create_res.json()["data"]["id"]

    fake_audio = b"ID3" + b"\x00" * 512
    await client.post(
        f"/api/v1/meetings/{meeting_id}/upload",
        files={"file": ("sync.mp3", io.BytesIO(fake_audio), "audio/mpeg")},
        headers=auth_headers,
    )

    # 2. Process
    await client.post(f"/api/v1/meetings/{meeting_id}/process", headers=auth_headers)

    # 3. Get Transcript and Speakers
    transcript_res = await client.get(f"/api/v1/meetings/{meeting_id}/transcript", headers=auth_headers)
    assert transcript_res.status_code == 200
    speakers = transcript_res.json()["data"]["speakers"]
    assert len(speakers) > 0
    speaker_id = speakers[0]["id"]

    # 4. Rename Speaker 1 -> "Abhishek R"
    rename_res = await client.put(
        f"/api/v1/meetings/{meeting_id}/speakers/{speaker_id}",
        json={"display_name": "Abhishek R"},
        headers=auth_headers,
    )
    assert rename_res.status_code == 200
    assert rename_res.json()["data"]["display_name"] == "Abhishek R"

    # 5. Search in Transcript
    search_res = await client.get(
        f"/api/v1/meetings/{meeting_id}/transcript/search?q=authentication",
        headers=auth_headers,
    )
    assert search_res.status_code == 200
    assert search_res.json()["data"]["total_matches"] >= 1
