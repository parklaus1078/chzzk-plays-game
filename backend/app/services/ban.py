import structlog

from app.db.repositories.ban_repo import BanRepository

logger = structlog.get_logger()


class BanService:
    """Ban check service with access logging for PIPA compliance."""

    def __init__(self, ban_repo: BanRepository):
        self._ban_repo = ban_repo

    async def is_banned(self, user_id: str) -> bool:
        """Check if user is banned and log access for PIPA compliance."""
        is_banned = await self._ban_repo.is_banned(user_id)
        if is_banned:
            logger.info(
                "ban_check_blocked",
                user_id=user_id,
                action="donation_rejected",
            )
        return is_banned

    async def add_ban(
        self, user_id: str, reason: str, expires_at: str | None = None
    ) -> None:
        """Add a ban with reason (PIPA: users have right to know ban reason)."""
        await self._ban_repo.add(user_id, reason, expires_at)
        logger.warning(
            "user_banned",
            user_id=user_id,
            reason=reason,
            expires_at=expires_at,
        )

    async def remove_ban(self, user_id: str) -> None:
        """Remove a ban (PIPA: right-to-deletion)."""
        await self._ban_repo.remove(user_id)
        logger.info("user_unbanned", user_id=user_id)

    async def get_ban_details(self, user_id: str) -> dict | None:
        """Get ban details for a specific user."""
        return await self._ban_repo.get(user_id)

    async def get_all_bans(self) -> list[dict]:
        """List all bans for admin review."""
        return await self._ban_repo.get_all()
