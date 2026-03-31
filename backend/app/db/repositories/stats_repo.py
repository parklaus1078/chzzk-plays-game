
import aiosqlite


class StatsRepository:
    """Repository for cost tracking and statistics aggregation."""

    def __init__(self, db: aiosqlite.Connection):
        self._db = db

    async def record(
        self,
        prompt_id: str,
        donor_id: str,
        tier: str,
        cost_usd: float,
        input_tokens: int,
        output_tokens: int,
        duration_ms: int,
    ) -> int:
        """Insert a cost record and return the row ID."""
        cursor = await self._db.execute(
            """
            INSERT INTO cost_records (prompt_id, donor_id, tier, cost_usd, input_tokens, output_tokens, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (prompt_id, donor_id, tier, cost_usd, input_tokens, output_tokens, duration_ms),
        )
        await self._db.commit()
        return cursor.lastrowid

    async def get_daily_cost_usd(self, date: str | None = None) -> float:
        """Sum today's costs (or specific date in YYYY-MM-DD format)."""
        if date is None:
            date_filter = "date(created_at) = date('now')"
            params = ()
        else:
            date_filter = "date(created_at) = ?"
            params = (date,)

        cursor = await self._db.execute(
            f"""
            SELECT COALESCE(SUM(cost_usd), 0.0) as total
            FROM cost_records
            WHERE {date_filter}
            """,
            params,
        )
        row = await cursor.fetchone()
        return row["total"] if row else 0.0

    async def get_session_stats(self) -> dict:
        """Get aggregate stats for the entire session."""
        # Get donation stats
        cursor = await self._db.execute(
            """
            SELECT
                COUNT(*) as total_donations,
                COALESCE(SUM(amount), 0) as total_revenue_krw,
                COALESCE(SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END), 0) as prompts_completed,
                COALESCE(SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END), 0) as prompts_failed,
                COALESCE(SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END), 0) as prompts_rejected
            FROM donations
            """
        )
        donation_stats = await cursor.fetchone()

        # Get cost stats
        cursor = await self._db.execute(
            """
            SELECT COALESCE(SUM(cost_usd), 0.0) as total_api_cost_usd
            FROM cost_records
            """
        )
        cost_stats = await cursor.fetchone()

        return {
            "total_donations": donation_stats["total_donations"],
            "total_revenue_krw": donation_stats["total_revenue_krw"],
            "total_api_cost_usd": cost_stats["total_api_cost_usd"],
            "prompts_completed": donation_stats["prompts_completed"],
            "prompts_failed": donation_stats["prompts_failed"],
            "prompts_rejected": donation_stats["prompts_rejected"],
        }

    async def get_cost_by_tier(self) -> list[dict]:
        """Get cost breakdown by tier."""
        cursor = await self._db.execute(
            """
            SELECT
                tier,
                COUNT(*) as count,
                COALESCE(SUM(cost_usd), 0.0) as total_cost_usd,
                COALESCE(AVG(cost_usd), 0.0) as avg_cost_usd,
                COALESCE(SUM(input_tokens), 0) as total_input_tokens,
                COALESCE(SUM(output_tokens), 0) as total_output_tokens
            FROM cost_records
            GROUP BY tier
            ORDER BY total_cost_usd DESC
            """
        )
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
