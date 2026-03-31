import asyncio
from unittest.mock import Mock

import pytest

from app.models.donation import DonationTier
from app.services.cooldown import CooldownTracker


@pytest.fixture
def tracker():
    """Create a CooldownTracker instance."""
    return CooldownTracker()


@pytest.fixture
def mock_loop_time():
    """Mock asyncio event loop time for deterministic testing."""
    original_get_event_loop = asyncio.get_event_loop
    mock_loop = Mock()
    mock_loop.time = Mock(return_value=1000.0)

    def mock_get_event_loop():
        return mock_loop

    asyncio.get_event_loop = mock_get_event_loop
    yield mock_loop
    asyncio.get_event_loop = original_get_event_loop


def test_first_donation_allowed(tracker, mock_loop_time):
    """First donation from a user should always be allowed."""
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is True
    assert remaining == 0.0


def test_cooldown_active(tracker, mock_loop_time):
    """Donation immediately after previous should be blocked with remaining time."""
    # Record first donation
    tracker.record("user1")

    # Immediately check again (same time)
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is False
    assert remaining == 60.0  # ONE_LINE cooldown is 60 seconds


def test_cooldown_expired(tracker, mock_loop_time):
    """Donation after cooldown period should be allowed."""
    # Record first donation at t=1000
    tracker.record("user1")

    # Advance time past cooldown (60 seconds for ONE_LINE)
    mock_loop_time.time.return_value = 1061.0

    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is True
    assert remaining == 0.0


def test_different_tiers_different_cooldowns(tracker, mock_loop_time):
    """Each tier should have its own cooldown duration."""
    # Test ONE_LINE (60s)
    tracker.record("user1")
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is False
    assert remaining == 60.0

    # Test CHAOS (600s)
    tracker.record("user2")
    allowed, remaining = tracker.check("user2", DonationTier.CHAOS)
    assert allowed is False
    assert remaining == 600.0


def test_different_users_independent(tracker, mock_loop_time):
    """Different users should have independent cooldowns."""
    # User1 donates
    tracker.record("user1")

    # User2 should be allowed immediately
    allowed, remaining = tracker.check("user2", DonationTier.ONE_LINE)
    assert allowed is True
    assert remaining == 0.0

    # User1 should still be in cooldown
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is False
    assert remaining == 60.0


def test_cooldown_boundary(tracker, mock_loop_time):
    """Test cooldown at exact boundary (edge case)."""
    # Record donation at t=1000
    tracker.record("user1")

    # Check at exactly cooldown threshold (t=1060 for ONE_LINE = 60s cooldown)
    mock_loop_time.time.return_value = 1060.0
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is True
    assert remaining == 0.0


def test_partial_cooldown_remaining(tracker, mock_loop_time):
    """Test remaining time during active cooldown."""
    # Record donation at t=1000
    tracker.record("user1")

    # Check at t=1030 (30 seconds elapsed, 30 remaining)
    mock_loop_time.time.return_value = 1030.0
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is False
    assert remaining == 30.0


def test_reset_user_cooldown(tracker, mock_loop_time):
    """Test resetting cooldown for a specific user."""
    tracker.record("user1")

    # Should be in cooldown
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is False

    # Reset cooldown
    tracker.reset("user1")

    # Should now be allowed
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is True
    assert remaining == 0.0


def test_clear_all_cooldowns(tracker, mock_loop_time):
    """Test clearing all cooldowns."""
    tracker.record("user1")
    tracker.record("user2")

    # Both should be in cooldown
    assert tracker.check("user1", DonationTier.ONE_LINE)[0] is False
    assert tracker.check("user2", DonationTier.ONE_LINE)[0] is False

    # Clear all
    tracker.clear_all()

    # Both should now be allowed
    assert tracker.check("user1", DonationTier.ONE_LINE)[0] is True
    assert tracker.check("user2", DonationTier.ONE_LINE)[0] is True


def test_cooldown_with_tier_upgrade(tracker, mock_loop_time):
    """Test cooldown when user donates at different tiers."""
    # User donates at ONE_LINE tier
    tracker.record("user1")

    # Check with FEATURE tier (180s cooldown)
    # Since last donation was just recorded, should be blocked
    mock_loop_time.time.return_value = 1070.0  # 70 seconds later
    allowed, remaining = tracker.check("user1", DonationTier.FEATURE)
    assert allowed is False
    # Remaining should be 180 - 70 = 110 seconds
    assert remaining == 110.0


def test_multiple_donations_from_same_user(tracker, mock_loop_time):
    """Test recording multiple donations from the same user."""
    # First donation at t=1000
    tracker.record("user1")

    # Second donation at t=1100 (after cooldown)
    mock_loop_time.time.return_value = 1100.0
    tracker.record("user1")

    # Check immediately after second donation
    allowed, remaining = tracker.check("user1", DonationTier.ONE_LINE)
    assert allowed is False
    assert remaining == 60.0
