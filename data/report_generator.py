"""HTML report generator for burndown charts and metrics."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Template
import pandas as pd

logger = logging.getLogger(__name__)


def generate_html_report(
    sections: List[str],
    time_period_weeks: int = 12,
    profile_id: Optional[str] = None,
) -> str:
    """
    Generate a self-contained HTML report with project metrics snapshot.

    Args:
        sections: List of section identifiers: ["burndown", "dora", "flow"]
        time_period_weeks: Number of weeks to include (4, 12, 26, 52)
        profile_id: Profile ID (defaults to active profile)

    Returns:
        HTML string containing the complete report

    Raises:
        ValueError: If no sections selected or invalid data
    """
    if not sections:
        raise ValueError("At least one section must be selected")

    # Get active profile and query context
    from data.profile_manager import get_active_profile_and_query_display_names
    from data.query_manager import get_active_profile_id

    if not profile_id:
        profile_id = get_active_profile_id()

    # Get display names for header
    context = get_active_profile_and_query_display_names()
    profile_name = context.get("profile_name") or profile_id
    query_name = context.get("query_name") or "Unknown Query"

    logger.info(
        f"Generating report: {profile_name} / {query_name}, sections={sections}, weeks={time_period_weeks}"
    )

    # Load all data
    report_data = _load_report_data(profile_id, time_period_weeks)

    # Calculate metrics
    metrics = _calculate_all_metrics(report_data, sections, time_period_weeks)

    # Load and render template
    template_path = Path(__file__).parent / "report_template.html"
    with open(template_path, "r", encoding="utf-8") as f:
        template = Template(f.read())

    # Prepare chart JavaScript code (avoids Jinja2 in JS which triggers linter errors)
    chart_scripts = []

    # Weekly breakdown chart
    if "burndown" in sections and metrics.get("burndown", {}).get("weekly_data"):
        weekly = metrics["burndown"]["weekly_data"]
        dates_js = json.dumps([w["date"] for w in weekly])
        items_created_js = json.dumps([w["created_items"] for w in weekly])
        items_closed_js = json.dumps([w["completed_items"] for w in weekly])
        points_created_js = json.dumps([w["created_points"] for w in weekly])
        points_closed_js = json.dumps([w["completed_points"] for w in weekly])

        chart_script = f"""
        (function() {{
            const ctx = document.getElementById('weeklyBreakdownChart');
            if (ctx) {{
                new Chart(ctx, {{
                    type: 'bar',
                    data: {{
                        labels: {dates_js},
                        datasets: [
                            {{
                                label: 'Items Created',
                                data: {items_created_js},
                                backgroundColor: '#6ea8fe',
                                stack: 'items'
                            }},
                            {{
                                label: 'Items Closed',
                                data: {items_closed_js}.map(v => -v),
                                backgroundColor: '#0a58ca',
                                stack: 'items'
                            }},
                            {{
                                label: 'Points Created',
                                data: {points_created_js},
                                backgroundColor: '#ffb347',
                                stack: 'points'
                            }},
                            {{
                                label: 'Points Closed',
                                data: {points_closed_js}.map(v => -v),
                                backgroundColor: '#dc6502',
                                stack: 'points'
                            }}
                        ]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {{
                            x: {{
                                grid: {{ display: false }}
                            }},
                            y: {{
                                beginAtZero: true,
                                grid: {{ color: '#e9ecef' }},
                                ticks: {{
                                    callback: function(value) {{
                                        return Math.abs(value);
                                    }}
                                }}
                            }}
                        }},
                        plugins: {{
                            legend: {{
                                display: true,
                                position: 'bottom'
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        return context.dataset.label + ': ' + Math.abs(context.parsed.y);
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}
        }})();
        """
        chart_scripts.append(chart_script)

    # Work distribution pie chart
    if "flow" in sections and metrics.get("flow", {}).get("work_distribution"):
        work_dist = metrics["flow"]["work_distribution"]
        labels_js = json.dumps(list(work_dist.keys()))
        values_js = json.dumps(list(work_dist.values()))
        colors = [
            "#198754",
            "#dc3545",
            "#ffc107",
            "#6c757d",
        ]  # Feature, Bug, Debt, Risk
        colors_js = json.dumps(colors[: len(work_dist)])

        work_chart_script = f"""
        (function() {{
            const ctx = document.getElementById('workDistributionChart');
            if (ctx) {{
                new Chart(ctx, {{
                    type: 'doughnut',
                    data: {{
                        labels: {labels_js},
                        datasets: [{{
                            data: {values_js},
                            backgroundColor: {colors_js},
                            borderWidth: 2,
                            borderColor: '#fff'
                        }}]
                    }},
                    options: {{
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {{
                            legend: {{
                                display: false
                            }},
                            tooltip: {{
                                callbacks: {{
                                    label: function(context) {{
                                        return context.label + ': ' + context.parsed + '%';
                                    }}
                                }}
                            }}
                        }}
                    }}
                }});
            }}
        }})();
        """
        chart_scripts.append(work_chart_script)

    combined_chart_script = "\n".join(chart_scripts)

    # Generate timestamp with day of week
    now = datetime.now()
    generated_at = now.strftime("%A, %Y-%m-%d %H:%M:%S")

    html = template.render(
        profile_name=profile_name,
        query_name=query_name,
        generated_at=generated_at,
        time_period_weeks=time_period_weeks,
        sections=sections,
        metrics=metrics,
        chart_script=combined_chart_script,
    )

    logger.info(f"Report generated successfully: {len(html)} bytes")
    return html


def _load_report_data(profile_id: str, weeks: int) -> Dict[str, Any]:
    """
    Load all data needed for the report.

    Args:
        profile_id: Profile ID
        weeks: Number of weeks to include

    Returns:
        Dictionary with all available project data, including JIRA issues for ad-hoc calculations
    """
    from data.persistence import load_unified_project_data, load_app_settings
    from data.metrics_snapshots import load_snapshots
    from data.profile_manager import get_active_query_workspace
    from datetime import datetime, timedelta
    import json

    project_data = load_unified_project_data()
    metrics_snapshots = load_snapshots()

    # Load JIRA issues for ad-hoc bug/scope calculations
    jira_issues = []
    bug_type_mappings = {}
    try:
        # Load issues from query workspace cache
        query_workspace = get_active_query_workspace()
        cache_file = query_workspace / "jira_cache.json"

        if cache_file.exists():
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
                jira_issues = cache_data.get("issues", [])

        # Get bug type mappings from settings
        settings = load_app_settings()
        bug_type_mappings = settings.get("bug_types", {})

        logger.info(f"Loaded {len(jira_issues)} JIRA issues for report calculations")
    except Exception as e:
        logger.warning(f"Could not load JIRA issues for report: {e}")

    # Filter snapshots to time period
    cutoff_date = datetime.now() - timedelta(weeks=weeks) if weeks else None
    filtered_snapshots = {}

    if metrics_snapshots and cutoff_date:
        for week_label, data in metrics_snapshots.items():
            if _parse_week_label(week_label) >= cutoff_date:
                filtered_snapshots[week_label] = data
    else:
        filtered_snapshots = metrics_snapshots

    # Filter statistics to time period
    statistics = project_data.get("statistics", [])
    if cutoff_date and statistics:
        filtered_stats = []
        for row in statistics:
            # Handle both date formats: "YYYY-MM-DD" and "YYYY-MM-DDTHH:MM:SS"
            date_str = row["date"].split("T")[0]
            row_date = datetime.strptime(date_str, "%Y-%m-%d")
            if row_date >= cutoff_date:
                filtered_stats.append(row)
    else:
        filtered_stats = statistics

    return {
        "project_data": project_data,
        "statistics": filtered_stats,
        "metrics_snapshots": filtered_snapshots,
        "jira_issues": jira_issues,
        "bug_type_mappings": bug_type_mappings,
        "weeks": weeks,
        "profile_id": profile_id,
    }


def _parse_week_label(week_label: str) -> datetime:
    """
    Parse week label (e.g., '2025-W01') to datetime.

    Args:
        week_label: Week label string

    Returns:
        Datetime object for the start of that week
    """
    try:
        # Parse ISO week format: YYYY-Www
        year, week = week_label.split("-W")
        # Use ISO calendar: week 1 is the first week with a Thursday
        return datetime.strptime(f"{year}-W{int(week):02d}-1", "%Y-W%W-%w")
    except Exception as e:
        logger.warning(f"Failed to parse week label '{week_label}': {e}")
        return datetime.min


def _calculate_all_metrics(
    report_data: Dict[str, Any], sections: List[str], weeks: int
) -> Dict[str, Any]:
    """
    Calculate all metrics for the report based on selected sections.

    Args:
        report_data: Loaded report data
        sections: Selected sections
        weeks: Time period

    Returns:
        Dictionary with all calculated metrics organized by section
    """
    metrics: Dict[str, Any] = {"has_data": False}

    statistics = report_data["statistics"]
    project_data = report_data["project_data"]
    snapshots = report_data["metrics_snapshots"]

    if not statistics:
        return metrics

    metrics["has_data"] = True

    # Dashboard Overview (always include)
    metrics["dashboard"] = _calculate_dashboard_metrics(project_data, statistics)

    # Burndown & Velocity Metrics
    if "burndown" in sections:
        metrics["burndown"] = _calculate_burndown_metrics(statistics, project_data)

    # Bug Analysis
    if "burndown" in sections:  # Include in burndown section
        jira_issues = report_data.get("jira_issues", [])
        bug_type_mappings = report_data.get("bug_type_mappings", {})
        metrics["bug_analysis"] = _calculate_bug_metrics(jira_issues, bug_type_mappings)

    # Scope Analysis
    if "burndown" in sections:  # Include in burndown section
        metrics["scope"] = _calculate_scope_metrics(statistics, project_data)

    # DORA Metrics
    if "dora" in sections:
        metrics["dora"] = _calculate_dora_metrics(snapshots)

    # Flow Metrics
    if "flow" in sections:
        jira_issues = report_data.get("jira_issues", [])
        metrics["flow"] = _calculate_flow_metrics(snapshots, jira_issues)

    return metrics


def _calculate_dashboard_metrics(project_data: Dict, statistics: List[Dict]) -> Dict:
    """Calculate dashboard overview metrics."""
    project_scope = project_data.get("project_scope", {})

    # Calculate velocity using unique ISO weeks (matches UI calculation)
    if statistics:
        df = pd.DataFrame(statistics)
        df["date"] = pd.to_datetime(df["date"])
        df["iso_week"] = df["date"].dt.strftime("%Y-%U")  # type: ignore[attr-defined]
        unique_weeks = df["iso_week"].nunique()

        total_completed_items = df["completed_items"].sum()
        total_completed_points = df["completed_points"].sum()

        avg_items_per_week = (
            round(total_completed_items / unique_weeks, 1) if unique_weeks else 0
        )
        avg_points_per_week = (
            round(total_completed_points / unique_weeks, 1) if unique_weeks else 0
        )
    else:
        avg_items_per_week = 0
        avg_points_per_week = 0

    return {
        "total_items": project_scope.get("total_items", 0),
        "total_points": project_scope.get("total_points", 0),
        "completed_items": project_scope.get("completed_items", 0),
        "completed_points": project_scope.get("completed_points", 0),
        "remaining_items": project_scope.get("remaining_items", 0),
        "remaining_points": round(project_scope.get("remaining_total_points", 0)),
        "estimated_items": project_scope.get("estimated_items", 0),
        "estimated_points": project_scope.get("estimated_points", 0),
        "unestimated_items": project_scope.get("unestimated_items", 0),
        "avg_points_per_item": round(project_scope.get("avg_points_per_item", 0), 2),
        "avg_items_per_week": avg_items_per_week,
        "avg_points_per_week": avg_points_per_week,
    }


def _calculate_burndown_metrics(statistics: List[Dict], project_data: Dict) -> Dict:
    """Calculate burndown and velocity metrics."""
    if not statistics:
        return {}

    # Use DataFrame for proper velocity calculation with unique ISO weeks
    df = pd.DataFrame(statistics)
    df["date"] = pd.to_datetime(df["date"])
    df["iso_week"] = df["date"].dt.strftime("%Y-%U")  # type: ignore[attr-defined]

    # Ensure all required columns exist
    if "created_items" not in df.columns:
        df["created_items"] = 0
    if "created_points" not in df.columns:
        df["created_points"] = 0

    total_completed_items = df["completed_items"].sum()
    total_completed_points = df["completed_points"].sum()
    total_created_items = df["created_items"].sum()
    total_created_points = df["created_points"].sum()

    # Calculate velocity using unique weeks (not row count)
    unique_weeks = df["iso_week"].nunique()
    avg_items_per_week = total_completed_items / unique_weeks if unique_weeks else 0
    avg_points_per_week = total_completed_points / unique_weeks if unique_weeks else 0

    # Last 4 weeks velocity
    recent_df = df.tail(min(len(df), 28))  # Approximately 4 weeks of daily data
    recent_unique_weeks = recent_df["iso_week"].nunique()
    recent_items = recent_df["completed_items"].sum()
    recent_points = recent_df["completed_points"].sum()
    recent_weeks_count = max(recent_unique_weeks, 1)  # Avoid division by zero

    # Get CURRENT remaining work from project scope
    project_scope = project_data.get("project_scope", {})
    remaining_items = project_scope.get("remaining_items", 0)
    remaining_points = project_scope.get("remaining_total_points", 0)

    # Get actual weeks count for reporting
    weeks_count = unique_weeks

    # Weekly breakdown with pre-calculated bar heights for chart
    recent_weeks_df = df.tail(min(len(df), 84)).copy()  # Approximately 12 weeks
    # Convert date to string before converting to dict to avoid Timestamp issues
    recent_weeks_df["date"] = recent_weeks_df["date"].dt.strftime("%Y-%m-%d")  # type: ignore[attr-defined]
    weekly_data = []
    recent_weeks = recent_weeks_df.to_dict("records")

    # Calculate max values for scaling bars - separate scales for items and points
    items_values = []
    points_values = []
    for row in recent_weeks:
        items_values.extend(
            [
                row.get("completed_items", 0),
                row.get("created_items", 0),
            ]
        )
        points_values.extend(
            [
                row.get("completed_points", 0),
                row.get("created_points", 0),
            ]
        )
    max_items = max(items_values) if items_values else 1
    max_points = max(points_values) if points_values else 1

    for row in recent_weeks:
        # Date is already formatted as YYYY-MM-DD string
        date_str = row.get("date", "")

        # Get raw values
        completed_items = row.get("completed_items", 0)
        completed_points = row.get("completed_points", 0)
        created_items = row.get("created_items", 0)
        created_points = row.get("created_points", 0)

        # Calculate bar heights as percentages (0-50 for half-height chart)
        weekly_data.append(
            {
                "date": date_str,
                "completed_items": completed_items,
                "completed_points": completed_points,
                "created_items": created_items,
                "created_points": created_points,
                # Pre-calculated percentages for CSS (halved for above/below y=0)
                # Items and points use separate scales for better visibility
                "completed_items_pct": round(
                    (completed_items / max_items * 50) if max_items > 0 else 0, 1
                ),
                "completed_points_pct": round(
                    (completed_points / max_points * 50) if max_points > 0 else 0, 1
                ),
                "created_items_pct": round(
                    (created_items / max_items * 50) if max_items > 0 else 0, 1
                ),
                "created_points_pct": round(
                    (created_points / max_points * 50) if max_points > 0 else 0, 1
                ),
            }
        )

    return {
        "total_completed_items": total_completed_items,
        "total_completed_points": total_completed_points,
        "total_created_items": total_created_items,
        "total_created_points": total_created_points,
        "avg_items_per_week": round(avg_items_per_week, 1),
        "avg_points_per_week": round(avg_points_per_week, 1),
        "recent_items_velocity": round(recent_items / recent_weeks_count, 1)
        if recent_weeks_count
        else 0,
        "recent_points_velocity": round(recent_points / recent_weeks_count, 1)
        if recent_weeks_count
        else 0,
        "remaining_items": int(remaining_items),
        "remaining_points": round(remaining_points),
        "weeks_count": weeks_count,
        "weekly_data": weekly_data,
    }


def _calculate_bug_metrics(jira_issues: List[Dict], bug_type_mappings: Dict) -> Dict:
    """Calculate bug analysis metrics from JIRA issues."""
    from data.bug_processing import filter_bug_issues

    # Filter to get only bugs
    bug_issues = filter_bug_issues(jira_issues, bug_type_mappings)

    if not bug_issues:
        return {
            "total_bugs": 0,
            "open_bugs": 0,
            "closed_bugs": 0,
            "bug_rate": 0,
            "avg_resolution_time": 0,
            "priority_breakdown": {},
            "severity_breakdown": {},
        }

    # Count bugs by status
    open_bugs = 0
    closed_bugs = 0
    resolution_times = []
    priority_counts = {}

    for bug in bug_issues:
        fields = bug.get("fields", {})
        resolution_date = fields.get("resolutiondate")
        created_date = fields.get("created")
        priority = fields.get("priority", {}).get("name", "Unknown")

        # Count by status
        if resolution_date:
            closed_bugs += 1
            # Calculate resolution time
            if created_date and resolution_date:
                try:
                    created = datetime.fromisoformat(
                        created_date.replace("Z", "+00:00")
                    )
                    resolved = datetime.fromisoformat(
                        resolution_date.replace("Z", "+00:00")
                    )
                    days = (resolved - created).days
                    if days >= 0:
                        resolution_times.append(days)
                except Exception:
                    pass
        else:
            open_bugs += 1

        # Count by priority
        priority_counts[priority] = priority_counts.get(priority, 0) + 1

    total_bugs = len(bug_issues)
    total_issues = len(jira_issues)
    bug_rate = (total_bugs / total_issues * 100) if total_issues > 0 else 0
    avg_resolution_time = (
        sum(resolution_times) / len(resolution_times) if resolution_times else 0
    )

    return {
        "total_bugs": total_bugs,
        "open_bugs": open_bugs,
        "closed_bugs": closed_bugs,
        "bug_rate": round(bug_rate, 2),
        "avg_resolution_time": round(avg_resolution_time, 1),
        "priority_breakdown": priority_counts,
        "severity_breakdown": {},
    }


def _calculate_scope_metrics(statistics: List[Dict], project_data: Dict) -> Dict:
    """Calculate scope analysis metrics from statistics."""
    from data.scope_metrics import calculate_total_project_scope

    if not statistics:
        return {
            "initial_scope_items": 0,
            "initial_scope_points": 0,
            "current_scope_items": 0,
            "current_scope_points": 0,
            "added_items": 0,
            "added_points": 0,
            "removed_items": 0,
            "removed_points": 0,
            "scope_change_pct": 0,
        }

    # Get current remaining work from project scope (CURRENT state)
    project_scope = project_data.get("project_scope", {})
    current_remaining_items = project_scope.get("remaining_items", 0)
    current_remaining_points = project_scope.get("remaining_total_points", 0)

    # Calculate completed work in the selected time window
    completed_in_window_items = sum(row.get("completed_items", 0) for row in statistics)
    completed_in_window_points = sum(
        row.get("completed_points", 0) for row in statistics
    )

    # Calculate scope at START of window = current remaining + completed in window
    scope_at_start_items = current_remaining_items + completed_in_window_items
    scope_at_start_points = current_remaining_points + completed_in_window_points

    # Calculate initial scope at START of window (before any work in this window)
    df = pd.DataFrame(statistics)
    initial_scope = calculate_total_project_scope(
        df, scope_at_start_items, scope_at_start_points
    )
    initial_items = initial_scope["total_items"]
    initial_points = initial_scope["total_points"]

    # Calculate created items/points during the window
    added_items = sum(row.get("created_items", 0) for row in statistics)
    added_points = sum(row.get("created_points", 0) for row in statistics)

    # Current scope = initial + created during window
    current_items = initial_items + added_items
    current_points = initial_points + added_points

    # Calculate scope change percentage
    scope_change_pct = (added_items / initial_items * 100) if initial_items > 0 else 0

    return {
        "initial_scope_items": initial_items,
        "initial_scope_points": round(initial_points),
        "current_scope_items": current_items,
        "current_scope_points": round(current_points),
        "scope_at_start_items": scope_at_start_items,
        "scope_at_start_points": round(scope_at_start_points),
        "remaining_current_items": current_remaining_items,
        "remaining_current_points": round(current_remaining_points),
        "completed_in_window_items": completed_in_window_items,
        "completed_in_window_points": round(completed_in_window_points),
        "added_items": added_items,
        "added_points": round(added_points),
        "removed_items": 0,  # Not tracked in statistics
        "removed_points": 0,  # Not tracked in statistics
        "scope_change_pct": round(scope_change_pct, 1),
    }


def _calculate_dora_metrics(snapshots: Dict) -> Dict:
    """Calculate DORA metrics from snapshots."""
    if not snapshots:
        return {"has_data": False}

    # Get latest snapshot
    latest_week = max(snapshots.keys())
    latest = snapshots[latest_week]

    # Extract deployment frequency
    deploy_freq_data = latest.get("dora_deployment_frequency", {})
    latest_deploy_freq = deploy_freq_data.get("deployment_count", 0)

    # Extract lead time (convert hours to days)
    lead_time_data = latest.get("dora_lead_time", {})
    latest_lead_time = round(lead_time_data.get("mean_hours", 0) / 24, 1)

    # Extract change failure rate
    cfr_data = latest.get("dora_change_failure_rate", {})
    latest_cfr = round(cfr_data.get("change_failure_rate_percent", 0), 1)

    # Extract MTTR
    mttr_data = latest.get("dora_mttr", {})
    latest_mttr = round(mttr_data.get("mean_hours", 0) or 0, 1)

    # Calculate averages across period
    deploy_freqs = []
    lead_times = []
    cfrs = []
    mttrs = []

    for snapshot in snapshots.values():
        df = snapshot.get("dora_deployment_frequency", {}).get("deployment_count")
        if df is not None:
            deploy_freqs.append(df)

        lt = snapshot.get("dora_lead_time", {}).get("mean_hours")
        if lt is not None and lt > 0:
            lead_times.append(lt / 24)  # Convert to days

        cfr = snapshot.get("dora_change_failure_rate", {}).get(
            "change_failure_rate_percent"
        )
        if cfr is not None:
            cfrs.append(cfr)

        mttr = snapshot.get("dora_mttr", {}).get("mean_hours")
        if mttr is not None and mttr > 0:
            mttrs.append(mttr)

    return {
        "has_data": True,
        "latest_deployment_frequency": latest_deploy_freq,
        "latest_lead_time": latest_lead_time,
        "latest_change_failure_rate": latest_cfr,
        "latest_mttr": latest_mttr,
        "avg_deployment_frequency": round(sum(deploy_freqs) / len(deploy_freqs), 1)
        if deploy_freqs
        else 0,
        "avg_lead_time": round(sum(lead_times) / len(lead_times), 1)
        if lead_times
        else 0,
        "avg_change_failure_rate": round(sum(cfrs) / len(cfrs), 1) if cfrs else 0,
        "avg_mttr": round(sum(mttrs) / len(mttrs), 1) if mttrs else 0,
        "snapshots_count": len(snapshots),
    }


def _calculate_flow_metrics(snapshots: Dict, jira_issues: List[Dict]) -> Dict:
    """Calculate Flow metrics from snapshots and JIRA issues.

    Args:
        snapshots: Metric snapshots dict
        jira_issues: JIRA issues for calculating work distribution

    Returns:
        Flow metrics dictionary including work_distribution
    """
    if not snapshots:
        return {"has_data": False}

    # Get latest snapshot
    latest_week = max(snapshots.keys())
    latest = snapshots[latest_week]

    # Extract latest metrics
    velocity_data = latest.get("flow_velocity", {})
    latest_velocity = velocity_data.get("completed_count", 0)

    time_data = latest.get("flow_time", {})
    latest_time = round(time_data.get("median_days", 0), 1)

    efficiency_data = latest.get("flow_efficiency", {})
    latest_efficiency = round(efficiency_data.get("overall_pct", 0), 1)

    load_data = latest.get("flow_load", {})
    latest_load = load_data.get("wip_count", 0)

    # Calculate averages across period
    velocities = []
    times = []
    efficiencies = []
    loads = []

    for snapshot in snapshots.values():
        vel = snapshot.get("flow_velocity", {}).get("completed_count")
        if vel is not None:
            velocities.append(vel)

        time_val = snapshot.get("flow_time", {}).get("median_days")
        if time_val is not None and time_val > 0:
            times.append(time_val)

        eff = snapshot.get("flow_efficiency", {}).get("overall_pct")
        if eff is not None:
            efficiencies.append(eff)

        load_val = snapshot.get("flow_load", {}).get("wip_count")
        if load_val is not None:
            loads.append(load_val)

    # Calculate work distribution from metrics snapshots (matches UI approach)
    work_distribution = {"Feature": 0, "Defect": 0, "Technical Debt": 0, "Risk": 0}
    if snapshots:
        try:
            # Aggregate distribution counts from all snapshot weeks (same as UI)
            total_feature = 0
            total_defect = 0
            total_tech_debt = 0
            total_risk = 0
            total_completed = 0

            for snapshot in snapshots.values():
                velocity_data = snapshot.get("flow_velocity", {})
                distribution = velocity_data.get("distribution", {})

                total_feature += distribution.get("feature", 0)
                total_defect += distribution.get("defect", 0)
                total_tech_debt += distribution.get("tech_debt", 0)
                total_risk += distribution.get("risk", 0)
                total_completed += velocity_data.get("completed_count", 0)

            # Calculate percentages (matches UI calculation)
            if total_completed > 0:
                work_distribution = {
                    "Feature": round((total_feature / total_completed) * 100, 1),
                    "Defect": round((total_defect / total_completed) * 100, 1),
                    "Technical Debt": round(
                        (total_tech_debt / total_completed) * 100, 1
                    ),
                    "Risk": round((total_risk / total_completed) * 100, 1),
                }
        except Exception as e:
            logger.warning(f"Failed to calculate work distribution from snapshots: {e}")

    return {
        "has_data": True,
        "latest_flow_velocity": latest_velocity,
        "latest_flow_time": latest_time,
        "latest_flow_efficiency": latest_efficiency,
        "latest_flow_load": latest_load,
        "work_distribution": work_distribution,
        "avg_flow_velocity": round(sum(velocities) / len(velocities), 1)
        if velocities
        else 0,
        "avg_flow_time": round(sum(times) / len(times), 1) if times else 0,
        "avg_flow_efficiency": round(sum(efficiencies) / len(efficiencies), 1)
        if efficiencies
        else 0,
        "avg_flow_load": round(sum(loads) / len(loads), 1) if loads else 0,
        "snapshots_count": len(snapshots),
    }
