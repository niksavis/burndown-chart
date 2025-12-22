"""
Comprehensive Help Content for Progressive Disclosure Help System

This module stores detailed help content for the help system modals and dialogs.
Content provides comprehensive explanations that complement the concise tooltips.

Content is organized by category to match the original help text structure.
"""

# FORECAST HELP CONTENT - Comprehensive explanations for help pages
FORECAST_HELP_DETAILED = {
    "pert_methodology": """
        PERT (Program Evaluation and Review Technique) uses three-point estimation for probabilistic forecasting:
        
        [Stats] **Formula Components:**
        • Optimistic (O): Best-case scenario from top velocity periods
        • Most Likely (ML): Current average velocity from recent data
        • Pessimistic (P): Worst-case scenario from lowest velocity periods
        • Expected (E): Weighted average = (O + 4×ML + P) ÷ 6
        
        [Calc] **Mathematical Foundation:**
        The formula weights the Most Likely estimate 4x more heavily than extreme scenarios,
        following beta distribution principles for realistic project estimation.
        
        [Trend] **Confidence Intervals (Statistical Percentiles):**
        • 50% (Median): The PERT forecast itself - 50% chance of completion by this date
        • 80% (Good Confidence): PERT + 0.84 standard deviations - 80% chance of completion
        • 95% (High Confidence): PERT + 1.65 standard deviations - 95% chance of completion
        
        Wider ranges indicate higher velocity uncertainty; narrower ranges show more predictable delivery.
    """,
    "optimistic_forecast": """
        Best-case completion estimate based on your highest velocity periods.
        
        Calculated using the top performing periods from your historical data.
        This represents what's possible if everything goes well and velocity improves.
    """,
    "most_likely_forecast": """
        Most probable completion estimate based on current average velocity.
        
        Uses the mathematical average of your recent velocity data points.
        This is typically the most reliable single-point estimate.
    """,
    "pessimistic_forecast": """
        Worst-case completion estimate based on your lowest velocity periods.
        
        Calculated using the poorest performing periods from your historical data.
        This helps identify risks and plan for potential delays.
    """,
    "expected_forecast": """
        PERT Expected estimate using weighted average of all three scenarios.
        
        [Calc] **Step-by-Step Calculation:**
        1. Expected = (Optimistic + 4×Most Likely + Pessimistic) ÷ 6
        2. Example: (8 + 4×12 + 20) ÷ 6 = (8 + 48 + 20) ÷ 6 = 76 ÷ 6 = 12.67 weeks
        
        [Stats] **Why This Formula:**
        • Weights Most Likely 4x more than extremes (follows beta distribution)
        • Balances optimism with realism for statistically sound estimates
        • Reduces impact of outlier scenarios while acknowledging uncertainty
        
        [Note] **Interpretation:** Most reliable single-point forecast for project planning.
    """,
    "three_point_estimation": """
        Three-point estimation technique provides forecast ranges instead of single points.
        
        [Tip] **Mathematical Advantage:**
        Single estimates ignore uncertainty; ranges acknowledge project variability.
        
        [Trend] **Confidence Calculation:**
        Uncertainty bands calculated from variance between optimistic and pessimistic scenarios.
        Wider bands = higher uncertainty, narrower bands = more predictable outcomes.
        
        [Apply] **Practical Application:**
        Use ranges for risk planning, resource allocation, and stakeholder communication.
        The expected value provides planning target while ranges show risk boundaries.
    """,
    "project_overview": """
        Project Overview provides a comprehensive dashboard of your project's current state and progress metrics.
        
        [Stats] **Progress Tracking:**
        • Items Completion: Shows percentage of work items completed vs remaining
        • Points Completion: Shows percentage of story points completed vs remaining
        • Timeline Progress: Visual representation of project advancement
        
        [Tip] **Key Metrics Displayed:**
        • Total project scope (items and points)
        • Completed work (items and points) 
        • Remaining work estimates
        • Completion percentages for both items and points
        
        [Trend] **Visual Indicators:**
        Progress bars provide immediate visual feedback on project completion status.
        Different completion rates for items vs points can indicate scope or estimation changes.
        
        [Note] **Interpretation Guide:**
        Items and points completion percentages may differ due to:
        • Variable item complexity (some items worth more points)
        • Scope changes affecting total estimates
        • Estimation refinements during development
    """,
    "forecast_graph_overview": """
        Interactive forecast visualization showing project completion timeline with uncertainty ranges.
        
        [Trend] **Chart Elements:**
        • Historical Data: Solid lines showing actual completed work over time
        • PERT Forecasts: Dashed lines showing three-point estimation projections
        • Confidence Bands: Shaded areas indicating forecast uncertainty ranges
        • Scope Changes: Vertical markers showing requirement additions
        
        [Calc] **PERT Integration:**
        The chart displays all three PERT scenarios:
        • Optimistic: Best-case completion timeline (green)
        • Most Likely: Expected completion timeline (blue) 
        • Pessimistic: Worst-case completion timeline (red)
        • Expected: Weighted PERT calculation (primary forecast)
        
        [Stats] **Burndown Chart:**
        • Shows remaining work decreasing toward zero over time
        • Ideal for tracking progress against fixed deadlines
        • Visual representation of project velocity and completion trends
        
        [Tip] **Practical Usage:**
        • Use for stakeholder communication and deadline planning
        • Monitor actual progress against forecasted timelines
        • Identify trends and potential delays early
        • Understand impact of scope changes on delivery dates
    """,
    "pert_analysis_detailed": """
        Comprehensive PERT (Program Evaluation and Review Technique) analysis using statistical forecasting.
        
        [Calc] **Three-Point Calculation Method:**
        
        **Data Collection Process:**
        • Optimistic (O): Average of top 25% velocity periods from your historical data
        • Most Likely (ML): Simple arithmetic mean of all recent data points (typically 8-12 weeks)
        • Pessimistic (P): Average of bottom 25% velocity periods from your historical data
        
        **Expected Value Formula:**
        ```
        Expected = (O + 4×ML + P) ÷ 6
        ```
        
        **Interactive Example with Your Project Data:**
        Let's say your recent velocity data shows:
        • Best weeks averaged: 15 items/week (optimistic scenario)
        • Recent average: 10 items/week (most likely scenario) 
        • Worst weeks averaged: 6 items/week (pessimistic scenario)
        
        **Step-by-Step Calculation:**
        ```
        Expected = (15 + 4×10 + 6) ÷ 6
        Expected = (15 + 40 + 6) ÷ 6  
        Expected = 61 ÷ 6 = 10.17 items/week
        ```
        
        **Your Completion Timeline:**
        With 50 remaining items: 50 ÷ 10.17 = ~5 weeks expected completion
        
        [Stats] **Statistical Foundation:**
        • **Beta Distribution**: Mathematically models project uncertainty patterns naturally
        • **4× Most Likely Weighting**: Statistically optimal balance (proven by decades of project data)
        • **Confidence Intervals**: Calculated using coefficient of variation (CV = std/mean) applied to forecast
          - 50th percentile: The PERT forecast (median)
          - 80th percentile: PERT + 0.84 × forecast_std
          - 95th percentile: PERT + 1.65 × forecast_std
        
        [Link] **Related Topics:**
        See also: Weekly Velocity Calculation, Forecast Graph Overview, Input Parameters Guide
        
        [Tip] **Forecast Applications:**
        • Timeline Planning: Use Expected value for primary planning
        • Risk Assessment: Monitor gap between Optimistic and Pessimistic
        • Stakeholder Communication: Present ranges rather than single dates
        • Buffer Planning: Use Pessimistic scenario for contingency planning
        
        [Trend] **Accuracy Factors:**
        Forecast accuracy improves with:
        • More historical data points (8+ weeks recommended)
        • Consistent team composition and working patterns
        • Stable definition of "done" and estimation practices
        • Regular, complete data collection without gaps
    """,
    "input_parameters_guide": """
        Input Parameters control forecast calculations and scope definitions for your project.
        
        [Config] **Parameter Relationships:**
        
        **PERT Factor (Default: 6):**
        • Controls forecast horizon (number of data points)
        • Higher values = more conservative forecasts using more historical data
        • Lower values = more responsive forecasts using recent trends
        • Range: 2-15 based on project stability needs
        
        **Data Points Count:**
        • Number of weeks of historical data to include
        • Minimum: 4-6 weeks for basic trends
        • Recommended: 8-12 weeks for reliable forecasts
        • Maximum: 20+ weeks for very stable long-term projects
        
        **Scope Parameters:**
        • Total Items: Complete project scope (all work items)
        • Estimated Items: Remaining work items to complete
        • Total Points: Complete project effort (all story points)
        • Estimated Points: Remaining effort to complete
        
        [!] **Critical Relationships:**
        • Estimated values should be ≤ Total values
        • Changes affect all forecast calculations immediately
        • Points-based forecasts often more accurate than item-based
        • Regular updates improve forecast accuracy over time
        
        [Tip] **Optimization Tips:**
        • Increase PERT Factor for volatile teams (new teams, changing scope)
        • Decrease PERT Factor for stable teams with consistent delivery
        • Update scope parameters weekly as requirements evolve
        • Monitor forecast accuracy and adjust parameters accordingly
        
        [Stats] **Impact on Forecasting:**
        These parameters directly affect:
        • PERT calculation timeframes and confidence ranges
        • Velocity trend analysis and weighting
        • Scope change detection and adaptability metrics
        • Weekly forecast generation and accuracy
    """,
}

