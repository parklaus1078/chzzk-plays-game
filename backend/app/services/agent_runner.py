import asyncio
import sys
import time
from concurrent.futures import ThreadPoolExecutor

import structlog
from claude_agent_sdk import (
    ClaudeAgentOptions,
    HookMatcher,
    ResultMessage,
    query,
)

from app.config import Settings
from app.core.constants import TIER_CONFIGS
from app.models.prompt import PromptResult
from app.models.queue import QueueItem
from app.services.security import security_hook, set_project_root

logger = structlog.get_logger()

# Thread pool for running Claude SDK on Windows (needs ProactorEventLoop)
_sdk_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="claude-sdk")

SYSTEM_PROMPT = """너는 Unity C# 게임 개발자이다.
현재 프로젝트의 Assets/Scripts/ 폴더에서 작업한다.
시각적 오브젝트는 반드시 Unity 기본 프리미티브(Cube, Sphere, Capsule, Cylinder, Plane)만 사용한다.
색상은 new Material()의 color 속성으로 구분한다.
UI는 Unity 내장 Canvas + TextMeshPro를 사용한다.
외부 에셋은 사용하지 않는다.
후원자의 요청을 최대한 수용하되, 현재 게임의 장르와 구조를 유지하면서 구현한다.
코드는 깔끔하고 동작 가능한 상태로 작성한다."""


def _run_query_sync(
    prompt: str, options: ClaudeAgentOptions, timeout_seconds: int
) -> ResultMessage | None:
    """Run claude_agent_sdk.query() synchronously in a thread with its own event loop.

    On Windows, this creates a ProactorEventLoop that supports subprocess spawning.
    On other platforms, uses the default event loop.
    """
    if sys.platform == "win32":
        loop = asyncio.ProactorEventLoop()
    else:
        loop = asyncio.new_event_loop()

    asyncio.set_event_loop(loop)
    try:

        async def _inner():
            result_msg = None
            async with asyncio.timeout(timeout_seconds):
                async for message in query(prompt=prompt, options=options):
                    if isinstance(message, ResultMessage):
                        result_msg = message
            return result_msg

        return loop.run_until_complete(_inner())
    finally:
        loop.close()


async def post_tool_use_hook(
    input_data: dict, tool_use_id: str | None, context: object
) -> dict:
    """Layer 2.5: PostToolUse hook — logs tool execution details."""
    tool_name = input_data.get("tool_name", "")
    is_error = input_data.get("is_error", False)

    logger.info(
        "tool_executed",
        tool=tool_name,
        tool_use_id=tool_use_id,
        success=not is_error,
    )
    return {}


class AgentRunner:
    def __init__(self, settings: Settings):
        self._settings = settings
        self._session_id: str | None = None
        self._current_task: asyncio.Task | None = None
        set_project_root(settings.unity_project_path)

    async def execute_prompt(self, item: QueueItem) -> PromptResult:
        """Execute a donation prompt with tier-specific constraints."""
        tier_config = TIER_CONFIGS[item.tier]
        start_time = time.monotonic()

        # Use query() for independent prompt execution
        options = ClaudeAgentOptions(
            model=self._settings.claude_model,
            cwd=self._settings.unity_project_path,
            system_prompt=SYSTEM_PROMPT,
            allowed_tools=tier_config.allowed_tools,
            max_turns=tier_config.max_turns,
            permission_mode="acceptEdits",
            hooks={
                "PreToolUse": [
                    HookMatcher(matcher=".*", hooks=[security_hook])
                ],
                "PostToolUse": [
                    HookMatcher(matcher=".*", hooks=[post_tool_use_hook])
                ],
            },
        )

        # If resuming session for context continuity
        if self._session_id:
            options.resume = self._session_id

        result_msg: ResultMessage | None = None
        try:
            loop = asyncio.get_running_loop()
            result_msg = await loop.run_in_executor(
                _sdk_executor,
                _run_query_sync,
                item.prompt,
                options,
                tier_config.timeout_seconds,
            )
            if result_msg:
                self._session_id = result_msg.session_id
        except TimeoutError:
            elapsed_ms = int((time.monotonic() - start_time) * 1000)
            logger.warning(
                "prompt_timeout",
                prompt_id=item.id,
                tier=item.tier,
                timeout_seconds=tier_config.timeout_seconds,
                duration_ms=elapsed_ms,
            )
            return PromptResult(
                prompt_id=item.id,
                success=False,
                error_message=f"Timeout after {tier_config.timeout_seconds}s",
                duration_ms=elapsed_ms,
            )

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        if result_msg is None:
            logger.error(
                "prompt_no_result",
                prompt_id=item.id,
                duration_ms=elapsed_ms,
            )
            return PromptResult(
                prompt_id=item.id,
                success=False,
                error_message="No result from agent",
                duration_ms=elapsed_ms,
            )

        logger.info(
            "prompt_completed",
            prompt_id=item.id,
            cost_usd=result_msg.total_cost_usd,
            turns=result_msg.num_turns,
            duration_ms=elapsed_ms,
        )

        return PromptResult(
            prompt_id=item.id,
            success=True,
            cost_usd=result_msg.total_cost_usd,
            input_tokens=result_msg.usage.input_tokens if result_msg.usage else 0,
            output_tokens=result_msg.usage.output_tokens if result_msg.usage else 0,
            duration_ms=elapsed_ms,
            session_id=result_msg.session_id,
        )

    def interrupt(self) -> None:
        """Cancel the currently running prompt execution.

        This method can be called to interrupt a long-running prompt,
        typically triggered by admin intervention or emergency stop.
        """
        if self._current_task and not self._current_task.done():
            self._current_task.cancel()
            logger.warning("prompt_interrupted", task_cancelled=True)
