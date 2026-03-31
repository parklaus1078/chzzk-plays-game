
import aiosqlite


class BanRepository:
    """Repository for ban list with PIPA compliance (reason required, deletion supported)."""

    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    async def add(self, user_id: str, reason: str, expires_at: str | None = None) -> None:
        """Add a ban with reason and timestamp (PIPA: users have right to know ban reason)."""
        await self._db.execute(
            """
            INSERT OR REPLACE INTO bans (user_id, reason, expires_at)
            VALUES (?, ?, ?)
            """,
            (user_id, reason, expires_at),
        )
        await self._db.commit()

    async def is_banned(self, user_id: str) -> bool:
        """Check if user is currently banned."""
        cursor = await self._db.execute(
            """
            SELECT user_id FROM bans
            WHERE user_id = ?
            AND (expires_at IS NULL OR expires_at > datetime('now'))
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return row is not None

    async def remove(self, user_id: str) -> None:
        """Remove a ban (PIPA: right-to-deletion)."""
        await self._db.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
        await self._db.commit()

    async def get_all(self) -> list[dict]:
        """List all bans (for admin review)."""
        cursor = await self._db.execute(
            """
            SELECT user_id, reason, banned_at, expires_at
            FROM bans
            ORDER BY banned_at DESC
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get(self, user_id: str) -> dict | None:
        """Get ban details for a specific user."""
        cursor = await self._db.execute(
            """
            SELECT user_id, reason, banned_at, expires_at
            FROM bans
            WHERE user_id = ?
            """,
            (user_id,),
        )
        row = await cursor.fetchone()
        return dict(row) if row else None