# VELOCITY HELP CONTENT - Comprehensive explanations for help pages
VELOCITY_HELP_DETAILED = {
    "weekly_velocity_calculation": """
        Weekly velocity represents your team's average completion rate calculated over the last 10 weeks of data.
        
        [Stats] **Calculation Methods:**
        • Average Velocity: Simple arithmetic mean (sum ÷ count)
        • Median Velocity: Middle value when sorted (outlier resistant)
        • Weighted Average: Recent weeks weighted more heavily
        
        [Calc] **Mathematical Examples:**
        Average: (12 + 15 + 8 + 18 + 10) ÷ 5 = 12.6 items/week
        Median: Sort [8, 10, 12, 15, 18], middle value = 12 items/week
        
        [Trend] **Trend Analysis:**
        Trend indicators show percentage change from previous periods:
        • Up arrows: Velocity acceleration (positive trend)
        • Down arrows: Velocity deceleration (negative trend)  
        • Stable indicators: Consistent velocity patterns (±5% variation)
    """,
    "velocity_trend_indicators": """
        Visual indicators showing velocity change patterns over time.
        
        [Tip] **Trend Calculation:**
        Percentage change = ((Current Period - Previous Period) ÷ Previous Period) × 100%
        
        [Stats] **Visual Meanings:**
        • [UP] Green Up Arrow: >5% improvement (acceleration)
        • [DOWN] Red Down Arrow: >5% decline (deceleration)
        • [STABLE] Gray Stable: ±5% variation (consistent)
        
        [Note] **Interpretation Guide:**
        Consistent upward trends may indicate team learning or process improvements.
        Consistent downward trends may indicate technical debt, scope creep, or team changes.
        Stable trends indicate predictable delivery capacity.
    """,
    "data_quality_impact": """
        Data quality and quantity directly affect forecast accuracy and confidence levels.
        
        [Trend] **Data Point Requirements:**
        • Minimum: 4-6 weeks for basic trends
        • Recommended: 8-12 weeks for reliable forecasts
        • Optimal: 12+ weeks for high-confidence predictions
        
        [Tip] **Quality Factors:**
        • Consistency: Regular data collection intervals
        • Completeness: No missing weeks or partial data
        • Accuracy: Reflects actual work completed (not started)
        • Context: Accounts for holidays, team changes, scope shifts
        
        [Stats] **Impact on Forecasts:**
        More data points = narrower confidence intervals = more reliable predictions
        Less data points = wider confidence intervals = higher uncertainty ranges
    """,
    "velocity_average_calculation": """
        Average Velocity calculation using arithmetic mean for consistent baseline forecasting.
        
        [Calc] **Mathematical Formula:**
        ```
        Average Velocity = Σ(completed items/points) ÷ Number of weeks
        ```
        
        **Interactive Calculation with Your Data:**
        Let's walk through a realistic example using 5 weeks of project data:
        • Week 1: 12 items (normal sprint)
        • Week 2: 15 items (good momentum week)  
        • Week 3: 8 items (holiday week, reduced capacity)
        • Week 4: 18 items (excellent focus week)
        • Week 5: 10 items (mixed priorities week)
        
        **Step-by-Step Calculation:**
        ```
        Sum = 12 + 15 + 8 + 18 + 10 = 63 total items
        Weeks = 5 weeks of data
        Average = 63 ÷ 5 = 12.6 items/week
        ```
        
        **Real Forecasting Application:**
        With 50 remaining items: 50 ÷ 12.6 = ~4 weeks expected completion
        
        [Stats] **Statistical Characteristics:**
        • **Equal Weighting**: Every week contributes equally to final calculation
        • **Outlier Sensitivity**: Week 4 (18 items) and Week 3 (8 items) both pull the average 
        • **Stability Indicator**: Consistent averages = predictable delivery capacity
        • **Trending Capability**: Shows velocity evolution over rolling time periods
        
        [Trend] **Advanced Trend Analysis:**
        ```
        Trend % = ((Current Period - Previous Period) ÷ Previous Period) × 100%
        ```
        
        **Practical Trend Example:**
        • Previous 5-week average: 10.2 items/week
        • Current 5-week average: 12.6 items/week
        • Calculation: ((12.6 - 10.2) ÷ 10.2) × 100% = +23.5% 
        • Interpretation: ↗️ **Positive acceleration** - team improving over time
        
        [Tip] **Integration with PERT Forecasting:**
        • Average velocity = "Most Likely" scenario in three-point estimation
        • Provides statistical foundation for expected completion dates
        • Combined with optimistic/pessimistic bounds for full PERT analysis
        
        [Config] **When to Use Average vs Median:**
        • **Choose Average** for stable teams with consistent delivery patterns
        • **Choose Median** when dealing with frequent scope changes or capacity variations
        
        [Link] **Related Topics:**
        See also: Median Velocity Calculation, PERT Analysis Detailed, Velocity Trend Indicators
    """,
    "velocity_median_calculation": """
        Median Velocity calculation using middle value for outlier-resistant forecasting.
        
        [Calc] **Formula:**
        Median Velocity = Middle value when all weekly velocities are sorted
        
        **Step-by-Step Example:**
        Weekly velocities: 12, 15, 8, 18, 10 items
        
        Calculation:
        • Sort values: [8, 10, 12, 15, 18]
        • Count: 5 values (odd number)
        • Median: Middle value = 12 items/week
        
        **Even Number Example:**
        Weekly velocities: 8, 10, 12, 15 items (4 weeks)
        • Sort values: [8, 10, 12, 15]
        • Median: (10 + 12) ÷ 2 = 11 items/week
        
        [Stats] **Characteristics:**
        • **Outlier Resistance**: High - extreme values don't affect result
        • **Stability**: More stable than average when data has outliers
        • **Use Case**: Best for teams with variable delivery or scope changes
        • **Interpretation**: Represents "typical" week performance
        
        [Trend] **Advantage Over Average:**
        
        **Example with Outlier:**
        Weekly data: [2, 10, 12, 13, 48] items
        • Average: (2+10+12+13+48) ÷ 5 = 17 items/week
        • Median: 12 items/week (middle value)
        
        The median (12) better represents typical performance than average (17) 
        which is skewed by the outlier week of 48 items.
        
        [Tip] **Forecasting Application:**
        Median velocity provides more realistic estimates when:
        • Team has inconsistent delivery patterns
        • Data includes exceptional weeks (holidays, crunch periods, blockers)
        • Scope changes create velocity variations
        • New team members joining/leaving affect capacity
    """,
}

