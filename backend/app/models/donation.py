from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class DonationTier(StrEnum):
    ONE_LINE = "one_line"
    FEATURE = "feature"
    MAJOR = "major"
    CHAOS = "chaos"


class DonationEvent(BaseModel):
    donor_name: str
    donor_id: str
    amount: int = Field(gt=0)
    message: str
    tier: DonationTier | None = None
    timestamp: datetime = Field(default_factory=datetime.now)


def classify_tier(amount: int) -> DonationTier | None:
    """Classify donation amount into tier. Rounds DOWN to nearest tier threshold."""
    if amount >= 30_000:
        return DonationTier.CHAOS
    elif amount >= 10_000:
        return DonationTier.MAJOR
    elif amount >= 5_000:
        return DonationTier.FEATURE
    elif amount >= 1_000:
        return DonationTier.ONE_LINE
    return None
