import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import Settings
from app.models.donation import DonationEvent, DonationTier
from app.services.donation_listener import DonationListener


@pytest.fixture
def settings() -> Settings:
    """Test settings."""
    return Settings(
        anthropic_api_key="test-key",
        chzzk_client_id="test-client-id",
        chzzk_client_secret="test-client-secret",
        unity_project_path="/tmp/test",
        db_path=":memory:",
    )


@pytest.fixture
def mock_donation():
    """Create a mock Donation object."""

    def _create_donation(amount: int, nickname: str = "TestDonor", message: str = "Test prompt"):
        donation = MagicMock()
        donation.pay_amount = amount
        donation.donation_text = message
        donation.donator_name = nickname
        donation.donator_id = "test-user-123"
        return donation

    return _create_donation


@pytest.mark.asyncio
async def test_donation_creates_event(settings: Settings, mock_donation: Any):
    """Test that a donation creates a DonationEvent with correct fields."""
    received_events: list[DonationEvent] = []

    async def on_donation(event: DonationEvent) -> None:
        received_events.append(event)

    listener = DonationListener(settings, on_donation)

    # Mock the client and connection
    with patch("app.services.donation_listener.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_user_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.login = AsyncMock(return_value=mock_user_client)

        # Simulate donation by calling the registered event handler
        donation = mock_donation(amount=5000, nickname="Alice", message="Add a feature")

        # Start connection in background
        connect_task = asyncio.create_task(listener._connect_and_listen())
        await asyncio.sleep(0.1)  # Let it register the event handler

        # Get the registered on_donation handler
        assert mock_client.event.called
        registered_handler = mock_client.event.call_args[0][0]

        # Simulate receiving a donation
        await registered_handler(donation)

        # Cancel the connection task
        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    # Verify DonationEvent was created correctly
    assert len(received_events) == 1
    event = received_events[0]
    assert event.donor_name == "Alice"
    assert event.donor_id == "test-user-123"
    assert event.amount == 5000
    assert event.message == "Add a feature"
    assert event.tier == DonationTier.FEATURE


@pytest.mark.asyncio
async def test_donation_below_minimum_skipped(settings: Settings, mock_donation: Any):
    """Test that donations below 1000 KRW are skipped."""
    received_events: list[DonationEvent] = []

    async def on_donation(event: DonationEvent) -> None:
        received_events.append(event)

    listener = DonationListener(settings, on_donation)

    with patch("app.services.donation_listener.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_user_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.login = AsyncMock(return_value=mock_user_client)

        donation = mock_donation(amount=500, nickname="Bob", message="Too small")

        connect_task = asyncio.create_task(listener._connect_and_listen())
        await asyncio.sleep(0.1)

        registered_handler = mock_client.event.call_args[0][0]
        await registered_handler(donation)

        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    # Verify callback was NOT called
    assert len(received_events) == 0


@pytest.mark.asyncio
async def test_tier_classification_forwarded(settings: Settings, mock_donation: Any):
    """Test that 5000 KRW donation is classified as feature tier."""
    received_events: list[DonationEvent] = []

    async def on_donation(event: DonationEvent) -> None:
        received_events.append(event)

    listener = DonationListener(settings, on_donation)

    with patch("app.services.donation_listener.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_user_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.login = AsyncMock(return_value=mock_user_client)

        donation = mock_donation(amount=5000, nickname="Charlie", message="Feature request")

        connect_task = asyncio.create_task(listener._connect_and_listen())
        await asyncio.sleep(0.1)

        registered_handler = mock_client.event.call_args[0][0]
        await registered_handler(donation)

        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    assert len(received_events) == 1
    assert received_events[0].tier == DonationTier.FEATURE


@pytest.mark.asyncio
async def test_reconnect_backoff(settings: Settings):
    """Test that backoff increases exponentially on disconnection."""

    async def on_donation(event: DonationEvent) -> None:
        pass

    listener = DonationListener(settings, on_donation)

    with patch("app.services.donation_listener.Client") as mock_client_class:
        # Make the client always raise an exception to simulate disconnection
        mock_client_class.side_effect = Exception("Connection failed")

        sleep_calls: list[float] = []
        _real_sleep = asyncio.sleep

        async def fake_sleep(duration: float) -> None:
            sleep_calls.append(duration)
            # Stop after collecting enough samples
            if len(sleep_calls) >= 4:
                listener.stop()
                return
            # Yield control so the event loop can proceed
            await _real_sleep(0)

        with patch("app.services.donation_listener.asyncio.sleep", side_effect=fake_sleep):
            run_task = asyncio.create_task(listener.run())
            try:
                await asyncio.wait_for(run_task, timeout=5.0)
            except (asyncio.CancelledError, TimeoutError):
                pass

        # Verify sleep was called with increasing backoffs: 1, 2, 4, 8, ...
        assert len(sleep_calls) >= 4, f"Expected at least 4 backoff calls, got {len(sleep_calls)}"
        for i in range(len(sleep_calls) - 1):
            assert sleep_calls[i + 1] >= sleep_calls[i], (
                f"Backoff should increase: {sleep_calls}"
            )
        # Check that backoff doesn't exceed 60 seconds
        for duration in sleep_calls:
            assert duration <= 60.0, f"Backoff should not exceed 60s: {duration}"


@pytest.mark.asyncio
async def test_stop_cancels_listener(settings: Settings):
    """Test that stop() method cancels the listener gracefully."""

    async def on_donation(event: DonationEvent) -> None:
        pass

    listener = DonationListener(settings, on_donation)

    with patch("app.services.donation_listener.Client") as mock_client_class:
        # Make connection wait forever so we can test stop
        mock_client = MagicMock()
        mock_user_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.login = AsyncMock(return_value=mock_user_client)

        async def wait_forever(*args, **kwargs):
            await asyncio.sleep(999)

        mock_user_client.connect = wait_forever

        # Start the listener
        run_task = asyncio.create_task(listener.run())
        await asyncio.sleep(0.2)  # Let it start

        # Call stop (cancels the task)
        listener.stop()

        # Wait for task to complete — stop() cancels, so it should finish quickly
        try:
            await asyncio.wait_for(run_task, timeout=2.0)
        except (TimeoutError, asyncio.CancelledError):
            pass

        # Verify the listener is no longer running
        assert not listener._running


@pytest.mark.asyncio
async def test_multiple_tier_donations(settings: Settings, mock_donation: Any):
    """Test handling multiple donations with different tiers."""
    received_events: list[DonationEvent] = []

    async def on_donation(event: DonationEvent) -> None:
        received_events.append(event)

    listener = DonationListener(settings, on_donation)

    with patch("app.services.donation_listener.Client") as mock_client_class:
        mock_client = MagicMock()
        mock_user_client = AsyncMock()
        mock_client_class.return_value = mock_client
        mock_client.login = AsyncMock(return_value=mock_user_client)

        donations = [
            mock_donation(amount=1000, nickname="User1", message="One line"),
            mock_donation(amount=5000, nickname="User2", message="Feature"),
            mock_donation(amount=10000, nickname="User3", message="Major"),
            mock_donation(amount=30000, nickname="User4", message="Chaos"),
        ]

        connect_task = asyncio.create_task(listener._connect_and_listen())
        await asyncio.sleep(0.1)

        registered_handler = mock_client.event.call_args[0][0]

        # Simulate all donations
        for donation in donations:
            await registered_handler(donation)

        connect_task.cancel()
        try:
            await connect_task
        except asyncio.CancelledError:
            pass

    # Verify all donations were processed with correct tiers
    assert len(received_events) == 4
    assert received_events[0].tier == DonationTier.ONE_LINE
    assert received_events[1].tier == DonationTier.FEATURE
    assert received_events[2].tier == DonationTier.MAJOR
    assert received_events[3].tier == DonationTier.CHAOS
