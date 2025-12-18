"""
Version Checker Utility

Checks GitHub for newer commits on the main branch to notify users
of available updates. Operates on app startup only, with graceful
fallback if no internet connection is available.
"""

#######################################################################
# IMPORTS
#######################################################################
import logging
import subprocess
from pathlib import Path
from typing import Optional

import requests

#######################################################################
# CONFIGURATION
#######################################################################

logger = logging.getLogger(__name__)

GITHUB_REPO_OWNER = "niksavis"
GITHUB_REPO_NAME = "burndown-chart"
GITHUB_API_URL = (
    f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/commits/main"
)

# Timeout for GitHub API request (seconds)
REQUEST_TIMEOUT = 3

#######################################################################
# FUNCTIONS
#######################################################################


def get_current_commit() -> Optional[str]:
    """
    Get the current git commit hash of the local repository.

    Returns:
        Short commit hash (7 characters) or None if git is not available
    """
    try:
        app_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=app_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()[:7]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Could not get current git commit: {e}")
    return None


def check_for_updates() -> dict:
    """
    Check if newer commits are available on GitHub main branch.

    This function:
    1. Gets the local commit hash
    2. Queries GitHub API for the latest commit on main branch
    3. Compares the two to determine if an update is available

    Gracefully handles:
    - No internet connection
    - Git not installed
    - Not a git repository
    - GitHub API rate limiting
    - Network timeouts

    Returns:
        dict with keys:
            - update_available (bool): True if remote has newer commits
            - current_commit (str): Local commit hash (short)
            - latest_commit (str): Remote commit hash (short)
            - error (str): Error message if check failed
    """
    result = {
        "update_available": False,
        "current_commit": None,
        "latest_commit": None,
        "error": None,
    }

    # Step 1: Get current local commit
    current_commit = get_current_commit()
    if not current_commit:
        logger.debug("Version check skipped: Not a git repository or git not installed")
        result["error"] = "not_a_git_repo"
        return result

    result["current_commit"] = current_commit

    # Step 2: Check GitHub for latest commit
    try:
        logger.debug(f"Checking GitHub for updates (current: {current_commit})...")
        response = requests.get(
            GITHUB_API_URL,
            timeout=REQUEST_TIMEOUT,
            headers={"Accept": "application/vnd.github.v3+json"},
        )

        if response.status_code == 200:
            data = response.json()
            latest_commit = data.get("sha", "")[:7]
            result["latest_commit"] = latest_commit

            if current_commit != latest_commit:
                logger.info(f"Update available: {current_commit} -> {latest_commit}")
                result["update_available"] = True
            else:
                logger.debug("No updates available - on latest commit")

        elif response.status_code == 403:
            # Rate limited
            logger.debug("GitHub API rate limit reached - skipping version check")
            result["error"] = "rate_limited"

        elif response.status_code == 404:
            # Repository not found (shouldn't happen but handle gracefully)
            logger.debug("GitHub repository not found - skipping version check")
            result["error"] = "repo_not_found"

        else:
            logger.debug(
                f"GitHub API returned status {response.status_code} - skipping version check"
            )
            result["error"] = f"api_error_{response.status_code}"

    except requests.exceptions.Timeout:
        logger.debug("GitHub API timeout - no internet connection or slow network")
        result["error"] = "timeout"

    except requests.exceptions.ConnectionError:
        logger.debug("No internet connection - skipping version check")
        result["error"] = "no_internet"

    except Exception as e:
        logger.debug(f"Version check failed: {e}")
        result["error"] = f"unknown_{type(e).__name__}"

    return result
