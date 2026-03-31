from pydantic import BaseModel


class PromptResult(BaseModel):
    prompt_id: str
    success: bool
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    duration_ms: int = 0
    commit_id: str | None = None
    error_message: str | None = None
    session_id: str | None = None