# SCOPE HELP CONTENT - Comprehensive explanations for help pages
SCOPE_HELP_DETAILED = {
    "scope_change_methodology": """
        Scope change rate measures the percentage increase in project requirements relative to the original baseline.
        
        [Calc] **Calculation Formula:**
        Scope Change Rate = (Items Created ÷ Baseline Items) × 100%
        
        [Stats] **Example Calculation:**
        • Original baseline: 100 items
        • Items added during project: 25 items
        • Scope change rate: (25 ÷ 100) × 100% = 25%
        
        [Tip] **Agile Context:**
        In agile projects, scope changes are normal and healthy, representing:
        • Discovery of new requirements
        • User feedback integration  
        • Market responsiveness
        • Learning and adaptation
        
        [Trend] **Healthy Ranges:**
        • 10-30%: Good adaptability without excessive thrash
        • 30-50%: High responsiveness, monitor for scope creep
        • >50%: Potential planning or requirements issues
    """,
    "adaptability_index": """
        Adaptability Index measures how well your team balances scope changes with delivery consistency.
        
        [Calc] **Calculation Method:**
        Adaptability = 1 - (Standard Deviation of Weekly Scope Changes ÷ Mean Weekly Scope Changes)
        
        [Stats] **Interpretation Scale:**
        • 0.8-1.0: Highly adaptable (excellent scope management)
        • 0.5-0.8: Good adaptability (normal agile patterns)
        • 0.2-0.5: Moderate adaptability (some instability)
        • 0.0-0.2: Low adaptability (high scope volatility)
        
        [Tip] **Agile Context:**
        Low values (0.2-0.5) are NORMAL for responsive agile teams!
        This indicates healthy adaptation to changing requirements.
        Very high values might suggest insufficient customer feedback or market responsiveness.
        
        [Note] **Action Insights:**
        Use trends over time rather than absolute values for decision making.
    """,
    "throughput_ratio": """
        Throughput ratio compares the rate of new work creation to work completion.
        
        [Calc] **Calculation Formula:**
        Throughput Ratio = Created Items ÷ Completed Items
        
        [Stats] **Ratio Interpretation:**
        • 1.0: Perfect balance (creating = completing)
        • <1.0: Burning down backlog (completing > creating)
        • >1.0: Growing backlog (creating > completing)
        
        [Tip] **Healthy Patterns:**
        • Early project: >1.0 (discovery and planning phase)
        • Mid project: ~1.0 (steady state development)
        • Late project: <1.0 (completion and cleanup phase)
        
        [Trend] **Strategic Insights:**
        Sustained ratios >1.5 may indicate:
        • Insufficient development capacity
        • Scope creep or poor requirements management
        • Need for capacity planning or priority refinement
    """,
}

