import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

from data.database import get_db_connection
from data.persistence.factory import get_backend
from data.time_formatting import get_relative_time_string

logger = logging.getLogger(__name__)


class DependencyError(Exception):
    pass


def _generate_unique_query_id() -> str:

    import uuid  # noqa: PLC0415

    return f"q_{uuid.uuid4().hex[:12]}"


def get_active_query_id() -> str | None:

    backend = get_backend()
    active_query_id = backend.get_app_state("active_query_id")
    return active_query_id


def get_active_profile_id() -> str:

    backend = get_backend()
    active_profile_id = backend.get_app_state("active_profile_id")
    if not active_profile_id:
        raise ValueError("active_profile_id not found in app state")
    return active_profile_id


def switch_query(query_id: str) -> None:

    backend = get_backend()

    active_profile_id = backend.get_app_state("active_profile_id")
    if not active_profile_id:
        raise ValueError("active_profile_id not found in app state")

    if hasattr(backend, "db_path"):
        db_path = Path(str(cast(Any, backend).db_path))
        with get_db_connection(db_path) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT 1 FROM queries WHERE profile_id = ? AND id = ?",
                (active_profile_id, query_id),
            )
            if not cursor.fetchone():
                cursor.execute(
                    "SELECT id FROM queries "
                    "WHERE profile_id = ? ORDER BY last_used DESC",
                    (active_profile_id,),
                )
                available_ids = [row["id"] for row in cursor.fetchall()]
                raise ValueError(
                    f"Query '{query_id}' not found in profile '{active_profile_id}'. "
                    f"Available queries: {available_ids}"
                )

            cursor.execute(
                "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
                ("active_query_id", query_id),
            )
            conn.commit()

        logger.info(f"Switched to query '{query_id}' in profile '{active_profile_id}'")
        return

    query = backend.get_query(active_profile_id, query_id)
    if not query:
        available_queries = backend.list_queries(active_profile_id)
        available_ids = [q["id"] for q in available_queries]
        raise ValueError(
            f"Query '{query_id}' not found in profile '{active_profile_id}'. "
            f"Available queries: {available_ids}"
        )

    backend.set_app_state("active_query_id", query_id)

    logger.info(f"Switched to query '{query_id}' in profile '{active_profile_id}'")


def list_queries_for_profile(profile_id: str | None = None) -> list[dict]:

    backend = get_backend()

    if profile_id is None:
        profile_id = get_active_profile_id()

    queries = backend.list_queries(profile_id)

    try:
        active_query_id = get_active_query_id()
    except ValueError:
        active_query_id = None

    for query in queries:
        query["is_active"] = query["id"] == active_query_id

    return queries


