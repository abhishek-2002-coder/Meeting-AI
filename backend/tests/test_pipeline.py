"""End-to-End Meeting Pipeline and Search Tests"""
import io
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_end_to_end_pipeline_and_intelligence(client: AsyncClient, auth_headers: dict):
    # 1. Create meeting
    create_res = await client.post(
        "/api/v1/meetings",
        json={"title": "Q4 Engineering Milestone Planning", "description": "Reviewing API deadlines and Docker deployment"},
        headers=auth_headers,
    )
    assert create_res.status_code == 201
    meeting_id = create_res.json()["data"]["id"]

    # 2. Upload recording
    fake_audio = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00D\xac\x00\x00\x88X\x01\x00\x02\x00\x10\x00data\x00\x00\x00\x00"
    upload_res = await client.post(
        f"/api/v1/meetings/{meeting_id}/upload",
        files={"file": ("planning-sync.wav", io.BytesIO(fake_audio), "audio/wav")},
        headers=auth_headers,
    )
    assert upload_res.status_code == 201

    # 3. Trigger processing pipeline
    proc_res = await client.post(f"/api/v1/meetings/{meeting_id}/process", headers=auth_headers)
    assert proc_res.status_code == 200

    # 4. Check processing status
    status_res = await client.get(f"/api/v1/meetings/{meeting_id}/processing-status", headers=auth_headers)
    assert status_res.status_code == 200
    assert "jobs" in status_res.json()["data"]

    # 5. Fetch transcript
    transcript_res = await client.get(f"/api/v1/meetings/{meeting_id}/transcript", headers=auth_headers)
    assert transcript_res.status_code == 200
    transcript_data = transcript_res.json()["data"]
    assert len(transcript_data["segments"]) > 0

    # 6. Fetch summary
    summary_res = await client.get(f"/api/v1/meetings/{meeting_id}/summary", headers=auth_headers)
    assert summary_res.status_code == 200
    summary_data = summary_res.json()["data"]
    assert "executive" in summary_data["short_summary"].lower() or len(summary_data["short_summary"]) > 10

    # 7. Fetch decisions
    decisions_res = await client.get(f"/api/v1/meetings/{meeting_id}/decisions", headers=auth_headers)
    assert decisions_res.status_code == 200
    decisions = decisions_res.json()["data"]
    assert len(decisions) >= 1

    # 8. Fetch action items
    actions_res = await client.get(f"/api/v1/meetings/{meeting_id}/action-items", headers=auth_headers)
    assert actions_res.status_code == 200
    action_items = actions_res.json()["data"]
    assert len(action_items) >= 1
    action_item_id = action_items[0]["id"]

    # 9. Update action item status to COMPLETED
    patch_res = await client.put(
        f"/api/v1/action-items/{action_item_id}",
        json={"status": "COMPLETED"},
        headers=auth_headers,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["data"]["status"] == "COMPLETED"

    # 10. Test cross-meeting search
    search_res = await client.get("/api/v1/search/meetings?q=Docker", headers=auth_headers)
    assert search_res.status_code == 200
    search_data = search_res.json()["data"]
    assert search_data["total_results"] >= 1

    # 11. Test dashboard stats
    dash_res = await client.get("/api/v1/dashboard/stats", headers=auth_headers)
    assert dash_res.status_code == 200
    dash_data = dash_res.json()["data"]
    assert dash_data["total_meetings"] >= 1
    assert dash_data["total_action_items"] >= 1