# STATISTICS HELP CONTENT - Comprehensive explanations for help pages
STATISTICS_HELP_DETAILED = {
    "data_collection_methodology": """
        Data collection methodology for accurate project tracking and forecasting.
        
        [Date] **Weekly Data Collection:**
        • Collection Point: End of each work week (typically Friday)
        • Scope: Monday-Sunday work period for consistency
        • Frequency: Weekly snapshots for trend analysis
        
        [Calc] **Data Fields Explained:**
        
        **Week Start (Monday)**: 
        - Date marking the beginning of the work week
        - Used as the reference point for all weekly measurements
        - Should be actual Monday date even if work starts Tuesday
        
        **Items Done This Week**:
        - Count of work items completed during the weekly period
        - Must be truly "done" items that deliver value to users
        - Incremental value (not cumulative) for proper trend analysis
        
        **Points Done This Week**:
        - Story points or effort units completed during the weekly period
        - Should match the point values of items marked as done
        - Incremental value for accurate velocity calculations
        
        **New Items Added**:
        - Count of new work items discovered or added to backlog
        - Includes user stories, bugs, technical tasks, scope additions
        - Tracks scope growth and requirement discovery patterns
        
        **New Points Added**:
        - Point estimate for newly added work items
        - Represents effort impact of scope changes
        - Used for scope change rate and throughput ratio calculations
    """,
    "data_quality_guidelines": """
        Guidelines for maintaining high-quality project data for accurate forecasting.
        
        [OK] **Data Quality Checklist:**
        
        **Completeness:**
        • No missing weeks in the data series
        • All required fields populated for each week
        • Consistent data collection schedule
        
        **Accuracy:**
        • Items marked "done" are truly complete and deliverable
        • Point estimates reflect actual effort, not initial estimates
        • Scope additions captured when decisions are made, not retroactively
        
        **Consistency:**
        • Same definition of "done" applied throughout project
        • Consistent point estimation approach across the team
        • Regular weekly collection schedule maintained
        
        **Context:**
        • Document significant events (holidays, team changes, major scope shifts)
        • Note any data collection irregularities or exceptions
        • Track external factors that might affect velocity patterns
        
        [Stats] **Impact on Forecasting:**
        High-quality data leads to:
        • More accurate PERT forecasts
        • Narrower confidence intervals
        • Better trend detection
        • More reliable completion predictions
        
        Poor data quality results in:
        • Wide uncertainty ranges
        • Unreliable forecasts
        • Missed trend signals
        • Reduced stakeholder confidence
    """,
    "weekly_progress_data_explanation": """
        Weekly Progress Data table provides comprehensive tracking of team velocity and scope changes.
        
        [Stats] **Table Structure:**
        Each row represents one week of project activity with key metrics for forecasting.
        
        [Calc] **Column Definitions:**
        
        **Week Start (Monday):**
        • Reference date for the work week (Monday-Sunday period)
        • Used for chronological sorting and trend analysis
        • Should be actual calendar Monday even if team starts different day
        
        **Items Done This Week:**
        • Count of work items completed during this specific week
        • Must be truly "done" items (passed testing, deployed, delivered)
        • Incremental count (not cumulative total)
        • Used for velocity trend analysis and PERT calculations
        
        **Points Done This Week:**
        • Story points or effort units completed during this specific week
        • Should match the estimated effort of items marked done
        • Incremental points (not cumulative total)
        • More accurate than item count for teams with variable item complexity
        
        **New Items Added:**
        • Work items discovered, created, or added to backlog this week
        • Includes user stories, bugs, technical debt, scope additions
        • Tracks scope growth and requirement discovery patterns
        • Used for scope change rate and adaptability calculations
        
        **New Points Added:**
        • Estimated effort for newly added work items
        • Represents scope impact of new requirements
        • Used for throughput ratio and scope stability analysis
        
        [Trend] **Usage for Forecasting:**
        
        **Velocity Calculations:**
        • Average: Sum of "Items/Points Done" ÷ Number of weeks
        • Trend analysis: Percentage change between recent periods
        • PERT scenarios: Best/worst/typical performance identification
        
        **Scope Analysis:**
        • Growth rate: New items/points added vs baseline scope
        • Throughput ratio: Created vs completed work comparison
        • Adaptability index: Consistency of scope change patterns
        
        **Data Quality Tips:**
        • Enter data weekly for accurate trend detection
        • Use consistent "done" definition throughout project
        • Include all work types (features, bugs, technical tasks)
        • Estimate new items promptly for accurate scope tracking
        
        [!] **Common Mistakes:**
        • Entering cumulative totals instead of weekly increments
        • Inconsistent item/point estimation practices
        • Missing weeks creating gaps in trend analysis
        • Different "done" definitions across team members
    """,
}

