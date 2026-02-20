"""Active Work Timeline Callbacks Module

This module provides callback functions for the Active Work Timeline feature,
handling epic/feature timeline rendering with recent activity.

Follows Sprint Tracker pattern for conditional tab display.
"""

import logging
import re

import dash_bootstrap_components as dbc
from dash import ClientsideFunction, Input, Output, State, ctx, html

logger = logging.getLogger(__name__)


def _remove_last_clause(query: str) -> str:
    """Remove the last top-level clause from a builder query string."""
    text = (query or "").strip()
    if not text:
        return ""

    clauses: list[str] = []
    operators: list[str] = []
    chunk_start = 0
    depth = 0
    in_quote = False

    for index, char in enumerate(text):
        if char == '"':
            in_quote = not in_quote
            continue

        if in_quote:
            continue

        if char == "(":
            depth += 1
            continue

        if char == ")":
            depth = max(0, depth - 1)
            continue

        if depth == 0 and char in {"&", "|"}:
            clauses.append(text[chunk_start:index].strip())
            operators.append(char)
            chunk_start = index + 1

    clauses.append(text[chunk_start:].strip())

    clauses = [clause for clause in clauses if clause]
    if len(clauses) <= 1:
        return ""

    keep_clauses = clauses[:-1]
    keep_operators = operators[: len(keep_clauses) - 1]

    rebuilt = keep_clauses[0]
    for op, clause in zip(keep_operators, keep_clauses[1:], strict=False):
        rebuilt = f"{rebuilt} {op} {clause}"

    return rebuilt.strip()


