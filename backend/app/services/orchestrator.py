import asyncio
import uuid
from typing import Protocol

import structlog

from app.config import Settings
from app.core.constants import TIER_CONFIGS, TIER_PRIORITY
from app.core.exceptions import QueueFullError
from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.models.donation import DonationEvent
from app.models.prompt import PromptResult
from app.models.queue import PrioritizedPrompt, PromptState, QueueItem, QueueState
from app.services.ban import BanService
from app.services.cooldown import CooldownTracker
from app.services.security import pre_filter_prompt

logger = structlog.get_logger()


# Protocol definitions for dependencies from future tickets
class AgentRunner(Protocol):
    """Protocol for AgentRunner (Ticket 7)."""

    async def execute_prompt(self, item: QueueItem) -> PromptResult: ...


class GitManager(Protocol):
    """Protocol for GitManager (Ticket 8)."""

    async def revert_last(self) -> bool: ...


class CostTracker(Protocol):
    """Protocol for CostTracker (Ticket 10)."""

    async def record(self, item: QueueItem, result: PromptResult) -> None: ...

    async def check_budget(self) -> tuple[bool, float]: ...


class ConnectionManager(Protocol):
    """Protocol for WebSocket ConnectionManager."""

    async def broadcast(self, data: dict) -> None: ...


