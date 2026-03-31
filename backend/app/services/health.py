"""Health monitoring service for system status checks."""

import time
from typing import Protocol

import aiosqlite
import structlog

from app.core.constants import TIER_CONFIGS
from app.models.queue import PromptState, QueueItem

logger = structlog.get_logger()


class CostTracker(Protocol):
    """Protocol for CostTracker."""

    async def check_budget(self) -> tuple[bool, float]: ...


class Orchestrator(Protocol):
    """Protocol for Orchestrator."""

    def get_queue_size(self) -> int: ...

    def get_queue_state(self): ...

    def is_budget_exceeded(self) -> bool: ...


class HealthService:
    """System health monitoring with queue stall detection.

    Monitors:
    - Database connectivity
    - Donation listener status
    - Queue state and size
    - Current prompt execution
    - Daily cost and budget
    - Queue stalls (item running > 2x tier timeout)
    """

    def __init__(
        self,
        db: aiosqlite.Connection,
        orchestrator: Orchestrator,
        cost_tracker: CostTracker,
        daily_budget_usd: float,
    ):
        self._db = db
        self._orchestrator = orchestrator
        self._cost_tracker = cost_tracker
        self._daily_budget_usd = daily_budget_usd
        self._listener_connected = False
        self._last_listener_update = 0.0

    def set_listener_connected(self, connected: bool) -> None:
        """Update donation listener connection status.

        Should be called by the donation listener when connection state changes.
        """
        self._listener_connected = connected
        self._last_listener_update = time.time()
        logger.info("listener_status_updated", connected=connected)

    async def check(self) -> dict:
        """Perform comprehensive health check.

        Returns:
            Dict with health status fields:
            - server_ok: bool
            - db_ok: bool
            - donation_listener_connected: bool
            - queue_size: int
            - current_prompt_id: str | None
            - daily_cost_usd: float
            - budget_remaining_usd: float
            - queue_stalled: bool (if current item running > 2x timeout)
        """
        # Check database
        db_ok = await self._check_db()

        # Check cost tracking
        within_budget, daily_cost = await self._cost_tracker.check_budget()
        budget_remaining = max(0.0, self._daily_budget_usd - daily_cost)

        # Get queue state
        queue_size = self._orchestrator.get_queue_size()
        queue_state = self._orchestrator.get_queue_state()
        current_prompt_id = queue_state.current.id if queue_state.current else None

        # Check for queue stall
        queue_stalled = self._check_queue_stall(queue_state.current)

        return {
            "server_ok": True,
            "db_ok": db_ok,
            "donation_listener_connected": self._listener_connected,
            "queue_size": queue_size,
            "current_prompt_id": current_prompt_id,
            "daily_cost_usd": round(daily_cost, 4),
            "budget_remaining_usd": round(budget_remaining, 4),
            "queue_stalled": queue_stalled,
        }

    async def _check_db(self) -> bool:
        """Check database connectivity."""
        try:
            cursor = await self._db.execute("SELECT 1")
            await cursor.fetchone()
            return True
        except Exception as exc:
            logger.error("db_health_check_failed", error=str(exc))
            return False

    def _check_queue_stall(self, current_item: QueueItem | None) -> bool:
        """Check if current item has been running longer than 2x tier timeout.

        Args:
            current_item: Currently executing queue item, or None

        Returns:
            True if stalled, False otherwise
        """
        if current_item is None:
            return False

        if current_item.state != PromptState.RUNNING:
            return False

        # Calculate elapsed time
        elapsed = time.time() - current_item.created_at.timestamp()

        # Get tier timeout
        tier_config = TIER_CONFIGS.get(current_item.tier)
        if tier_config is None:
            return False

        max_expected = tier_config.timeout_seconds * 2

        if elapsed > max_expected:
            logger.warning(
                "queue_stalled",
                prompt_id=current_item.id,
                tier=current_item.tier,
                elapsed_seconds=elapsed,
                expected_max_seconds=max_expected,
            )
            return True

        return False
