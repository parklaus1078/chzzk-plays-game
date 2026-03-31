from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from itertools import count

from pydantic import BaseModel

from app.models.donation import DonationTier


class PromptState(StrEnum):
    IDLE = "idle"
    FILTERING = "filtering"
    QUEUED = "queued"
    RUNNING = "running"
    BUILDING = "building"
    DONE = "done"
    FAILED = "failed"
    REJECTED = "rejected"
    TIMEOUT = "timeout"
    REVERTING = "reverting"
    REVERTED = "reverted"


_counter = count()


@dataclass(order=True)
class PrioritizedPrompt:
    priority: int
    data: dict = field(compare=False)
    sequence: int = field(default_factory=lambda: next(_counter))


class QueueItem(BaseModel):
    id: str
    donor_name: str
    donor_id: str
    prompt: str
    tier: DonationTier
    state: PromptState = PromptState.QUEUED
    created_at: datetime
    elapsed_seconds: float = 0


class QueueState(BaseModel):
    current: QueueItem | None = None
    pending: list[QueueItem] = []
    recent_completed: QueueItem | None = None
    recent_ban: dict | None = None