# CHART HELP CONTENT - Comprehensive explanations for help pages
CHART_HELP_DETAILED = {
    "burndown_chart": """
        Comprehensive guide to interpreting burndown charts for project tracking.
        
        📉 **Burndown Charts:**
        • Show remaining work decreasing over time
        • Start high (total scope) and trend toward zero
        • Ideal for tracking progress against fixed deadlines
        • Emphasize completion progress and deadline tracking
        
        [Tip] **Best Practices:**
        • Monitor actual progress against forecasted timelines
        • Track "how much work is left" to completion
        • Identify trends and potential delays early
        • Communicate project status to stakeholders
        
        [Stats] **Visual Elements:**
        • Solid lines: Historical actual data
        • Dashed lines: PERT forecast projections  
        • Dotted lines: Confidence intervals and uncertainty ranges
        • Vertical line: Current date marker
        • Scope change indicators: Show requirement additions/removals
    """,
    "pert_forecast_methodology": """
        PERT (Program Evaluation Review Technique) creates realistic forecasts using three-point estimation.
        
        [Calc] **Three-Point Estimation Process:**
        1. **Optimistic Scenario**: Best-case timeline from peak velocity periods
        2. **Most Likely Scenario**: Realistic estimate from current average velocity
        3. **Pessimistic Scenario**: Worst-case timeline from lowest velocity periods
        4. **Expected Value**: Weighted calculation = (O + 4×ML + P) ÷ 6
        
        [Stats] **Mathematical Foundation:**
        • Follows beta distribution for project estimation
        • Weights most likely scenario 4x more than extremes
        • Provides statistically sound forecasts with confidence intervals
        • Accounts for both optimism bias and risk factors
        
        [Trend] **Confidence Intervals:**
        • Calculated using coefficient of variation applied to PERT forecast
        • 50th percentile: The PERT forecast itself (median estimate)
        • 80th percentile: PERT + 0.84 standard deviations
        • 95th percentile: PERT + 1.65 standard deviations
        • Wider intervals indicate higher velocity uncertainty
        • Narrower intervals suggest more predictable delivery patterns
        • Use for risk planning and stakeholder communication
        
        [Tip] **Practical Application:**
        • Expected value: Primary planning target
        • Optimistic: Best-case scenario for resource planning
        • Pessimistic: Risk mitigation and buffer planning
        • Confidence bands: Communication of forecast uncertainty
        
        [Note] **Accuracy Factors:**
        Forecast accuracy improves with:
        • More historical data points (8+ weeks recommended)
        • Consistent team composition and working arrangements
        • Stable definition of "done" and point estimation
        • Regular, complete data collection practices
    """,
    "weekly_chart_methodology": """
        Weekly velocity charts with predictive forecasting using weighted moving averages.
        
        [Stats] **Chart Components:**
        • Historical bars: Actual weekly completion rates
        • Forecast bars: Predicted next week performance using PERT methodology  
        • Trend lines: Moving average patterns for visual trend identification
        • Confidence intervals: Error bars showing forecast uncertainty ranges
        
        [Calc] **Forecasting Methodology:**
        **Weighted Moving Average:**
        • Most recent week: 40% weight
        • Second recent: 30% weight  
        • Third recent: 20% weight
        • Fourth recent: 10% weight
        • Formula: 0.4×W1 + 0.3×W2 + 0.2×W3 + 0.1×W4
        
        **PERT Integration:**
        • Optimistic: Top 25% of historical weekly performance
        • Most Likely: Weighted moving average calculation
        • Pessimistic: Bottom 25% of historical weekly performance
        • Expected: (O + 4×ML + P) ÷ 6 for next week prediction
        
        [Trend] **Visual Interpretation:**
        • Solid bars: Confirmed historical performance
        • Patterned bars: Forecasted performance with uncertainty
        • Error bars: Confidence intervals using coefficient of variation method
        • Trend direction: Overall velocity acceleration or deceleration patterns
        
        [Tip] **Usage Guidelines:**
        • Use for short-term capacity planning (1-2 weeks ahead)
        • Compare forecast vs actual for methodology refinement
        • Monitor confidence interval width for prediction reliability
        • Adjust team capacity based on consistent trend patterns
    """,
}

