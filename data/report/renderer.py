"""Template rendering and report generation utilities.

This module handles HTML template rendering using Jinja2, date range calculations,
and progress tracking for report generation.
"""

import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger(__name__)


def render_template(
    profile_name: str,
    query_name: str,
    time_period_weeks: int,
    sections: List[str],
    metrics: Dict[str, Any],
    chart_script: str,
) -> str:
    """
    Render HTML report template with provided data.

    Args:
        profile_name: Profile display name
        query_name: Query display name
        time_period_weeks: Number of weeks in analysis
        sections: List of sections included
        metrics: Calculated metrics dictionary
        chart_script: Combined Chart.js initialization scripts

    Returns:
        Rendered HTML string
    """
    # Setup Jinja2 environment with custom filters
    # Handle PyInstaller frozen executable path
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        template_dir = Path(sys._MEIPASS) / "report_assets"  # type: ignore[attr-defined]
    else:
        template_dir = Path(__file__).parent.parent.parent / "report_assets"
    env = Environment(loader=FileSystemLoader(template_dir))

    # Add number formatting filters
    def format_int(value):
        """Format as integer (no decimals)."""
        if value is None:
            return "0"
        return f"{int(round(value)):,}"

    def format_decimal1(value):
        """Format with 1 decimal place."""
        if value is None:
            return "0.0"
        return f"{value:.1f}"

    def format_decimal2(value):
        """Format with 2 decimal places."""
        if value is None:
            return "0.00"
        return f"{value:.2f}"

    env.filters["int"] = format_int
    env.filters["dec1"] = format_decimal1
    env.filters["dec2"] = format_decimal2

    template = env.get_template("report_template.html")

    # Generate timestamp with day of week
    generated_at = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

    # Get weeks count from metrics (actual weeks with data)
    weeks_count = metrics.get("dashboard", {}).get("weeks_count", time_period_weeks)

    # Calculate date range for the report period
    from data.iso_week_bucketing import get_iso_week_bounds
    from data.time_period_calculator import get_iso_week, format_year_week

    # Calculate start date (Monday of the oldest week)
    current_date = datetime.now()
    weeks_list = []
    for i in range(weeks_count):
        year, week = get_iso_week(current_date)
        week_label = format_year_week(year, week)
        weeks_list.append(week_label)
        current_date = current_date - timedelta(days=7)

    if weeks_list:
        # Get the oldest week (start of period)
        oldest_week = weeks_list[-1]
        # Parse week label to datetime, then get Monday of that week
        oldest_week_date = parse_week_label(oldest_week)
        start_monday, _ = get_iso_week_bounds(oldest_week_date)
        start_date = start_monday.strftime("%Y-%m-%d")

        # End date is today
        end_date = datetime.now().strftime("%Y-%m-%d")

        # Get first and last week numbers for display
        first_week = weeks_list[-1]  # Oldest
        last_week = weeks_list[0]  # Newest (current)
    else:
        start_date = ""
        end_date = ""
        first_week = ""
        last_week = ""

    # Load and embed external dependencies for offline reports
    from data.report_assets_embedder import embed_report_dependencies

    embedded_deps = embed_report_dependencies()

    html = template.render(
        profile_name=profile_name,
        query_name=query_name,
        generated_at=generated_at,
        time_period_weeks=time_period_weeks,
        weeks_count=weeks_count,
        start_date=start_date,
        end_date=end_date,
        first_week=first_week,
        last_week=last_week,
        sections=sections,
        metrics=metrics,
        chart_script=chart_script,
        show_points=metrics.get("dashboard", {}).get(
            "show_points", False
        ),  # Pass show_points flag
        # Embedded dependencies for offline use
        bootstrap_css=embedded_deps["bootstrap_css"],
        fontawesome_css=embedded_deps["fontawesome_css"],
        chartjs=embedded_deps["chartjs"],
        chartjs_annotation=embedded_deps["chartjs_annotation"],
    )

    return html


def parse_week_label(week_label: str) -> datetime:
    """
    Parse ISO week label to datetime.

    Args:
        week_label: Week label in format "YYYY-WXX" (ISO 8601)

    Returns:
        Datetime for the Monday of that ISO week
    """
    try:
        # Use ISO 8601 week date format: %G (ISO year), %V (ISO week), %u (ISO weekday where 1=Monday)
        return datetime.strptime(week_label + "-1", "%G-W%V-%u")
    except ValueError:
        # Fallback to current date if parsing fails
        logger.warning(f"Could not parse week label: {week_label}")
        return datetime.now()


def update_report_progress(percent: int, message: str) -> None:
    """Helper to update report generation progress.

    Args:
        percent: Progress percentage (0-100)
        message: Progress message
    """
    progress_file = Path("task_progress.json")
    if not progress_file.exists():
        return

    try:
        with open(progress_file, "r", encoding="utf-8") as f:
            state = json.load(f)

        if state.get("task_id") != "generate_report":
            return

        # Update report_progress object (consistent with fetch_progress/calculate_progress)
        state["report_progress"] = {"percent": percent, "message": message}

        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update report progress: {e}")
