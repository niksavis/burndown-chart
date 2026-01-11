"""AI prompt generator for project analysis.

Generates sanitized, condensed prompts for AI agent analysis.
Follows Constitution Principle V (Data Privacy) - strips all customer PII.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import pandas as pd

logger = logging.getLogger(__name__)


def generate_ai_analysis_prompt(
    time_period_weeks: int = 12,
    profile_id: Optional[str] = None,
) -> str:
    """
    Generate sanitized AI prompt with project metrics.

    Creates a condensed, privacy-safe prompt containing:
    - Project health summary
    - Velocity trends
    - Scope changes
    - DORA metrics (if available)
    - Budget utilization (if configured)
    - Forecast data

    All customer-identifying information is stripped per Constitution Principle V.

    Args:
        time_period_weeks: Number of weeks to analyze (matches Data Points slider)
        profile_id: Profile to generate from (defaults to active)

    Returns:
        Formatted prompt string ready for clipboard (3000-5000 chars typical)

    Raises:
        ValueError: If no active profile or insufficient data
    """
    logger.info(f"Generating AI prompt for {time_period_weeks} weeks")

    # 1. Export full data (without token)
    from data.import_export import export_profile_with_mode
    from data.query_manager import get_active_profile_id, get_active_query_id

    if not profile_id:
        profile_id = get_active_profile_id()
    query_id = get_active_query_id()

    if not profile_id or not query_id:
        raise ValueError("No active profile or query selected")

    # Get FULL_DATA export with budget, without token
    export_data = export_profile_with_mode(
        profile_id=profile_id,
        query_id=query_id,
        export_mode="FULL_DATA",
        include_token=False,
        include_budget=True,
    )

    # 2. Sanitize customer-identifying info (Constitution Principle V)
    sanitized_data = _sanitize_for_ai(export_data)

    # 3. Condense to summary statistics (not raw data)
    summary = _create_summary_statistics(sanitized_data, time_period_weeks)

    # 4. Generate prompt with structured output specification
    prompt = _format_ai_prompt(summary, time_period_weeks)

    logger.info(f"AI prompt generated: {len(prompt)} characters")
    return prompt


def _sanitize_for_ai(export_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove customer-identifying information from export.

    Constitution Principle V compliance:
    - Real company/organization names → "Acme Corp"
    - Production domains → "example.com"
    - Email addresses → "user@example.com"
    - JIRA URLs → "https://jira.example.com"
    - Profile/query names → "Project Alpha", "Sprint Analysis"

    Preserves:
    - Field mapping structure (useful for context)
    - Statistical data (no PII)
    - Metric calculations

    Args:
        export_data: Raw export from export_profile_with_mode()

    Returns:
        Deep copy with all PII stripped
    """
    import copy
    from data.import_export import strip_credentials

    sanitized = copy.deepcopy(export_data)

    # Strip credentials (already implemented, Constitution-compliant)
    if "profile_data" in sanitized:
        sanitized["profile_data"] = strip_credentials(sanitized["profile_data"])

    # Sanitize profile metadata
    if "profile_data" in sanitized:
        profile = sanitized["profile_data"]
        profile["name"] = "Project Alpha"
        profile["jira_url"] = "https://jira.example.com"
        profile["jira_email"] = "user@example.com"

        # Note: Field mappings kept as-is (structure useful, IDs not PII)

    # Sanitize query metadata
    if "query_data" in sanitized:
        for query_id, query_data in sanitized["query_data"].items():
            if "query_metadata" in query_data:
                query_data["query_metadata"]["name"] = "Sprint Analysis"
                query_data["query_metadata"]["jql"] = (
                    "project = PROJ AND sprint = CURRENT"
                )

    return sanitized


