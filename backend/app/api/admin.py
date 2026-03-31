"""Admin endpoints for ban management and controls."""

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.db.repositories.access_log_repo import AccessLogRepository
from app.db.repositories.ban_repo import BanRepository
from app.dependencies import get_access_log_repo, get_ban_repo

logger = structlog.get_logger()
router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.post("/ban/{user_id}")
async def ban_user(
    user_id: str,
    reason: str,
    ban_repo: BanRepository = Depends(get_ban_repo),
    access_log_repo: AccessLogRepository = Depends(get_access_log_repo),
):
    """Ban a user with a reason.

    PIPA compliance: reason is required, logged to access_log.
    """
    await ban_repo.add(user_id, reason)
    await access_log_repo.log_action(
        action="ban_user",
        actor="admin",
        target_user_id=user_id,
        details=f"reason: {reason}",
    )
    logger.info("user_banned", user_id=user_id, reason=reason)
    return {"status": "banned", "user_id": user_id, "reason": reason}


@router.delete("/ban/{user_id}")
async def unban_user(
    user_id: str,
    ban_repo: BanRepository = Depends(get_ban_repo),
    access_log_repo: AccessLogRepository = Depends(get_access_log_repo),
):
    """Unban a user.

    PIPA compliance: deletion logged to access_log.
    """
    ban = await ban_repo.get(user_id)
    if ban is None:
        raise HTTPException(status_code=404, detail="User not banned")

    await ban_repo.remove(user_id)
    await access_log_repo.log_action(
        action="unban_user",
        actor="admin",
        target_user_id=user_id,
    )
    logger.info("user_unbanned", user_id=user_id)
    return {"status": "unbanned", "user_id": user_id}


@router.get("/bans")
async def get_all_bans(ban_repo: BanRepository = Depends(get_ban_repo)):
    """List all bans for admin review."""
    bans = await ban_repo.get_all()
    return {"bans": bans, "count": len(bans)}
