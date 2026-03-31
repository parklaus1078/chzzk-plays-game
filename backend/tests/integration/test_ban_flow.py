"""Integration tests for ban lifecycle and enforcement.

Tests the complete ban workflow: ban creation, donation rejection,
unban, and ban list management.
"""

import asyncio

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.donation import DonationEvent, DonationTier


@pytest.fixture
async def client():
    """Create AsyncClient with lifespan support."""
    async with LifespanManager(app) as manager:
        async with AsyncClient(
            transport=ASGITransport(app=manager.app), base_url="http://test"
        ) as ac:
            yield ac


@pytest.mark.anyio
async def test_ban_user_then_donation_not_queued(client):
    """Ban user → POST donation → not queued.

    Verifies that donations from banned users are not processed.
    """
    user_id = "banned_test_user_1"

    # Ban the user
    ban_response = await client.post(f"/api/admin/ban/{user_id}?reason=test_ban_manual")
    assert ban_response.status_code == 200

    await asyncio.sleep(0.1)

    # Try to submit donation from banned user
    donation = DonationEvent(
        donor_name="BannedUser1",
        donor_id=user_id,
        amount=5000,
        message="This should be ignored",
        tier=DonationTier.FEATURE,
    )

    response = await client.post("/api/donation", json=donation.model_dump(mode="json"))
    # May return 200 (accepted) or 403 (rejected) depending on implementation
    assert response.status_code in (200, 403)

    await asyncio.sleep(0.1)

    # Verify donation is NOT in queue
    queue_response = await client.get("/api/queue")
    assert queue_response.status_code == 200
    queue_data = queue_response.json()

    # Check that banned user's donation is not in any queue state
    for item in queue_data["pending"]:
        assert item["donor_id"] != user_id

    if queue_data["current"]:
        assert queue_data["current"]["donor_id"] != user_id


@pytest.mark.anyio
async def test_ban_unban_then_donation_queued(client):
    """Ban user → unban → POST donation → queued.

    Verifies that after unbanning, the user can submit donations again.
    """
    user_id = "ban_unban_test_user"

    # Ban the user
    ban_response = await client.post(f"/api/admin/ban/{user_id}?reason=test_temporary_ban")
    assert ban_response.status_code == 200

    await asyncio.sleep(0.1)

    # Unban the user
    unban_response = await client.delete(f"/api/admin/ban/{user_id}")
    assert unban_response.status_code == 200

    await asyncio.sleep(0.1)

    # Submit donation from unbanned user
    donation = DonationEvent(
        donor_name="UnbannedUser",
        donor_id=user_id,
        amount=5000,
        message="This should be queued after unban",
        tier=DonationTier.FEATURE,
    )

    response = await client.post("/api/donation", json=donation.model_dump(mode="json"))
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "queued"

    await asyncio.sleep(0.1)

    # Verify donation is in queue
    queue_response = await client.get("/api/queue")
    assert queue_response.status_code == 200
    queue_data = queue_response.json()

    # Check if donation is in pending or current
    found = False
    for item in queue_data["pending"]:
        if item["donor_id"] == user_id:
            found = True
            break

    if not found and queue_data["current"]:
        if queue_data["current"]["donor_id"] == user_id:
            found = True

    if not found and queue_data.get("recent_completed"):
        if queue_data["recent_completed"]["donor_id"] == user_id:
            found = True

    assert found, "Unbanned user's donation should be queued"


@pytest.mark.anyio
async def test_ban_list_management(client):
    """Ban user → GET /admin/bans → user in list → DELETE → user removed.

    Verifies the complete ban list management workflow.
    """
    user_id = "ban_list_test_user"

    # Get initial ban list
    initial_response = await client.get("/api/admin/bans")
    assert initial_response.status_code == 200
    initial_data = initial_response.json()
    initial_count = len(initial_data["bans"])

    # Ban a user
    ban_response = await client.post(f"/api/admin/ban/{user_id}?reason=test_ban_list_management")
    assert ban_response.status_code == 200

    await asyncio.sleep(0.1)

    # Get updated ban list
    list_response = await client.get("/api/admin/bans")
    assert list_response.status_code == 200
    list_data = list_response.json()

    # Verify user is in the list
    banned_user_found = False
    ban_entry = None
    for ban in list_data["bans"]:
        if ban["user_id"] == user_id:
            banned_user_found = True
            ban_entry = ban
            break

    assert banned_user_found, f"User {user_id} should be in ban list"
    assert ban_entry is not None
    assert ban_entry["reason"] == "test_ban_list_management"
    assert "banned_at" in ban_entry

    # Verify ban count increased
    assert len(list_data["bans"]) == initial_count + 1

    # Delete the ban
    delete_response = await client.delete(f"/api/admin/ban/{user_id}")
    assert delete_response.status_code == 200

    await asyncio.sleep(0.1)

    # Get final ban list
    final_response = await client.get("/api/admin/bans")
    assert final_response.status_code == 200
    final_data = final_response.json()

    # Verify user is NOT in the list anymore
    user_still_banned = any(ban["user_id"] == user_id for ban in final_data["bans"])
    assert not user_still_banned, f"User {user_id} should be removed from ban list"

    # Verify ban count returned to initial (or close to it)
    assert len(final_data["bans"]) <= initial_count + 1  # Allow for other tests adding bans
