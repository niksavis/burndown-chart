"""Workspace validation on application startup.

Ensures the active profile and active query are set consistently before
the Dash application begins serving requests.
"""

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
    """
    Validate application workspace on startup.

    This function checks the workspace state and ensures:
    1. If profiles exist, active profile is set
    2. If active profile exists, it has at least one query
    3. If queries exist, active query is set

    Unlike previous versions, this does NOT create a default profile.
    The app starts with a clean slate - users create their first profile via UI.

    Called during app initialization (after migration).
    """
    try:
        logger.info("[Workspace] Starting workspace validation...")

        # Step 1: Check if any profiles exist
        all_profiles = list_profiles()
        if not all_profiles:
            logger.info(
                "[Workspace] No profiles found - fresh installation. "
                "User will create first profile via UI."
            )
            logger.info("[Workspace] Workspace validation complete [OK]")
            return

        # Step 2: Ensure active profile is set (if profiles exist)
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

        # Step 3: Ensure profile has at least one query
        if active_profile:
            queries = list_queries_for_profile(active_profile.id)
            if not queries:
                logger.info(
                    f"[Workspace] No queries in profile '{active_profile.name}' - "
                    "User will need to create a query before using JIRA integration"
                )
                # Note: We don't auto-create queries here because they require
                # JIRA configuration. The UI will enforce creating queries
                # after JIRA config is complete.

            # Step 4: Ensure active query is set (if queries exist)
            active_query_id = get_active_query_id()
            if queries and not active_query_id:
                logger.info("[Workspace] No active query, switching to first query")
                switch_query(active_profile.id, queries[0]["id"])

        logger.info("[Workspace] Workspace validation complete [OK]")

    except Exception as e:
        # Log error but don't crash - allow app to continue
        logger.error(f"[Workspace] Validation failed: {e}", exc_info=True)
        print(
            f"WARNING: Workspace validation failed - {e}. See logs/app.log for details."
        )


# Validate workspace before app initialization
