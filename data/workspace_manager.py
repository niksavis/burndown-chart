import logging

from data.profile_manager import (
    get_active_profile,
    list_profiles,
    switch_profile,
    switch_query,
)
from data.query_manager import get_active_query_id, list_queries_for_profile

logger = logging.getLogger(__name__)


def ensure_valid_workspace() -> None:

    try:
        logger.info("[Workspace] Starting workspace validation...")

        all_profiles = list_profiles()
        if not all_profiles:
            logger.info(
                "[Workspace] No profiles found - fresh installation. "
                "User will create first profile via UI."
            )
            logger.info("[Workspace] Workspace validation complete [OK]")
            return

        active_profile = get_active_profile()
        if not active_profile:
            logger.warning(
                "[Workspace] Profiles exist but no active profile set. "
                f"Switching to first profile: {all_profiles[0]['name']}"
            )
            switch_profile(all_profiles[0]["id"])
            active_profile = get_active_profile()

        logger.info(
            "[Workspace] Active profile: "
            f"{active_profile.name if active_profile else 'None'}"
        )

        if active_profile:
            queries = list_queries_for_profile(active_profile.id)
            if not queries:
                logger.info(
                    f"[Workspace] No queries in profile '{active_profile.name}' - "
                    "User will need to create a query before using JIRA integration"
                )

            active_query_id = get_active_query_id()
            if queries and not active_query_id:
                logger.info("[Workspace] No active query, switching to first query")
                switch_query(active_profile.id, queries[0]["id"])

        logger.info("[Workspace] Workspace validation complete [OK]")

    except Exception as e:
        logger.error(f"[Workspace] Validation failed: {e}", exc_info=True)
        print(
            f"WARNING: Workspace validation failed - {e}. See logs/app.log for details."
        )
