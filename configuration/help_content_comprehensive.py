"""Comprehensive help content and DORA/settings tooltips.

Contains the canonical FORECAST_HELP_DETAILED (overrides the earlier
draft version in help_content_forecast.py), DORA metrics tooltips,
settings panel tooltips, and the top-level COMPREHENSIVE_HELP_CONTENT
aggregator dictionary.
"""

from configuration.help_content_forecast import (  # noqa: F401
    FORECAST_HELP_DETAILED as _FORECAST_HELP_DETAILED_DRAFT,
)
from configuration.help_content_forecast import (
    SCOPE_HELP_DETAILED,
    VELOCITY_HELP_DETAILED,
)
from configuration.help_content_metrics import (
    BUG_ANALYSIS_TOOLTIPS,
    CHART_HELP_DETAILED,
    DASHBOARD_METRICS_TOOLTIPS,
    FLOW_METRICS_TOOLTIPS,
    FORECAST_HELP_CONTENT,
    PARAMETER_INPUTS_TOOLTIPS,
    STATISTICS_HELP_DETAILED,
)

# FORECAST DETAILED HELP - Comprehensive explanations for help modal
FORECAST_HELP_DETAILED = {
    "forecast_algorithm": """
        4-Week Weighted Forecast provides actionable predictions for next week's
        performance.
        
        [Stats] **Weighting Strategy:**
        Recent weeks are weighted more heavily using exponential decay:
        • Week 0 (current): 1.0 (100% weight)
        • Week -1 (last week): 0.8 (80% weight)
        • Week -2 (2 weeks ago): 0.6 (60% weight)
        • Week -3 (3 weeks ago): 0.4 (40% weight)
        
        [Calc] **Calculation Formula:**
        ```python
        weights = [1.0, 0.8, 0.6, 0.4]  # Week 0 → Week -3
        weighted_sum = sum(value × weight for value, weight in zip(values, weights))
        forecast = weighted_sum / sum(weights)  # Normalize by total weight
        ```
        
        [Trend] **Interactive Example:**
        Your team's Flow Velocity over last 4 weeks: [15, 12, 18, 10] items/week
        
        **Step-by-Step Calculation:**
        ```
        Weighted sum = (15 × 1.0) + (12 × 0.8) + (18 × 0.6) + (10 × 0.4)
                     = 15 + 9.6 + 10.8 + 4.0
                     = 39.4
        
        Total weights = 1.0 + 0.8 + 0.6 + 0.4 = 2.8
        
        Forecast = 39.4 / 2.8 = 14.07 items/week (predicted next week)
        ```
        
        [Tip] **Why Weighted Average?**
        • Recent performance matters more than old data (recency bias)
        • Smooths out weekly volatility without ignoring trends
        • Balances responsiveness with stability
        • Proven effective in time series forecasting
        
        [Stats] **Confidence Levels:**
        • **High (4 weeks)**: Full weighting, most reliable forecast
        • **Medium (3 weeks)**: Reduced accuracy, still useful guidance
        • **Low (2 weeks)**: Limited data, use with caution
        • **Insufficient (<2 weeks)**: "Gathering data..." message shown
        
        [Note] **Practical Application:**
        Use forecasts to:
        • Proactively identify performance issues before they impact delivery
        • Plan capacity and resource allocation for next sprint
        • Communicate expected performance to stakeholders
        • Detect early warning signs of velocity degradation
    """,
    "trend_vs_forecast_explained": """
        Trend vs Forecast Indicator compares actual performance against predictions.
        
        [Tip] **Purpose:**
        Shows if your team is exceeding, meeting, or falling short of forecast
        expectations.
        
        [Calc] **Calculation:**
        ```python
        deviation_percent = ((current_value - forecast_value) / forecast_value) × 100%
        ```
        
        [Stats] **Interpretation:**
        
        **Deviation Thresholds:**
        • **On Track (→)**: ±5% deviation - performing as expected
        • **Moderate (↗/↘)**: 5-15% deviation - minor variation, monitor
        • **Significant (↗/↘)**: >15% deviation - investigate cause
        
        **Direction Meanings:**
        • **↗ (Up Arrow)**: Above forecast
          - For "higher is better" metrics (velocity, efficiency): [OK] Good (green)
          - For "lower is better" metrics (lead time, MTTR): [!] Warning (yellow/red)
        
        • **↘ (Down Arrow)**: Below forecast
          - For "higher is better" metrics: [!] Warning (yellow/red)
          - For "lower is better" metrics: [OK] Good (green)
        
        • **→ (Stable)**: Within ±5% of forecast - on track (neutral)
        
        [Trend] **Real-World Examples:**
        
        **Example 1: Flow Velocity (higher is better)**
        • Forecast: 12 items/week
        • Actual: 15 items/week
        • Calculation: ((15 - 12) / 12) × 100% = +25%
        • Result: ↗ "25% above forecast" (green - excellent)
        
        **Example 2: Lead Time for Changes (lower is better)**
        • Forecast: 5 days
        • Actual: 7 days
        • Calculation: ((7 - 5) / 5) × 100% = +40%
        • Result: ↗ "40% above forecast" (red - needs attention)
        
        **Example 3: Deployment Frequency (higher is better)**
        • Forecast: 8 deployments/month
        • Actual: 8.3 deployments/month
        • Calculation: ((8.3 - 8) / 8) × 100% = +3.75%
        • Result: → "On track" (neutral - stable performance)
        
        🚨 **Special Case - Monday Morning:**
        When current_value = 0 and deviation = -100%:
        • Message: "Week starting..." (instead of "-100% vs forecast")
        • Color: Secondary (neutral, not danger)
        • Interpretation: Week just started, no completions yet (not a failure)
        
        [Note] **Action Insights:**
        • **Consistent ↗ (good direction)**: Celebrate success, document what's working
        • **Consistent ↘ (bad direction)**: Investigate blockers, address issues
        • **Volatile trends**: Examine team stability, process consistency
        • **Stable (→)**: Predictable performance, reliable planning
    """,
    "metric_snapshots_explained": """
        Metric Snapshots store weekly historical data for forecast calculations.
        
        📁 **Storage Location:**
        `metrics_snapshots.json` → `{metric_name: [{date, value, iso_week}, ...]}`
        
        [Calc] **Data Structure:**
        ```python
        {
            "flow_velocity": [
                {"date": "2025-11-03", "value": 15.0, "iso_week": "2025-W45"},
                {"date": "2025-11-10", "value": 12.0, "iso_week": "2025-W46"},
                // ... up to 4 weeks of historical data
            ],
            "deployment_frequency": [...],
            // ... other metrics
        }
        ```
        
        [Config] **Automatic Capture:**
        Snapshots are automatically saved when metrics are calculated via:
        • `callbacks/dora_flow_metrics.py` - DORA & Flow metrics
        • `callbacks/scope_metrics.py` - Scope metrics (velocity, throughput)
        
        [Stats] **Retention Policy:**
        • Keeps last 4 weeks of data per metric (for weighted forecast)
        • Older data automatically pruned to prevent file bloat
        • One snapshot per ISO week (no duplicates)
        
        [Flow] **Usage Flow:**
        1. Metric calculated (e.g., Flow Velocity = 15 items/week)
        2. `save_weekly_snapshot(metric_name, value, current_week)` called
        3. Snapshot stored with ISO week number and timestamp
        4. `get_historical_values(metric_name, weeks=4)` retrieves for forecast
        5. Forecast calculated using weighted average algorithm
        
        [Maint] **Maintenance:**
        • **File Size**: Minimal (~10KB with 9 metrics × 4 weeks × 50 bytes/entry)
        • **Corruption Recovery**: File recreated automatically if invalid JSON
        • **Manual Reset**: Delete `metrics_snapshots.json` to clear all history
        
        [Note] **Troubleshooting:**
        • **"Gathering data..." message**: <2 weeks of snapshots available
        • **Stale forecasts**: Check snapshot timestamps, verify weekly updates
        • **Missing metrics**: Confirm metric is being calculated and saved
    """,
    "configuration_options": """
        Forecast Configuration controls weighting strategy and deviation thresholds.
        
        📁 **Configuration File:**
        `configuration/metrics_config.py` → `FORECAST_CONFIG` dictionary
        
        [Config] **Configurable Parameters:**
        
        ```python
        FORECAST_CONFIG = {
            # Weighting strategy for historical data
            "weights": [1.0, 0.8, 0.6, 0.4],  # Week 0 → Week -3 (exponential decay)
            
            # Minimum weeks required for forecast
            "min_weeks": 2,  # At least 2 weeks needed (low confidence)
            
            # Deviation thresholds for trend indicators
            "deviation_threshold_on_track": 5.0,   # ±5% = on track (→)
            "deviation_threshold_moderate": 15.0   # >15% = significant (↗/↘)
        }
        ```
        
        [Stats] **Metric Direction Mapping:**
        
        ```python
        METRIC_DIRECTIONS = {
            # Higher is better
            "deployment_frequency": "higher_better",
            "flow_velocity": "higher_better",
            "flow_efficiency": "higher_better",
            
            # Lower is better
            "lead_time_for_changes": "lower_better",
            "mean_time_to_recovery": "lower_better",
            "change_failure_rate": "lower_better",
            "flow_time": "lower_better",
            
            # Context-dependent
            "flow_load": "stable_better"  # WIP should be stable
        }
        ```
        
        [Config] **Customization Examples:**
        
        **More Responsive Forecasts (favor recent data):**
        ```python
        "weights": [1.0, 0.7, 0.4, 0.1]  # Steeper decay
        ```
        
        **More Stable Forecasts (balance recent vs historical):**
        ```python
        "weights": [1.0, 0.9, 0.8, 0.7]  # Gentler decay
        ```
        
        **Stricter "On Track" Definition:**
        ```python
        "deviation_threshold_on_track": 3.0  # Only ±3% considered on track
        ```
        
        **Require More Historical Data:**
        ```python
        "min_weeks": 3  # Need 3+ weeks before showing forecast
        ```
        
        [Note] **Best Practices:**
        • **Default weights (1.0, 0.8, 0.6, 0.4)**: Proven effective for most teams
        • **Adjust weights**: Only if forecasts consistently lag or overshoot reality
        • **Test changes**: Compare forecast accuracy before/after adjustments
        • **Document rationale**: Explain why custom weights fit your team's patterns
    """,
}