# BUG ANALYSIS HELP CONTENT - Tooltips for bug metrics
BUG_ANALYSIS_TOOLTIPS = {
    "resolution_rate": "Percentage of closed bugs. ≥80% excellent, 70-79% good, <70% needs attention.",
    "open_bugs": "Current unresolved bug count. Green: 0, Teal: 1-5, Orange: >5 bugs.",
    "expected_resolution": "Forecast weeks to clear bug backlog using last 8 weeks of data. Green: ≤2 weeks, Teal: 3-4 weeks, Yellow: >4 weeks.",
}

# DASHBOARD METRICS HELP CONTENT - Tooltips for main dashboard cards
DASHBOARD_METRICS_TOOLTIPS = {
    "completion_forecast": "Estimated project completion date using PERT three-point estimation. Based on optimistic, most likely, and pessimistic velocity scenarios from your historical data.",
    "completion_forecast_detail": "This forecast uses your team's actual velocity data to predict when all remaining work will be completed. The calculation accounts for best-case, average, and worst-case scenarios to provide a realistic estimate with confidence ranges.",
    "remaining_work": "Current backlog of incomplete work items and story points. Tracks both the number of items and their estimated effort to give you a complete picture of what's left to deliver.",
    "remaining_items": "Number of work items (tasks, stories, bugs) not yet completed. This count helps track progress independently of estimation complexity.",
    "remaining_points": "Total story points for all incomplete work. Represents the estimated effort remaining, which may differ from item count due to varying complexity.",
    "velocity_trend": "Team's delivery rate over time, measured in items and points completed per week. Shows whether your team is accelerating, maintaining pace, or slowing down.",
    "current_velocity": "Average items and points completed per week based on recent historical data. This is your team's current sustainable delivery pace used for forecasting.",
    "pert_expected": "Weighted average of optimistic, most likely, and pessimistic forecasts using the formula: (O + 4×ML + P) ÷ 6. Provides the most statistically reliable single-point estimate.",
    "confidence_range": "Uncertainty band around the forecast showing the range of possible completion dates. Wider ranges indicate higher unpredictability; narrower ranges show consistent velocity.",
    "scope_changes": "Additions or removals to project scope over time. Tracks how requirements evolve and impacts forecast accuracy and completion dates.",
    "health_score": "Health score (0-100 points) combines four components: Progress (0-30 points - completion %), Schedule (0-30 points - buffer vs deadline using smooth sigmoid), Stability (0-20 points - velocity consistency via CV = Coefficient of Variation, which measures how much velocity varies: CV = std dev / mean × 100%), and Trend (0-20 points - recent velocity change). Continuous formulas provide smooth, gradual score changes. Incomplete weeks are automatically filtered to prevent mid-week score fluctuations.",
}

