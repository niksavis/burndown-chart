import logging

from dash import Input, Output, callback, callback_context, html

from data.persistence import load_app_settings

logger = logging.getLogger(__name__)


@callback(
    Output("field-mapping-status-indicator", "children"),
    [
        Input("field-mapping-modal", "is_open"),
        Input("field-mapping-save-button", "n_clicks"),
        Input("profile-selector", "value"),
    ],
    prevent_initial_call=False,
)
def update_field_mapping_status(modal_is_open, save_clicks, profile_id):

    import time  # noqa: PLC0415

    try:
        if (
            callback_context.triggered
            and callback_context.triggered[0]["prop_id"] == "profile-selector.value"
        ):
            time.sleep(0.1)

        settings = load_app_settings()
        field_mappings = settings.get("field_mappings", {})

        dora_mappings = field_mappings.get("dora", {})
        flow_mappings = field_mappings.get("flow", {})

        dora_count = sum(1 for v in dora_mappings.values() if v and str(v).strip())
        flow_count = sum(1 for v in flow_mappings.values() if v and str(v).strip())
        total_count = dora_count + flow_count

        if total_count > 0:
            return html.Div(
                [
                    html.I(className="fas fa-check-circle text-success me-2"),
                    html.Span(
                        f"Configured: {dora_count} DORA + {flow_count} Flow fields",
                        className="text-success small",
                        title=(
                            f"DORA metrics: {dora_count} fields mapped, "
                            f"Flow metrics: {flow_count} fields mapped"
                        ),
                    ),
                ],
                className="d-flex align-items-center",
                style={"overflow": "hidden", "textOverflow": "ellipsis"},
            )
        else:
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
