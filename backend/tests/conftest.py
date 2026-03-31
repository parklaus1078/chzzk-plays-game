import os
import shutil
from pathlib import Path

import pytest
import pytest_asyncio
from aiosqlite import Connection

from app.config import Settings
from app.db.connection import init_database


# Set test environment variables before any imports
@pytest.fixture(scope="session", autouse=True)
def set_test_env():
    """Set test environment variables for all tests."""
    os.environ["ANTHROPIC_API_KEY"] = "test-key"
    os.environ["CHZZK_CLIENT_ID"] = "test-client-id"
    os.environ["CHZZK_CLIENT_SECRET"] = "test-client-secret"
    os.environ["UNITY_PROJECT_PATH"] = "/tmp/test-unity"
    os.environ["DB_PATH"] = ":memory:"

    # Create test Unity directory
    test_unity_path = Path("/tmp/test-unity")
    test_unity_path.mkdir(parents=True, exist_ok=True)
    (test_unity_path / "Assets").mkdir(exist_ok=True)
    (test_unity_path / "Assets" / "Scripts").mkdir(exist_ok=True)

    yield

    # Cleanup test Unity directory
    if test_unity_path.exists():
        shutil.rmtree(test_unity_path, ignore_errors=True)


@pytest.fixture
def settings_override() -> Settings:
    """Override settings for testing."""
    return Settings(
        anthropic_api_key="test-key",
        chzzk_client_id="test-client-id",
        chzzk_client_secret="test-client-secret",
        unity_project_path="/tmp/test-unity",
        db_path=":memory:",
        daily_budget_usd=10.0,
        max_queue_size=10,
    )


@pytest_asyncio.fixture
async def test_db() -> Connection:
    """In-memory database for testing."""
    db = await init_database(":memory:")
    yield db
    await db.close()