def _create_summary_statistics(
    sanitized_data: Dict[str, Any], time_period_weeks: int
) -> Dict[str, Any]:
    """
    Condense full export to summary statistics.

    Instead of thousands of raw issues, extract:
    - Aggregate metrics (velocity, completion %)
    - Trend indicators (improving/stable/declining)
    - Key statistics (bug ratio, cycle time)
    - Time-series summaries (weekly averages, not raw data)

    Args:
        sanitized_data: PII-stripped export data
        time_period_weeks: Analysis window

    Returns:
        Dictionary with condensed statistics
    """
    summary = {
        "time_period_weeks": time_period_weeks,
        "generated_at": datetime.now().isoformat(),
        "data_source": "Burndown Chart Generator (sanitized export)",
    }

    # Extract statistics from query data
    query_data = sanitized_data.get("query_data", {})
    if not query_data:
        logger.warning("No query data available for AI prompt")
        return summary

    first_query = next(iter(query_data.values()))
    statistics = first_query.get("statistics", [])

    if not statistics or len(statistics) == 0:
        logger.warning(
            f"No statistics data available for AI prompt (got {type(statistics)} with length {len(statistics) if statistics else 0})"
        )
        return summary

    # Log first record for debugging
    logger.debug(
        f"Statistics data structure: {statistics[0] if statistics else 'empty'}"
    )

    # Calculate aggregates, not raw data
    summary["metrics"] = _aggregate_statistics(statistics, time_period_weeks)

    # Extract project scope for forecasting context
    if "project_scope" in first_query:
        project_scope = first_query["project_scope"]
        remaining_items = project_scope.get("remaining_items", 0)
        remaining_points = project_scope.get("remaining_total_points", 0)
        total_items = project_scope.get("total_items", 0)

        # Calculate completion percentage
        completed_items = total_items - remaining_items if total_items > 0 else 0
        completion_pct = (completed_items / total_items * 100) if total_items > 0 else 0

        # Estimate weeks remaining (using velocity from metrics)
        avg_velocity_items = summary["metrics"].get("avg_velocity_items", 0)
        weeks_remaining = (
            (remaining_items / avg_velocity_items) if avg_velocity_items > 0 else None
        )

        summary["project_scope"] = {
            "total_items": total_items,
            "remaining_items": remaining_items,
            "completed_items": completed_items,
            "completion_pct": round(completion_pct, 1),
        }

        # Include points only if project uses them (not always 0)
        points_field_available = project_scope.get("points_field_available", False)
        if points_field_available:
            total_points = project_scope.get("total_points", 0)
            completed_points = (
                total_points - remaining_points if total_points > 0 else 0
            )
            points_completion_pct = (
                (completed_points / total_points * 100) if total_points > 0 else 0
            )

            summary["project_scope"]["total_points"] = total_points
            summary["project_scope"]["remaining_points"] = remaining_points
            summary["project_scope"]["completed_points"] = completed_points
            summary["project_scope"]["points_completion_pct"] = round(
                points_completion_pct, 1
            )

        # Add forecast estimate
        if weeks_remaining is not None:
            summary["project_scope"]["estimated_weeks_remaining"] = round(
                weeks_remaining, 1
            )

    # Extract budget if present
    if "budget_settings" in first_query:
        budget_settings = first_query["budget_settings"]
        summary["budget"] = {
            "allocated_hours": budget_settings.get("budget_hours"),
            "team_size": budget_settings.get("team_size"),
        }

    return summary


def _aggregate_statistics(statistics: List[Dict], weeks: int) -> Dict[str, Any]:
    """
    Aggregate statistics into summary metrics.

    Returns weekly averages, trends, and key indicators
    instead of raw time-series data.

    Args:
        statistics: Raw statistics array
        weeks: Time window

    Returns:
        Dictionary with aggregated metrics
    """
    if not statistics:
        return {"error": "No statistics available"}

    df = pd.DataFrame(statistics)
    if df.empty:
        return {"error": "Empty statistics DataFrame"}

    # Handle both 'date' and 'stat_date' column names (database uses 'stat_date')
    if "date" not in df.columns and "stat_date" not in df.columns:
        available_columns = ", ".join(df.columns.tolist())
        logger.error(
            f"Statistics DataFrame missing date column. Available columns: {available_columns}"
        )
        return {"error": f"Missing date column. Found: {available_columns}"}

    # Normalize column name to 'date'
    if "stat_date" in df.columns and "date" not in df.columns:
        df["date"] = df["stat_date"]

    # Filter to requested time period
    df["date"] = pd.to_datetime(df["date"])
    cutoff = df["date"].max() - timedelta(weeks=weeks)
    df_windowed = df[df["date"] >= cutoff]

    if df_windowed.empty:
        return {"error": "No data in requested time window"}

    # Calculate aggregates
    total_completed_items = int(df_windowed["completed_items"].sum())
    total_created_items = int(df_windowed["created_items"].sum())

    return {
        "weeks_analyzed": len(df_windowed),
        "avg_velocity_items": round(df_windowed["completed_items"].mean(), 1),
        "avg_velocity_points": round(
            df_windowed.get("completed_points", pd.Series([0])).mean(), 1
        ),
        "total_completed_items": total_completed_items,
        "total_created_items": total_created_items,
        "scope_change_rate_pct": round(
            (total_created_items / total_completed_items * 100)
            if total_completed_items > 0
            else 0,
            1,
        ),
        "velocity_trend": _calculate_trend(df_windowed["completed_items"]),
        "velocity_coefficient_of_variation": round(
            (
                df_windowed["completed_items"].std()
                / df_windowed["completed_items"].mean()
                * 100
            )
            if df_windowed["completed_items"].mean() > 0
            else 0,
            1,
        ),
    }


