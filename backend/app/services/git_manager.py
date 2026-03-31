import asyncio
import re
import subprocess

import structlog

logger = structlog.get_logger()


class GitManager:
    def __init__(self, repo_path: str):
        self._repo_path = repo_path

    async def auto_commit(self, donor_name: str, prompt_summary: str) -> str:
        """Commit all changes. Returns commit hash."""
        sanitized_name = self._sanitize(donor_name)
        summary = prompt_summary[:80].replace("\n", " ")
        message = f"[auto] {sanitized_name}: {summary}"

        await self._run("git", "add", "-A")
        await self._run("git", "commit", "-m", message)
        result = await self._run("git", "rev-parse", "HEAD")
        commit_hash = result.strip()
        logger.info("git_auto_commit", commit=commit_hash, donor=sanitized_name)
        return commit_hash

    async def revert_last(self) -> bool:
        """Revert last commit. Returns True on success."""
        try:
            await self._run("git", "revert", "HEAD", "--no-edit")
            logger.info("git_auto_revert_success")
            return True
        except subprocess.CalledProcessError:
            logger.error("git_auto_revert_failed")
            return False

    async def has_changes(self) -> bool:
        """Check if working tree has uncommitted changes."""
        result = await self._run("git", "status", "--porcelain")
        return bool(result.strip())

    async def _run(self, *args: str) -> str:
        proc = await asyncio.create_subprocess_exec(
            *args,
            cwd=self._repo_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise subprocess.CalledProcessError(
                proc.returncode, args, stdout, stderr
            )
        return stdout.decode()

    @staticmethod
    def _sanitize(name: str) -> str:
        """Remove characters that could break git commit messages."""
        return re.sub(r"[^\w\s가-힣-]", "", name).strip()[:30]
