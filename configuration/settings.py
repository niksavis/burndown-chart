import logging
from datetime import datetime, timedelta

import pandas as pd

from configuration.logging_config import cleanup_old_logs, setup_logging

setup_logging(
    log_dir="logs", max_bytes=10 * 1024 * 1024, backup_count=5, log_level="INFO"
)

cleanup_old_logs(log_dir="logs", max_age_days=30)

logger = logging.getLogger(__name__)
logger.info("Application configuration loaded - logging initialized")

DEFAULT_PERT_FACTOR = 6
DEFAULT_TOTAL_ITEMS = 100
DEFAULT_TOTAL_POINTS = 1000
DEFAULT_DEADLINE = (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d")
DEFAULT_ESTIMATED_ITEMS = 20
DEFAULT_ESTIMATED_POINTS = 200
DEFAULT_DATA_POINTS_COUNT = 12

SETTINGS_FILE = "forecast_settings.json"
APP_SETTINGS_FILE = "app_settings.json"
PROJECT_DATA_FILE = "project_data.json"

SAMPLE_DATA = pd.DataFrame(
    {
        "date": [
            (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            for i in range(10, 0, -1)
        ],
        "completed_items": [5, 7, 3, 6, 4, 8, 5, 6, 7, 4],
        "completed_points": [50, 70, 30, 60, 40, 80, 50, 60, 70, 40],
    }
)

COLOR_PALETTE = {
    "items": "rgb(0, 99, 178)",
    "points": "rgb(255, 127, 14)",
    "optimistic": "rgb(20, 168, 150)",
    "pessimistic": "rgb(128, 0, 128)",
    "deadline": "rgb(220, 20, 60)",
    "items_grid": "rgba(0, 99, 178, 0.1)",
    "points_grid": "rgba(255, 127, 14, 0.1)",
    "info": "rgb(13, 110, 253)",
    "success": "rgb(25, 135, 84)",
    "warning": "rgb(255, 193, 7)",
    "danger": "rgb(220, 53, 69)",
    "secondary": "rgb(108, 117, 125)",
    "muted": "rgb(108, 117, 125)",
}

FORECAST_HELP_TEXTS = {
    "pert_methodology": (
        "3-point estimation combining optimistic, likely, and pessimistic scenarios."
    ),
    "optimistic_forecast": "Best-case completion estimate from peak velocity periods.",
    "most_likely_forecast": "Most probable estimate based on current average velocity.",
    "pessimistic_forecast": "Worst-case estimate from lowest velocity periods.",
    "expected_forecast": "Balanced forecast weighing likely scenario most heavily.",
    "three_point_estimation": "Forecast ranges instead of single-point estimates.",
    "forecast-info": """
        Comprehensive guide to interpreting the forecast graph and its components.
        
        Visual Elements:
        • Solid lines: Historical actual data from your project
        • Dashed lines: PERT forecast projections (optimistic/most likely/pessimistic)
        • Confidence bands: Uncertainty ranges around forecasts
        • Deadline marker: Target completion date (red vertical line)
        • Milestone indicators: Interim project goals and checkpoints
        
        Reading the Chart:
        • Y-axis: Work remaining (burndown) or completed (burnup)
        • X-axis: Time progression from start to deadline
        • Forecast accuracy improves with more historical data points
        • Color coding matches PERT methodology (blue/orange/teal/indigo)
    """,
}

VELOCITY_HELP_TEXTS = {
    "weekly_velocity": (
        "Team's completion rate over recent weeks with trend indicators."
    ),
    "velocity_average": (
        "Simple average of weekly completion rates over selected period."
    ),
    "velocity_median": "Middle value of weekly rates, resistant to outliers.",
    "velocity_trend": (
        "Direction of velocity change - up, down, or stable with percentage."
    ),
    "ten_week_calculation": "Uses 10 weeks of data for statistical reliability.",
    "trend_significance": "Bold trends indicate statistically significant changes.",
    "weighted_moving_average": "Recent weeks weighted more heavily in calculations.",
}

PROJECT_HELP_TEXTS = {
    "project_overview": "High-level project completion status and progress metrics.",
    "completion_percentage": "Percentage of work completed based on items or points.",
    "items_vs_points": "Comparison of item-based vs point-based progress tracking.",
    "weekly_averages": "Average completion rates showing sustainable team velocity.",
    "velocity_stability": (
        "Consistency of weekly completion rates - stable, moderate, or variable."
    ),
    "completion_timeline": "Projected completion dates based on PERT calculations.",
}

SCOPE_HELP_TEXTS = {
    "scope_change_rate": (
        "New work added vs baseline scope. Baseline = work remaining "
        "at window start (current remaining + completed in period - "
        "created in period). Shows scope expansion within selected "
        "timeframe (e.g., 12 weeks)."
    ),
    "throughput_ratio": (
        "Work creation vs completion ratio. >1 = adding faster than "
        "completing (growing backlog), <1 = completing faster "
        "(shrinking backlog). Calculated for selected time window."
    ),
    "threshold_color_coding": (
        "Visual indicators showing velocity impact of scope changes."
    ),
    "adaptability_index": (
        "Scope Stability Index: Measures how stable the scope is relative "
        "to total work. Calculated as 1 - (created / total_scope). "
        "Higher values (0.7+) = stable, predictable scope with few "
        "additions. Lower values (0.3-0.6) = dynamic, evolving scope "
        "with frequent additions (normal for responsive agile teams)."
    ),
    "weekly_scope_patterns": "Week-by-week tracking of requirement discovery patterns.",
    "agile_scope_philosophy": (
        "Scope changes are expected and valuable in agile projects."
    ),
    "scope_metrics_explanation": (
        "Tracks scope changes within selected time window. "
        "Baseline = scope at window start. All metrics respond "
        "to data point slider setting."
    ),
    "jira_scope_calculation": (
        "Intelligent extrapolation for items without story points."
    ),
    "cumulative_chart": (
        "Shows actual remaining work over time. Begins with the backlog "
        "size at the start of the selected window (baseline) and tracks "
        "week-by-week changes. Values represent real backlog size "
        "that cannot go negative."
    ),
    "weekly_growth": (
        "Week-by-week scope additions and reductions showing discovery patterns."
    ),
}

STATISTICS_HELP_TEXTS = {
    "date_field": "Data collection date - weekly snapshots in YYYY-MM-DD format.",
    "completed_items": "Number of work items finished during this period.",
    "completed_points": "Story points completed during this period.",
    "created_items": "Number of new work items added during this period.",
    "created_points": "Story points for new work items added during this period.",
    "velocity_items": "Weekly completion rate for items based on historical data.",
    "velocity_points": "Weekly completion rate for points based on historical data.",
    "data_frequency": "Weekly snapshots provide optimal balance for forecasting.",
    "cumulative_vs_incremental": (
        "Values represent incremental work per period, not cumulative totals."
    ),
}

CHART_HELP_TEXTS = {
    "weighted_moving_average": (
        "Recent weeks weighted more heavily than older data (40%, 30%, 20%, 10%)."
    ),
    "forecast_vs_actual_bars": (
        "Solid bars show historical data, patterned bars "
        "show forecasts with error bars."
    ),
    "forecast_confidence_intervals": (
        "Error bars show uncertainty range around forecast predictions."
    ),
    "exponential_weighting": (
        "Recent performance emphasized over older data for better trend capture."
    ),
    "weekly_chart_methodology": (
        "Weekly aggregation with PERT forecasts and confidence intervals."
    ),
    "pert_forecast_methodology": (
        "Three-point estimation using optimistic, likely, and pessimistic scenarios."
    ),
    "historical_data_influence": (
        "More data points improve forecast accuracy - 6+ weeks recommended."
    ),
    "chart_legend_explained": (
        "Visual cues distinguish historical data, forecasts, and confidence bands."
    ),
    "forecast_confidence_bands": (
        "Band width indicates forecast uncertainty based on velocity variability."
    ),
    "scope_change_indicators": (
        "Vertical markers show scope changes with automatic forecast adjustments."
    ),
    "data_points_precision": (
        "8-15 recent data points provide optimal forecast accuracy."
    ),
    "burndown_vs_burnup": (
        "Burndown shows remaining work decreasing; "
        "Burnup shows completed work increasing."
    ),
    "forecast_explanation": """The graph shows your burndown forecast
based on historical data:
        - Solid lines: Historical progress
        - Dashed lines: Most likely forecast
        - Dotted lines: Optimistic and pessimistic forecasts
        - Blue/Green lines: Items tracking
        - Orange/Yellow lines: Points tracking
        - Red vertical line: Your deadline
        
        Where forecast lines cross zero indicates estimated completion dates.""",
}


def get_bug_analysis_config() -> dict:

    from data.persistence import load_app_settings  # noqa: PLC0415

    settings = load_app_settings()

    default_config = {
        "enabled": True,
        "issue_type_mappings": {"Bug": "bug", "Defect": "bug", "Incident": "bug"},
        "default_bug_type": "Bug",
    }

    return settings.get("bug_analysis_config", default_config)
