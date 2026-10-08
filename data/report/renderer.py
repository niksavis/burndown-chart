import json
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader
from jinja2.runtime import Undefined

from data.iso_week_bucketing import get_iso_week_bounds
from data.report_assets_embedder import embed_report_dependencies
from data.time_period_calculator import format_year_week, get_iso_week

logger = logging.getLogger(__name__)


def render_template(
    profile_name: str,
    query_name: str,
    time_period_weeks: int,
    sections: list[str],
    metrics: dict[str, Any],
    chart_script: str,
) -> str:

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        template_dir = Path(sys._MEIPASS) / "report_assets"  # type: ignore[attr-defined]
    else:
        template_dir = Path(__file__).parent.parent.parent / "report_assets"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=True,
    )

    def format_int(value):
        if value is None or isinstance(value, Undefined):
            return "0"
        return f"{int(round(value)):,}"

    def format_decimal1(value):
        if value is None or isinstance(value, Undefined):
            return "0.0"
        return f"{value:.1f}"

    def format_decimal2(value):
        if value is None or isinstance(value, Undefined):
            return "0.00"
        return f"{value:.2f}"

    env.filters["int"] = format_int
    env.filters["dec1"] = format_decimal1
    env.filters["dec2"] = format_decimal2

    template = env.get_template("report_template.html")

    generated_at = datetime.now().strftime("%A, %Y-%m-%d %H:%M:%S")

    weeks_count = metrics.get("dashboard", {}).get("weeks_count", time_period_weeks)

    current_date = datetime.now()
    weeks_list = []
    for _i in range(weeks_count):
        year, week = get_iso_week(current_date)
        week_label = format_year_week(year, week)
        weeks_list.append(week_label)
        current_date = current_date - timedelta(days=7)

    if weeks_list:
        oldest_week = weeks_list[-1]
        oldest_week_date = parse_week_label(oldest_week)
        start_monday, _ = get_iso_week_bounds(oldest_week_date)
        start_date = start_monday.strftime("%Y-%m-%d")

        end_date = datetime.now().strftime("%Y-%m-%d")

        first_week = weeks_list[-1]
        last_week = weeks_list[0]
    else:
        start_date = ""
        end_date = ""
        first_week = ""
        last_week = ""

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
        show_points=metrics.get("dashboard", {}).get("show_points", False),
        bootstrap_css=embedded_deps["bootstrap_css"],
        fontawesome_css=embedded_deps["fontawesome_css"],
        chartjs=embedded_deps["chartjs"],
        chartjs_annotation=embedded_deps["chartjs_annotation"],
    )

    return html


def parse_week_label(week_label: str) -> datetime:

    try:
        return datetime.strptime(week_label + "-1", "%G-W%V-%u")
    except ValueError:
        logger.warning(f"Could not parse week label: {week_label}")
        return datetime.now()


def update_report_progress(percent: int, message: str) -> None:

    progress_file = Path("task_progress.json")
    if not progress_file.exists():
        return

    try:
        with open(progress_file, encoding="utf-8") as f:
            state = json.load(f)

        if state.get("task_id") != "generate_report":
            return

        state["report_progress"] = {"percent": percent, "message": message}

        with open(progress_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.warning(f"Failed to update report progress: {e}")