# PARAMETER INPUTS HELP CONTENT - Tooltips for parameter panel controls
PARAMETER_INPUTS_TOOLTIPS = {
    "pert_factor": "Forecast Range: Controls how many weeks to sample for best/worst case forecasts. Higher values (8-12) provide conservative estimates using sustained performance patterns. Lower values (3-6) reflect recent variability. Minimum 6 weeks of data recommended for reliability.",
    "pert_factor_detail": "This parameter determines how many of your best and worst performing weeks are averaged to calculate optimistic and pessimistic scenarios. For example, with a value of 6, your forecast uses the average of your 6 best weeks as the optimistic case and your 6 worst weeks as the pessimistic case. The most likely scenario always uses the average of all available data. This approach provides data-driven forecasts based on your team's actual historical performance, which is more reliable than simple averages or gut feelings. Recommended: 20-30% of your total history (e.g., 6 weeks if you have 30 weeks of data).",
    "deadline": "Target completion date for your project. Used to calculate timeline pressure and whether current velocity will meet the deadline. Shown as a vertical line on forecast charts.",
    "deadline_detail": "Set your desired or committed project deadline. The forecast will compare this date against velocity-based predictions to show if you're on track, ahead, or behind schedule.",
    "estimated_items": "Number of work items that have effort estimates (story points, hours, etc.). Used to calculate average effort per item. If 0, the system will use historical averages. Manual changes will be overwritten by JIRA updates.",
    "remaining_items": "Total number of currently open/unresolved work items. This is your current remaining scope. Used to calculate total remaining effort when combined with estimated points. Manual changes will be overwritten by JIRA updates.",
    "estimated_points": "Total story points for items that have been estimated. Used with Estimated Items to calculate average points per item. Leave at 0 if story points are unavailable. Manual changes will be overwritten by JIRA updates.",
    "remaining_points": "Auto-calculated total remaining effort. Formula: Estimated Points + (avg_points_per_item × unestimated_items), where avg = Estimated Points ÷ Estimated Items, and unestimated = Remaining Items - Estimated Items. Updates automatically when any input changes.",
    "total_items": "Baseline Items (at window start): Total work items that needed to be completed at the start of your selected time window. This baseline is used for tracking progress and calculating completion percentage within the window. Currently Open = Baseline - Completed.",
    "completed_items": "Number of work items finished within the selected time window. Used to calculate completion percentage and determine currently open work: Baseline Items - Completed Items.",
    "total_points": "Baseline Points (at window start): Total story points that needed to be completed at the start of your selected time window. This baseline includes both estimated and extrapolated points for items without estimates. Currently Open = Baseline - Completed.",
    "completed_points": "Story points for work items finished within the selected time window. Used to calculate effort-based completion percentage: Completed Points ÷ Baseline Points × 100%.",
    "scope_buffer": "Optional reserve capacity for scope changes and unknowns. Adding a buffer (e.g., 10-20% of total scope) provides contingency for new requirements.",
    "data_points": "Time Period: Number of historical weeks to include for baseline and velocity calculations. Minimum 4-6 weeks recommended; 8-12 weeks optimal for stable forecasts. This defines your analysis window.",
    "data_points_detail": "More data points provide stability but may miss recent trends. Fewer points are more responsive to changes but can be volatile. Balance based on your project's stability.",
}

# FLOW METRICS HELP CONTENT - Tooltips for Flow Framework metrics
FLOW_METRICS_TOOLTIPS = {
    "flow_velocity": "Completed items per week (average). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. Higher velocity = faster delivery.",
    "flow_time": "Start-to-completion time (median of weekly medians). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. Lower time = faster cycles.",
    "flow_efficiency": "Active work time ÷ total time (average). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. 25-40% is typical for healthy teams.",
    "flow_load": "Current work in progress (WIP snapshot). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. Lower WIP = better focus and faster delivery.",
    "flow_distribution": "Breakdown of completed work by type: Features (new value), Defects (quality issues), Risk (security/compliance), and Tech Debt (maintenance). Aggregated totals across the selected period. Balanced distribution indicates healthy development practices.",
}

