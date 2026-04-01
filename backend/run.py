"""
Programmatic entry point for the backend server.

This module MUST set the Windows event loop policy BEFORE importing uvicorn
to fix the NotImplementedError when Claude Agent SDK spawns subprocesses.

On Windows, uvicorn uses SelectorEventLoop by default, which doesn't support
asyncio.create_subprocess_exec(). By setting WindowsProactorEventLoopPolicy()
before uvicorn starts, we ensure subprocess support is available.
"""

import asyncio
import sys

# CRITICAL: Set event loop policy BEFORE any other imports
# This must happen before uvicorn, FastAPI, or any async code runs
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import uvicorn

from app.config import Settings


def main() -> None:
    """Start the FastAPI server with proper Windows subprocess support."""
    settings = Settings()  # type: ignore[call-arg]  # Settings loads from .env file

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        loop="asyncio",  # Tell uvicorn to respect the existing event loop policy
    )


if __name__ == "__main__":
    main()
