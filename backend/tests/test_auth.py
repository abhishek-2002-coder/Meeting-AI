"""Authentication Tests for Meeting AI"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient):
    # 1. Register
    reg_payload = {
        "name": "Jane Doe",
        "email": "jane@example.com",
        "password": "strongpassword123",
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["success"] is True
    assert reg_data["data"]["user"]["email"] == "jane@example.com"
    access_token = reg_data["data"]["tokens"]["access_token"]
    refresh_token = reg_data["data"]["tokens"]["refresh_token"]
    assert access_token is not None

    # 2. Login
    login_payload = {
        "email": "jane@example.com",
        "password": "strongpassword123",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["success"] is True

    # 3. /me
    me_res = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["data"]["email"] == "jane@example.com"

    # 4. Refresh token
    refresh_res = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert refresh_res.status_code == 200
    assert "access_token" in refresh_res.json()["data"]
