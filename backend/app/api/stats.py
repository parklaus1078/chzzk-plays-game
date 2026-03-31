"""Statistics endpoints."""

from fastapi import APIRouter, Depends

from app.db.repositories.stats_repo import StatsRepository
from app.dependencies import get_stats_repo
from app.models.stats import SessionStats

router = APIRouter(prefix="/api", tags=["stats"])


@router.get("/stats", response_model=SessionStats)
async def get_session_stats(
    stats_repo: StatsRepository = Depends(get_stats_repo),
):
    """Get aggregate statistics for the entire session.

    Includes donation count, revenue, API costs, success/failure counts.
    """
    stats_data = await stats_repo.get_session_stats()
    return SessionStats(**stats_data)


@router.get("/stats/daily")
async def get_daily_stats(
    stats_repo: StatsRepository = Depends(get_stats_repo),
):
    """Get daily statistics breakdown.

    Returns cost by tier, daily totals, etc.
    """
    cost_by_tier = await stats_repo.get_cost_by_tier()
    return {"cost_by_tier": cost_by_tier}
