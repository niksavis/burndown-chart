"""Helper functions for field mapping.

Provides display helpers and mock data for field mapping modal.
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import html


def create_dora_flow_mappings_display(field_mappings: dict) -> html.Div:
    """Create a read-only display of DORA/Flow field mappings.

    Args:
        field_mappings: Nested dict with 'dora' and 'flow' keys

    Returns:
        html.Div with formatted display of current mappings
    """
    content = []

    # DORA Metrics Section
    if "dora" in field_mappings:
        content.append(html.H5("DORA Metrics Configuration", className="mt-3 mb-3"))
        dora = field_mappings["dora"]

        for metric_name, metric_fields in dora.items():
            # Format metric name nicely
            display_name = metric_name.replace("_", " ").title()
            content.append(html.H6(display_name, className="text-primary mt-3"))

            # Create table of field mappings
            rows = []
            for field_name, field_value in metric_fields.items():
                rows.append(
                    html.Tr(
                        [
                            html.Td(
                                field_name.replace("_", " ").title(),
                                className="font-weight-bold",
                            ),
                            html.Td(html.Code(str(field_value))),
                        ]
                    )
                )

            content.append(
                html.Table(
                    [html.Tbody(rows)], className="table table-sm table-borderless mb-3"
                )
            )

    # Flow Metrics Section
    if "flow" in field_mappings:
        content.append(html.H5("Flow Metrics Configuration", className="mt-4 mb-3"))
        flow = field_mappings["flow"]

        for metric_name, metric_fields in flow.items():
            # Format metric name nicely
            display_name = metric_name.replace("_", " ").title()
            content.append(html.H6(display_name, className="text-primary mt-3"))

            # Create table of field mappings
            rows = []
            for field_name, field_value in metric_fields.items():
                if isinstance(field_value, list):
                    field_value = ", ".join(field_value)
                rows.append(
                    html.Tr(
                        [
                            html.Td(
                                field_name.replace("_", " ").title(),
                                className="font-weight-bold",
                            ),
                            html.Td(html.Code(str(field_value))),
                        ]
                    )
                )

            content.append(
                html.Table(
                    [html.Tbody(rows)], className="table table-sm table-borderless mb-3"
                )
            )

    # Add informational alert
    return html.Div(
        [
            dbc.Alert(
                [
                    html.I(className="fas fa-info-circle me-2"),
                    "DORA and Flow metrics use structured field mappings configured in ",
                    html.Code("app_settings.json"),
                    ". See ",
                    html.Code("DORA_FLOW_FIELD_MAPPING.md"),
                    " for detailed documentation on these mappings.",
                ],
                color="info",
                className="mb-4",
            ),
            *content,
        ]
    )


def get_mock_jira_fields() -> list[dict[str, Any]]:
    """Get mock Jira fields for testing or when API fails.

    Includes standard Jira fields that work with Apache Kafka JIRA.

    Returns:
        List of mock field metadata
    """
    return [
        # Standard Jira fields (always available)
        {
            "field_id": "created",
            "field_name": "Created",
            "field_type": "datetime",
        },
        {
            "field_id": "resolutiondate",
            "field_name": "Resolution Date",
            "field_type": "datetime",
        },
        {
            "field_id": "issuetype",
            "field_name": "Issue Type",
            "field_type": "select",
        },
        {
            "field_id": "status",
            "field_name": "Status",
            "field_type": "select",
        },
        # Mock custom fields (for full Jira instances)
        {
            "field_id": "customfield_10001",
            "field_name": "Deployment Date",
            "field_type": "datetime",
        },
        {
            "field_id": "customfield_10002",
            "field_name": "Story Points",
            "field_type": "number",
        },
        {
            "field_id": "customfield_10003",
            "field_name": "Environment",
            "field_type": "select",
        },
        {
            "field_id": "customfield_10004",
            "field_name": "Commit Date",
            "field_type": "datetime",
        },
        {
            "field_id": "customfield_10005",
            "field_name": "Production Impact",
            "field_type": "select",
        },
        {
            "field_id": "customfield_10006",
            "field_name": "Incident Flag",
            "field_type": "checkbox",
        },
        {
            "field_id": "customfield_10007",
            "field_name": "Work Item Type",
            "field_type": "select",
        },
        {
            "field_id": "customfield_10008",
            "field_name": "Active Hours",
            "field_type": "number",
        },
    ]


def get_mock_mappings() -> dict[str, dict[str, str]]:
    """Get mock field mappings for Phase 4 stub.

    Phase 5+ will extract actual values from form.

    Returns:
        Mock field mappings structure
    """
    return {
        "dora": {
            "deployment_date": "customfield_10001",
            "code_commit_date": "customfield_10004",
        },
        "flow": {
            "flow_item_type": "customfield_10007",
            "status": "status",
            "completed_date": "resolutiondate",
        },
    }
