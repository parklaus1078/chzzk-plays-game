from datetime import datetime

from pydantic import BaseModel

from app.models.donation import DonationTier


class CostRecord(BaseModel):
    prompt_id: str
    donor_id: str
    tier: DonationTier
    cost_usd: float
    input_tokens: int
    output_tokens: int
    duration_ms: int
    timestamp: datetime


class SessionStats(BaseModel):
    total_donations: int = 0
    total_revenue_krw: int = 0
    total_api_cost_usd: float = 0.0
    prompts_completed: int = 0
    prompts_failed: int = 0
    prompts_rejected: int = 0


class DailyStats(BaseModel):
    date: str
    donation_count: int
    revenue_krw: int
    api_cost_usd: float
    margin_percent: float
