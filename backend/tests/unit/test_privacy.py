"""Unit tests for PIPA compliance privacy service."""
import pytest_asyncio

from app.db.repositories.access_log_repo import AccessLogRepository
from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.db.repositories.stats_repo import StatsRepository
from app.services.privacy import PrivacyService


@pytest_asyncio.fixture
async def donation_repo(test_db):
    """Donation repository fixture."""
    return DonationRepository(test_db)


@pytest_asyncio.fixture
async def ban_repo(test_db):
    """Ban repository fixture."""
    return BanRepository(test_db)


@pytest_asyncio.fixture
async def stats_repo(test_db):
    """Stats repository fixture."""
    return StatsRepository(test_db)


@pytest_asyncio.fixture
async def access_log_repo(test_db):
    """Access log repository fixture."""
    return AccessLogRepository(test_db)


@pytest_asyncio.fixture
async def privacy_service(donation_repo, ban_repo, stats_repo, access_log_repo):
    """Privacy service fixture."""
    return PrivacyService(donation_repo, ban_repo, stats_repo, access_log_repo)


async def test_export_user_data_includes_donations(privacy_service, donation_repo):
    """Test that export_user_data includes donation records."""
    # Arrange: Create test donation
    await donation_repo.record(
        donor_id="user123",
        donor_name="테스트유저",
        amount=5000,
        prompt="테스트 프롬프트",
        tier="feature",
        status="completed",
    )

    # Act: Export user data
    result = await privacy_service.export_user_data("user123", actor="test")

    # Assert: Verify donations are included
    assert result["user_id"] == "user123"
    assert len(result["donations"]) == 1
    assert result["donations"][0]["donor_name"] == "테스트유저"
    assert result["donations"][0]["amount"] == 5000


async def test_export_user_data_includes_ban(privacy_service, ban_repo):
    """Test that export_user_data includes ban info with reason."""
    # Arrange: Create test ban
    await ban_repo.add("user456", reason="악의적인 명령어 시도")

    # Act: Export user data
    result = await privacy_service.export_user_data("user456", actor="test")

    # Assert: Verify ban is included with reason
    assert result["user_id"] == "user456"
    assert result["ban"] is not None
    assert result["ban"]["reason"] == "악의적인 명령어 시도"


async def test_export_user_data_logs_access(privacy_service, access_log_repo):
    """Test that export_user_data logs access to audit trail."""
    # Act: Export user data
    await privacy_service.export_user_data("user789", actor="admin")

    # Assert: Verify access log entry created
    logs = await access_log_repo.get_recent(limit=10)
    assert len(logs) == 1
    assert logs[0]["action"] == "data_export"
    assert logs[0]["actor"] == "admin"
    assert logs[0]["target_user_id"] == "user789"
    assert "export" in logs[0]["details"].lower()


async def test_delete_user_data_anonymizes_donations(privacy_service, donation_repo):
    """Test that delete_user_data anonymizes donation records."""
    # Arrange: Create test donation
    await donation_repo.record(
        donor_id="user_to_delete",
        donor_name="삭제될사용자",
        amount=10000,
        prompt="테스트 프롬프트",
        tier="major",
        status="completed",
    )

    # Act: Delete user data
    await privacy_service.delete_user_data("user_to_delete", actor="admin")

    # Assert: Verify donor_name is anonymized and donor_id is hashed
    donations = await donation_repo.get_by_donor("user_to_delete", limit=10)
    # Original ID should have no results
    assert len(donations) == 0

    # Check all donations - should find the anonymized one
    all_donations = await donation_repo.get_all(limit=100)
    anonymized = [d for d in all_donations if d["donor_name"] == "삭제됨"]
    assert len(anonymized) == 1
    assert anonymized[0]["donor_name"] == "삭제됨"
    assert anonymized[0]["donor_id"] != "user_to_delete"
    assert len(anonymized[0]["donor_id"]) == 16  # SHA256 hash truncated to 16 chars


async def test_delete_user_data_preserves_financials(privacy_service, donation_repo):
    """Test that delete_user_data preserves amount, tier, and date (tax compliance)."""
    # Arrange: Create test donation with specific amount
    await donation_repo.record(
        donor_id="user_financial",
        donor_name="재무데이터사용자",
        amount=30000,
        prompt="카오스 프롬프트",
        tier="chaos",
        status="completed",
    )

    # Act: Delete user data
    await privacy_service.delete_user_data("user_financial", actor="admin")

    # Assert: Verify financial data (amount, tier, date) is preserved
    all_donations = await donation_repo.get_all(limit=100)
    anonymized = [d for d in all_donations if d["donor_name"] == "삭제됨"]
    assert len(anonymized) == 1
    assert anonymized[0]["amount"] == 30000  # Amount preserved
    assert anonymized[0]["tier"] == "chaos"  # Tier preserved
    assert anonymized[0]["created_at"] is not None  # Date preserved


async def test_delete_user_data_removes_ban(privacy_service, ban_repo):
    """Test that delete_user_data removes ban records entirely."""
    # Arrange: Create test ban
    await ban_repo.add("user_banned", reason="보안 위반")

    # Act: Verify ban exists before deletion
    ban_before = await ban_repo.get("user_banned")
    assert ban_before is not None

    # Delete user data
    await privacy_service.delete_user_data("user_banned", actor="admin")

    # Assert: Verify ban is removed
    ban_after = await ban_repo.get("user_banned")
    assert ban_after is None


async def test_delete_user_data_logs_action(privacy_service, access_log_repo):
    """Test that delete_user_data logs the deletion action."""
    # Arrange: Create test donation (so there's something to delete)
    donation_repo = privacy_service._donation_repo
    await donation_repo.record(
        donor_id="user_logged",
        donor_name="로그테스트",
        amount=1000,
        prompt="테스트",
        tier="one_line",
        status="completed",
    )

    # Act: Delete user data
    await privacy_service.delete_user_data("user_logged", actor="admin")

    # Assert: Verify deletion action logged
    logs = await access_log_repo.get_recent(limit=10)
    deletion_logs = [log for log in logs if log["action"] == "data_deletion"]
    assert len(deletion_logs) == 1
    assert deletion_logs[0]["actor"] == "admin"
    assert deletion_logs[0]["target_user_id"] == "user_logged"
    assert "anonymized" in deletion_logs[0]["details"].lower()


async def test_multiple_donations_anonymized_together(privacy_service, donation_repo):
    """Test that multiple donations from same user are all anonymized."""
    # Arrange: Create multiple donations from same user
    for i in range(3):
        await donation_repo.record(
            donor_id="multi_user",
            donor_name="다중후원자",
            amount=1000 * (i + 1),
            prompt=f"프롬프트 {i+1}",
            tier="one_line",
            status="completed",
        )

    # Act: Delete user data
    await privacy_service.delete_user_data("multi_user", actor="admin")

    # Assert: All donations from this user should be anonymized
    all_donations = await donation_repo.get_all(limit=100)
    anonymized = [d for d in all_donations if d["donor_name"] == "삭제됨"]
    assert len(anonymized) == 3
    # All should have the same anonymized ID
    anonymized_ids = {d["donor_id"] for d in anonymized}
    assert len(anonymized_ids) == 1  # All same hash


async def test_export_empty_user_returns_empty_lists(privacy_service):
    """Test that exporting data for non-existent user returns empty collections."""
    # Act: Export data for user with no records
    result = await privacy_service.export_user_data("nonexistent_user", actor="test")

    # Assert: Empty lists/None for collections
    assert result["user_id"] == "nonexistent_user"
    assert result["donations"] == []
    assert result["ban"] is None

