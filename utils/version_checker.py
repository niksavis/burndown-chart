import logging
import subprocess
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

GITHUB_REPO_OWNER = "niksavis"
GITHUB_REPO_NAME = "burndown-chart"
GITHUB_API_URL = (
    f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/commits/main"
)

REQUEST_TIMEOUT_SECONDS = 3


def get_current_commit() -> str | None:

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
            return result.stdout.strip().split("\n")[0]
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logger.debug(f"Could not get tag for commit {commit_sha}: {e}")
    return None


def check_for_updates() -> dict:

    result = {
        "update_available": False,
        "current_commit": None,
        "latest_commit": None,
        "current_tag": None,
        "latest_tag": None,
        "error": None,
    }

    current_commit = get_current_commit()
    if not current_commit:
        logger.debug("Version check skipped: Not a git repository or git not installed")
        result["error"] = "not_a_git_repo"
        return result

    result["current_commit"] = current_commit

    try:
        logger.debug(f"Checking GitHub for updates (current: {current_commit})...")
        response = requests.get(
            GITHUB_API_URL,
            timeout=REQUEST_TIMEOUT_SECONDS,
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

            current_tag = get_tag_for_commit(current_commit)
            if current_tag:
                result["current_tag"] = current_tag
                logger.debug(
                    f"Current commit {current_commit} is tagged as {current_tag}"
                )

            try:
                tags_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/tags"
                tags_response = requests.get(
                    tags_url,
                    timeout=REQUEST_TIMEOUT_SECONDS,
                    headers={"Accept": "application/vnd.github.v3+json"},
                )
                if tags_response.status_code == 200:
                    tags_data = tags_response.json()
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
            logger.debug("GitHub API rate limit reached - skipping version check")
            result["error"] = "rate_limited"

        elif response.status_code == 404:
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
