import asyncio
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from claude_agent_sdk import ResultMessage

from app.config import Settings
from app.core.constants import TIER_CONFIGS
from app.models.donation import DonationTier
from app.models.queue import QueueItem
from app.services.agent_runner import AgentRunner


@pytest.fixture
def mock_settings():
    """Create mock Settings with test values."""
    settings = MagicMock(spec=Settings)
    settings.claude_model = "claude-sonnet-4-6-20250514"
    settings.unity_project_path = "/test/unity/project"
    settings.anthropic_api_key = "test-api-key"
    return settings


@pytest.fixture
def sample_queue_item():
    """Create a sample QueueItem for testing."""
    return QueueItem(
        id="test-prompt-001",
        donor_name="TestDonor",
        donor_id="donor123",
        prompt="Add a blue cube",
        tier=DonationTier.ONE_LINE,
        created_at=datetime.now(),
    )


@pytest.fixture
def mock_result_message():
    """Create a mock ResultMessage from Claude Agent SDK."""
    result = MagicMock(spec=ResultMessage)
    result.total_cost_usd = 0.05
    result.session_id = "session-abc123"
    result.num_turns = 1
    result.usage = MagicMock()
    result.usage.input_tokens = 1000
    result.usage.output_tokens = 200
    return result


async def test_execute_prompt_returns_result(
    mock_settings, sample_queue_item, mock_result_message
):
    """Test that execute_prompt returns a PromptResult with all fields populated."""
    runner = AgentRunner(mock_settings)

    async def mock_query(*args, **kwargs):
        yield mock_result_message

    with patch("app.services.agent_runner.query", side_effect=mock_query):
        result = await runner.execute_prompt(sample_queue_item)

    assert result.prompt_id == "test-prompt-001"
    assert result.success is True
    assert result.cost_usd == 0.05
    assert result.input_tokens == 1000
    assert result.output_tokens == 200
    assert result.duration_ms >= 0  # Mocked queries run instantly
    assert result.session_id == "session-abc123"
    assert result.error_message is None


async def test_execute_prompt_timeout():
    """Test that execute_prompt raises TimeoutError when query takes too long."""
    settings = MagicMock(spec=Settings)
    settings.claude_model = "claude-sonnet-4-6-20250514"
    settings.unity_project_path = "/test/unity/project"

    runner = AgentRunner(settings)

    # ONE_LINE tier has 60s timeout
    item = QueueItem(
        id="test-timeout",
        donor_name="TestDonor",
        donor_id="donor123",
        prompt="Add a complex feature",
        tier=DonationTier.ONE_LINE,  # 60s timeout
        created_at=datetime.now(),
    )

    async def slow_query(*args, **kwargs):
        # Simulate a query that takes longer than timeout
        await asyncio.sleep(100)  # 100 seconds
        yield MagicMock(spec=ResultMessage)

    with patch("app.services.agent_runner.query", side_effect=slow_query):
        result = await runner.execute_prompt(item)

    # Should return PromptResult with success=False and timeout error
    assert result.success is False
    assert result.error_message is not None
    assert "Timeout" in result.error_message or "timeout" in result.error_message.lower()
    assert result.prompt_id == "test-timeout"


async def test_tier_config_applied(mock_settings):
    """Test that tier-specific config (max_turns, allowed_tools) is applied."""
    runner = AgentRunner(mock_settings)

    feature_item = QueueItem(
        id="test-feature",
        donor_name="TestDonor",
        donor_id="donor123",
        prompt="Add a health bar",
        tier=DonationTier.FEATURE,
        created_at=datetime.now(),
    )

    mock_result = MagicMock(spec=ResultMessage)
    mock_result.total_cost_usd = 0.10
    mock_result.session_id = "session-xyz"
    mock_result.num_turns = 3
    mock_result.usage = MagicMock()
    mock_result.usage.input_tokens = 2000
    mock_result.usage.output_tokens = 500

    captured_options = None

    async def mock_query(prompt, options):
        nonlocal captured_options
        captured_options = options
        yield mock_result

    with patch("app.services.agent_runner.query", side_effect=mock_query):
        result = await runner.execute_prompt(feature_item)

    # Verify tier config was applied
    feature_config = TIER_CONFIGS[DonationTier.FEATURE]
    assert captured_options is not None
    assert captured_options.max_turns == feature_config.max_turns
    assert captured_options.allowed_tools == feature_config.allowed_tools
    assert captured_options.permission_mode == "acceptEdits"
    assert result.success is True


async def test_cost_tracking(mock_settings, mock_result_message):
    """Test that cost_usd, input_tokens, and output_tokens are captured."""
    runner = AgentRunner(mock_settings)

    item = QueueItem(
        id="test-cost",
        donor_name="TestDonor",
        donor_id="donor123",
        prompt="Test prompt",
        tier=DonationTier.MAJOR,
        created_at=datetime.now(),
    )

    # Set specific cost and token values
    mock_result_message.total_cost_usd = 0.25
    mock_result_message.usage.input_tokens = 5000
    mock_result_message.usage.output_tokens = 1500

    async def mock_query(*args, **kwargs):
        yield mock_result_message

    with patch("app.services.agent_runner.query", side_effect=mock_query):
        result = await runner.execute_prompt(item)

    assert result.cost_usd == 0.25
    assert result.input_tokens == 5000
    assert result.output_tokens == 1500
    assert result.duration_ms >= 0  # Mocked queries run instantly


