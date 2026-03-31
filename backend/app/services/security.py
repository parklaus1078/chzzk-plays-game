import re
from pathlib import Path

import structlog

logger = structlog.get_logger()

BLOCKED_PATTERNS = [
    r"\.\./",                                         # Directory traversal
    r"(?:^|[;&|`])\s*(?:curl|wget|ssh|nc|ncat)\b",   # Network commands
    r"(?:^|[;&|`])\s*(?:rm\s+-rf|chmod|chown)\b",    # Destructive commands
    r"/(?:etc|home|root|var|tmp)/",                   # System paths
    r"(?:API_KEY|SECRET|TOKEN|PASSWD|PASSWORD)",      # Secret references
    r"\b(?:eval|exec)\s*\(",                          # Code execution
    r"\b(?:import|from)\s+(?:os|subprocess|shutil)\b",  # Dangerous Python imports
    r"(?:^|[;&|`])\s*(?:python|python3|node|ruby|perl)\s+-", # Script execution
    r"\b(?:env|export)\s+\w+=",                       # Env manipulation
    r"\$\(",                                          # Command substitution
]
BLOCKED_RE = re.compile("|".join(BLOCKED_PATTERNS), re.IGNORECASE)


def pre_filter_prompt(message: str) -> tuple[bool, str | None]:
    """Layer 1: Pre-filter prompt text before sending to Claude.
    Returns (is_safe, denial_reason)."""
    if BLOCKED_RE.search(message):
        return False, "Blocked by pre-filter: dangerous pattern detected"
    return True, None


async def security_hook(
    input_data: dict, tool_use_id: str | None, context: object
) -> dict:
    """Layer 2: PreToolUse hook — inspects every tool call at runtime."""
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    # Check Bash commands against blocked patterns
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if BLOCKED_RE.search(command):
            logger.warning(
                "security_hook_denied",
                tool=tool_name,
                reason="dangerous_pattern",
            )
            return _deny("Blocked dangerous pattern in Bash command")

    # Check file paths for all file-access tools
    if tool_name in ("Read", "Edit", "Write", "Glob", "Grep"):
        file_path = tool_input.get("file_path", "") or tool_input.get("path", "")
        if file_path and not _is_within_project(file_path):
            logger.warning(
                "security_hook_denied",
                tool=tool_name,
                path=file_path,
                reason="outside_project",
            )
            return _deny("File access outside project directory")

    return {}


# Module-level project root — set during app startup
_project_root: str = ""


def set_project_root(path: str) -> None:
    global _project_root
    _project_root = str(Path(path).resolve())


def _is_within_project(file_path: str) -> bool:
    """Check if path resolves within the project root. Prevents symlink attacks."""
    if not _project_root:
        return False
    try:
        resolved = str(Path(file_path).resolve())
        return resolved.startswith(_project_root)
    except (OSError, ValueError):
        return False


def _deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