# DORA METRICS HELP CONTENT - Tooltips for DORA metrics
DORA_METRICS_TOOLTIPS = {
    "deployment_frequency": (
        "Production releases per week (average). Forecast uses last 4 weeks weighted "
        "[10%, 20%, 30%, 40%]. Elite: multiple/day, High: weekly."
    ),
    "lead_time_for_changes": (
        "Commit-to-production time (median of weekly medians). Forecast uses last 4 "
        "weeks weighted [10%, 20%, 30%, 40%]. Elite: <1 day, High: <1 week."
    ),
    "change_failure_rate": (
        "Failed deployments ÷ total deployments (overall rate). Forecast uses last 4 "
        "weeks weighted [10%, 20%, 30%, 40%]. Elite: <15%."
    ),
    "mean_time_to_recovery": (
        "Incident-to-recovery time (median of weekly medians). Forecast uses last 4 "
        "weeks weighted [10%, 20%, 30%, 40%]. Elite: <1 hour."
    ),
}

# SETTINGS PANEL HELP CONTENT - Tooltips for settings panel features
SETTINGS_PANEL_TOOLTIPS = {
    "jira_integration": (
        "Connect to your JIRA instance to automatically import project data. "
        "Configure your JIRA server URL, authentication, and field mappings to sync "
        "work items, story points, and completion dates."
    ),
    "jira_config": (
        "Configure JIRA connection settings including server URL, authentication "
        "credentials, and custom field mappings. Required before fetching data from "
        "JIRA. Click 'Configure JIRA' to open the setup modal."
    ),
    "jql_query": (
        "JQL (JIRA Query Language) filters which issues to import. Use JIRA's "
        "powerful query syntax to target specific projects, issue types, sprints, or "
        "custom criteria. Example: 'project = MYPROJECT AND created >= "
        "startOfYear()'"
    ),
    "jql_syntax": (
        "JQL syntax allows complex queries: 'project = KEY' (project filter), "
        "'status = Done' (status filter), 'created >= 2025-01-01' (date filter), "
        "'AND/OR' (logical operators). Combine filters for precise data selection."
    ),
    "saved_queries": (
        "Save frequently used JQL queries for quick access. Create multiple profiles "
        "for different projects, sprints, or reporting needs. Star a profile to make "
        "it the default query loaded on startup."
    ),
    "query_profiles": (
        "Query profiles store JQL queries with descriptive names. Load saved profiles "
        "to quickly switch between different data views. Edit existing profiles to "
        "update queries or rename them. Delete profiles you no longer need."
    ),
    "fetch_data": (
        "Import work items from JIRA using the configured connection and JQL query. "
        "Fetches issue keys, statuses, story points, creation dates, and completion "
        "dates. Updates scope metrics and velocity data automatically."
    ),
    "update_data": (
        "Refresh project data from JIRA to get the latest work item statuses and "
        "metrics. Recommended frequency: daily for active projects, weekly for "
        "stable projects. Data is cached locally for offline viewing."
    ),
    "calculate_metrics": (
        "Calculate Flow and DORA metrics from JIRA changelog data. Downloads status "
        "history if needed (~2 minutes), then computes Flow Time, Flow Efficiency, "
        "Lead Time, and Deployment Frequency. Run after updating JIRA data to "
        "refresh metrics with latest changes."
    ),
    "import_data": (
        "Upload project data from JSON or CSV files saved previously. Useful for "
        "offline analysis, data migration, or working with historical snapshots. "
        "Supports both full project data and weekly statistics exports."
    ),
    "export_data": (
        "Download complete project data as JSON for backup, sharing, or analysis in "
        "external tools. Includes all work items, statistics, settings, and JIRA "
        "cache. Preserves full project state for later restoration."
    ),
    "data_formats": (
        "JSON format: Complete structured data with all metadata. CSV format: "
        "Simplified tabular data for spreadsheet analysis. Choose JSON for full "
        "backups, CSV for external reporting and data analysis."
    ),
}

# Combined comprehensive help content for easy access
COMPREHENSIVE_HELP_CONTENT = {
    "forecast": FORECAST_HELP_DETAILED,
    "velocity": VELOCITY_HELP_DETAILED,
    "scope": SCOPE_HELP_DETAILED,
    "statistics": STATISTICS_HELP_DETAILED,
    "charts": CHART_HELP_DETAILED,
    "bug_analysis": BUG_ANALYSIS_TOOLTIPS,
    "dashboard": DASHBOARD_METRICS_TOOLTIPS,
    "parameters": PARAMETER_INPUTS_TOOLTIPS,
    "flow_metrics": FLOW_METRICS_TOOLTIPS,
    "dora_metrics": DORA_METRICS_TOOLTIPS,
    "settings": SETTINGS_PANEL_TOOLTIPS,
    "forecast_feature": FORECAST_HELP_CONTENT,  # Feature 009
    # 4-week weighted forecasts
}
