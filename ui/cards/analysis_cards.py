import dash_bootstrap_components as dbc
from dash import html

from ui.styles import create_metric_card_header, create_standardized_card


def create_pert_analysis_card() -> dbc.Card:

    header_content = create_metric_card_header(
        title="PERT Analysis",
        tooltip_text=(
            "PERT (Program Evaluation and Review Technique) estimates "
            "project completion time based on optimistic, pessimistic, "
            "and most likely scenarios."
        ),
        tooltip_id="pert-info",
    )

    body_content = html.Div(id="pert-info-container", className="text-center")

    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100",
        body_className="p-3",
        shadow="sm",
    )
