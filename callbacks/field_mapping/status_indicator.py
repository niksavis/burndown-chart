"""Status indicator callback for field mapping.

Shows current field mapping configuration status.
"""

import logging
from dash import callback, callback_context, Output, Input, html

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-status-indicator", "children"),
    [
        Input("field-mapping-modal", "is_open"),
        Input("field-mapping-save-button", "n_clicks"),
        Input("profile-selector", "value"),
    ],
    prevent_initial_call=False,  # Run on page load to show initial status
)
def update_field_mapping_status(modal_is_open, save_clicks, profile_id):
    """Update the field mapping status indicator to show whether fields are mapped.

    Args:
        modal_is_open: Whether the modal is currently open
        save_clicks: Number of times save button has been clicked (triggers refresh)
        profile_id: Active profile ID (triggers refresh on profile switch)

    Returns:
        Status indicator component showing mapping state
    """
    from data.persistence import load_app_settings
    import time

    try:
        # If triggered by profile switch, wait briefly for switch to complete
        if (
            callback_context.triggered
            and callback_context.triggered[0]["prop_id"] == "profile-selector.value"
        ):
            time.sleep(0.1)  # 100ms delay to let profile switch complete

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})

        # Check if any DORA or Flow fields are mapped
        dora_mappings = field_mappings.get("dora", {})
        flow_mappings = field_mappings.get("flow", {})

        # Count non-empty mappings (excluding empty strings and None)
        dora_count = sum(1 for v in dora_mappings.values() if v and str(v).strip())
        flow_count = sum(1 for v in flow_mappings.values() if v and str(v).strip())
        total_count = dora_count + flow_count

        if total_count > 0:
            # Fields are mapped - show green success status
            return html.Div(
                [
                    html.I(className="fas fa-check-circle text-success me-2"),
                    html.Span(
                        f"Configured: {dora_count} DORA + {flow_count} Flow fields",
                        className="text-success small",
                        title=f"DORA metrics: {dora_count} fields mapped, Flow metrics: {flow_count} fields mapped",
                    ),
                ],
                className="d-flex align-items-center",
                style={"overflow": "hidden", "textOverflow": "ellipsis"},
            )
        else:
            # No fields mapped - show warning
            return html.Div(
                [
                    html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                    html.Span(
                        "Configure field mappings to enable metrics",
                        className="text-muted small",
                    ),
                ],
                className="d-flex align-items-center",
            )

    except Exception as e:
        logger.error(f"Error loading field mapping status: {e}", exc_info=True)
        return html.Div(
            [
                html.I(className="fas fa-exclamation-triangle text-warning me-2"),
                html.Span(
                    "Error loading field mappings",
                    className="text-muted small",
                ),
            ],
            className="d-flex align-items-center",
        )
