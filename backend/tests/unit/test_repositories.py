"""Unit tests for repository layer with in-memory SQLite."""
import aiosqlite
import pytest
import pytest_asyncio

from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.db.repositories.stats_repo import StatsRepository


@pytest_asyncio.fixture
async def db():
    """In-memory database for tests."""
    conn = await aiosqlite.connect(":memory:")
    await conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = aiosqlite.Row

    # Run migrations
    from pathlib import Path
    migrations_dir = Path(__file__).parent.parent.parent / "app" / "db" / "migrations"
    migration_file = migrations_dir / "001_initial.sql"
    migration_sql = migration_file.read_text()
    await conn.executescript(migration_sql)
    await conn.commit()

    yield conn
    await conn.close()


@pytest_asyncio.fixture
async def donation_repo(db):
    """DonationRepository fixture."""
    return DonationRepository(db)


@pytest_asyncio.fixture
async def ban_repo(db):
    """BanRepository fixture."""
    return BanRepository(db)


@pytest_asyncio.fixture
async def stats_repo(db):
    """StatsRepository fixture."""
    return StatsRepository(db)


# ============================================================================
# DonationRepository Tests
# ============================================================================


async def test_record_donation(donation_repo):
    """Test inserting a donation and retrieving it."""
    donation_id = await donation_repo.record(
        donor_id="user123",
        donor_name="TestUser",
        amount=5000,
        prompt="Add a health bar",
        tier="feature",
        status="queued",
    )

    assert donation_id is not None
    assert donation_id > 0

    # Verify retrieval
    donations = await donation_repo.get_by_donor("user123")
    assert len(donations) == 1
    assert donations[0]["donor_name"] == "TestUser"
    assert donations[0]["amount"] == 5000
    assert donations[0]["tier"] == "feature"


async def test_get_donations_by_donor(donation_repo):
    """Test filtering donations by donor_id."""
    # Insert multiple donations from different users
    await donation_repo.record("user1", "Alice", 1000, "Fix bug", "one_line")
    await donation_repo.record("user2", "Bob", 5000, "Add feature", "feature")
    await donation_repo.record("user1", "Alice", 10000, "Refactor", "major")

    # Get donations for user1
    donations = await donation_repo.get_by_donor("user1")
    assert len(donations) == 2
    # Verify both amounts are present (order may vary due to same timestamp)
    amounts = {d["amount"] for d in donations}
    assert amounts == {1000, 10000}
    assert all(d["donor_name"] == "Alice" for d in donations)

    # Get donations for user2
    donations = await donation_repo.get_by_donor("user2")
    assert len(donations) == 1
    assert donations[0]["donor_name"] == "Bob"


async def test_update_donation_status(donation_repo):
    """Test updating donation status after processing."""
    donation_id = await donation_repo.record(
        donor_id="user123",
        donor_name="TestUser",
        amount=5000,
        prompt="Test prompt",
        tier="feature",
        status="queued",
    )

    # Update to completed
    await donation_repo.update_status(
        donation_id, status="completed", commit_id="abc123"
    )

    # Verify update
    donations = await donation_repo.get_by_donor("user123")
    assert donations[0]["status"] == "completed"
    assert donations[0]["commit_id"] == "abc123"

    # Update to failed with error
    await donation_repo.update_status(
        donation_id, status="failed", error_message="Timeout"
    )

    donations = await donation_repo.get_by_donor("user123")
    assert donations[0]["status"] == "failed"
    assert donations[0]["error_message"] == "Timeout"


# ============================================================================
# BanRepository Tests
# ============================================================================


async def test_add_ban(ban_repo):
    """Test adding a ban with reason."""
    await ban_repo.add("malicious_user", "Security violation: attempted directory traversal")

    # Verify ban was added
    bans = await ban_repo.get_all()
    assert len(bans) == 1
    assert bans[0]["user_id"] == "malicious_user"
    assert "directory traversal" in bans[0]["reason"]


async def test_is_banned_true(ban_repo):
    """Test checking if a banned user is banned."""
    await ban_repo.add("banned_user", "Spam")

    is_banned = await ban_repo.is_banned("banned_user")
    assert is_banned is True


async def test_is_banned_false(ban_repo):
    """Test checking if a non-banned user is not banned."""
    is_banned = await ban_repo.is_banned("innocent_user")
    assert is_banned is False


async def test_remove_ban(ban_repo):
    """Test removing a ban (PIPA right-to-deletion)."""
    await ban_repo.add("temp_ban", "Minor infraction")

    # Verify banned
    assert await ban_repo.is_banned("temp_ban") is True

    # Remove ban
    await ban_repo.remove("temp_ban")

    # Verify no longer banned
    assert await ban_repo.is_banned("temp_ban") is False
    bans = await ban_repo.get_all()
    assert len(bans) == 0


