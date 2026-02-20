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


def get_current_commit() -> str | None:
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


def get_tag_for_commit(commit_sha: str) -> str | None:
    """
    Get the git tag associated with a commit (if any).

    Args:
        commit_sha: Full or short commit hash

    Returns:
        Tag name (e.g., "v2.2.0") or None if no tag found
    """
    try:
        app_root = Path(__file__).parent.parent
        result = subprocess.run(
            ["git", "tag", "--points-at", commit_sha],
            cwd=app_root,
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode == 0 and result.stdout.strip():
            # Return first tag if multiple tags point to same commit
            return result.stdout.strip().split("\n")[0]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Could not get tag for commit {commit_sha}: {e}")
    return None


def check_for_updates() -> dict:
    """
    Check if newer commits are available on GitHub main branch.

    This function:
    1. Gets the local commit hash
    2. Queries GitHub API for the latest commit on main branch
    3. Compares the two to determine if an update is available
    4. Attempts to resolve commits to version tags for display

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
            - current_tag (str): Local version tag (if available)
            - latest_tag (str): Remote version tag (if available)
            - error (str): Error message if check failed
    """
    result = {
        "update_available": False,
        "current_commit": None,
        "latest_commit": None,
        "current_tag": None,
        "latest_tag": None,
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

            # Try to resolve commits to tags for better display
            current_tag = get_tag_for_commit(current_commit)
            if current_tag:
                result["current_tag"] = current_tag
                logger.debug(
                    f"Current commit {current_commit} is tagged as {current_tag}"
                )

            # For remote tag, we need to query GitHub tags API
            try:
                tags_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/tags"
                tags_response = requests.get(
                    tags_url,
                    timeout=REQUEST_TIMEOUT,
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if tags_response.status_code == 200:
                    tags_data = tags_response.json()
                    # Find tag that points to latest commit
                    for tag in tags_data:
                        if tag.get("commit", {}).get("sha", "")[:7] == latest_commit:
                            result["latest_tag"] = tag.get("name")
                            logger.debug(
                                f"Latest commit {latest_commit} is tagged as "
                                f"{result['latest_tag']}"
                            )
                            break
            except Exception as e:
                logger.debug(f"Could not fetch remote tags: {e}")

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
                "GitHub API returned status "
                f"{response.status_code} - skipping version check"
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