def _render_active_work_timeline_content(
    show_points: bool = False, data_points_count: int = 30
) -> html.Div:
    """Render Active Work Timeline content with nested epic timeline.

    Structure:
    1. Epic Timeline with nested issues (sorted: Blocked/WIP → To Do → Completed)
    2. Issues filtered by data_points_count week range

    Args:
        show_points: Whether to show story points metrics
        data_points_count: Number of weeks to look back (from Data Points slider)

    Returns:
        Div containing nested epic timeline
    """
    try:
        from data.active_work_manager import get_active_work_data
        from data.persistence.factory import get_backend
        from ui.active_work_epic_timeline import create_nested_epic_timeline
        from ui.empty_states import create_no_active_work_state

        backend = get_backend()

        # Get active profile and query
        active_profile_id = backend.get_app_state("active_profile_id")
        active_query_id = backend.get_app_state("active_query_id")

        if not active_profile_id or not active_query_id:
            logger.warning("No active profile/query - cannot render timeline")
            return create_no_active_work_state()

        logger.info(
            f"[ACTIVE WORK] Rendering Active Work Timeline for profile={active_profile_id}, query={active_query_id}, data_points={data_points_count}"
        )

        # Load issues from database
        issues = backend.get_issues(
            profile_id=active_profile_id, query_id=active_query_id
        )

        if not issues:
            logger.warning("[ACTIVE WORK] No issues found for active profile/query")
            return create_no_active_work_state()

        logger.info(f"[ACTIVE WORK] Loaded {len(issues)} issues from database")

        # Get configuration
        from data.persistence import load_app_settings

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})
        general_mappings = field_mappings.get("general", {})
        workflow_mappings = field_mappings.get("workflow", {})

        parent_field = general_mappings.get("parent_field")
        flow_end_statuses = workflow_mappings.get("flow_end_statuses", [])
        flow_wip_statuses = workflow_mappings.get("flow_wip_statuses", [])
        development_projects = settings.get("development_projects", [])
        devops_projects = settings.get("devops_projects", [])

        # DEBUG: Log configuration
        logger.info(f"[ACTIVE WORK DEBUG] development_projects: {development_projects}")
        logger.info(f"[ACTIVE WORK DEBUG] devops_projects: {devops_projects}")
        logger.info(f"[ACTIVE WORK DEBUG] Before filtering: {len(issues)} total issues")

        # Filter to only configured development project issues
        from data.project_filter import filter_development_issues

        issues = filter_development_issues(
            issues, development_projects, devops_projects
        )
        logger.info(
            f"[ACTIVE WORK] After project filtering: {len(issues)} development issues"
        )

        # Check if parent field is configured
        parent_field_configured = bool(parent_field)

        if not parent_field_configured:
            logger.info(
                "Parent field not configured - will show issues without epic timeline"
            )
            # Use dummy parent field to still process issues
            parent_field = "parent"  # Won't match anything, all issues will be orphaned

        logger.info(
            f"[ACTIVE WORK] Using parent field: {parent_field} (configured: {parent_field_configured})"
        )

        # Get active work data with nested structure
        try:
            logger.info(
                f"[ACTIVE WORK] Calling get_active_work_data with {len(issues)} issues..."
            )
            work_data = get_active_work_data(
                issues,
                backend=backend,
                profile_id=active_profile_id,
                query_id=active_query_id,
                data_points_count=data_points_count,
                parent_field=parent_field,
                flow_end_statuses=flow_end_statuses if flow_end_statuses else None,
                flow_wip_statuses=flow_wip_statuses if flow_wip_statuses else None,
                filter_parents=True,  # Filter out parent issues from child calculations
            )
            logger.info("[ACTIVE WORK] get_active_work_data returned successfully")
        except Exception as e:
            logger.error(
                f"[ACTIVE WORK] Error in get_active_work_data: {e}", exc_info=True
            )
            return create_no_active_work_state(
                parent_field_configured=parent_field_configured
            )

        timeline = work_data.get("timeline", [])

        logger.info(f"[ACTIVE WORK] Got work_data: timeline={len(timeline)} epics")

        if not timeline:
            logger.warning(
                "[ACTIVE WORK] No active work found after filtering - empty timeline"
            )
            return create_no_active_work_state(
                parent_field_configured=parent_field_configured
            )

        # Count total issues across all epics
        total_issues = sum(epic.get("total_issues", 0) for epic in timeline)

        logger.info(f"Found {len(timeline)} epics with {total_issues} total issues")

        # Get recently completed items by week
        from data.active_work_completed import get_completed_items_by_week
        from ui.active_work_completed_components import create_completed_items_section

        completed_by_week = get_completed_items_by_week(
            issues=issues,
            flow_end_statuses=flow_end_statuses if flow_end_statuses else None,
            n_weeks=2,  # Current week + last week
            parent_field=parent_field,
        )

        completed_section = create_completed_items_section(
            completed_by_week, show_points=show_points
        )

        # Create nested epic timeline
        summary_text = (
            f"Showing {len(timeline)} epics with {total_issues} issues "
            f"(last {data_points_count} week"
            f"{'s' if data_points_count != 1 else ''})"
        )

        timeline_content = create_nested_epic_timeline(
            timeline,
            show_points,
            parent_field_configured,
            summary_text,
            completed_section=completed_section,  # Insert between legend and epics
        )

        # Assemble layout
        return html.Div(
            [
                dbc.Container(
                    [
                        # Nested epic timeline (includes legend, completed items, and epics)
                        timeline_content,
                    ],
                    fluid=True,
                    className="py-3",
                )
            ]
        )

    except Exception as e:
        logger.error(f"Error rendering Active Work Timeline: {e}", exc_info=True)
        from ui.empty_states import create_no_active_work_state

        return create_no_active_work_state()


