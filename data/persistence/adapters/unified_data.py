import logging
from typing import Any

import pandas as pd

from data.exceptions import PersistenceError
from data.persistence.factory import get_backend
from data.schema import get_default_unified_data

logger = logging.getLogger(__name__)


def load_unified_project_data() -> dict[str, Any]:

    try:
        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return get_default_unified_data()

        data = get_default_unified_data()

        scope = backend.get_scope(active_profile_id, active_query_id)
        if scope:
            data["project_scope"].update(scope)
            logger.info(
                f"[Cache] Loaded scope from DB - Total: {scope.get('total_items')}, "
                f"Completed: {scope.get('completed_items')}, "
                f"Remaining: {scope.get('remaining_items')}"
            )

        stats_rows = backend.get_statistics(active_profile_id, active_query_id)
        statistics = []
        if stats_rows:
            for row in stats_rows:
                stat = dict(row)
                if "stat_date" in stat:
                    stat["date"] = stat["stat_date"]
                statistics.append(stat)
            data["statistics"] = statistics

        logger.info(
            "[Cache] Loaded unified data from database for "
            f"{active_profile_id}/{active_query_id}: {len(statistics)} stats"
        )
        if statistics:
            logger.info(
                f"[Cache] First stat: date={statistics[0].get('date')}, "
                f"items={statistics[0].get('remaining_items')}, "
                f"points={statistics[0].get('remaining_total_points')}"
            )
            logger.info(
                f"[Cache] Last stat: date={statistics[-1].get('date')}, "
                f"items={statistics[-1].get('remaining_items')}, "
                f"points={statistics[-1].get('remaining_total_points')}"
            )
        return data

    except (
        AttributeError,
        KeyError,
        PersistenceError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[Cache] Error loading unified project data: {e}")
        return get_default_unified_data()


def save_unified_project_data(data: dict[str, Any]) -> None:

    try:
        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("[Cache] Cannot save - no active profile/query")
            return

        if "project_scope" in data:
            backend.save_scope(
                active_profile_id, active_query_id, data["project_scope"]
            )

        if "statistics" in data and data["statistics"]:
            stat_list = []
            for stat in data["statistics"]:
                stat_data = dict(stat)
                if "date" in stat_data:
                    if "stat_date" not in stat_data or not stat_data["stat_date"]:
                        stat_data["stat_date"] = stat_data["date"]

                if stat_data.get("stat_date"):
                    try:
                        parsed_date = pd.to_datetime(
                            stat_data["stat_date"], format="mixed", errors="coerce"
                        )
                        if pd.notna(parsed_date):
                            stat_data["stat_date"] = parsed_date.strftime("%Y-%m-%d")
                        else:
                            logger.warning(
                                "[Cache] Could not parse date: "
                                f"{stat_data['stat_date']}"
                            )
                            continue
                    except (AttributeError, TypeError, ValueError) as e:
                        logger.warning(
                            "[Cache] Error normalizing date "
                            f"{stat_data.get('stat_date')}: {e}"
                        )
                        continue

                if not stat_data.get("stat_date"):
                    logger.warning(
                        f"[Cache] Skipping statistic with no date: {stat_data}"
                    )
                    continue
                stat_list.append(stat_data)
            if stat_list:
                backend.save_statistics_batch(
                    active_profile_id, active_query_id, stat_list
                )
                logger.info(f"[Cache] Saved {len(stat_list)} statistics to database")
            else:
                logger.warning(
                    "[Cache] No valid statistics to save (all missing dates)"
                )

        logger.info("[Cache] Saved unified project data to database")
    except (
        AttributeError,
        KeyError,
        PersistenceError,
        TypeError,
        ValueError,
    ) as e:
        logger.error(f"[Cache] Error saving unified project data: {e}")
        raise