def _calculate_trend(series: pd.Series) -> str:
    """
    Calculate trend direction (improving/stable/declining).

    Args:
        series: Time series data (velocity, throughput, etc.)

    Returns:
        "improving" | "stable" | "declining" | "insufficient_data"
    """
    if len(series) < 4:
        return "insufficient_data"

    first_half_mean = series.iloc[: len(series) // 2].mean()
    second_half_mean = series.iloc[len(series) // 2 :].mean()

    if first_half_mean == 0:
        return "insufficient_data"

    change_pct = (second_half_mean - first_half_mean) / first_half_mean * 100

    if change_pct > 10:
        return "improving"
    elif change_pct < -10:
        return "declining"
    else:
        return "stable"


def _format_ai_prompt(summary: Dict[str, Any], time_period_weeks: int) -> str:
    """
    Format summary into AI-ready prompt with flexible structure.

    Creates comprehensive prompt with:
    - Context section
    - Data section (JSON summary)
    - Analysis guidance (not rigid format)
    - Actionable focus

    Args:
        summary: Condensed statistics dictionary
        time_period_weeks: Analysis window

    Returns:
        Formatted prompt string (markdown)
    """
    # Get app version for footer
    try:
        from bump_version import get_current_version

        version = get_current_version()
    except Exception:
        version = "2.4.4"

    metrics_json = json.dumps(summary.get("metrics", {}), indent=2)
    metrics = summary.get("metrics", {})

    # Build project scope section if available
    scope_section = ""
    if "project_scope" in summary:
        scope = summary["project_scope"]
        scope_section = f"""
## Project Scope & Progress

**Current State**:
- Progress: {scope.get("completion_pct", 0):.1f}% complete ({scope.get("completed_items", 0)}/{scope.get("total_items", 0)} items)
- Remaining: {scope.get("remaining_items", 0)} items"""

        # Add points if project uses them
        if "total_points" in scope:
            scope_section += f"""
- Story Points: {scope.get("points_completion_pct", 0):.1f}% complete ({scope.get("completed_points", 0)}/{scope.get("total_points", 0)} points)"""

        # Add forecast
        if "estimated_weeks_remaining" in scope:
            scope_section += f"""
- Projected Completion: ~{scope.get("estimated_weeks_remaining", 0):.1f} weeks at current velocity"""

        scope_section += "\n\n---\n"

    # Build velocity insights
    velocity_items = metrics.get("avg_velocity_items", 0)
    velocity_trend = metrics.get("velocity_trend", "unknown")
    velocity_cv = metrics.get("velocity_coefficient_of_variation", 0)

    # Interpret velocity consistency
    consistency_label = (
        "high" if velocity_cv < 20 else "moderate" if velocity_cv < 40 else "low"
    )

    # Build scope change insights
    scope_rate = metrics.get("scope_change_rate_pct", 0)
    scope_assessment = (
        "healthy" if scope_rate < 110 else "moderate" if scope_rate < 150 else "high"
    )

    prompt = f"""# Agile Project Analysis Request

You are an expert agile project manager analyzing project health and forecasting outcomes. Provide data-driven insights with specific, actionable recommendations.

## Project Data ({time_period_weeks}-week analysis window)

**Velocity Metrics**:
- Average: {velocity_items:.1f} items/week
- Trend: {velocity_trend}
- Consistency: {consistency_label} (CV: {velocity_cv:.1f}%)
- Total completed: {metrics.get("total_completed_items", 0)} items

**Scope Dynamics**:
- Scope change rate: {scope_rate:.1f}%
- New items created: {metrics.get("total_created_items", 0)}
- Items completed: {metrics.get("total_completed_items", 0)}
- Assessment: {scope_assessment} scope volatility
{scope_section}
---

## Analysis Objectives

Provide a comprehensive project assessment covering:

### 1. Executive Summary (2-3 sentences)
- Overall project health (Green/Yellow/Red status)
- Most critical insight requiring immediate attention
- Confidence level in current trajectory

### 2. Velocity & Performance Analysis
- Evaluate velocity trend and what's driving it
- Assess velocity consistency ({consistency_label} CV of {velocity_cv:.1f}%)
- Identify patterns or anomalies in delivery performance
- Compare recent performance to historical baseline

### 3. Scope Management Assessment
- Analyze scope change rate of {scope_rate:.1f}% (items created vs. completed)
- Determine if scope volatility is healthy or problematic
- Identify risks from scope creep or under-planning
- Recommend scope management adjustments if needed

### 4. Delivery Forecast
Based on current velocity ({velocity_items:.1f} items/week) and remaining work:
- Provide realistic completion date with confidence intervals (P20/P50/P80)
- State key assumptions underlying the forecast
- Identify factors that could accelerate or delay completion
- Calculate schedule variance if a deadline is specified

### 5. Risk Identification
Identify top 3-5 data-driven risks, prioritized by impact:
- Each risk should reference specific metrics (velocity trend, scope rate, etc.)
- Assess likelihood (High/Medium/Low) and impact (High/Medium/Low)
- Propose concrete mitigation strategies with effort estimates

### 6. Actionable Recommendations
Provide 3-5 prioritized recommendations in three tiers:

**Immediate Actions** (next 1-2 weeks):
- Critical interventions to address urgent issues
- Quick wins to improve trajectory

**Short-term Improvements** (next 4-6 weeks):
- Process improvements to stabilize performance
- Proactive risk mitigation

**Strategic Initiatives** (long-term):
- Structural changes for sustained improvement
- Capability building

For each recommendation, specify:
- What: Specific action to take
- Why: Expected benefit (quantify if possible)
- Who: Suggested owner (role/team)
- Effort: Low/Medium/High estimate

### 7. Key Questions for Stakeholders
Identify 2-3 critical questions that require leadership discussion or clarification to improve accuracy of analysis.

---

## Analysis Guidelines

**Be Data-Driven**: Ground all insights in the provided metrics. Avoid generic advice.

**Be Specific**: Use actual numbers from the data (e.g., "velocity declined 15% in last 4 weeks" not "velocity is declining").

**Be Actionable**: Every recommendation should be implementable within the specified timeframe.

**Consider Context**: Acknowledge that metrics don't tell the whole story. Flag where additional context would improve analysis.

**Prioritize Ruthlessly**: Focus on the 20% of actions that will deliver 80% of impact.

**Use Agile Terminology**: Reference sprints, iterations, backlogs, ceremonies as appropriate for agile teams.

---

## Optional Context (add if available for better insights)

**Team Context**:
- Team size: [specify if known]
- Sprint/iteration length: [specify if known]
- Team maturity: [new/established/high-performing]

**Project Constraints**:
- Hard deadline: [YYYY-MM-DD if applicable]
- Budget limits: [hours/week if applicable]
- Regulatory/compliance requirements: [if applicable]

**Recent Events** (explain anomalies in data):
- [e.g., "Holiday break Dec 20-Jan 3 reduced velocity"]
- [e.g., "Major technical spike in week of Dec 15"]
- [e.g., "3 team members onboarded Jan 6"]

**Specific Questions**:
- [Add any specific questions for targeted analysis]

---

**Full Metrics Export** (for reference):
```json
{metrics_json}
```

---

*Generated by Burndown Chart Generator v{version}*  
*Data sanitized for privacy - no customer-identifying information*
"""

    return prompt
