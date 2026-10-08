import logging
import re

logger = logging.getLogger(__name__)


def build_jql_with_parent_types(user_jql: str, parent_types: list[str]) -> str:

    if not parent_types:
        logger.debug("[Query Builder] No parent types configured - query unchanged")
        return user_jql

    if not user_jql or not user_jql.strip():
        logger.warning("[Query Builder] Empty JQL query provided")
        return user_jql

    pattern = r"\bissuetype\s+in\s*\(([^)]+)\)"

    match = re.search(pattern, user_jql, re.IGNORECASE)

    if not match:
        logger.info(
            "[Query Builder] No issuetype filter in JQL - "
            "parent types already included (no modification needed)"
        )
        return user_jql

    types_str = match.group(1)

    existing_types = _parse_issue_types(types_str)

    existing_types_lower = {t.lower() for t in existing_types}
    types_to_add = [pt for pt in parent_types if pt.lower() not in existing_types_lower]

    if not types_to_add:
        logger.info(
            "[Query Builder] Parent types already in JQL - no modification needed"
        )
        logger.debug(f"[Query Builder] Existing types: {existing_types}")
        return user_jql

    modified_types = existing_types + types_to_add

    new_clause = _build_issuetype_clause(modified_types)

    modified_jql = user_jql[: match.start()] + new_clause + user_jql[match.end() :]

    logger.info(
        f"[Query Builder] Added {len(types_to_add)} parent type(s) to JQL: "
        f"{', '.join(types_to_add)}"
    )
    logger.debug(f"[Query Builder] Original JQL: {user_jql}")
    logger.debug(f"[Query Builder] Modified JQL: {modified_jql}")

    return modified_jql


def _parse_issue_types(types_str: str) -> list[str]:

    if not types_str:
        return []

    parts = types_str.split(",")

    types = []
    for part in parts:
        cleaned = part.strip()

        if cleaned.startswith(('"', "'")):
            cleaned = cleaned[1:]
        if cleaned.endswith(('"', "'")):
            cleaned = cleaned[:-1]

        cleaned = cleaned.strip()

        if cleaned:
            types.append(cleaned)

    return types


def _build_issuetype_clause(types: list[str]) -> str:

    if not types:
        return "issuetype in ()"

    quoted_types = []
    for t in types:
        if " " in t or "," in t or '"' in t or "'" in t:
            escaped = t.replace('"', '\\"')
            quoted_types.append(f'"{escaped}"')
        else:
            quoted_types.append(t)

    types_list = ", ".join(quoted_types)
    return f"issuetype in ({types_list})"


def extract_parent_types_from_config(config: dict) -> list[str]:

    parent_types = (
        config.get("field_mappings", {})
        .get("general", {})
        .get("parent_issue_types", [])
    )

    if not isinstance(parent_types, list):
        logger.warning(
            f"[Query Builder] parent_issue_types is not a list: {type(parent_types)}"
        )
        return []

    cleaned_types = [t for t in parent_types if t and isinstance(t, str)]

    if len(cleaned_types) != len(parent_types):
        logger.warning(
            f"[Query Builder] Filtered {len(parent_types) - len(cleaned_types)} "
            "invalid parent type entries"
        )

    return cleaned_types
