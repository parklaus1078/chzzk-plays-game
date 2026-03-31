"""Top-level API router aggregator."""

from fastapi import APIRouter

from app.api import admin, donation, health, privacy, queue, stats

# Create main API router
api_router = APIRouter()

# Include all route modules (each defines its own prefix and tags)
api_router.include_router(queue.router)
api_router.include_router(donation.router)
api_router.include_router(stats.router)
api_router.include_router(admin.router)
api_router.include_router(privacy.router)
api_router.include_router(health.router)
