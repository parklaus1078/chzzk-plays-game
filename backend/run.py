"""
Programmatic entry point for the backend server.
"""

import uvicorn

from app.config import Settings


def main() -> None:
    """Start the FastAPI server."""
    settings = Settings()  # type: ignore[call-arg]  # Settings loads from .env file

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
