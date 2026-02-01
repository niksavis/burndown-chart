"""
Analysis Card Components

This module provides specialized analysis card components for displaying
complex analysis results like PERT analysis timelines.

Analysis Cards:
- create_pert_analysis_card: PERT timeline visualization card
"""

import dash_bootstrap_components as dbc
from dash import html

from ui.styles import create_card_header_with_tooltip, create_standardized_card


def create_pert_analysis_card() -> dbc.Card:
    """
    Create the PERT analysis card component.

    Returns:
        Dash Card component for PERT analysis
    """
    # Create the card header with tooltip and Phase 9.2 Progressive Disclosure help button
    header_content = create_card_header_with_tooltip(
        "PERT Analysis",
        tooltip_id="pert-info",
        tooltip_text="PERT (Program Evaluation and Review Technique) estimates project completion time based on optimistic, pessimistic, and most likely scenarios.",
        help_key="pert_analysis_detailed",
        help_category="forecast",
    )

    # Create the card body content
    body_content = html.Div(id="pert-info-container", className="text-center")

    # Return the standardized card
    return create_standardized_card(
        header_content=header_content,
        body_content=body_content,
        className="mb-3 h-100",
        body_className="p-3",
        shadow="sm",
    )
