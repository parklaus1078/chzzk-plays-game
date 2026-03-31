import structlog
from fastapi import APIRouter, Depends, HTTPException

from app.dependencies import get_privacy_service as get_privacy_service_dep
from app.services.privacy import PrivacyService

logger = structlog.get_logger()
router = APIRouter(prefix="/admin/privacy", tags=["privacy"])


@router.get("/export/{user_id}")
async def export_user_data(
    user_id: str,
    service: PrivacyService = Depends(get_privacy_service_dep),
):
    """PIPA Article 35: Export all personal data for a user.

    Returns JSON with user's donations, ban info, and cost records.
    Admin endpoint — should be protected with authentication in production.
    """
    try:
        data = await service.export_user_data(user_id, actor="admin")
        return data
    except Exception as e:
        logger.error("export_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@router.delete("/delete/{user_id}")
async def delete_user_data(
    user_id: str,
    service: PrivacyService = Depends(get_privacy_service_dep),
):
    """PIPA Article 36: Delete/anonymize user's personal data.

    - Anonymizes donation records (replaces name/ID with hash)
    - Removes ban records entirely
    - Preserves financial data for tax compliance (5 years)

    Admin endpoint — should be protected with authentication in production.
    """
    try:
        await service.delete_user_data(user_id, actor="admin")
        return {"status": "success", "message": f"User {user_id} data anonymized/deleted"}
    except Exception as e:
        logger.error("deletion_failed", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@router.get("/audit-log")
async def get_audit_log(
    limit: int = 100,
    service: PrivacyService = Depends(get_privacy_service_dep),
):
    """Get recent access log entries.

    Returns audit trail of data access/export/deletion actions.
    PIPA requirement: maintain access records for PII.

    Admin endpoint — should be protected with authentication in production.
    """
    try:
        logs = await service._access_log_repo.get_recent(limit)
        return {"logs": logs, "count": len(logs)}
    except Exception as e:
        logger.error("audit_log_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Audit log retrieval failed: {str(e)}")
