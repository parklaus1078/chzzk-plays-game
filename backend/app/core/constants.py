from dataclasses import dataclass

from app.models.donation import DonationTier


@dataclass(frozen=True)
class TierConfig:
    max_turns: int
    allowed_tools: list[str]
    timeout_seconds: int
    cooldown_seconds: int
    min_amount: int  # KRW


TIER_CONFIGS: dict[DonationTier, TierConfig] = {
    DonationTier.ONE_LINE: TierConfig(
        max_turns=1,
        allowed_tools=["Read", "Edit"],
        timeout_seconds=60,
        cooldown_seconds=60,
        min_amount=1_000,
    ),
    DonationTier.FEATURE: TierConfig(
        max_turns=3,
        allowed_tools=["Read", "Edit", "Write", "Bash"],
        timeout_seconds=120,
        cooldown_seconds=180,
        min_amount=5_000,
    ),
    DonationTier.MAJOR: TierConfig(
        max_turns=8,
        allowed_tools=["Read", "Edit", "Write", "Bash", "Glob"],
        timeout_seconds=180,
        cooldown_seconds=300,
        min_amount=10_000,
    ),
    DonationTier.CHAOS: TierConfig(
        max_turns=15,
        allowed_tools=["Read", "Edit", "Write", "Bash", "Glob", "Grep"],
        timeout_seconds=300,
        cooldown_seconds=600,
        min_amount=30_000,
    ),
}

TIER_PRIORITY = {
    DonationTier.CHAOS: 1,
    DonationTier.MAJOR: 2,
    DonationTier.FEATURE: 3,
    DonationTier.ONE_LINE: 4,
}
