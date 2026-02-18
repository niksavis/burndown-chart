"""Active Work Search filtering logic."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set


@dataclass
class SearchPredicate:
    """Single predicate in a search expression."""

    field: Optional[str]
    value_groups: List[List[str]]
    text_value: Optional[str]


@dataclass
class SearchNode:
    """Expression node (predicate, and, or)."""

    kind: str
    predicate: Optional[SearchPredicate] = None
    left: Optional["SearchNode"] = None
    right: Optional["SearchNode"] = None


class _SearchParser:
    """Recursive-descent parser for Active Work search grammar."""

    def __init__(self, tokens: List[str]) -> None:
        self._tokens = tokens
        self._index = 0

    def parse(self) -> Optional[SearchNode]:
        """Parse full expression."""
        if not self._tokens:
            return None

        expression = self._parse_or_expression()
        if expression is None:
            return None

        if self._index < len(self._tokens):
            return None

        return expression

    def _parse_or_expression(self) -> Optional[SearchNode]:
        left = self._parse_and_expression()
        if left is None:
            return None

        while self._peek() == "|":
            self._consume("|")
            right = self._parse_and_expression()
            if right is None:
                return None
            left = SearchNode(kind="or", left=left, right=right)

        return left

    def _parse_and_expression(self) -> Optional[SearchNode]:
        left = self._parse_factor()
        if left is None:
            return None

        while self._peek() == "&":
            self._consume("&")
            right = self._parse_factor()
            if right is None:
                return None
            left = SearchNode(kind="and", left=left, right=right)

        return left

    def _parse_factor(self) -> Optional[SearchNode]:
        current = self._peek()
        if current is None:
            return None

        if current == "(":
            self._consume("(")
            inner = self._parse_or_expression()
            if inner is None or self._peek() != ")":
                return None
            self._consume(")")
            return inner

        token = self._consume()
        predicate = _parse_predicate_token(token)
        if predicate is None:
            return None
        return SearchNode(kind="predicate", predicate=predicate)

    def _peek(self) -> Optional[str]:
        if self._index >= len(self._tokens):
            return None
        return self._tokens[self._index]

    def _consume(self, expected: Optional[str] = None) -> str:
        token = self._tokens[self._index]
        if expected is not None and token != expected:
            raise ValueError(f"Expected token '{expected}' but got '{token}'")
        self._index += 1
        return token


def _tokenize_query(query: str) -> List[str]:
    """Tokenize query into operators, parentheses, and predicate chunks."""
    tokens: List[str] = []
    buffer: List[str] = []

    def flush_buffer() -> None:
        chunk = "".join(buffer).strip()
        if chunk:
            tokens.append(chunk)
        buffer.clear()

    for char in query:
        if char in ("(", ")", "&", "|"):
            flush_buffer()
            tokens.append(char)
        else:
            buffer.append(char)

    flush_buffer()
    return tokens


def _parse_predicate_token(token: str) -> Optional[SearchPredicate]:
    """Parse a single predicate token into fielded or free-text predicate."""
    value = token.strip()
    if not value:
        return None

    if ":" not in value:
        return SearchPredicate(
            field="_text", value_groups=[[value.lower()]], text_value=None
        )

    field, raw_values = value.split(":", 1)
    normalized_field = _resolve_field_alias(field.strip().lower())
    if not normalized_field:
        return None

    value_groups = _parse_field_value_groups(raw_values)
    if not value_groups:
        return None

    return SearchPredicate(
        field=normalized_field,
        value_groups=value_groups,
        text_value=None,
    )


def _parse_field_value_groups(raw_values: str) -> List[List[str]]:
    """Parse value expression using ';' as OR and ',' as AND within a field."""
    groups: List[List[str]] = []
    for or_group in _split_unquoted(raw_values, ";"):
        and_values = [
            _normalize_value_token(part)
            for part in _split_unquoted(or_group, ",")
            if _normalize_value_token(part)
        ]
        if and_values:
            groups.append(and_values)
    return groups


def parse_search_query(query: str) -> Dict[str, Any]:
    """Parse search query into expression tree.

    Args:
        query: Search query like "(labels:backend;frontend | assignee:jack) & issuetype:bug"

    Returns:
        Dict containing parsed expression under "_expr"
    """
    if not query or not query.strip():
        return {}

    tokens = _tokenize_query(query.strip())
    parser = _SearchParser(tokens)
    expression = parser.parse()

    if expression is None:
        return {}

    return {"_expr": expression}  # type: ignore[return-value]


def matches_all_filters(issue: Dict[str, Any], filters: Dict[str, Any]) -> bool:
    """Check if issue matches all filters (AND logic across fields).

    Args:
        issue: Issue dict with fields
        filters: Parsed expression dictionary

    Returns:
        True if issue matches all filters
    """
    expression = filters.get("_expr")
    if expression is None:
        return True
    return _evaluate_expression(issue, expression)


def _evaluate_expression(issue: Dict[str, Any], node: SearchNode) -> bool:
    """Evaluate parsed search expression against a single issue."""
    if node.kind == "predicate" and node.predicate is not None:
        return _evaluate_predicate(issue, node.predicate)

    if node.kind == "and" and node.left and node.right:
        return _evaluate_expression(issue, node.left) and _evaluate_expression(
            issue, node.right
        )

    if node.kind == "or" and node.left and node.right:
        return _evaluate_expression(issue, node.left) or _evaluate_expression(
            issue, node.right
        )

    return False


def _evaluate_predicate(issue: Dict[str, Any], predicate: SearchPredicate) -> bool:
    """Evaluate a single field/text predicate against issue values."""
    issue_value = get_issue_field_value(issue, predicate.field or "")
    if issue_value is None:
        return False

    for and_group in predicate.value_groups:
        if all(matches_value(issue_value, value) for value in and_group):
            return True

    return False


def matches_filter(issue: Dict[str, Any], field: str, filter_values: List[str]) -> bool:
    """Check if issue matches filter for a single field (OR logic within values).

    Args:
        issue: Issue dict
        field: Field name to check
        filter_values: List of values to match (OR logic)

    Returns:
        True if issue matches any of the filter values
    """
    issue_value = get_issue_field_value(issue, field)

    if issue_value is None:
        return False

    # OR logic - match if ANY filter value matches
    for filter_value in filter_values:
        if matches_value(issue_value, filter_value):
            return True

    return False


def matches_value(issue_value: Any, filter_value: str) -> bool:
    """Check if issue value matches filter value (case insensitive, partial match).

    Args:
        issue_value: Value from issue (string or list)
        filter_value: Filter value (lowercase)

    Returns:
        True if matches
    """
    if isinstance(issue_value, list):
        # JSON array fields (labels, components, fix_versions)
        for item in issue_value:
            if isinstance(item, dict):
                # Object with name field
                name = item.get("name", "")
                if name and filter_value in str(name).lower():
                    return True
            elif filter_value in str(item).lower():
                return True
        return False
    else:
        # String field - partial match (case insensitive)
        return filter_value in str(issue_value).lower()


def get_issue_field_value(issue: Dict[str, Any], field: str):
    """Get issue field value by field name.

    Args:
        issue: Issue dict
        field: Field name

    Returns:
        Field value or None
    """
    if field == "_text":
        searchable_parts = [
            issue.get("issue_key"),
            issue.get("summary"),
            issue.get("assignee"),
            issue.get("issue_type"),
            issue.get("project_key"),
            issue.get("project_name"),
        ]

        for list_field in ("labels", "components", "fix_versions"):
            values = issue.get(list_field) or []
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, dict):
                        searchable_parts.append(value.get("name") or value.get("value"))
                    else:
                        searchable_parts.append(value)

        return " ".join(str(part) for part in searchable_parts if part)

    field_map = {
        "key": issue.get("issue_key"),
        "summary": issue.get("summary"),
        "assignee": issue.get("assignee"),
        "issuetype": issue.get("issue_type"),
        "project": issue.get("project_key"),
        "fixversion": issue.get("fix_versions"),
        "labels": issue.get("labels"),
        "components": issue.get("components"),
    }

    return field_map.get(field)


def filter_timeline_by_query(
    timeline: List[Dict[str, Any]], query: str
) -> List[Dict[str, Any]]:
    """Filter timeline based on search query.

    Args:
        timeline: List of epic dicts with child_issues
        query: Search query string

    Returns:
        Filtered timeline with only matching issues
    """
    if not query or not query.strip():
        return timeline

    filters = parse_search_query(query)

    if not filters:
        return timeline

    filtered_timeline = []

    for epic in timeline:
        child_issues = epic.get("child_issues", [])

        # Filter child issues
        matching_children = [
            issue for issue in child_issues if matches_all_filters(issue, filters)
        ]

        if matching_children:
            # Recalculate epic metrics for filtered children
            completed_count = sum(
                1
                for issue in matching_children
                if issue.get("health_indicators", {}).get("is_completed")
            )
            completion_pct = (
                (completed_count / len(matching_children) * 100)
                if matching_children
                else 0
            )

            filtered_epic = {
                **epic,
                "child_issues": matching_children,
                "total_issues": len(matching_children),
                "completion_pct": completion_pct,
            }

            filtered_timeline.append(filtered_epic)

    return filtered_timeline


def is_strict_query_valid(timeline: List[Dict[str, Any]], query: str) -> bool:
    """Validate strict mode query rules.

    Rules:
    - summary is free text
    - all other fields must use predefined values from timeline metadata
    - field names must be known
    """
    if not query or not query.strip():
        return True

    known_fields = {
        "key",
        "summary",
        "assignee",
        "issuetype",
        "project",
        "fixversion",
        "labels",
        "components",
    }

    field_values = _extract_field_value_sets(timeline)
    tokens = _tokenize_query(query)

    for token in tokens:
        if token in {"(", ")", "&", "|"}:
            continue

        if ":" not in token:
            continue

        field_name, raw_values = token.split(":", 1)
        normalized_field = _resolve_field_alias(field_name.strip().lower())

        if normalized_field not in known_fields:
            return False

        normalized_values = [
            _normalize_value_token(value)
            for group in _split_unquoted(raw_values, ";")
            for value in _split_unquoted(group, ",")
            if _normalize_value_token(value)
        ]

        if not normalized_values:
            return False

        # Free-text fields: summary (any text) and key (any issue key like A942-3404)
        if normalized_field == "summary" or normalized_field == "key":
            continue

        allowed_values = field_values.get(normalized_field, set())
        if not allowed_values:
            return False

        if any(value not in allowed_values for value in normalized_values):
            return False

    return True


def _extract_field_value_sets(timeline: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    field_values: Dict[str, Set[str]] = {
        "key": set(),
        "assignee": set(),
        "issuetype": set(),
        "project": set(),
        "fixversion": set(),
        "labels": set(),
        "components": set(),
    }

    for epic in timeline:
        child_issues = epic.get("child_issues", []) or []
        for issue in child_issues:
            _add_if_present(field_values["key"], issue.get("issue_key"))
            _add_if_present(field_values["assignee"], issue.get("assignee"))
            _add_if_present(field_values["issuetype"], issue.get("issue_type"))
            _add_if_present(field_values["project"], issue.get("project_key"))

            for fix_version in issue.get("fix_versions") or []:
                if isinstance(fix_version, dict):
                    _add_if_present(
                        field_values["fixversion"],
                        fix_version.get("name") or fix_version.get("value"),
                    )
                else:
                    _add_if_present(field_values["fixversion"], fix_version)

            for label in issue.get("labels") or []:
                if isinstance(label, dict):
                    _add_if_present(
                        field_values["labels"], label.get("name") or label.get("value")
                    )
                else:
                    _add_if_present(field_values["labels"], label)

            for component in issue.get("components") or []:
                if isinstance(component, dict):
                    _add_if_present(
                        field_values["components"],
                        component.get("name") or component.get("value"),
                    )
                else:
                    _add_if_present(field_values["components"], component)

    return field_values


def _add_if_present(target: Set[str], value: Any) -> None:
    if value is None:
        return
    normalized = str(value).strip().lower()
    if normalized:
        target.add(normalized)


def _resolve_field_alias(field_name: str) -> str:
    aliases = {
        "key": "key",
        "issuekey": "key",
        "issue_key": "key",
        "issuetype": "issuetype",
        "issue_type": "issuetype",
        "type": "issuetype",
        "project": "project",
        "projectkey": "project",
        "project_key": "project",
        "fixversion": "fixversion",
        "fix_versions": "fixversion",
        "fix_version": "fixversion",
        "fixversions": "fixversion",
        "label": "labels",
        "labels": "labels",
        "component": "components",
        "components": "components",
    }
    return aliases.get(field_name, field_name)


def _split_unquoted(raw_text: str, delimiter: str) -> List[str]:
    values: List[str] = []
    token: List[str] = []
    in_quote = False

    for char in raw_text:
        if char == '"':
            in_quote = not in_quote
            token.append(char)
            continue

        if not in_quote and char == delimiter:
            values.append("".join(token))
            token = []
            continue

        token.append(char)

    values.append("".join(token))
    return values


def _normalize_value_token(raw_value: str) -> str:
    normalized = raw_value.strip().lower()
    if len(normalized) >= 2 and normalized.startswith('"') and normalized.endswith('"'):
        normalized = normalized[1:-1]
    return normalized.strip()