def get_query_dropdown_options(profile_id: str | None = None) -> list[dict]:

    import logging  # noqa: PLC0415

    logger = logging.getLogger(__name__)

    backend = get_backend()
    if profile_id is None:
        profile_id = backend.get_app_state("active_profile_id")

    if not profile_id:
        return [{"label": "→ Create New Query", "value": "__create_new__"}]

    queries = list_queries_for_profile(profile_id)

    options = [{"label": "→ Create New Query", "value": "__create_new__"}]

    timestamp_map = {}
    try:
        db_path = getattr(backend, "db_path", Path("profiles/burndown.db"))

        with get_db_connection(Path(db_path)) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT query_id, MAX(fetched_at) as latest_fetch
                FROM jira_issues
                WHERE profile_id = ?
                GROUP BY query_id
                """,
                (profile_id,),
            )
            rows = cursor.fetchall()
            timestamp_map = {row[0]: row[1] for row in rows}
            logger.info(
                f"[DROPDOWN] Fetched timestamps for {len(timestamp_map)} "
                "queries in single query"
            )
    except Exception as e:
        logger.error(
            f"[DROPDOWN] Failed to fetch timestamps: {e}",
            exc_info=True,
        )

    for query in queries:
        label = query.get("name", "Unnamed Query")
        query_id = query.get("id", "")

        logger.info(
            f"[DROPDOWN] Processing query: id={query_id}, name='{label}', "
            f"is_active={query.get('is_active', False)}"
        )

        if query.get("is_active", False):
            label += " [Active]"

        if query_id in timestamp_map:
            timestamp_iso = timestamp_map[query_id]
            logger.info(f"[DROPDOWN] Found timestamp for {query_id}: {timestamp_iso}")
            relative_time = get_relative_time_string(timestamp_iso)
            label += f" ({relative_time})"
        else:
            logger.debug(f"[DROPDOWN] No data fetched yet for query {query_id}")

        options.append({"label": label, "value": query_id})

    return options


def create_query(profile_id: str, name: str, jql: str, description: str = "") -> str:

    backend = get_backend()

    profile = backend.get_profile(profile_id)
    if not profile:
        raise ValueError(f"Profile '{profile_id}' not found")

    jira_config = profile.get("jira_config", {})
    if not jira_config.get("configured"):
        raise DependencyError(
            "JIRA must be configured before creating queries. "
            "Go to 'JIRA Configuration' section and test connection first."
        )

    field_mappings = profile.get("field_mappings", {})
    if not field_mappings:
        logger.warning(
            f"[Query] Field mappings not configured in profile '{profile_id}' - "
            "metrics may be limited. Configure field mappings for full "
            "DORA/Flow metrics."
        )

    query_id = _generate_unique_query_id()

    query_dict = {
        "id": query_id,
        "name": name,
        "jql": jql,
        "description": description,
        "created_at": datetime.now(UTC).isoformat(),
        "last_used": datetime.now(UTC).isoformat(),
    }

    backend.save_query(profile_id, query_dict)

    logger.info(f"Created query '{query_id}' in profile '{profile_id}'")

    return query_id


def update_query(
    profile_id: str,
    query_id: str,
    name: str | None = None,
    jql: str | None = None,
    description: str | None = None,
) -> bool:

    backend = get_backend()

    query_data = backend.get_query(profile_id, query_id)
    if not query_data:
        raise ValueError(f"Query '{query_id}' not found in profile '{profile_id}'")

    changes = []

    if name is not None and name != query_data.get("name"):
        old_name = query_data.get("name")
        query_data["name"] = name
        changes.append(f"name: '{old_name}' -> '{name}'")

    if jql is not None and jql != query_data.get("jql"):
        query_data["jql"] = jql
        changes.append("jql updated")

    if description is not None and description != query_data.get("description"):
        query_data["description"] = description
        changes.append("description updated (not persisted)")

    if not changes:
        logger.info(f"No changes to query '{query_id}' in profile '{profile_id}'")
        return True

    query_data["id"] = query_id

    backend.save_query(profile_id, query_data)

    logger.info(
        f"Updated query '{query_id}' in profile '{profile_id}': {', '.join(changes)}"
    )

    return True


def delete_query(profile_id: str, query_id: str, allow_cascade: bool = False) -> None:

    backend = get_backend()

    if not allow_cascade:
        try:
            active_query_id = get_active_query_id()
            if query_id == active_query_id:
                raise PermissionError(
                    f"Cannot delete active query '{query_id}'. "
                    "Switch to another query first."
                )
        except ValueError:
            pass

    query = backend.get_query(profile_id, query_id)
    if not query:
        raise ValueError(f"Query '{query_id}' not found in profile '{profile_id}'")

    backend.delete_query(profile_id, query_id)

    logger.info(f"Deleted query '{query_id}' from profile '{profile_id}'")


def validate_query_exists_for_data_operation(query_id: str) -> None:

    backend = get_backend()

    try:
        active_profile_id = get_active_profile_id()
    except ValueError as e:
        raise ValueError(f"Cannot validate query: {e}") from e

    query = backend.get_query(active_profile_id, query_id)
    if not query:
        raise DependencyError(
            f"Query '{query_id}' must be saved before executing data operations. "
            "Click 'Save Query' first, then 'Update Data'."
        )

    if not query.get("name") or not query.get("jql"):
        raise DependencyError(
            f"Query '{query_id}' is not properly initialized. "
            "Re-save the query with name and JQL, then try again."
        )

    logger.debug(f"[Query] Validated query '{query_id}' exists for data operation")


def resolve_jql_query(jql_query: str, app_settings: dict) -> str:

    if not jql_query or not jql_query.strip():
        try:
            backend = get_backend()
            active_query_id = backend.get_app_state("active_query_id")
            active_profile_id = backend.get_app_state("active_profile_id")
            if active_query_id and active_profile_id:
                query_data = backend.get_query(active_profile_id, active_query_id)
                if query_data:
                    return query_data.get("jql", "")
        except Exception as e:
            logger.error(f"[Query] Failed to load JQL from active query: {e}")
        return app_settings.get("jql_query", "project = JRASERVER")
    return jql_query.strip()
