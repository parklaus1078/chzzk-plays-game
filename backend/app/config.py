from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

    # Anthropic
    anthropic_api_key: str
    claude_model: str = "claude-sonnet-4-6-20250514"

    # Chzzk
    chzzk_client_id: str
    chzzk_client_secret: str

    # Paths
    unity_project_path: str = "./unity-project"
    db_path: str = "data/chzzk_plays.db"

    # Limits
    daily_budget_usd: float = Field(default=50.0)
    max_queue_size: int = Field(default=50)

    # Server
    host: str = "0.0.0.0"
    port: int = 8080

    # Discord alerts (optional)
    discord_webhook_url: str | None = None
