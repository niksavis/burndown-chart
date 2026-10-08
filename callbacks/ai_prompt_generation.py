import logging

import pyperclip
from dash import Input, Output, State, callback, no_update

from data.ai_prompt_generator import generate_ai_analysis_prompt
from ui.toast_notifications import create_toast

logger = logging.getLogger(__name__)


@callback(
    Output("ai-prompt-weeks-display", "children"),
    Input("data-points-input", "value"),
    prevent_initial_call=False,
)
def sync_ai_prompt_weeks_display(data_points: int) -> str:
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

    if not n_clicks:
        return no_update

    try:
        time_period = data_points or 12

        logger.info(f"[AI Prompt] Generating for {time_period} weeks")

        prompt = generate_ai_analysis_prompt(time_period_weeks=time_period)

        pyperclip.copy(prompt)

        logger.info(f"[AI Prompt] Generated and copied: {len(prompt)} characters")

        return create_toast(
            (
                f"AI analysis prompt ({len(prompt):,} characters) "
                "copied to clipboard and ready to paste."
            ),
            toast_type="success",
            header="Prompt Generated Successfully",
            duration=5000,
        )

    except ValueError as e:
        logger.warning(f"[AI Prompt] Generation failed: {e}")

        return create_toast(
            str(e),
            toast_type="warning",
            header="Cannot Generate Prompt",
        )

    except Exception as e:
        logger.error(f"[AI Prompt] Unexpected error: {e}", exc_info=True)

        return create_toast(
            f"Could not generate AI prompt: {str(e)}",
            toast_type="danger",
            header="Generation Failed",
        )
