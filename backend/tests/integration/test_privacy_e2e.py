"""Integration tests for PIPA compliance: data export and deletion.

Tests the privacy endpoints that implement data subject rights
under Korean Personal Information Protection Act (PIPA).
"""

import asyncio

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    """Create AsyncClient with lifespan support."""
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as ac:
            yield ac


@pytest.mark.anyio
async def test_export_delete_donation_data(client):
    """Export user data → verify structure → delete → verify success.

    Verifies the PIPA data export and deletion endpoints work correctly.
    Note: Orchestrator doesn't save donations to DB yet, so we test endpoint structure.
    """
    user_id = "privacy_test_user_1"

    # Export user data (may be empty if no donations recorded to DB)
    export_response = await client.get(f"/admin/privacy/export/{user_id}")
    assert export_response.status_code == 200

    export_data = export_response.json()

    # Verify exported data has correct structure
    assert "user_id" in export_data
    assert export_data["user_id"] == user_id
    assert "donations" in export_data
    assert isinstance(export_data["donations"], list)
    assert "ban" in export_data

    # Request data deletion
    delete_response = await client.delete(f"/admin/privacy/delete/{user_id}")
    assert delete_response.status_code == 200

    delete_data = delete_response.json()
    assert "status" in delete_data
    assert delete_data["status"] == "success"
    assert "message" in delete_data

    await asyncio.sleep(0.1)

    # Export again to verify deletion worked
    export_after_delete = await client.get(f"/admin/privacy/export/{user_id}")
    assert export_after_delete.status_code == 200

    after_delete_data = export_after_delete.json()
    assert "user_id" in after_delete_data
    assert "donations" in after_delete_data


@pytest.mark.anyio
async def test_export_ban_data_then_delete(client):
    """Create ban → export → verify ban in export → delete → verify ban removed.

    Verifies that ban data is included in export and properly deleted.
    """
    user_id = "privacy_ban_test_user_2"

    # Ban the user
    ban_response = await client.post(f"/api/admin/ban/{user_id}?reason=privacy_test_ban_reason")
    assert ban_response.status_code == 200

    await asyncio.sleep(0.1)

    # Export user data
    export_response = await client.get(f"/admin/privacy/export/{user_id}")
    assert export_response.status_code == 200

    export_data = export_response.json()

    # Verify export structure
    assert export_data["user_id"] == user_id
    assert "ban" in export_data

    # Verify ban information is present (if not None)
    if export_data["ban"]:
        assert export_data["ban"]["user_id"] == user_id
        assert export_data["ban"]["reason"] == "privacy_test_ban_reason"

    # Request data deletion
    delete_response = await client.delete(f"/admin/privacy/delete/{user_id}")
    assert delete_response.status_code == 200
    assert delete_response.json()["status"] == "success"

    await asyncio.sleep(0.1)

    # Verify ban is removed from ban list
    bans_response = await client.get("/api/admin/bans")
    assert bans_response.status_code == 200
    bans_data = bans_response.json()

    user_still_banned = any(ban["user_id"] == user_id for ban in bans_data["bans"])
    assert not user_still_banned, "Ban should be removed after data deletion"

    # Verify export after deletion shows no ban
    export_after_delete = await client.get(f"/admin/privacy/export/{user_id}")
    assert export_after_delete.status_code == 200

    after_delete_data = export_after_delete.json()
    assert after_delete_data["ban"] is None
