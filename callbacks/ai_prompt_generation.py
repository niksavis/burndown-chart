"""Callbacks for AI prompt generation.

Handles button click → generate prompt → copy to clipboard → show success toast.
Follows Constitution Principle I (Layered Architecture) - delegates to data layer.
"""

import logging

import pyperclip  # Cross-platform clipboard support
from dash import Input, Output, State, callback, no_update

logger = logging.getLogger(__name__)


@callback(
    Output("ai-prompt-weeks-display", "children"),
    Input("data-points-input", "value"),
    prevent_initial_call=False,
)
def sync_ai_prompt_weeks_display(data_points: int) -> str:
    """Sync AI Prompt weeks display with Data Points slider (mirrors Reports tab)."""
    if data_points is None:
        return "12"
    return str(data_points)


@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Input("generate-ai-prompt-button", "n_clicks"),
    State("data-points-input", "value"),
    prevent_initial_call=True,
)
def generate_and_copy_ai_prompt(n_clicks: int, data_points: int):
    """
    Generate AI prompt and copy to clipboard.

    Delegates business logic to data layer (Constitution Principle I).
    Uses pyperclip for cross-platform clipboard support.
    Outputs toast to top-right corner (same as other actions).

    Args:
        n_clicks: Button click count (trigger)
        data_points: Number of weeks from slider (12 default)

    Returns:
        Toast notification component (success or error)
    """
    if not n_clicks:
        return no_update

    try:
        from data.ai_prompt_generator import generate_ai_analysis_prompt
        from ui.toast_notifications import create_toast

        time_period = data_points or 12

        logger.info(f"[AI Prompt] Generating for {time_period} weeks")

        # Delegate to data layer
        prompt = generate_ai_analysis_prompt(time_period_weeks=time_period)

        # Copy to clipboard (cross-platform)
        pyperclip.copy(prompt)

        logger.info(f"[AI Prompt] Generated and copied: {len(prompt)} characters")

        # Show success message (matches export/import toast format)
        return create_toast(
            f"AI analysis prompt ({len(prompt):,} characters) copied to clipboard and ready to paste.",
            toast_type="success",
            header="Prompt Generated Successfully",
            duration=5000,
        )

    except ValueError as e:
        # User-facing errors (no profile, insufficient data)
        logger.warning(f"[AI Prompt] Generation failed: {e}")
        from ui.toast_notifications import create_toast

        return create_toast(
            str(e),
            toast_type="warning",
            header="Cannot Generate Prompt",
        )

    except Exception as e:
        # System errors
        logger.error(f"[AI Prompt] Unexpected error: {e}", exc_info=True)
        from ui.toast_notifications import create_toast

        return create_toast(
            f"Could not generate AI prompt: {str(e)}",
            toast_type="danger",
            header="Generation Failed",
        )
