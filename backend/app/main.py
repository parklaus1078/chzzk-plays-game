import asyncio
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.config import Settings
from app.core.exceptions import (
    BannedUserError,
    BudgetExceededError,
    QueueFullError,
    SecurityViolationError,
)
from app.core.logging import setup_logging
from app.db.connection import init_database
from app.db.repositories.access_log_repo import AccessLogRepository
from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.db.repositories.stats_repo import StatsRepository
from app.services.agent_runner import AgentRunner
from app.services.connection_manager import ConnectionManager
from app.services.cost_tracker import CostTracker
from app.services.donation_listener import DonationListener
from app.services.git_manager import GitManager
from app.services.health import HealthService
from app.services.orchestrator import Orchestrator
from app.services.privacy import PrivacyService

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown logic."""
    settings = Settings()
    setup_logging()

    logger.info("app_starting", version="1.0.0")

    # Initialize DB
    db = await init_database(settings.db_path)

    # Initialize repositories
    donation_repo = DonationRepository(db)
    ban_repo = BanRepository(db)
    stats_repo = StatsRepository(db)
    access_log_repo = AccessLogRepository(db)

    # Initialize services
    connection_manager = ConnectionManager()
    git_manager = GitManager(settings.unity_project_path)
    cost_tracker = CostTracker(settings, stats_repo)
    privacy_service = PrivacyService(
        donation_repo=donation_repo,
        ban_repo=ban_repo,
        stats_repo=stats_repo,
        access_log_repo=access_log_repo,
    )

    # Initialize agent runner with error handling
    agent_runner = None
    try:
        agent_runner = AgentRunner(settings)
        logger.info("agent_runner_initialized")
    except Exception as exc:
        logger.error(
            "agent_runner_initialization_failed",
            error=str(exc),
            exc_info=True,
        )
        logger.warning("server_starting_without_agent_runner")

    orchestrator = Orchestrator(
        settings=settings,
        ban_repo=ban_repo,
        donation_repo=donation_repo,
        connection_manager=connection_manager,
        agent_runner=agent_runner,
        git_manager=git_manager,
        cost_tracker=cost_tracker,
    )

    # Initialize health service
    health_service = HealthService(
        db=db,
        orchestrator=orchestrator,
        cost_tracker=cost_tracker,
        daily_budget_usd=settings.daily_budget_usd,
    )

    # Store on app state for dependency injection
    app.state.orchestrator = orchestrator
    app.state.connection_manager = connection_manager
    app.state.db = db
    app.state.settings = settings
    app.state.donation_repo = donation_repo
    app.state.ban_repo = ban_repo
    app.state.stats_repo = stats_repo
    app.state.access_log_repo = access_log_repo
    app.state.privacy_service = privacy_service
    app.state.agent_runner = agent_runner
    app.state.git_manager = git_manager
    app.state.cost_tracker = cost_tracker
    app.state.health_service = health_service

    # Start background tasks
    donation_listener = DonationListener(settings, orchestrator.handle_donation)

    # Set up listener status tracking for health monitoring
    original_connect = donation_listener._connect_and_listen
    async def wrapped_connect():
        health_service.set_listener_connected(True)
        try:
            await original_connect()
        finally:
            health_service.set_listener_connected(False)
    donation_listener._connect_and_listen = wrapped_connect

    listener_task = asyncio.create_task(donation_listener.run())
    processor_task = asyncio.create_task(orchestrator.process_queue())

    logger.info("app_started", db_path=settings.db_path)

    yield

    # Shutdown
    logger.info("app_shutting_down")
    donation_listener.stop()
    listener_task.cancel()
    processor_task.cancel()

    # Wait for tasks to cancel
    try:
        await asyncio.gather(listener_task, processor_task, return_exceptions=True)
    except asyncio.CancelledError:
        pass

    await db.close()
    logger.info("app_shutdown_complete")


app = FastAPI(title="Chzzk Plays Gamedev", lifespan=lifespan)

# Include API routes
app.include_router(api_router)

# CORS — localhost only
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:*",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:*",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Exception handlers
@app.exception_handler(SecurityViolationError)
async def security_violation_handler(request: Request, exc: SecurityViolationError):
    logger.warning("security_violation", detail=str(exc))
    return JSONResponse(
        status_code=403,
        content={"detail": "Blocked by security filter"},
    )


@app.exception_handler(QueueFullError)
async def queue_full_handler(request: Request, exc: QueueFullError):
    logger.error("queue_full", detail=str(exc))
    return JSONResponse(
        status_code=429,
        content={"detail": "Queue is full"},
    )


@app.exception_handler(BannedUserError)
async def banned_user_handler(request: Request, exc: BannedUserError):
    logger.info("banned_user_attempt", detail=str(exc))
    return JSONResponse(
        status_code=403,
        content={"detail": "User is banned"},
    )


@app.exception_handler(BudgetExceededError)
async def budget_exceeded_handler(request: Request, exc: BudgetExceededError):
    logger.critical("budget_exceeded_error", detail=str(exc))
    return JSONResponse(
        status_code=503,
        content={"detail": "Daily budget exceeded"},
    )


@app.get("/")
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Chzzk Plays Gamedev"}
