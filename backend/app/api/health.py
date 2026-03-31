"""Health monitoring API endpoint."""

from fastapi import APIRouter, Depends, Request

from app.services.health import HealthService

router = APIRouter(prefix="/api", tags=["health"])


async def get_health_service(request: Request) -> HealthService:
    """Get health service from app state."""
    return request.app.state.health_service


@router.get("/health")
async def health_check(
    health_service: HealthService = Depends(get_health_service),
) -> dict:
    """Comprehensive health check endpoint.

    Returns system health status including:
    - Server status
    - Database connectivity
    - Donation listener connection
    - Queue metrics
    - Cost tracking
    - Budget status

    Returns:
        JSON with health status fields
    """
    return await health_service.check()
