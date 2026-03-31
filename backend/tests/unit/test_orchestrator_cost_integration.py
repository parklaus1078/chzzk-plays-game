"""Integration tests for orchestrator cost tracking."""
from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest

from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.db.repositories.stats_repo import StatsRepository
from app.models.donation import DonationTier
from app.models.prompt import PromptResult
from app.models.queue import QueueItem
from app.services.connection_manager import ConnectionManager
from app.services.cost_tracker import CostTracker
from app.services.orchestrator import Orchestrator


@pytest.fixture
def mock_agent_runner():
    """Mock agent runner that returns successful results."""
    runner = AsyncMock()
    runner.execute_prompt.return_value = PromptResult(
        prompt_id="test-123",
        success=True,
        cost_usd=0.50,
        input_tokens=1000,
        output_tokens=500,
        duration_ms=1500,
    )
    return runner


@pytest.fixture
async def orchestrator_with_cost_tracker(test_db, settings_override):
    """Orchestrator with cost tracker enabled."""
    ban_repo = BanRepository(test_db)
    donation_repo = DonationRepository(test_db)
    stats_repo = StatsRepository(test_db)
    cost_tracker = CostTracker(settings_override, stats_repo)
    connection_manager = ConnectionManager()

    return Orchestrator(
        settings=settings_override,
        ban_repo=ban_repo,
        donation_repo=donation_repo,
        connection_manager=connection_manager,
        cost_tracker=cost_tracker,
    )


@pytest.mark.anyio
async def test_orchestrator_records_cost_after_execution(
    orchestrator_with_cost_tracker, mock_agent_runner, test_db
):
    """Test that orchestrator records cost after successful execution."""
    orchestrator_with_cost_tracker._agent_runner = mock_agent_runner

    # Create a sample queue item
    item = QueueItem(
        id="test-prompt-123",
        donor_name="테스트유저",
        donor_id="donor-123",
        prompt="점프 높이 2배로",
        tier=DonationTier.ONE_LINE,
        created_at=datetime.now(UTC),
    )

    # Manually enqueue (bypassing donation flow)
    from app.models.queue import PrioritizedPrompt

    prioritized = PrioritizedPrompt(priority=1, data=item.model_dump())
    await orchestrator_with_cost_tracker._queue.put(prioritized)

    # Process one item
    from app.db.repositories.stats_repo import StatsRepository

    stats_repo = StatsRepository(test_db)

    # Verify no costs before processing
    initial_cost = await stats_repo.get_daily_cost_usd()
    assert initial_cost == 0.0

    # Process queue (with timeout to prevent infinite loop)
    import asyncio

    process_task = asyncio.create_task(orchestrator_with_cost_tracker.process_queue())

    # Wait for item to be processed
    await asyncio.sleep(0.2)

    # Cancel the task
    process_task.cancel()
    try:
        await process_task
    except asyncio.CancelledError:
        pass

    # Verify cost was recorded
    final_cost = await stats_repo.get_daily_cost_usd()
    assert final_cost == 0.50


@pytest.mark.anyio
async def test_orchestrator_pauses_when_budget_exceeded(
    test_db, settings_override, mock_agent_runner
):
    """Test that orchestrator pauses queue processing when budget exceeded."""
    # Set a very low budget
    settings_override.daily_budget_usd = 0.25

    ban_repo = BanRepository(test_db)
    donation_repo = DonationRepository(test_db)
    stats_repo = StatsRepository(test_db)
    cost_tracker = CostTracker(settings_override, stats_repo)
    connection_manager = ConnectionManager()

    orchestrator = Orchestrator(
        settings=settings_override,
        ban_repo=ban_repo,
        donation_repo=donation_repo,
        connection_manager=connection_manager,
        agent_runner=mock_agent_runner,
        cost_tracker=cost_tracker,
    )

    # Create a sample queue item
    item = QueueItem(
        id="test-prompt-123",
        donor_name="테스트유저",
        donor_id="donor-123",
        prompt="점프 높이 2배로",
        tier=DonationTier.ONE_LINE,
        created_at=datetime.now(UTC),
    )

    # Enqueue item
    from app.models.queue import PrioritizedPrompt

    prioritized = PrioritizedPrompt(priority=1, data=item.model_dump())
    await orchestrator._queue.put(prioritized)

    # Process queue (will execute one item and exceed budget)
    import asyncio

    process_task = asyncio.create_task(orchestrator.process_queue())

    # Wait for item to be processed
    await asyncio.sleep(0.2)

    # Verify budget flag is set
    assert orchestrator.is_budget_exceeded() is True

    # Cancel the task
    process_task.cancel()
    try:
        await process_task
    except asyncio.CancelledError:
        pass


@pytest.mark.anyio
async def test_orchestrator_without_cost_tracker_works(
    test_db, settings_override, mock_agent_runner
):
    """Test that orchestrator works without cost tracker (optional dependency)."""
    ban_repo = BanRepository(test_db)
    donation_repo = DonationRepository(test_db)
    connection_manager = ConnectionManager()

    orchestrator = Orchestrator(
        settings=settings_override,
        ban_repo=ban_repo,
        donation_repo=donation_repo,
        connection_manager=connection_manager,
        agent_runner=mock_agent_runner,
        cost_tracker=None,  # No cost tracker
    )

    # Create a sample queue item
    item = QueueItem(
        id="test-prompt-123",
        donor_name="테스트유저",
        donor_id="donor-123",
        prompt="점프 높이 2배로",
        tier=DonationTier.ONE_LINE,
        created_at=datetime.now(UTC),
    )

    # Enqueue item
    from app.models.queue import PrioritizedPrompt

    prioritized = PrioritizedPrompt(priority=1, data=item.model_dump())
    await orchestrator._queue.put(prioritized)

    # Process queue (should work without cost tracker)
    import asyncio

    process_task = asyncio.create_task(orchestrator.process_queue())

    # Wait for item to be processed
    await asyncio.sleep(0.2)

    # Verify budget flag is still False (no tracker to set it)
    assert orchestrator.is_budget_exceeded() is False

    # Cancel the task
    process_task.cancel()
    try:
        await process_task
    except asyncio.CancelledError:
        pass
