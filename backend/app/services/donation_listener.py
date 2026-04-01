import asyncio
from collections.abc import Awaitable, Callable

import structlog
from chzzkpy import Client, Donation, UserPermission

from app.config import Settings
from app.models.donation import DonationEvent, classify_tier

logger = structlog.get_logger()


class DonationListener:
    def __init__(
        self, settings: Settings, on_donation: Callable[[DonationEvent], Awaitable[None]]
    ):
        self._settings = settings
        self._on_donation = on_donation
        self._client: Client | None = None
        self._running = False
        self._task: asyncio.Task[None] | None = None

    async def run(self) -> None:
        """Long-running task. Start with asyncio.create_task(listener.run())."""
        self._running = True
        self._task = asyncio.current_task()
        backoff = 1.0
        attempt = 0

        try:
            while self._running:
                try:
                    attempt += 1
                    logger.info("donation_listener_connecting", attempt=attempt)
                    await self._connect_and_listen()
                    # Reset backoff on successful connection
                    backoff = 1.0
                    attempt = 0
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    if not self._running:
                        break
                    logger.warning(
                        "donation_listener_disconnected",
                        backoff_seconds=backoff,
                        attempt=attempt,
                        error=str(exc),
                    )
                    await asyncio.sleep(backoff)
                    backoff = min(backoff * 2, 60.0)
        except asyncio.CancelledError:
            pass

    async def _connect_and_listen(self) -> None:
        self._client = Client(
            self._settings.chzzk_client_id,
            self._settings.chzzk_client_secret,
        )

        @self._client.event
        async def on_donation(donation: Donation) -> None:
            tier = classify_tier(donation.pay_amount)
            if tier is None:
                logger.debug(
                    "donation_below_minimum",
                    amount=donation.pay_amount,
                    donor=donation.donator_name,
                )
                return

            event = DonationEvent(
                donor_name=donation.donator_name,
                donor_id=donation.donator_id,
                amount=donation.pay_amount,
                message=donation.donation_text,
                tier=tier,
            )
            logger.info(
                "donation_received",
                donor_id=event.donor_id,
                amount=event.amount,
                tier=event.tier,
            )
            await self._on_donation(event)

        user_client = await self._client.login()
        permission = UserPermission(donation=True)
        await user_client.connect(permission=permission)

    def stop(self) -> None:
        self._running = False
        if self._task is not None:
            self._task.cancel()