# 4-WEEK FORECAST HELP CONTENT - Tooltips and detailed help for forecasting feature (Feature 009)
FORECAST_HELP_CONTENT = {
    "forecast_overview": "4-week weighted forecast predicting next week's performance based on historical trends. Uses exponential weighting (1.0, 0.8, 0.6, 0.4) to emphasize recent data while considering longer patterns. Helps teams proactively address performance issues before they impact delivery.",
    "forecast_value": "Predicted metric value for next week calculated using weighted average of last 4 weeks. Recent weeks contribute more weight than older weeks (Week 0: 100%, Week -1: 80%, Week -2: 60%, Week -3: 40%). Normalized by total weight for accurate prediction.",
    "forecast_confidence": "Forecast reliability based on available historical data. High: 4 weeks (full weighting), Medium: 3 weeks (reduced accuracy), Low: 2 weeks (limited reliability). Forecasts require minimum 2 weeks of data; insufficient data shows 'Gathering data...'",
    "trend_vs_forecast": "Compares current week's actual performance against forecast to show if team is on track. Positive deviation (↗) indicates exceeding forecast; negative (↘) below forecast; stable (→) on track within ±5%. Color coding: Green (favorable trend), Yellow (moderate deviation 5-15%), Red (significant deviation >15%).",
    "monday_morning": "Special handling for week start when current value is zero. Shows 'Week starting...' message with neutral indicator instead of '-100% vs forecast'. Prevents false alarms at beginning of work week when no completions have occurred yet.",
    "deviation_thresholds": "Performance deviation bands: On track (±5%), Moderate (5-15%), Significant (>15%). Direction interpretation depends on metric type: higher is better for velocity/efficiency, lower is better for lead time/MTTR. Bands help identify when intervention may be needed.",
    "metric_snapshots": "Weekly historical data stored for forecast calculations. Automatically captured when metrics update. Includes metric value, ISO week number, and timestamp. Used for weighted average calculation and trend analysis. Stored in metrics_snapshots.json.",
    "weighting_strategy": "Exponential decay weighting: Most recent week (1.0) → 3 weeks ago (0.4). Formula: weighted_sum = Σ(value × weight) / Σ(weights). Balances responsiveness to recent changes with stability from historical patterns. Configurable via FORECAST_CONFIG in metrics_config.py.",
}

# FORECAST DETAILED HELP - Comprehensive explanations for help modal
FORECAST_HELP_DETAILED = {
    "forecast_algorithm": """
        4-Week Weighted Forecast provides actionable predictions for next week's performance.
        
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
        Shows if your team is exceeding, meeting, or falling short of forecast expectations.
        
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
    "deployment_frequency": "Production releases per week (average). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. Elite: multiple/day, High: weekly.",
    "lead_time_for_changes": "Commit-to-production time (median of weekly medians). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. Elite: <1 day, High: <1 week.",
    "change_failure_rate": "Failed deployments ÷ total deployments (overall rate). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. Elite: <15%.",
    "mean_time_to_recovery": "Incident-to-recovery time (median of weekly medians). Forecast uses last 4 weeks weighted [10%, 20%, 30%, 40%]. Elite: <1 hour.",
}

# SETTINGS PANEL HELP CONTENT - Tooltips for settings panel features
SETTINGS_PANEL_TOOLTIPS = {
    "jira_integration": "Connect to your JIRA instance to automatically import project data. Configure your JIRA server URL, authentication, and field mappings to sync work items, story points, and completion dates.",
    "jira_config": "Configure JIRA connection settings including server URL, authentication credentials, and custom field mappings. Required before fetching data from JIRA. Click 'Configure JIRA' to open the setup modal.",
    "jql_query": "JQL (JIRA Query Language) filters which issues to import. Use JIRA's powerful query syntax to target specific projects, issue types, sprints, or custom criteria. Example: 'project = MYPROJECT AND created >= startOfYear()'",
    "jql_syntax": "JQL syntax allows complex queries: 'project = KEY' (project filter), 'status = Done' (status filter), 'created >= 2025-01-01' (date filter), 'AND/OR' (logical operators). Combine filters for precise data selection.",
    "saved_queries": "Save frequently used JQL queries for quick access. Create multiple profiles for different projects, sprints, or reporting needs. Star a profile to make it the default query loaded on startup.",
    "query_profiles": "Query profiles store JQL queries with descriptive names. Load saved profiles to quickly switch between different data views. Edit existing profiles to update queries or rename them. Delete profiles you no longer need.",
    "fetch_data": "Import work items from JIRA using the configured connection and JQL query. Fetches issue keys, statuses, story points, creation dates, and completion dates. Updates scope metrics and velocity data automatically.",
    "update_data": "Refresh project data from JIRA to get the latest work item statuses and metrics. Recommended frequency: daily for active projects, weekly for stable projects. Data is cached locally for offline viewing.",
    "calculate_metrics": "Calculate Flow and DORA metrics from JIRA changelog data. Downloads status history if needed (~2 minutes), then computes Flow Time, Flow Efficiency, Lead Time, and Deployment Frequency. Run after updating JIRA data to refresh metrics with latest changes.",
    "import_data": "Upload project data from JSON or CSV files saved previously. Useful for offline analysis, data migration, or working with historical snapshots. Supports both full project data and weekly statistics exports.",
    "export_data": "Download complete project data as JSON for backup, sharing, or analysis in external tools. Includes all work items, statistics, settings, and JIRA cache. Preserves full project state for later restoration.",
    "data_formats": "JSON format: Complete structured data with all metadata. CSV format: Simplified tabular data for spreadsheet analysis. Choose JSON for full backups, CSV for external reporting and data analysis.",
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
    "forecast_feature": FORECAST_HELP_CONTENT,  # Feature 009 - 4-week weighted forecasts
}
