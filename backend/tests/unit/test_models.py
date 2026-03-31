from app.models.queue import PrioritizedPrompt


def test_priority_ordering():
    chaos = PrioritizedPrompt(priority=1, data={"tier": "chaos"})
    feature = PrioritizedPrompt(priority=3, data={"tier": "feature"})
    assert chaos < feature  # Lower number = higher priority


def test_fifo_within_same_priority():
    first = PrioritizedPrompt(priority=1, data={"order": "first"})
    second = PrioritizedPrompt(priority=1, data={"order": "second"})
    assert first < second  # First created has lower sequence
