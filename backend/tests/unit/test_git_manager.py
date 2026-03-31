import asyncio
import subprocess

import pytest

from app.services.git_manager import GitManager


@pytest.fixture
async def git_repo(tmp_path):
    """Create a temporary git repository for testing."""
    repo_path = tmp_path / "test_repo"
    repo_path.mkdir()

    # Initialize git repo
    proc = await asyncio.create_subprocess_exec(
        "git", "init",
        cwd=str(repo_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await proc.communicate()

    # Configure git user for commits
    await asyncio.create_subprocess_exec(
        "git", "config", "user.email", "test@example.com",
        cwd=str(repo_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    await asyncio.create_subprocess_exec(
        "git", "config", "user.name", "Test User",
        cwd=str(repo_path),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    return repo_path


@pytest.mark.anyio
async def test_auto_commit_creates_commit(git_repo):
    """Test that auto_commit creates a commit successfully."""
    git_manager = GitManager(str(git_repo))

    # Create a test file
    test_file = git_repo / "test.txt"
    test_file.write_text("Hello, World!")

    # Commit the file
    commit_hash = await git_manager.auto_commit("TestDonor", "Add test file")

    # Verify commit hash is valid (40 character hex string)
    assert len(commit_hash) == 40
    assert all(c in "0123456789abcdef" for c in commit_hash)

    # Verify commit exists
    proc = await asyncio.create_subprocess_exec(
        "git", "rev-parse", "HEAD",
        cwd=str(git_repo),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    current_head = stdout.decode().strip()
    assert commit_hash == current_head


@pytest.mark.anyio
async def test_auto_commit_message_format(git_repo):
    """Test that commit message follows [auto] donor: summary format."""
    git_manager = GitManager(str(git_repo))

    # Create a test file
    test_file = git_repo / "feature.txt"
    test_file.write_text("New feature")

    # Commit with specific donor and message
    await git_manager.auto_commit("Alice", "Add new feature")

    # Get the commit message
    proc = await asyncio.create_subprocess_exec(
        "git", "log", "-1", "--pretty=%B",
        cwd=str(git_repo),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    commit_message = stdout.decode().strip()

    # Verify format
    assert commit_message == "[auto] Alice: Add new feature"


@pytest.mark.anyio
async def test_auto_commit_truncates_summary(git_repo):
    """Test that commit summary is truncated to 80 characters."""
    git_manager = GitManager(str(git_repo))

    # Create a test file
    test_file = git_repo / "long.txt"
    test_file.write_text("Long summary test")

    # Create a summary longer than 80 characters
    long_summary = "A" * 100

    # Commit
    await git_manager.auto_commit("Bob", long_summary)

    # Get the commit message
    proc = await asyncio.create_subprocess_exec(
        "git", "log", "-1", "--pretty=%B",
        cwd=str(git_repo),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    commit_message = stdout.decode().strip()

    # Extract the summary part (after "[auto] Bob: ")
    prefix = "[auto] Bob: "
    summary_part = commit_message[len(prefix):]

    # Verify truncation
    assert len(summary_part) == 80
    assert summary_part == "A" * 80


@pytest.mark.anyio
async def test_revert_last_success(git_repo):
    """Test that revert_last successfully reverts a commit."""
    git_manager = GitManager(str(git_repo))

    # Create initial file
    test_file = git_repo / "revert_test.txt"
    test_file.write_text("Initial content")
    await git_manager.auto_commit("Carol", "Initial commit")

    # Modify file
    test_file.write_text("Modified content")
    await git_manager.auto_commit("Carol", "Modify file")

    # Revert the last commit
    result = await git_manager.revert_last()

    # Verify revert succeeded
    assert result is True

    # Verify file content is back to initial
    assert test_file.read_text() == "Initial content"


@pytest.mark.anyio
async def test_has_changes_dirty(git_repo):
    """Test has_changes returns True when there are uncommitted changes."""
    git_manager = GitManager(str(git_repo))

    # Create a new file (untracked)
    test_file = git_repo / "untracked.txt"
    test_file.write_text("Untracked file")

    # Check for changes
    has_changes = await git_manager.has_changes()

    # Should detect the untracked file
    assert has_changes is True


@pytest.mark.anyio
async def test_has_changes_clean(git_repo):
    """Test has_changes returns False for a clean repository."""
    git_manager = GitManager(str(git_repo))

    # Create and commit a file
    test_file = git_repo / "committed.txt"
    test_file.write_text("Committed file")
    await git_manager.auto_commit("Dave", "Add committed file")

    # Check for changes (should be clean now)
    has_changes = await git_manager.has_changes()

    # Should be clean
    assert has_changes is False


@pytest.mark.anyio
async def test_sanitize_name(git_repo):
    """Test that special characters are removed and Korean is preserved."""
    git_manager = GitManager(str(git_repo))

    # Create a test file
    test_file = git_repo / "sanitize.txt"
    test_file.write_text("Test")

    # Commit with special characters and Korean
    await git_manager.auto_commit("테스트User!@#$%", "Test commit")

    # Get the commit message
    proc = await asyncio.create_subprocess_exec(
        "git", "log", "-1", "--pretty=%B",
        cwd=str(git_repo),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    commit_message = stdout.decode().strip()

    # Should preserve Korean and alphanumerics, remove special chars
    assert "테스트User" in commit_message
    assert "!@#$%" not in commit_message


@pytest.mark.anyio
async def test_sanitize_name_truncation(git_repo):
    """Test that donor name is truncated to 30 characters."""
    git_manager = GitManager(str(git_repo))

    # Create a test file
    test_file = git_repo / "truncate.txt"
    test_file.write_text("Test")

    # Commit with a very long name
    long_name = "A" * 50
    await git_manager.auto_commit(long_name, "Test commit")

    # Get the commit message
    proc = await asyncio.create_subprocess_exec(
        "git", "log", "-1", "--pretty=%B",
        cwd=str(git_repo),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    commit_message = stdout.decode().strip()

    # Extract donor name (between "[auto] " and ": ")
    prefix = "[auto] "
    suffix_start = commit_message.index(": ")
    donor_part = commit_message[len(prefix):suffix_start]

    # Should be truncated to 30 characters
    assert len(donor_part) == 30


@pytest.mark.anyio
async def test_auto_commit_multiline_summary(git_repo):
    """Test that newlines in summary are replaced with spaces."""
    git_manager = GitManager(str(git_repo))

    # Create a test file
    test_file = git_repo / "multiline.txt"
    test_file.write_text("Test")

    # Commit with multiline summary
    multiline_summary = "Line 1\nLine 2\nLine 3"
    await git_manager.auto_commit("Eve", multiline_summary)

    # Get the commit message
    proc = await asyncio.create_subprocess_exec(
        "git", "log", "-1", "--pretty=%B",
        cwd=str(git_repo),
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, _ = await proc.communicate()
    commit_message = stdout.decode().strip()

    # Should have spaces instead of newlines
    assert "\n" not in commit_message or commit_message.count("\n") <= 1  # Allow single trailing newline
    assert "Line 1 Line 2 Line 3" in commit_message


@pytest.mark.anyio
async def test_revert_last_failure_on_empty_repo(git_repo):
    """Test that revert_last returns False when there's nothing to revert."""
    git_manager = GitManager(str(git_repo))

    # Try to revert on an empty repo (no commits)
    result = await git_manager.revert_last()

    # Should return False
    assert result is False


@pytest.mark.anyio
async def test_git_error_raises_exception(git_repo):
    """Test that git errors raise CalledProcessError."""
    git_manager = GitManager(str(git_repo))

    # Try to commit without staging anything (git commit with no changes)
    # This should fail and raise CalledProcessError
    with pytest.raises(subprocess.CalledProcessError):
        await git_manager._run("git", "commit", "-m", "test")
