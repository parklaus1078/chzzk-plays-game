from datetime import UTC, datetime

import pytest

from app.config import Settings
from app.db.repositories.stats_repo import StatsRepository
from app.models.donation import DonationTier
from app.models.prompt import PromptResult
from app.models.queue import QueueItem
from app.services.cost_tracker import CostTracker


@pytest.fixture
def settings():
    """Test settings with daily budget."""
    return Settings(
        anthropic_api_key="test-key",
        chzzk_client_id="test-id",
        chzzk_client_secret="test-secret",
        daily_budget_usd=50.0,
    )


@pytest.fixture
async def stats_repo(test_db):
    """Stats repository with test database."""
    return StatsRepository(test_db)


@pytest.fixture
async def cost_tracker(settings, stats_repo):
    """CostTracker instance for testing."""
    return CostTracker(settings, stats_repo)


@pytest.fixture
def sample_queue_item():
    """Sample queue item for testing."""
    return QueueItem(
        id="test-prompt-123",
        donor_name="테스트유저",
        donor_id="donor-123",
        prompt="점프 높이 2배로",
        tier=DonationTier.ONE_LINE,
        created_at=datetime.now(UTC),
    )


@pytest.fixture
def sample_result():
    """Sample prompt result for testing."""
    return PromptResult(
        prompt_id="test-prompt-123",
        success=True,
        cost_usd=0.29,
        input_tokens=15000,
        output_tokens=4000,
        duration_ms=1500,
    )


@pytest.mark.anyio
async def test_record_cost(cost_tracker, sample_queue_item, sample_result, stats_repo):
    """Test cost recording persists to database."""
    await cost_tracker.record(sample_queue_item, sample_result)

    # Verify record was inserted
    daily_cost = await stats_repo.get_daily_cost_usd()
    assert daily_cost == 0.29


@pytest.mark.anyio
async def test_check_budget_within_limit(
    cost_tracker, sample_queue_item, sample_result, stats_repo
):
    """Test budget check when under limit."""
    # Record $10 of costs (budget is $50)
    for i in range(10):
        item = QueueItem(
            id=f"prompt-{i}",
            donor_name="donor",
            donor_id=f"donor-{i}",
            prompt="test",
            tier=DonationTier.ONE_LINE,
            created_at=datetime.now(UTC),
        )
        result = PromptResult(
            prompt_id=f"prompt-{i}",
            success=True,
            cost_usd=1.0,
            input_tokens=1000,
            output_tokens=500,
            duration_ms=1000,
        )
        await cost_tracker.record(item, result)

    within_budget, total = await cost_tracker.check_budget()
    assert within_budget is True
    assert total == 10.0


@pytest.mark.anyio
async def test_check_budget_exceeded(
    cost_tracker, sample_queue_item, sample_result, settings
):
    """Test budget check when limit exceeded."""
    # Record $55 of costs (budget is $50)
    for i in range(55):
        item = QueueItem(
            id=f"prompt-{i}",
            donor_name="donor",
            donor_id=f"donor-{i}",
            prompt="test",
            tier=DonationTier.ONE_LINE,
            created_at=datetime.now(UTC),
        )
        result = PromptResult(
            prompt_id=f"prompt-{i}",
            success=True,
            cost_usd=1.0,
            input_tokens=1000,
            output_tokens=500,
            duration_ms=1000,
        )
        await cost_tracker.record(item, result)

    within_budget, total = await cost_tracker.check_budget()
    assert within_budget is False
    assert total == 55.0


def test_margin_calculation():
    """Test margin calculation with typical values."""
    # 5000 KRW donation, $0.29 cost, 1450 KRW/USD
    # Cost in KRW: 0.29 * 1450 = 420.5
    # Margin: (5000 - 420.5) / 5000 * 100 = 91.59%
    margin = CostTracker.get_margin(
        donation_amount_krw=5000, cost_usd=0.29, exchange_rate=1450.0
    )
    assert margin == pytest.approx(91.59, rel=0.01)


def test_margin_zero_donation():
    """Test margin returns 0 for zero donation."""
    margin = CostTracker.get_margin(
        donation_amount_krw=0, cost_usd=0.29, exchange_rate=1450.0
    )
    assert margin == 0.0


def test_margin_with_custom_exchange_rate():
    """Test margin calculation with custom exchange rate."""
    # 10000 KRW donation, $1.0 cost, 1200 KRW/USD
    # Cost in KRW: 1.0 * 1200 = 1200
    # Margin: (10000 - 1200) / 10000 * 100 = 88%
    margin = CostTracker.get_margin(
        donation_amount_krw=10000, cost_usd=1.0, exchange_rate=1200.0
    )
    assert margin == pytest.approx(88.0, rel=0.01)


def test_margin_negative_donation():
    """Test margin returns 0 for negative donation."""
    margin = CostTracker.get_margin(
        donation_amount_krw=-1000, cost_usd=0.5, exchange_rate=1450.0
    )
    assert margin == 0.0


@pytest.mark.anyio
async def test_multiple_cost_records(cost_tracker, stats_repo):
    """Test recording multiple costs accumulates correctly."""
    costs = [0.10, 0.25, 0.15, 0.30]

    for i, cost in enumerate(costs):
        item = QueueItem(
            id=f"prompt-{i}",
            donor_name=f"donor-{i}",
            donor_id=f"donor-id-{i}",
            prompt="test prompt",
            tier=DonationTier.FEATURE,
            created_at=datetime.now(UTC),
        )
        result = PromptResult(
            prompt_id=f"prompt-{i}",
            success=True,
            cost_usd=cost,
            input_tokens=1000,
            output_tokens=500,
            duration_ms=1000,
        )
        await cost_tracker.record(item, result)

    daily_cost = await stats_repo.get_daily_cost_usd()
    assert daily_cost == pytest.approx(sum(costs), rel=0.001)