class Orchestrator:
    """Central queue manager with state machine and donation handling.

    Manages:
    - asyncio.PriorityQueue with tier-based priority
    - State transitions: QUEUED → RUNNING → DONE/FAILED
    - Ban check, pre-filtering, cooldown enforcement
    - WebSocket broadcasting for UI updates
    """

    def __init__(
        self,
        settings: Settings,
        ban_repo: BanRepository,
        donation_repo: DonationRepository,
        connection_manager: ConnectionManager,
        agent_runner: AgentRunner | None = None,
        git_manager: GitManager | None = None,
        cost_tracker: CostTracker | None = None,
    ):
        self._settings = settings
        self._ban_service = BanService(ban_repo)
        self._donation_repo = donation_repo
        self._connection_manager = connection_manager
        self._agent_runner = agent_runner
        self._git_manager = git_manager
        self._cost_tracker = cost_tracker

        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue(
            maxsize=settings.max_queue_size
        )
        self._cooldown = CooldownTracker()
        self._current: QueueItem | None = None
        self._pending: list[QueueItem] = []
        self._sequence_counter = 0
        self._budget_exceeded = False

    async def handle_donation(self, event: DonationEvent) -> None:
        """Entry point for all donations.

        Performs: ban check → pre-filter → cooldown check → enqueue.

        Raises:
            QueueFullError: If queue is at max capacity
        """
        # 1. Ban check
        if await self._ban_service.is_banned(event.donor_id):
            logger.info(
                "donation_from_banned_user",
                donor_id=event.donor_id,
                donor_name=event.donor_name,
            )
            return

        # 2. Security pre-filter (Layer 1)
        is_safe, reason = pre_filter_prompt(event.message)
        if not is_safe:
            logger.warning(
                "prompt_rejected",
                donor_id=event.donor_id,
                donor_name=event.donor_name,
                reason=reason,
            )
            # Ban the user for security violation
            await self._ban_service.add_ban(
                event.donor_id, reason or "security_filter"
            )
            # Broadcast ban event
            await self._broadcast_ban(event, reason or "security_filter")
            return

        # 3. Cooldown check (log but allow queueing)
        allowed, remaining = self._cooldown.check(event.donor_id, event.tier)
        if not allowed:
            logger.info(
                "cooldown_active",
                donor_id=event.donor_id,
                tier=event.tier,
                remaining_seconds=remaining,
            )

        # 4. Enqueue
        item = QueueItem(
            id=str(uuid.uuid4()),
            donor_name=event.donor_name,
            donor_id=event.donor_id,
            prompt=event.message,
            tier=event.tier,
            state=PromptState.QUEUED,
            created_at=event.timestamp,
        )

        self._sequence_counter += 1
        prioritized = PrioritizedPrompt(
            priority=TIER_PRIORITY[event.tier],
            sequence=self._sequence_counter,
            data=item.model_dump(),
        )

        try:
            self._queue.put_nowait(prioritized)
        except asyncio.QueueFull:
            logger.error(
                "queue_full",
                queue_size=self._settings.max_queue_size,
                donor_id=event.donor_id,
            )
            raise QueueFullError(
                f"Queue full ({self._settings.max_queue_size})"
            ) from None

        # Record cooldown timestamp
        self._cooldown.record(event.donor_id)

        # Update pending list and broadcast
        self._update_pending()
        await self._broadcast_state()

        logger.info(
            "donation_queued",
            prompt_id=item.id,
            donor_id=event.donor_id,
            tier=event.tier,
            queue_size=self._queue.qsize(),
        )

    async def process_queue(self) -> None:
        """Long-running queue processor. One item at a time (non-preemptive).

        This should be run as a background asyncio task.
        """
        logger.info("queue_processor_started")
        while True:
            try:
                # Check budget before processing next item
                if self._cost_tracker is not None and not self._budget_exceeded:
                    within_budget, daily_total = await self._cost_tracker.check_budget()
                    if not within_budget:
                        self._budget_exceeded = True
                        logger.critical(
                            "queue_paused_budget_exceeded",
                            daily_total=daily_total,
                            budget_limit=self._settings.daily_budget_usd,
                        )

                # If budget exceeded, skip processing but keep queue running
                if self._budget_exceeded:
                    await asyncio.sleep(60)  # Check every minute
                    continue

                prioritized = await self._queue.get()
                item = QueueItem(**prioritized.data)

                self._current = item
                self._update_pending()

                try:
                    # Transition to RUNNING
                    await self._transition(item, PromptState.RUNNING)

                    # Execute prompt (if agent_runner available)
                    if self._agent_runner is None:
                        logger.warning(
                            "agent_runner_not_configured",
                            prompt_id=item.id,
                        )
                        await self._transition(item, PromptState.FAILED)
                        continue

                    # Execute with timeout from tier config
                    timeout = TIER_CONFIGS[item.tier].timeout_seconds
                    async with asyncio.timeout(timeout):
                        result = await self._agent_runner.execute_prompt(item)

                    # Record cost and check budget
                    if self._cost_tracker is not None:
                        await self._cost_tracker.record(item, result)
                        within_budget, daily_total = (
                            await self._cost_tracker.check_budget()
                        )
                        if not within_budget:
                            self._budget_exceeded = True

                    # Transition based on result
                    if result.success:
                        await self._transition(item, PromptState.DONE)
                        logger.info(
                            "prompt_completed",
                            prompt_id=item.id,
                            cost_usd=result.cost_usd,
                        )
                    else:
                        await self._transition(item, PromptState.FAILED)
                        logger.error(
                            "prompt_failed",
                            prompt_id=item.id,
                            error=result.error_message,
                        )
                        # Revert on failure
                        if self._git_manager:
                            await self._transition(item, PromptState.REVERTING)
                            await self._git_manager.revert_last()
                            await self._transition(item, PromptState.REVERTED)

                except TimeoutError:
                    logger.error(
                        "prompt_timeout",
                        prompt_id=item.id,
                        timeout_seconds=timeout,
                    )
                    await self._transition(item, PromptState.TIMEOUT)

                except Exception as exc:
                    logger.error(
                        "prompt_execution_error",
                        prompt_id=item.id,
                        error=str(exc),
                        exc_info=True,
                    )
                    await self._transition(item, PromptState.FAILED)

                finally:
                    self._current = None
                    self._queue.task_done()
                    self._update_pending()
                    await self._broadcast_state()

            except Exception as exc:
                logger.error(
                    "queue_processor_error",
                    error=str(exc),
                    exc_info=True,
                )
                await asyncio.sleep(1)  # Prevent tight loop on repeated errors

    async def _transition(self, item: QueueItem, new_state: PromptState) -> None:
        """Explicit state transition with logging and broadcasting."""
        old_state = item.state
        item.state = new_state
        logger.info(
            "state_transition",
            prompt_id=item.id,
            old_state=old_state,
            new_state=new_state,
        )
        await self._broadcast_state()

    def _update_pending(self) -> None:
        """Update the pending list from queue internal state."""
        # Access internal queue data
        # Note: This is a bit fragile but necessary since PriorityQueue doesn't expose pending items
        self._pending = [
            QueueItem(**item.data)
            for item in list(self._queue._queue)  # Access internal list
        ]

    async def _broadcast_state(self) -> None:
        """Broadcast current queue state to WebSocket clients."""
        state = self.get_queue_state()
        await self._connection_manager.broadcast(state.model_dump())

    async def _broadcast_ban(self, event: DonationEvent, reason: str) -> None:
        """Broadcast ban event to WebSocket clients."""
        ban_data = {
            "type": "ban",
            "donor_name": event.donor_name,
            "reason": reason,
        }
        await self._connection_manager.broadcast(ban_data)

    def get_queue_state(self) -> QueueState:
        """Returns current + pending items for the UI."""
        return QueueState(
            current=self._current,
            pending=self._pending,
        )

    def get_cooldown_tracker(self) -> CooldownTracker:
        """Access cooldown tracker (for testing/admin)."""
        return self._cooldown

    def get_queue_size(self) -> int:
        """Get current queue size."""
        return self._queue.qsize()

    def is_budget_exceeded(self) -> bool:
        """Check if daily budget has been exceeded."""
        return self._budget_exceeded

    def reset_budget_flag(self) -> None:
        """Reset budget exceeded flag (e.g., at start of new day)."""
        self._budget_exceeded = False
        logger.info("budget_flag_reset")
