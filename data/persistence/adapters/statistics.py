import logging
import sqlite3
from datetime import datetime
from datetime import datetime as dt_module
from typing import Any

import pandas as pd

from data.exceptions import PersistenceError
from data.iso_week_bucketing import get_week_label
from data.persistence.adapters.core import (
    convert_timestamps_to_strings,
)
from data.persistence.adapters.unified_data import (
    load_unified_project_data,
    save_unified_project_data,
)
from data.persistence.factory import get_backend

logger = logging.getLogger(__name__)


def save_statistics(data: list[dict[str, Any]]) -> None:

    logger.info(
        f"[Persistence] save_statistics called with {len(data) if data else 0} rows"
    )

    try:
        df = pd.DataFrame(data)
        logger.debug(f"[Persistence] Created DataFrame with {len(df)} rows")

        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        df = df.sort_values("date", ascending=True)

        df.loc[:, "date"] = df["date"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
        )

        statistics_data = df.to_dict("records")  # type: ignore[assignment]

        for stat in statistics_data:
            if "week_label" not in stat or not stat["week_label"]:
                if stat.get("date"):
                    try:
                        date_obj = datetime.strptime(stat["date"], "%Y-%m-%d")
                        stat["week_label"] = get_week_label(date_obj)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            "Could not calculate week_label for date "
                            f"{stat.get('date')}: {e}"
                        )

        statistics_data = convert_timestamps_to_strings(statistics_data)

        unified_data = load_unified_project_data()

        unified_data["statistics"] = statistics_data

        unified_data["metadata"].update(
            {
                "last_updated": datetime.now().isoformat(),
            }
        )

        save_unified_project_data(unified_data)

        logger.info(
            "[Persistence] ✓ Statistics saved successfully to DB: "
            f"{len(statistics_data)} rows"
        )
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        sqlite3.Error,
        PersistenceError,
    ) as e:
        logger.exception("[Persistence] ✗ FAILED to save statistics")
        raise PersistenceError("Failed to save statistics") from e


def save_statistics_from_csv_import(data: list[dict[str, Any]]) -> None:

    try:
        df = pd.DataFrame(data)

        df["date"] = pd.to_datetime(df["date"], errors="coerce")

        df = df.sort_values("date", ascending=True)

        df.loc[:, "date"] = df["date"].apply(
            lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else ""
        )

        statistics_data = df.to_dict("records")  # type: ignore[assignment]

        for stat in statistics_data:
            if "week_label" not in stat or not stat["week_label"]:
                if stat.get("date"):
                    try:
                        date_obj = dt_module.strptime(stat["date"], "%Y-%m-%d")
                        stat["week_label"] = get_week_label(date_obj)
                    except (ValueError, TypeError) as e:
                        logger.warning(
                            "Could not calculate week_label for date "
                            f"{stat.get('date')}: {e}"
                        )

        unified_data = load_unified_project_data()

        unified_data["statistics"] = statistics_data

        unified_data["metadata"].update(
            {
                "source": "csv_import",
                "last_updated": datetime.now().isoformat(),
                "jira_query": "",
            }
        )

        save_unified_project_data(unified_data)

        logger.info("[Cache] Statistics from CSV import saved to database")
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        sqlite3.Error,
        PersistenceError,
    ) as e:
        logger.exception("[Cache] Error saving CSV import statistics")
        persistence_error = PersistenceError("Failed to save CSV import statistics")
        logger.debug("[Cache] %s: %s", type(persistence_error).__name__, e)


def load_statistics() -> tuple:

    try:
        backend = get_backend()
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            return [], False

        stats_rows = backend.get_statistics(active_profile_id, active_query_id)
        if not stats_rows:
            return [], False

        statistics_df = pd.DataFrame(stats_rows)

        if "stat_date" in statistics_df.columns:
            statistics_df["date"] = statistics_df["stat_date"]

        statistics_df["date"] = pd.to_datetime(
            statistics_df["date"], errors="coerce", format="mixed"
        )

        if "date" in statistics_df.columns and not statistics_df.empty:
            statistics_df["date_normalized"] = statistics_df["date"].apply(
                lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else None
            )

            statistics_df = statistics_df.sort_values("date", ascending=False)
            statistics_df = statistics_df.drop_duplicates(
                subset=["date_normalized"], keep="first"
            )
            statistics_df = statistics_df.sort_values("date", ascending=True)

            statistics_df = statistics_df.drop(columns=["date_normalized"])
        statistics_df = statistics_df.sort_values("date", ascending=True)
        statistics_df["date"] = (
            statistics_df["date"]
            .apply(lambda x: x.strftime("%Y-%m-%d") if pd.notna(x) else "")
            .astype(str)
        )

        data = statistics_df.to_dict("records")  # type: ignore[assignment]
        data = convert_timestamps_to_strings(data)
        logger.info(f"[Cache] Statistics loaded from database: {len(data)} rows")
        return data, False
    except (
        ImportError,
        OSError,
        RuntimeError,
        ValueError,
        TypeError,
        KeyError,
        AttributeError,
        sqlite3.Error,
        PersistenceError,
    ) as e:
        logger.exception("[Cache] Error loading statistics")
        persistence_error = PersistenceError("Failed to load statistics")
        logger.debug("[Cache] %s: %s", type(persistence_error).__name__, e)
        return [], False
