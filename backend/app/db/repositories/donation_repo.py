import aiosqlite


class DonationRepository:
    """Repository for donation records with 5-year retention per Korean tax law."""

    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    async def record(
        self,
        donor_id: str,
        donor_name: str,
        amount: int,
        prompt: str,
        tier: str,
        status: str = "queued",
        commit_id: str | None = None,
        error_message: str | None = None,
    ) -> int:
        """Insert a donation record and return the row ID."""
        cursor = await self._db.execute(
            """
            INSERT INTO donations (donor_id, donor_name, amount, prompt, tier, status, commit_id, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (donor_id, donor_name, amount, prompt, tier, status, commit_id, error_message),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_by_donor(self, donor_id: str, limit: int = 10) -> list[dict]:
        """Retrieve donation history for a specific donor."""
        cursor = await self._db.execute(
            """
            SELECT id, donor_id, donor_name, amount, prompt, tier, status, commit_id, error_message, created_at
            FROM donations
            WHERE donor_id = ?
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (donor_id, limit),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def update_status(
        self, donation_id: int, status: str, commit_id: str | None = None, error_message: str | None = None
    ) -> None:
        """Update donation status after processing."""
        await self._db.execute(
            """
            UPDATE donations
            SET status = ?, commit_id = ?, error_message = ?
            WHERE id = ?
            """,
            (status, commit_id, error_message, donation_id),
        )
        await self._db.commit()

    async def get_all(self, limit: int = 100) -> list[dict]:
        """Retrieve all donations (for admin/stats purposes)."""
        cursor = await self._db.execute(
            """
            SELECT id, donor_id, donor_name, amount, prompt, tier, status, commit_id, error_message, created_at
            FROM donations
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]

    async def anonymize_donor(self, donor_id: str, anonymized_id: str) -> None:
        """Anonymize donor PII while preserving financial records for tax compliance.

        Replaces donor_name with '삭제됨' and donor_id with anonymized hash.
        Amount, tier, date remain intact per Korean tax law (5-year retention).
        """
        await self._db.execute(
            """
            UPDATE donations
            SET donor_name = '삭제됨', donor_id = ?
            WHERE donor_id = ?
            """,
            (anonymized_id, donor_id),
        )
        await self._db.commit()
