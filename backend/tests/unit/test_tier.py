import pytest

from app.models.donation import DonationTier, classify_tier


@pytest.mark.parametrize(
    "amount,expected",
    [
        (0, None),
        (999, None),
        (1_000, DonationTier.ONE_LINE),
        (4_999, DonationTier.ONE_LINE),
        (5_000, DonationTier.FEATURE),
        (9_999, DonationTier.FEATURE),
        (10_000, DonationTier.MAJOR),
        (29_999, DonationTier.MAJOR),
        (30_000, DonationTier.CHAOS),
        (100_000, DonationTier.CHAOS),
    ],
)
def test_classify_tier(amount, expected):
    assert classify_tier(amount) == expected
