"""
Budget revision history table component.

Builds the paginated revision history table for the budget settings card.
"""

import math

from dash import html

REVISIONS_PER_PAGE = 2


def create_revision_history_table(
    revisions: list,
    currency_symbol: str,
    page: int = 1,
    per_page: int = REVISIONS_PER_PAGE,
) -> tuple:
    """
    Create paginated revision history table with navigation controls.

    Args:
        revisions: List of revision tuples from database
        currency_symbol: Currency symbol for display
        page: Current page number (1-indexed)
        per_page: Number of revisions per page

    Returns:
        Tuple of (table_element, page_info, prev_disabled, next_disabled, total_pages)
    """
    if not revisions:
        return (
            html.P(
                "No revisions yet. Budget changes will appear here.",
                className="text-muted small text-center",
                style={"padding": "1rem 0"},
            ),
            "Page 1 of 1",
            True,
            True,
            1,
        )

    total_revisions = len(revisions)
    total_pages = math.ceil(total_revisions / per_page)

    # Ensure page is within bounds
    page = max(1, min(page, total_pages))

    start_idx = (page - 1) * per_page
    end_idx = min(start_idx + per_page, total_revisions)
    paginated_revisions = revisions[start_idx:end_idx]

    table_rows = []
    for rev in paginated_revisions:
        (
            rev_date,
            week_label,
            time_delta,
            cost_delta,
            total_delta,
            reason,
            created_at,
        ) = rev

        # Format effective date as "YYYY-Wxx (YYYY-MM-DD)"
        effective_date_str = rev_date[:10]
        effective_display = f"{week_label} ({effective_date_str})"

        changes = []
        if time_delta != 0:
            sign = "+" if time_delta > 0 else ""
            changes.append(
                html.Span(
                    f"{sign}{time_delta}w",
                    className="badge bg-primary me-1",
                    style={"fontSize": "0.7rem"},
                )
            )
        if cost_delta != 0:
            sign = "+" if cost_delta > 0 else ""
            changes.append(
                html.Span(
                    f"{sign}{currency_symbol}{cost_delta:.0f}/wk",
                    className="badge bg-info me-1",
                    style={"fontSize": "0.7rem"},
                )
            )
        if total_delta != 0:
            sign = "+" if total_delta > 0 else ""
            badge_class = "bg-success" if total_delta > 0 else "bg-danger"
            changes.append(
                html.Span(
                    f"{sign}{currency_symbol}{total_delta:,.0f}",
                    className=f"badge {badge_class}",
                    style={"fontSize": "0.7rem"},
                )
            )

        table_rows.append(
            html.Tr(
                [
                    html.Td(
                        html.Strong(
                            effective_display,
                            style={"fontSize": "0.7rem"},
                        ),
                        style={
                            "verticalAlign": "top",
                            "width": "180px",
                            "padding": "0.4rem",
                            "whiteSpace": "nowrap",
                        },
                    ),
                    html.Td(
                        html.Small(
                            created_at[:10] if created_at else rev_date[:10],
                            className="text-muted",
                            style={"fontSize": "0.7rem"},
                        ),
                        style={
                            "verticalAlign": "top",
                            "width": "90px",
                            "padding": "0.4rem",
                        },
                    ),
                    html.Td(
                        changes
                        if changes
                        else html.Span("No changes", className="text-muted small"),
                        style={"verticalAlign": "top", "padding": "0.4rem"},
                    ),
                    html.Td(
                        html.Small(
                            reason or "\u2014",
                            className="text-muted fst-italic",
                            style={"fontSize": "0.7rem"},
                        ),
                        style={"verticalAlign": "top", "padding": "0.4rem"},
                    )
                    if reason
                    else html.Td(
                        "\u2014",
                        className="text-muted",
                        style={"verticalAlign": "top", "padding": "0.4rem"},
                    ),
                ],
                style={"borderBottom": "1px solid #e9ecef"},
            )
        )

    table = html.Table(
        [
            html.Thead(
                html.Tr(
                    [
                        html.Th(
                            "Effective",
                            style={
                                "fontSize": "0.75rem",
                                "width": "180px",
                                "padding": "0.4rem",
                            },
                        ),
                        html.Th(
                            "Modified",
                            style={
                                "fontSize": "0.75rem",
                                "width": "90px",
                                "padding": "0.4rem",
                            },
                        ),
                        html.Th(
                            "Changes",
                            style={"fontSize": "0.75rem", "padding": "0.4rem"},
                        ),
                        html.Th(
                            "Reason",
                            style={"fontSize": "0.75rem", "padding": "0.4rem"},
                        ),
                    ],
                    style={"borderBottom": "2px solid #dee2e6"},
                )
            ),
            html.Tbody(table_rows),
        ],
        className="table table-sm table-hover",
        style={"fontSize": "0.8rem", "marginBottom": "0"},
    )

    page_info = f"Page {page} of {total_pages}"
    prev_disabled = page <= 1
    next_disabled = page >= total_pages

    return table, page_info, prev_disabled, next_disabled, total_pages
