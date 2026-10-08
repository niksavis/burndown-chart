import logging
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


def validate_migration(
    profile_id: str,
    profiles_path: Path = Path("profiles"),
    db_path: Path = Path("profiles/burndown.db"),
) -> tuple[bool, dict[str, Any]]:

    logger.info(f"Validating migration for profile: {profile_id}")

    report = {
        "profile_id": profile_id,
        "valid": False,
        "checks_passed": 0,
        "checks_failed": 0,
        "errors": [],
        "details": {},
    }

    try:
        from data.persistence.factory import get_backend  # noqa: PLC0415

        sqlite_backend = get_backend("sqlite", str(db_path))

        try:
            db_profile = sqlite_backend.get_profile(profile_id)
            if db_profile:
                report["checks_passed"] += 1
                report["details"]["profile_exists"] = True
            else:
                report["checks_failed"] += 1
                report["errors"].append(f"Profile {profile_id} not found in database")
                report["details"]["profile_exists"] = False
        except Exception as e:
            report["checks_failed"] += 1
            report["errors"].append(f"Profile check failed: {e}")
            report["details"]["profile_exists"] = False

        json_queries_dir = profiles_path / profile_id / "queries"
        if json_queries_dir.exists():
            json_query_count = len(
                [d for d in json_queries_dir.iterdir() if d.is_dir()]
            )
            db_queries = sqlite_backend.list_queries(profile_id)
            db_query_count = len(db_queries)

            if json_query_count == db_query_count:
                report["checks_passed"] += 1
                report["details"]["queries_count"] = {
                    "json": json_query_count,
                    "db": db_query_count,
                }
            else:
                report["checks_failed"] += 1
                report["errors"].append(
                    "Query count mismatch: "
                    f"JSON={json_query_count}, DB={db_query_count}"
                )
                report["details"]["queries_count"] = {
                    "json": json_query_count,
                    "db": db_query_count,
                }

        try:
            queries = sqlite_backend.list_queries(profile_id)
            for query in queries:
                if query["profile_id"] != profile_id:
                    report["checks_failed"] += 1
                    report["errors"].append(f"Query {query['id']} has wrong profile_id")
                else:
                    report["checks_passed"] += 1
        except Exception as e:
            report["checks_failed"] += 1
            report["errors"].append(f"Referential integrity check failed: {e}")

        report["valid"] = report["checks_failed"] == 0 and report["checks_passed"] > 0

        if report["valid"]:
            logger.info(
                f"Validation PASSED for {profile_id} ({report['checks_passed']} checks)"
            )
        else:
            logger.warning(
                f"Validation FAILED for {profile_id}: "
                f"{report['checks_failed']} failures, {len(report['errors'])} errors"
            )

    except Exception as e:
        logger.error(f"Validation error for {profile_id}: {e}")
        report["valid"] = False
        report["errors"].append(f"Validation exception: {e}")

    return report["valid"], report


def validate_all_profiles(
    profiles_path: Path = Path("profiles"),
    db_path: Path = Path("profiles/burndown.db"),
) -> tuple[bool, dict[str, Any]]:

    logger.info("Validating migration for all profiles")

    summary = {
        "all_valid": False,
        "profiles_count": 0,
        "profiles_valid": 0,
        "profiles_invalid": 0,
        "profile_reports": {},
    }

    try:
        profile_dirs = [
            d
            for d in profiles_path.iterdir()
            if d.is_dir() and (d / "profile.json").exists()
        ]
        summary["profiles_count"] = len(profile_dirs)

        for profile_dir in profile_dirs:
            profile_id = profile_dir.name
            is_valid, report = validate_migration(profile_id, profiles_path, db_path)

            summary["profile_reports"][profile_id] = report

            if is_valid:
                summary["profiles_valid"] += 1
            else:
                summary["profiles_invalid"] += 1

        summary["all_valid"] = (
            summary["profiles_invalid"] == 0 and summary["profiles_count"] > 0
        )

        logger.info(
            "Validation complete: "
            f"{summary['profiles_valid']}/{summary['profiles_count']} profiles valid"
        )

    except Exception as e:
        logger.error(f"Validation summary failed: {e}")
        summary["all_valid"] = False

    return summary["all_valid"], summary
