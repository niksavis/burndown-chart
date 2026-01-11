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
    Format summary into AI-ready prompt with structured output specification.

    Creates comprehensive prompt with:
    - Context section
    - Data section (JSON summary)
    - Questions/tasks section
    - Structured output format specification (ensures consistent responses)

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
    generated_at = summary.get("generated_at", datetime.now().isoformat())

    # Build project scope section if available
    scope_section = ""
    if "project_scope" in summary:
        scope_json = json.dumps(summary.get("project_scope", {}), indent=2)
        scope_section = f"""
## Project Scope & Progress

```json
{scope_json}
```

**Key Metrics**:
- **Completion**: {summary["project_scope"].get("completion_pct", 0):.1f}% ({summary["project_scope"].get("completed_items", 0)} of {summary["project_scope"].get("total_items", 0)} items)
- **Remaining Work**: {summary["project_scope"].get("remaining_items", 0)} items
"""
        # Add points info only if project uses them
        if "total_points" in summary["project_scope"]:
            scope_section += f"""- **Points Completion**: {summary["project_scope"].get("points_completion_pct", 0):.1f}% ({summary["project_scope"].get("completed_points", 0)} of {summary["project_scope"].get("total_points", 0)} points)
- **Remaining Points**: {summary["project_scope"].get("remaining_points", 0)} points
"""

        # Add forecast if available
        if "estimated_weeks_remaining" in summary["project_scope"]:
            scope_section += f"""- **Estimated Completion**: ~{summary["project_scope"].get("estimated_weeks_remaining", 0):.1f} weeks remaining at current velocity
"""

        scope_section += "\n---\n"

    prompt = f"""# Project Analysis Request

## Context
I'm managing an agile project and need analysis, forecasting, and recommendations based on historical data.

**Time Period**: Last {time_period_weeks} weeks  
**Data Generated**: {generated_at}  
**Data Source**: Burndown Chart Generator (sanitized export)

---

## Project Metrics Summary

```json
{metrics_json}
```

---
{scope_section}
## Analysis Tasks

Please analyze this data and provide insights in the **EXACT FORMAT** specified below.

---

## REQUIRED OUTPUT FORMAT

### 1. EXECUTIVE SUMMARY
**Current Status**: [One sentence: Green/Yellow/Red with primary reason]  
**Key Insight**: [One actionable insight in 1-2 sentences]

---

### 2. PROJECT HEALTH ASSESSMENT

**Overall Health Score**: [X/100]

**Component Breakdown**:
- Velocity Consistency: [Score/30] - [Brief assessment]
- Schedule Performance: [Score/25] - [Brief assessment]  
- Scope Stability: [Score/20] - [Brief assessment]
- Quality Trends: [Score/15] - [Brief assessment]
- Recent Performance: [Score/10] - [Brief assessment]

**Health Trend**: [Improving ↗ | Stable → | Declining ↘]

---

### 3. VELOCITY ANALYSIS

**Current Velocity**:
- Items: [X.X items/week]
- Story Points: [X.X points/week] (if applicable)

**Velocity Trend**: [Improving ↗ | Stable → | Declining ↘] ([+/- X%] change)

**Trend Analysis**:
- **What's happening**: [Describe the trend in 1-2 sentences]
- **Why it matters**: [Explain impact on delivery]
- **Contributing factors**: [List 2-3 likely causes]

---

### 4. COMPLETION FORECAST

**Realistic Completion Date**: [YYYY-MM-DD]

**Confidence Intervals**:
- Best case (80% confidence): [YYYY-MM-DD]
- Most likely (50% confidence): [YYYY-MM-DD]
- Worst case (20% confidence): [YYYY-MM-DD]

**Assumptions**:
- Current velocity remains stable
- No major scope changes
- Team capacity unchanged
- [Add any other assumptions]

**If deadline is provided**: 
- Target deadline: [YYYY-MM-DD]
- Schedule variance: [On track ✓ | X weeks ahead | X weeks behind]
- Probability of meeting deadline: [X%]

---

### 5. SCOPE MANAGEMENT

**Scope Change Rate**: [X.X%]
- New items created: [X items]
- Items completed: [X items]
- Net change: [+/- X items]

**Assessment**: [Healthy ✓ | Moderate ⚠ | Concerning ⚠⚠]

**Recommendation**: [One sentence action item]

---

### 6. RISK ANALYSIS

**TOP 3 RISKS** (Prioritized by Impact × Probability):

**Risk 1: [Risk Name]**
- **Likelihood**: [High/Medium/Low]
- **Impact**: [High/Medium/Low]
- **Description**: [1-2 sentences]
- **Mitigation**: [Specific action to reduce risk]

**Risk 2: [Risk Name]**
- **Likelihood**: [High/Medium/Low]
- **Impact**: [High/Medium/Low]
- **Description**: [1-2 sentences]
- **Mitigation**: [Specific action to reduce risk]

**Risk 3: [Risk Name]**
- **Likelihood**: [High/Medium/Low]
- **Impact**: [High/Medium/Low]
- **Description**: [1-2 sentences]
- **Mitigation**: [Specific action to reduce risk]

---

### 7. ACTIONABLE RECOMMENDATIONS

**IMMEDIATE ACTIONS** (Next 1-2 weeks):

1. **[Action Title]**
   - **What**: [Specific action to take]
   - **Why**: [Expected benefit]
   - **Owner**: [Suggested role/person]
   - **Effort**: [Low/Medium/High]

2. **[Action Title]**
   - **What**: [Specific action to take]
   - **Why**: [Expected benefit]
   - **Owner**: [Suggested role/person]
   - **Effort**: [Low/Medium/High]

**SHORT-TERM IMPROVEMENTS** (Next 4-6 weeks):

3. **[Action Title]**
   - **What**: [Specific action to take]
   - **Why**: [Expected benefit]
   - **Owner**: [Suggested role/person]
   - **Effort**: [Low/Medium/High]

4. **[Action Title]**
   - **What**: [Specific action to take]
   - **Why**: [Expected benefit]
   - **Owner**: [Suggested role/person]
   - **Effort**: [Low/Medium/High]

**STRATEGIC INITIATIVES** (Long-term):

5. **[Action Title]**
   - **What**: [Specific action to take]
   - **Why**: [Expected benefit]
   - **Owner**: [Suggested role/person]
   - **Effort**: [Low/Medium/High]

---

### 8. ADDITIONAL INSIGHTS

**Patterns Observed**:
- [Insight 1]
- [Insight 2]
- [Insight 3]

**Questions to Consider**:
- [Question 1 for team discussion]
- [Question 2 for team discussion]

---

## OPTIONAL CONTEXT (Fill in for better analysis)

**Team Details**:
- Team size: [X developers]
- Sprint length: [X weeks]
- Experience level: [Junior/Mid/Senior mix]

**Recent Events**:
- [e.g., Holiday break Dec 20-Jan 3]
- [e.g., New team member joined Jan 6]
- [e.g., Tech debt sprint completed]

**Project Constraints**:
- Hard deadline: [YYYY-MM-DD] (if applicable)
- Budget constraint: [X hours/week]
- Regulatory requirements: [Yes/No - describe if yes]

**Specific Questions**:
- [Add any specific questions you want answered]

---

*Generated by Burndown Chart Generator v{version} - AI Prompt Feature*  
*Data sanitized for privacy - no customer-identifying information included*
"""

    return prompt
