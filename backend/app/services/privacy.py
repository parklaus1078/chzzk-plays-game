import hashlib

import structlog

from app.db.repositories.access_log_repo import AccessLogRepository
from app.db.repositories.ban_repo import BanRepository
from app.db.repositories.donation_repo import DonationRepository
from app.db.repositories.stats_repo import StatsRepository

logger = structlog.get_logger()


class PrivacyService:
    """PIPA compliance: data subject rights (access, deletion, anonymization)."""

    def __init__(
        self,
        donation_repo: DonationRepository,
        ban_repo: BanRepository,
        stats_repo: StatsRepository,
        access_log_repo: AccessLogRepository,
    ):
        self._donation_repo = donation_repo
        self._ban_repo = ban_repo
        self._stats_repo = stats_repo
        self._access_log_repo = access_log_repo

    async def export_user_data(self, user_id: str, actor: str = "system") -> dict:
        """PIPA Article 35: Right to access personal information.

        Returns all PII for a user: donations, ban info, cost records.
        """
        await self._access_log_repo.log_action(
            action="data_export",
            actor=actor,
            target_user_id=user_id,
            details="User data export requested",
        )

        donations = await self._donation_repo.get_by_donor(user_id, limit=1000)
        ban = await self._ban_repo.get(user_id)

        logger.info("user_data_exported", user_id=user_id, actor=actor, donation_count=len(donations))

        return {
            "user_id": user_id,
            "donations": donations,
            "ban": ban,
        }

    async def delete_user_data(self, user_id: str, actor: str = "system") -> None:
        """PIPA Article 36: Right to correction/deletion.

        Anonymizes financial records (tax retention) but removes PII.
        - Donations: donor_name → '삭제됨', donor_id → anonymized hash
        - Bans: Completely removed
        - Financial data (amount, tier, date): Retained for 5 years (Korean tax law)
        """
        anonymized_id = hashlib.sha256(user_id.encode()).hexdigest()[:16]

        # Anonymize donation records
        await self._donation_repo.anonymize_donor(user_id, anonymized_id)

        # Remove ban records entirely
        await self._ban_repo.remove(user_id)

        # Log the deletion action
        await self._access_log_repo.log_action(
            action="data_deletion",
            actor=actor,
            target_user_id=user_id,
            details=f"PII removed, financial records anonymized to {anonymized_id}",
        )

        logger.info("user_data_deleted", user_id=user_id, actor=actor, anonymized_id=anonymized_id)