async def test_get_all_bans(ban_repo):
    """Test listing all bans."""
    await ban_repo.add("user1", "Reason 1")
    await ban_repo.add("user2", "Reason 2")
    await ban_repo.add("user3", "Reason 3")

    bans = await ban_repo.get_all()
    assert len(bans) == 3
    user_ids = [ban["user_id"] for ban in bans]
    assert "user1" in user_ids
    assert "user2" in user_ids
    assert "user3" in user_ids


async def test_ban_with_expiry(ban_repo):
    """Test ban with expiration date."""
    # Add ban that expires in the future
    await ban_repo.add("temp_user", "Temporary ban", expires_at="2099-12-31 23:59:59")
    assert await ban_repo.is_banned("temp_user") is True

    # Add ban that already expired
    await ban_repo.add("expired_user", "Old ban", expires_at="2020-01-01 00:00:00")
    assert await ban_repo.is_banned("expired_user") is False


# ============================================================================
# StatsRepository Tests
# ============================================================================


async def test_record_cost(stats_repo):
    """Test inserting a cost record."""
    record_id = await stats_repo.record(
        prompt_id="prompt_123",
        donor_id="user_456",
        tier="feature",
        cost_usd=0.045,
        input_tokens=1000,
        output_tokens=500,
        duration_ms=5000,
    )

    assert record_id is not None
    assert record_id > 0


async def test_get_daily_cost(stats_repo):
    """Test summing today's costs."""
    # Insert multiple cost records for today
    await stats_repo.record("p1", "u1", "one_line", 0.01, 100, 50, 1000)
    await stats_repo.record("p2", "u2", "feature", 0.05, 500, 250, 3000)
    await stats_repo.record("p3", "u3", "major", 0.10, 1000, 500, 5000)

    total = await stats_repo.get_daily_cost_usd()
    assert total == pytest.approx(0.16, abs=0.001)


async def test_get_session_stats(stats_repo, donation_repo):
    """Test aggregate session statistics."""
    # Insert donations
    await donation_repo.record("u1", "Alice", 5000, "Prompt 1", "feature", status="completed")
    await donation_repo.record("u2", "Bob", 10000, "Prompt 2", "major", status="completed")
    await donation_repo.record("u3", "Charlie", 1000, "Prompt 3", "one_line", status="failed")
    await donation_repo.record("u4", "Dave", 30000, "Prompt 4", "chaos", status="rejected")

    # Insert cost records
    await stats_repo.record("p1", "u1", "feature", 0.05, 500, 250, 3000)
    await stats_repo.record("p2", "u2", "major", 0.10, 1000, 500, 5000)

    stats = await stats_repo.get_session_stats()

    assert stats["total_donations"] == 4
    assert stats["total_revenue_krw"] == 46000
    assert stats["total_api_cost_usd"] == pytest.approx(0.15, abs=0.001)
    assert stats["prompts_completed"] == 2
    assert stats["prompts_failed"] == 1
    assert stats["prompts_rejected"] == 1


async def test_get_cost_by_tier(stats_repo):
    """Test cost breakdown by tier."""
    await stats_repo.record("p1", "u1", "one_line", 0.01, 100, 50, 1000)
    await stats_repo.record("p2", "u2", "one_line", 0.01, 100, 50, 1000)
    await stats_repo.record("p3", "u3", "feature", 0.05, 500, 250, 3000)
    await stats_repo.record("p4", "u4", "major", 0.10, 1000, 500, 5000)

    breakdown = await stats_repo.get_cost_by_tier()

    assert len(breakdown) == 3
    # Should be ordered by total_cost_usd DESC
    assert breakdown[0]["tier"] == "major"
    assert breakdown[0]["total_cost_usd"] == pytest.approx(0.10)
    assert breakdown[1]["tier"] == "feature"
    assert breakdown[1]["total_cost_usd"] == pytest.approx(0.05)
    assert breakdown[2]["tier"] == "one_line"
    assert breakdown[2]["count"] == 2
    assert breakdown[2]["total_cost_usd"] == pytest.approx(0.02)


# ============================================================================
# SQL Injection Prevention Tests
# ============================================================================


async def test_parameterized_queries(donation_repo, ban_repo):
    """Test that parameterized queries prevent SQL injection."""
    # Try to inject SQL through donor_name
    malicious_name = "Robert'; DROP TABLE donations; --"
    await donation_repo.record(
        donor_id="attacker",
        donor_name=malicious_name,
        amount=1000,
        prompt="Innocent prompt",
        tier="one_line",
    )

    # Verify donation was inserted with the literal string
    donations = await donation_repo.get_by_donor("attacker")
    assert len(donations) == 1
    assert donations[0]["donor_name"] == malicious_name

    # Try to inject through ban reason
    malicious_reason = "Banned'; DELETE FROM bans WHERE '1'='1"
    await ban_repo.add("attacker2", malicious_reason)

    bans = await ban_repo.get_all()
    # Should have the previous ban plus this one
    assert len(bans) == 1
    assert bans[0]["reason"] == malicious_reason
