import structlog

from app.config import Settings
from app.db.repositories.stats_repo import StatsRepository
from app.models.prompt import PromptResult
from app.models.queue import QueueItem

logger = structlog.get_logger()


class CostTracker:
    """Tracks API costs and enforces daily budget limits.

    Records cost for each prompt execution and monitors daily spending
    against configured budget limit.
    """

    def __init__(self, settings: Settings, stats_repo: StatsRepository):
        self._settings = settings
        self._stats_repo = stats_repo

    async def record(self, item: QueueItem, result: PromptResult) -> None:
        """Record cost for a completed prompt execution.

        Args:
            item: Queue item containing donor and tier information
            result: Prompt execution result with cost and token usage
        """
        await self._stats_repo.record(
            prompt_id=item.id,
            donor_id=item.donor_id,
            tier=item.tier,
            cost_usd=result.cost_usd,
            input_tokens=result.input_tokens,
            output_tokens=result.output_tokens,
            duration_ms=result.duration_ms,
        )

        logger.info(
            "cost_recorded",
            prompt_id=item.id,
            donor_id=item.donor_id,
            tier=item.tier,
            cost_usd=result.cost_usd,
        )

    async def check_budget(self) -> tuple[bool, float]:
        """Check if daily budget is exceeded.

        Returns:
            Tuple of (within_budget, daily_total_usd)
        """
        daily_total = await self._stats_repo.get_daily_cost_usd()

        if daily_total >= self._settings.daily_budget_usd:
            logger.critical(
                "daily_budget_exceeded",
                total=daily_total,
                limit=self._settings.daily_budget_usd,
            )
            return False, daily_total

        return True, daily_total

    @staticmethod
    def get_margin(
        donation_amount_krw: int, cost_usd: float, exchange_rate: float = 1450.0
    ) -> float:
        """Calculate profit margin percentage.

        Args:
            donation_amount_krw: Donation amount in Korean Won
            cost_usd: API cost in USD
            exchange_rate: KRW per USD (default: 1450.0)

        Returns:
            Margin percentage (0-100). Returns 0 for zero/negative donations.
        """
        if donation_amount_krw <= 0:
            return 0.0

        cost_krw = cost_usd * exchange_rate
        margin = ((donation_amount_krw - cost_krw) / donation_amount_krw) * 100

        return margin
