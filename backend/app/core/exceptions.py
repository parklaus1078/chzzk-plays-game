class ChzzkPlaysError(Exception):
    """Base exception."""


class SecurityViolationError(ChzzkPlaysError):
    """Prompt or tool use blocked by security filter."""


class QueueFullError(ChzzkPlaysError):
    """Queue has reached maximum capacity."""


class AgentTimeoutError(ChzzkPlaysError):
    """Claude agent did not complete within the tier timeout."""


class BuildFailedError(ChzzkPlaysError):
    """Unity build failed after agent changes."""


class BannedUserError(ChzzkPlaysError):
    """Donation from a banned user."""


class CooldownActiveError(ChzzkPlaysError):
    """User is still in cooldown period."""


class BudgetExceededError(ChzzkPlaysError):
    """Daily API budget has been exceeded."""