def register(app):
    """Register Active Work Timeline callbacks.

    Args:
        app: Dash application instance
    """
    if getattr(app, "_active_work_callbacks_registered", False):
        logger.debug("[ACTIVE WORK] Callbacks already registered; skipping")
        return

    app._active_work_callbacks_registered = True

    # Client-side callback: Build search metadata from timeline data
    app.clientside_callback(
        ClientsideFunction(
            namespace="activeWorkSearch", function_name="buildSearchMetadata"
        ),
        Output("active-work-search-metadata-store", "data"),
        Input("active-work-issues-store", "data"),
    )

    def _build_query_preview(query_text: str):
        """Build color-coded query preview for fields, values, and operators."""
        query = (query_text or "").strip()
        if not query:
            return ""

        preview_parts = []
        for token in re.split(r"(\s+|[&|()])", query):
            if token is None or token == "":
                continue

            if token.isspace():
                preview_parts.append(token)
                continue

            if token in {"&", "|", "(", ")"}:
                preview_parts.append(
                    html.Span(token, className="active-work-token-operator")
                )
                continue

            if ":" in token:
                field_name, value_text = token.split(":", 1)
                if field_name:
                    preview_parts.append(
                        html.Span(field_name, className="active-work-token-field")
                    )
                preview_parts.append(
                    html.Span(":", className="active-work-token-operator")
                )
                if value_text:
                    preview_parts.append(
                        html.Span(value_text, className="active-work-token-value")
                    )
                continue

            preview_parts.append(html.Span(token, className="active-work-token-value"))

        return html.Div(preview_parts, className="active-work-query-preview-line")

    def _build_query_outputs(query_text: str):
        """Return synchronized builder outputs with formatted preview."""
        query = (query_text or "").strip()
        return query, query, _build_query_preview(query)

    @app.callback(
        Output("active-work-builder-value-select", "options"),
        Output("active-work-builder-value-select", "style"),
        Output("active-work-builder-value-text", "style"),
        Input("active-work-builder-field", "value"),
        Input("active-work-search-metadata-store", "data"),
        prevent_initial_call=False,
    )
    def update_builder_value_options(selected_field, metadata):
        """Populate value options for selected field and toggle input type."""
        shared_style = {"flex": "1", "minWidth": "260px"}

        if not selected_field:
            return [], shared_style, {**shared_style, "display": "none"}

        if selected_field in {"summary", "key"}:
            return [], {**shared_style, "display": "none"}, shared_style

        values = ((metadata or {}).get("values") or {}).get(selected_field, [])
        if not isinstance(values, list):
            values = []

        options = [{"label": value, "value": value} for value in values if value]
        return options, shared_style, {**shared_style, "display": "none"}

    @app.callback(
        Output("active-work-builder-query-store", "data"),
        Output("active-work-search-input", "value"),
        Output("active-work-search-query-preview", "children"),
        Input("active-work-builder-add-and", "n_clicks"),
        Input("active-work-builder-add-or", "n_clicks"),
        Input("active-work-builder-undo", "n_clicks"),
        Input("active-work-search-clear", "n_clicks"),
        State("active-work-builder-field", "value"),
        State("active-work-builder-value-select", "value"),
        State("active-work-builder-value-text", "value"),
        State("active-work-builder-query-store", "data"),
        prevent_initial_call=False,
    )
    def build_query(
        n_add_and,
        n_add_or,
        n_undo,
        n_clear,
        selected_field,
        selected_value,
        text_value,
        current_query,
    ):
        """Build query via explicit AND/OR actions, clear resets everything."""
        triggered = ctx.triggered_id

        if triggered is None:
            return _build_query_outputs(current_query)

        if triggered == "active-work-search-clear":
            return "", "", ""

        if triggered == "active-work-builder-undo":
            next_query = _remove_last_clause(current_query or "")
            return _build_query_outputs(next_query)

        field_name = (selected_field or "").strip().lower()
        free_text = (text_value or "").strip()
        existing = (current_query or "").strip()

        if not field_name:
            return _build_query_outputs(existing)

        if field_name in {"summary", "key"}:
            value_tokens = [
                token.strip()
                for token in re.split(r"[|,;]", free_text)
                if token and token.strip()
            ]
            if not value_tokens:
                return _build_query_outputs(existing)

            if field_name == "summary":
                normalized_tokens = []
                for token in value_tokens:
                    normalized_tokens.append(
                        f'"{token}"' if ("," in token or ";" in token) else token
                    )
                if len(normalized_tokens) == 1:
                    predicate = f"summary:{normalized_tokens[0]}"
                else:
                    summary_predicates = [
                        f"summary:{token}" for token in normalized_tokens
                    ]
                    predicate = f"({' | '.join(summary_predicates)})"
            else:
                if len(value_tokens) == 1:
                    predicate = f"key:{value_tokens[0]}"
                else:
                    key_predicates = [f"key:{token}" for token in value_tokens]
                    predicate = f"({' | '.join(key_predicates)})"
        else:
            if isinstance(selected_value, list):
                values = [
                    str(value).strip() for value in selected_value if str(value).strip()
                ]
            elif selected_value:
                values = [str(selected_value).strip()]
            else:
                values = []

            if not values:
                return _build_query_outputs(existing)

            formatted_values = []
            for value in values:
                formatted_values.append(
                    f'"{value}"' if ("," in value or ";" in value) else value
                )
            value_expr = ";".join(formatted_values)
            predicate = f"{field_name}:{value_expr}"

        if not existing:
            next_query = predicate
        elif triggered == "active-work-builder-add-and":
            next_query = f"{existing} & {predicate}"
        elif triggered == "active-work-builder-add-or":
            next_query = f"{existing} | {predicate}"
        else:
            next_query = existing

        return _build_query_outputs(next_query)

    # Server-side callback: Filter timeline based on search
    @app.callback(
        Output("active-work-filtered-content", "children"),
        Output("completed-items-section", "children"),
        Input("active-work-applied-query-store", "data"),
        State("active-work-issues-store", "data"),
        prevent_initial_call=False,
    )
    def filter_timeline(search_input, timeline_data):
        """Filter timeline based on search input (server-side for now)."""
        from data.active_work_completed import get_completed_items_by_week
        from data.persistence import load_app_settings
        from ui.active_work_completed_components import create_completed_items_section
        from ui.active_work_epic_timeline import _render_filtered_timeline

        def _flatten_issues(epics):
            flattened = []
            for epic in epics or []:
                child_issues = epic.get("child_issues", [])
                if isinstance(child_issues, list):
                    flattened.extend(child_issues)
            return flattened

        def _build_completed_children(epics):
            settings = load_app_settings()
            field_mappings = settings.get("field_mappings", {})
            general_mappings = field_mappings.get("general", {})
            workflow_mappings = field_mappings.get("workflow", {})

            parent_field = general_mappings.get("parent_field")
            flow_end_statuses = workflow_mappings.get("flow_end_statuses", [])

            completed_by_week = get_completed_items_by_week(
                issues=_flatten_issues(epics),
                flow_end_statuses=flow_end_statuses if flow_end_statuses else None,
                n_weeks=2,
                parent_field=parent_field,
            )

            current_week_count = 0
            last_week_count = 0
            for week_data in completed_by_week.values():
                total_issues = int(week_data.get("total_issues", 0) or 0)
                if week_data.get("is_current"):
                    current_week_count = total_issues
                else:
                    last_week_count = total_issues

            completed_section = create_completed_items_section(
                completed_by_week, show_points=False
            )
            return completed_section.children, current_week_count, last_week_count

        if not timeline_data:
            return html.Div(), []

        from data.active_work_search import (
            filter_timeline_by_query,
            is_strict_query_valid,
        )

        query_text = (search_input or "").strip()
        query_state = "empty"
        display_timeline = timeline_data

        if query_text:
            if is_strict_query_valid(timeline_data, query_text):
                query_state = "applied"
                display_timeline = filter_timeline_by_query(timeline_data, query_text)
            else:
                query_state = "invalid"

        completed_children, current_week_count, last_week_count = (
            _build_completed_children(display_timeline)
        )
        all_work_issues = len(_flatten_issues(display_timeline))
        short_query = query_text[:120]

        logger.info(
            "[ACTIVE WORK FILTER] "
            f"query_state={query_state}, "
            f"query='{short_query}', "
            f"all_work_issues={all_work_issues}, "
            f"completed_last_week={last_week_count}, "
            f"completed_current_week={current_week_count}"
        )

        return (
            _render_filtered_timeline(display_timeline, show_points=False),
            completed_children,
        )

    @app.callback(
        Output("active-work-applied-query-store", "data"),
        Input("active-work-search-apply", "n_clicks"),
        Input("active-work-search-clear", "n_clicks"),
        State("active-work-builder-query-store", "data"),
        State("active-work-search-input", "value"),
        prevent_initial_call=False,
    )
    def apply_or_clear_search(n_apply, n_clear, builder_query, search_input):
        """Apply search only when Search is clicked; clear applied query on Clear."""
        triggered = ctx.triggered_id

        if triggered == "active-work-search-clear":
            return ""

        if triggered == "active-work-search-apply":
            query = (builder_query or search_input or "").strip()
            return query

        return ""

    # Server-side callback: Clear builder input value selector
    @app.callback(
        Output("active-work-builder-value-select", "value"),
        Output("active-work-builder-value-text", "value"),
        Input("active-work-search-clear", "n_clicks"),
        prevent_initial_call=True,
    )
    def clear_search(n_clicks):
        """Clear value selector when Clear button is clicked."""
        return [], ""
