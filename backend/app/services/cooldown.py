import asyncio

from app.core.constants import TIER_CONFIGS
from app.models.donation import DonationTier


class CooldownTracker:
    """Tracks per-user cooldowns using event loop time for testability."""

    def __init__(self):
        self._last_donation: dict[str, float] = {}  # user_id -> loop time

    def check(self, user_id: str, tier: DonationTier) -> tuple[bool, float]:
        """Returns (is_allowed, remaining_seconds). Uses event loop time for mockability."""
        now = asyncio.get_event_loop().time()
        last = self._last_donation.get(user_id, 0.0)
        cooldown = TIER_CONFIGS[tier].cooldown_seconds
        elapsed = now - last
        if elapsed >= cooldown:
            return True, 0.0
        return False, cooldown - elapsed

    def record(self, user_id: str) -> None:
        """Record a donation timestamp for cooldown tracking."""
        self._last_donation[user_id] = asyncio.get_event_loop().time()

    def reset(self, user_id: str) -> None:
        """Reset cooldown for a specific user (testing or admin override)."""
        self._last_donation.pop(user_id, None)

    def clear_all(self) -> None:
        """Clear all cooldown records (testing or session reset)."""
        self._last_donation.clear()
