"""
Git repository update utilities for auto-update functionality.

Handles checking git status, stashing changes, and pulling updates from remote.
"""

import logging
import subprocess
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


def run_git_command(args: list[str], cwd: Optional[str] = None) -> tuple[bool, str]:
    """
    Execute a git command and return success status and output.

    Args:
        args: Git command arguments (e.g., ["status", "--porcelain"])
        cwd: Working directory for command execution

    Returns:
        Tuple of (success: bool, output: str)
    """
    try:
        result = subprocess.run(
            ["git"] + args,
            capture_output=True,
            text=True,
            cwd=cwd,
            timeout=10,
        )
        return result.returncode == 0, result.stdout.strip()
    except subprocess.TimeoutExpired:
        logger.error("Git command timed out: %s", " ".join(args))
        return False, "Command timed out"
    except FileNotFoundError:
        logger.error("Git executable not found")
        return False, "Git not installed"
    except Exception as e:
        logger.error("Error running git command: %s", str(e))
        return False, str(e)


def check_git_status() -> Dict[str, Any]:
    """
    Check current git repository status before allowing update.

    Returns:
        Dict with keys:
        - can_update (bool): Whether update is allowed
        - current_branch (str): Current branch name
        - has_uncommitted_changes (bool): Whether there are uncommitted changes
        - error (str|None): Error message if check failed
        - details (str): Human-readable status description
    """
    result = {
        "can_update": False,
        "current_branch": "",
        "has_uncommitted_changes": False,
        "error": None,
        "details": "",
    }

    # Check current branch
    success, branch = run_git_command(["rev-parse", "--abbrev-ref", "HEAD"])
    if not success:
        result["error"] = "Failed to determine current branch"
        result["details"] = "Could not access git repository"
        return result

    result["current_branch"] = branch

    # Only allow updates on main branch
    if branch != "main":
        result["error"] = f"Not on main branch (currently on: {branch})"
        result["details"] = (
            "Updates can only be applied on the main branch. Please switch to main manually."
        )
        return result

    # Check for uncommitted changes
    success, status_output = run_git_command(["status", "--porcelain"])
    if not success:
        result["error"] = "Failed to check git status"
        result["details"] = "Could not determine if there are uncommitted changes"
        return result

    result["has_uncommitted_changes"] = bool(status_output.strip())

    # Check if remote exists
    success, _ = run_git_command(["remote", "get-url", "origin"])
    if not success:
        result["error"] = "No remote 'origin' configured"
        result["details"] = "Cannot pull updates without a configured remote repository"
        return result

    # All checks passed
    result["can_update"] = True
    if result["has_uncommitted_changes"]:
        result["details"] = (
            "Ready to update. Uncommitted changes will be stashed automatically."
        )
    else:
        result["details"] = "Ready to update."

    return result


def perform_update() -> Dict[str, Any]:
    """
    Perform git pull to update the application.

    Handles stashing uncommitted changes if needed, pulling from origin/main,
    and restoring stashed changes afterward.

    Returns:
        Dict with keys:
        - success (bool): Whether update succeeded
        - message (str): Human-readable result message
        - stashed (bool): Whether changes were stashed
        - pulled_commits (str): Summary of pulled commits (if any)
        - error (str|None): Error message if update failed
    """
    result = {
        "success": False,
        "message": "",
        "stashed": False,
        "pulled_commits": "",
        "error": None,
    }

    # Pre-flight check
    status = check_git_status()
    if not status["can_update"]:
        result["error"] = status["error"]
        result["message"] = status["details"]
        return result

    # Step 1: Stash changes if needed
    if status["has_uncommitted_changes"]:
        logger.info("Stashing uncommitted changes before update")
        success, _ = run_git_command(
            ["stash", "push", "-u", "-m", "Auto-stash before app update"]
        )
        if not success:
            result["error"] = "Failed to stash uncommitted changes"
            result["message"] = (
                "Could not save your local changes. Please commit or stash them manually."
            )
            return result
        result["stashed"] = True

    # Step 2: Fetch latest changes
    logger.info("Fetching latest changes from origin/main")
    success, fetch_output = run_git_command(["fetch", "origin", "main"])
    if not success:
        result["error"] = "Failed to fetch from remote"
        result["message"] = f"Network error or remote unavailable: {fetch_output}"
        # Restore stash if we stashed
        if result["stashed"]:
            run_git_command(["stash", "pop"])
        return result

    # Step 3: Get commit summary before pull
    success, old_commit = run_git_command(["rev-parse", "HEAD"])

    # Step 4: Pull changes
    logger.info("Pulling changes from origin/main")
    success, pull_output = run_git_command(["pull", "origin", "main"])
    if not success:
        result["error"] = "Failed to pull changes"
        result["message"] = f"Git pull failed: {pull_output}"
        # Restore stash if we stashed
        if result["stashed"]:
            run_git_command(["stash", "pop"])
        return result

    # Step 5: Get commit summary after pull
    if old_commit:
        success_new, new_commit = run_git_command(["rev-parse", "HEAD"])
        if success_new and old_commit != new_commit:
            # Get short log of pulled commits
            success_log, log_output = run_git_command(
                ["log", "--oneline", f"{old_commit[:7]}..{new_commit[:7]}"]
            )
            if success_log:
                result["pulled_commits"] = log_output

    # Step 6: Restore stashed changes
    if result["stashed"]:
        logger.info("Restoring stashed changes")
        success, stash_output = run_git_command(["stash", "pop"])
        if not success:
            logger.warning("Could not auto-restore stashed changes: %s", stash_output)
            result["message"] = (
                "✓ Update successful! (Changes stashed in git stash - restore manually)"
            )
            result["success"] = True
            return result

    # Success!
    result["success"] = True
    result["message"] = "✓ Update complete! Restart the app to apply changes."

    return result
