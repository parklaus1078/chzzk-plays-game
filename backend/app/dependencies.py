"""FastAPI dependency injection."""

from fastapi import Request

from app.db.repositories.access_log_repo import AccessLogRepository
from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.db.repositories.stats_repo import StatsRepository
from app.services.connection_manager import ConnectionManager
from app.services.cost_tracker import CostTracker
from app.services.orchestrator import Orchestrator
from app.services.privacy import PrivacyService


async def get_orchestrator(request: Request) -> Orchestrator:
    """Get orchestrator from app state."""
    return request.app.state.orchestrator


async def get_connection_manager(request: Request) -> ConnectionManager:
    """Get WebSocket connection manager from app state."""
    return request.app.state.connection_manager


async def get_donation_repo(request: Request) -> DonationRepository:
    """Get donation repository from app state."""
    return request.app.state.donation_repo


async def get_ban_repo(request: Request) -> BanRepository:
    """Get ban repository from app state."""
    return request.app.state.ban_repo


async def get_stats_repo(request: Request) -> StatsRepository:
    """Get stats repository from app state."""
    return request.app.state.stats_repo


async def get_access_log_repo(request: Request) -> AccessLogRepository:
    """Get access log repository from app state."""
    return request.app.state.access_log_repo


async def get_privacy_service(request: Request) -> PrivacyService:
    """Get privacy service from app state."""
    return request.app.state.privacy_service


async def get_cost_tracker(request: Request) -> CostTracker:
    """Get cost tracker from app state."""
    return request.app.state.cost_tracker