async def test_session_id_captured(mock_settings):
    """Test that session_id is stored for resume across prompts."""
    runner = AgentRunner(mock_settings)

    # First prompt
    first_item = QueueItem(
        id="test-first",
        donor_name="TestDonor",
        donor_id="donor123",
        prompt="Create a player",
        tier=DonationTier.FEATURE,
        created_at=datetime.now(),
    )

    first_result = MagicMock(spec=ResultMessage)
    first_result.total_cost_usd = 0.10
    first_result.session_id = "session-first-123"
    first_result.num_turns = 2
    first_result.usage = MagicMock()
    first_result.usage.input_tokens = 1500
    first_result.usage.output_tokens = 300

    async def mock_first_query(*args, **kwargs):
        yield first_result

    with patch("app.services.agent_runner.query", side_effect=mock_first_query):
        result1 = await runner.execute_prompt(first_item)

    # Verify session_id was stored
    assert result1.session_id == "session-first-123"
    assert runner._session_id == "session-first-123"

    # Second prompt should use the stored session_id for resume
    second_item = QueueItem(
        id="test-second",
        donor_name="TestDonor2",
        donor_id="donor456",
        prompt="Add enemy",
        tier=DonationTier.FEATURE,
        created_at=datetime.now(),
    )

    second_result = MagicMock(spec=ResultMessage)
    second_result.total_cost_usd = 0.08
    second_result.session_id = "session-second-456"
    second_result.num_turns = 1
    second_result.usage = MagicMock()
    second_result.usage.input_tokens = 1000
    second_result.usage.output_tokens = 250

    captured_options = None

    async def mock_second_query(prompt, options):
        nonlocal captured_options
        captured_options = options
        yield second_result

    with patch("app.services.agent_runner.query", side_effect=mock_second_query):
        result2 = await runner.execute_prompt(second_item)

    # Verify resume was used with previous session_id
    assert captured_options.resume == "session-first-123"
    assert result2.session_id == "session-second-456"
    assert runner._session_id == "session-second-456"


async def test_no_result_from_agent(mock_settings, sample_queue_item):
    """Test that missing ResultMessage is handled gracefully."""
    runner = AgentRunner(mock_settings)

    async def mock_empty_query(*args, **kwargs):
        # Generator that yields nothing
        if False:
            yield

    with patch("app.services.agent_runner.query", side_effect=mock_empty_query):
        result = await runner.execute_prompt(sample_queue_item)

    assert result.success is False
    assert result.error_message == "No result from agent"
    assert result.prompt_id == sample_queue_item.id


async def test_hooks_configured(mock_settings, sample_queue_item, mock_result_message):
    """Test that PreToolUse hook is configured with security_hook."""
    runner = AgentRunner(mock_settings)

    captured_options = None

    async def mock_query(prompt, options):
        nonlocal captured_options
        captured_options = options
        yield mock_result_message

    with patch("app.services.agent_runner.query", side_effect=mock_query):
        await runner.execute_prompt(sample_queue_item)

    # Verify hooks are configured
    assert captured_options is not None
    assert "PreToolUse" in captured_options.hooks
    assert len(captured_options.hooks["PreToolUse"]) == 1
    hook_matcher = captured_options.hooks["PreToolUse"][0]
    assert hook_matcher.matcher == ".*"  # All tools


async def test_system_prompt_in_korean(mock_settings, sample_queue_item, mock_result_message):
    """Test that system prompt is set and in Korean."""
    runner = AgentRunner(mock_settings)

    captured_options = None

    async def mock_query(prompt, options):
        nonlocal captured_options
        captured_options = options
        yield mock_result_message

    with patch("app.services.agent_runner.query", side_effect=mock_query):
        await runner.execute_prompt(sample_queue_item)

    assert captured_options is not None
    assert captured_options.system_prompt is not None
    # Check for Korean characters (UTF-8 range for Hangul)
    assert any("\uac00" <= char <= "\ud7a3" for char in captured_options.system_prompt)
    # Verify Unity-specific content
    assert "Unity" in captured_options.system_prompt
    assert "C#" in captured_options.system_prompt


async def test_post_tool_use_hook_configured(mock_settings, sample_queue_item, mock_result_message):
    """Test that PostToolUse hook is configured for logging."""
    runner = AgentRunner(mock_settings)

    captured_options = None

    async def mock_query(prompt, options):
        nonlocal captured_options
        captured_options = options
        yield mock_result_message

    with patch("app.services.agent_runner.query", side_effect=mock_query):
        await runner.execute_prompt(sample_queue_item)

    # Verify PostToolUse hook is configured
    assert captured_options is not None
    assert "PostToolUse" in captured_options.hooks
    assert len(captured_options.hooks["PostToolUse"]) == 1
    hook_matcher = captured_options.hooks["PostToolUse"][0]
    assert hook_matcher.matcher == ".*"  # All tools


async def test_interrupt_method():
    """Test that interrupt() cancels running task."""
    settings = MagicMock(spec=Settings)
    settings.claude_model = "claude-sonnet-4-6-20250514"
    settings.unity_project_path = "/test/unity/project"

    runner = AgentRunner(settings)

    # Create a mock task
    mock_task = MagicMock()
    mock_task.done.return_value = False
    runner._current_task = mock_task

    # Call interrupt
    runner.interrupt()

    # Verify cancel was called
    mock_task.cancel.assert_called_once()
