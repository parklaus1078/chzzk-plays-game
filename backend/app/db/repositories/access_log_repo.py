import aiosqlite


class AccessLogRepository:
    """Repository for access audit log (PIPA compliance: maintain access records for PII)."""

    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    async def log_action(
        self,
        action: str,
        actor: str,
        target_user_id: str | None = None,
        details: str | None = None,
    ) -> int:
        """Log an access action for audit trail."""
        cursor = await self._db.execute(
            """
            INSERT INTO access_log (action, actor, target_user_id, details)
            VALUES (?, ?, ?, ?)
            """,
            (action, actor, target_user_id, details),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_recent(self, limit: int = 100) -> list[dict]:
        """Retrieve recent access log entries."""
        cursor = await self._db.execute(
            """
            SELECT id, action, actor, target_user_id, details, created_at
            FROM access_log
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def get_by_user(self, user_id: str, limit: int = 50) -> list[dict]:
        """Retrieve access log entries for a specific user."""
        cursor = await self._db.execute(
            """
            SELECT id, action, actor, target_user_id, details, created_at
            FROM access_log
            WHERE target_user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (user_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
