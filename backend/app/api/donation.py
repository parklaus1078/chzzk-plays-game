"""Internal donation event endpoint."""

import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.core.exceptions import QueueFullError
from app.dependencies import get_orchestrator
from app.models.donation import DonationEvent
from app.services.orchestrator import Orchestrator

logger = structlog.get_logger()
router = APIRouter(prefix="/api", tags=["donation"])


@router.post("/donation")
async def receive_donation(
    event: DonationEvent,
    orchestrator: Orchestrator = Depends(get_orchestrator),
):
    """Receive donation event and queue for processing.

    Internal endpoint — typically called by donation listener, not directly exposed.
    Can also be used for manual testing/injection.
    """
    try:
        await orchestrator.handle_donation(event)
        logger.info(
            "donation_accepted",
            donor_id=event.donor_id,
            amount=event.amount,
            tier=event.tier,
        )
        return {"status": "queued", "prompt_id": None}
    except QueueFullError as exc:
        logger.error("queue_full", donor_id=event.donor_id, error=str(exc))
        raise HTTPException(status_code=429, detail="Queue is full") from exc
