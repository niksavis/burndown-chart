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
        
        📊 **Formula Components:**
        • Optimistic (O): Best-case scenario from top velocity periods
        • Most Likely (ML): Current average velocity from recent data
        • Pessimistic (P): Worst-case scenario from lowest velocity periods
        • Expected (E): Weighted average = (O + 4×ML + P) ÷ 6
        
        🔢 **Mathematical Foundation:**
        The formula weights the Most Likely estimate 4x more heavily than extreme scenarios,
        following beta distribution principles for realistic project estimation.
        
        📈 **Confidence Intervals:**
        Uncertainty range calculated as ±25% of variance between scenarios.
        Wider ranges indicate higher uncertainty; narrower ranges show more predictable velocity.
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
        
        🔢 **Step-by-Step Calculation:**
        1. Expected = (Optimistic + 4×Most Likely + Pessimistic) ÷ 6
        2. Example: (8 + 4×12 + 20) ÷ 6 = (8 + 48 + 20) ÷ 6 = 76 ÷ 6 = 12.67 weeks
        
        📊 **Why This Formula:**
        • Weights Most Likely 4x more than extremes (follows beta distribution)
        • Balances optimism with realism for statistically sound estimates
        • Reduces impact of outlier scenarios while acknowledging uncertainty
        
        💡 **Interpretation:** Most reliable single-point forecast for project planning.
    """,
    "three_point_estimation": """
        Three-point estimation technique provides forecast ranges instead of single points.
        
        🎯 **Mathematical Advantage:**
        Single estimates ignore uncertainty; ranges acknowledge project variability.
        
        📈 **Confidence Calculation:**
        Uncertainty bands calculated from variance between optimistic and pessimistic scenarios.
        Wider bands = higher uncertainty, narrower bands = more predictable outcomes.
        
        🔍 **Practical Application:**
        Use ranges for risk planning, resource allocation, and stakeholder communication.
        The expected value provides planning target while ranges show risk boundaries.
    """,
    "project_overview": """
        Project Overview provides a comprehensive dashboard of your project's current state and progress metrics.
        
        📊 **Progress Tracking:**
        • Items Completion: Shows percentage of work items completed vs remaining
        • Points Completion: Shows percentage of story points completed vs remaining
        • Timeline Progress: Visual representation of project advancement
        
        🎯 **Key Metrics Displayed:**
        • Total project scope (items and points)
        • Completed work (items and points) 
        • Remaining work estimates
        • Completion percentages for both items and points
        
        📈 **Visual Indicators:**
        Progress bars provide immediate visual feedback on project completion status.
        Different completion rates for items vs points can indicate scope or estimation changes.
        
        💡 **Interpretation Guide:**
        Items and points completion percentages may differ due to:
        • Variable item complexity (some items worth more points)
        • Scope changes affecting total estimates
        • Estimation refinements during development
    """,
    "forecast_graph_overview": """
        Interactive forecast visualization showing project completion timeline with uncertainty ranges.
        
        📈 **Chart Elements:**
        • Historical Data: Solid lines showing actual completed work over time
        • PERT Forecasts: Dashed lines showing three-point estimation projections
        • Confidence Bands: Shaded areas indicating forecast uncertainty ranges
        • Scope Changes: Vertical markers showing requirement additions
        
        🔢 **PERT Integration:**
        The chart displays all three PERT scenarios:
        • Optimistic: Best-case completion timeline (green)
        • Most Likely: Expected completion timeline (blue) 
        • Pessimistic: Worst-case completion timeline (red)
        • Expected: Weighted PERT calculation (primary forecast)
        
        📊 **Burndown Chart:**
        • Shows remaining work decreasing toward zero over time
        • Ideal for tracking progress against fixed deadlines
        • Visual representation of project velocity and completion trends
        
        🎯 **Practical Usage:**
        • Use for stakeholder communication and deadline planning
        • Monitor actual progress against forecasted timelines
        • Identify trends and potential delays early
        • Understand impact of scope changes on delivery dates
    """,
    "pert_analysis_detailed": """
        Comprehensive PERT (Program Evaluation and Review Technique) analysis using statistical forecasting.
        
        🔢 **Three-Point Calculation Method:**
        
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
        
        📊 **Statistical Foundation:**
        • **Beta Distribution**: Mathematically models project uncertainty patterns naturally
        • **4× Most Likely Weighting**: Statistically optimal balance (proven by decades of project data)
        • **Confidence Intervals**: ±25% of (Optimistic - Pessimistic) variance provides 68% confidence range
        
        🔗 **Related Topics:**
        See also: Weekly Velocity Calculation, Forecast Graph Overview, Input Parameters Guide
        
        🎯 **Forecast Applications:**
        • Timeline Planning: Use Expected value for primary planning
        • Risk Assessment: Monitor gap between Optimistic and Pessimistic
        • Stakeholder Communication: Present ranges rather than single dates
        • Buffer Planning: Use Pessimistic scenario for contingency planning
        
        📈 **Accuracy Factors:**
        Forecast accuracy improves with:
        • More historical data points (8+ weeks recommended)
        • Consistent team composition and working patterns
        • Stable definition of "done" and estimation practices
        • Regular, complete data collection without gaps
    """,
    "input_parameters_guide": """
        Input Parameters control forecast calculations and scope definitions for your project.
        
        🔧 **Parameter Relationships:**
        
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
        
        ⚠️ **Critical Relationships:**
        • Estimated values should be ≤ Total values
        • Changes affect all forecast calculations immediately
        • Points-based forecasts often more accurate than item-based
        • Regular updates improve forecast accuracy over time
        
        🎯 **Optimization Tips:**
        • Increase PERT Factor for volatile teams (new teams, changing scope)
        • Decrease PERT Factor for stable teams with consistent delivery
        • Update scope parameters weekly as requirements evolve
        • Monitor forecast accuracy and adjust parameters accordingly
        
        📊 **Impact on Forecasting:**
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
        
        📊 **Calculation Methods:**
        • Average Velocity: Simple arithmetic mean (sum ÷ count)
        • Median Velocity: Middle value when sorted (outlier resistant)
        • Weighted Average: Recent weeks weighted more heavily
        
        🔢 **Mathematical Examples:**
        Average: (12 + 15 + 8 + 18 + 10) ÷ 5 = 12.6 items/week
        Median: Sort [8, 10, 12, 15, 18], middle value = 12 items/week
        
        📈 **Trend Analysis:**
        Trend indicators show percentage change from previous periods:
        • Up arrows: Velocity acceleration (positive trend)
        • Down arrows: Velocity deceleration (negative trend)  
        • Stable indicators: Consistent velocity patterns (±5% variation)
    """,
    "velocity_trend_indicators": """
        Visual indicators showing velocity change patterns over time.
        
        🎯 **Trend Calculation:**
        Percentage change = ((Current Period - Previous Period) ÷ Previous Period) × 100%
        
        📊 **Visual Meanings:**
        • 🔺 Green Up Arrow: >5% improvement (acceleration)
        • 🔻 Red Down Arrow: >5% decline (deceleration)
        • ➡️ Gray Stable: ±5% variation (consistent)
        
        💡 **Interpretation Guide:**
        Consistent upward trends may indicate team learning or process improvements.
        Consistent downward trends may indicate technical debt, scope creep, or team changes.
        Stable trends indicate predictable delivery capacity.
    """,
    "data_quality_impact": """
        Data quality and quantity directly affect forecast accuracy and confidence levels.
        
        📈 **Data Point Requirements:**
        • Minimum: 4-6 weeks for basic trends
        • Recommended: 8-12 weeks for reliable forecasts
        • Optimal: 12+ weeks for high-confidence predictions
        
        🎯 **Quality Factors:**
        • Consistency: Regular data collection intervals
        • Completeness: No missing weeks or partial data
        • Accuracy: Reflects actual work completed (not started)
        • Context: Accounts for holidays, team changes, scope shifts
        
        📊 **Impact on Forecasts:**
        More data points = narrower confidence intervals = more reliable predictions
        Less data points = wider confidence intervals = higher uncertainty ranges
    """,
    "velocity_average_calculation": """
        Average Velocity calculation using arithmetic mean for consistent baseline forecasting.
        
        🔢 **Mathematical Formula:**
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
        
        📊 **Statistical Characteristics:**
        • **Equal Weighting**: Every week contributes equally to final calculation
        • **Outlier Sensitivity**: Week 4 (18 items) and Week 3 (8 items) both pull the average 
        • **Stability Indicator**: Consistent averages = predictable delivery capacity
        • **Trending Capability**: Shows velocity evolution over rolling time periods
        
        📈 **Advanced Trend Analysis:**
        ```
        Trend % = ((Current Period - Previous Period) ÷ Previous Period) × 100%
        ```
        
        **Practical Trend Example:**
        • Previous 5-week average: 10.2 items/week
        • Current 5-week average: 12.6 items/week
        • Calculation: ((12.6 - 10.2) ÷ 10.2) × 100% = +23.5% 
        • Interpretation: ↗️ **Positive acceleration** - team improving over time
        
        🎯 **Integration with PERT Forecasting:**
        • Average velocity = "Most Likely" scenario in three-point estimation
        • Provides statistical foundation for expected completion dates
        • Combined with optimistic/pessimistic bounds for full PERT analysis
        
        ⚙️ **When to Use Average vs Median:**
        • **Choose Average** for stable teams with consistent delivery patterns
        • **Choose Median** when dealing with frequent scope changes or capacity variations
        
        🔗 **Related Topics:**
        See also: Median Velocity Calculation, PERT Analysis Detailed, Velocity Trend Indicators
    """,
    "velocity_median_calculation": """
        Median Velocity calculation using middle value for outlier-resistant forecasting.
        
        🔢 **Formula:**
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
        
        📊 **Characteristics:**
        • **Outlier Resistance**: High - extreme values don't affect result
        • **Stability**: More stable than average when data has outliers
        • **Use Case**: Best for teams with variable delivery or scope changes
        • **Interpretation**: Represents "typical" week performance
        
        📈 **Advantage Over Average:**
        
        **Example with Outlier:**
        Weekly data: [2, 10, 12, 13, 48] items
        • Average: (2+10+12+13+48) ÷ 5 = 17 items/week
        • Median: 12 items/week (middle value)
        
        The median (12) better represents typical performance than average (17) 
        which is skewed by the outlier week of 48 items.
        
        🎯 **Forecasting Application:**
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
        
        🔢 **Calculation Formula:**
        Scope Change Rate = (Items Created ÷ Baseline Items) × 100%
        
        📊 **Example Calculation:**
        • Original baseline: 100 items
        • Items added during project: 25 items
        • Scope change rate: (25 ÷ 100) × 100% = 25%
        
        🎯 **Agile Context:**
        In agile projects, scope changes are normal and healthy, representing:
        • Discovery of new requirements
        • User feedback integration  
        • Market responsiveness
        • Learning and adaptation
        
        📈 **Healthy Ranges:**
        • 10-30%: Good adaptability without excessive thrash
        • 30-50%: High responsiveness, monitor for scope creep
        • >50%: Potential planning or requirements issues
    """,
    "adaptability_index": """
        Adaptability Index measures how well your team balances scope changes with delivery consistency.
        
        🔢 **Calculation Method:**
        Adaptability = 1 - (Standard Deviation of Weekly Scope Changes ÷ Mean Weekly Scope Changes)
        
        📊 **Interpretation Scale:**
        • 0.8-1.0: Highly adaptable (excellent scope management)
        • 0.5-0.8: Good adaptability (normal agile patterns)
        • 0.2-0.5: Moderate adaptability (some instability)
        • 0.0-0.2: Low adaptability (high scope volatility)
        
        🎯 **Agile Context:**
        Low values (0.2-0.5) are NORMAL for responsive agile teams!
        This indicates healthy adaptation to changing requirements.
        Very high values might suggest insufficient customer feedback or market responsiveness.
        
        💡 **Action Insights:**
        Use trends over time rather than absolute values for decision making.
    """,
    "throughput_ratio": """
        Throughput ratio compares the rate of new work creation to work completion.
        
        🔢 **Calculation Formula:**
        Throughput Ratio = Created Items ÷ Completed Items
        
        📊 **Ratio Interpretation:**
        • 1.0: Perfect balance (creating = completing)
        • <1.0: Burning down backlog (completing > creating)
        • >1.0: Growing backlog (creating > completing)
        
        🎯 **Healthy Patterns:**
        • Early project: >1.0 (discovery and planning phase)
        • Mid project: ~1.0 (steady state development)
        • Late project: <1.0 (completion and cleanup phase)
        
        📈 **Strategic Insights:**
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
        
        📅 **Weekly Data Collection:**
        • Collection Point: End of each work week (typically Friday)
        • Scope: Monday-Sunday work period for consistency
        • Frequency: Weekly snapshots for trend analysis
        
        🔢 **Data Fields Explained:**
        
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
        
        ✅ **Data Quality Checklist:**
        
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
        
        📊 **Impact on Forecasting:**
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
        
        📊 **Table Structure:**
        Each row represents one week of project activity with key metrics for forecasting.
        
        🔢 **Column Definitions:**
        
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
        
        📈 **Usage for Forecasting:**
        
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
        
        ⚠️ **Common Mistakes:**
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
        
        🎯 **Best Practices:**
        • Monitor actual progress against forecasted timelines
        • Track "how much work is left" to completion
        • Identify trends and potential delays early
        • Communicate project status to stakeholders
        
        📊 **Visual Elements:**
        • Solid lines: Historical actual data
        • Dashed lines: PERT forecast projections  
        • Dotted lines: Confidence intervals and uncertainty ranges
        • Vertical line: Current date marker
        • Scope change indicators: Show requirement additions/removals
    """,
    "pert_forecast_methodology": """
        PERT (Program Evaluation Review Technique) creates realistic forecasts using three-point estimation.
        
        🔢 **Three-Point Estimation Process:**
        1. **Optimistic Scenario**: Best-case timeline from peak velocity periods
        2. **Most Likely Scenario**: Realistic estimate from current average velocity
        3. **Pessimistic Scenario**: Worst-case timeline from lowest velocity periods
        4. **Expected Value**: Weighted calculation = (O + 4×ML + P) ÷ 6
        
        📊 **Mathematical Foundation:**
        • Follows beta distribution for project estimation
        • Weights most likely scenario 4x more than extremes
        • Provides statistically sound forecasts with confidence intervals
        • Accounts for both optimism bias and risk factors
        
        📈 **Confidence Intervals:**
        • Calculated as ±25% of variance between optimistic and pessimistic
        • Wider intervals indicate higher uncertainty
        • Narrower intervals suggest more predictable delivery patterns
        • Use for risk planning and stakeholder communication
        
        🎯 **Practical Application:**
        • Expected value: Primary planning target
        • Optimistic: Best-case scenario for resource planning
        • Pessimistic: Risk mitigation and buffer planning
        • Confidence bands: Communication of forecast uncertainty
        
        💡 **Accuracy Factors:**
        Forecast accuracy improves with:
        • More historical data points (8+ weeks recommended)
        • Consistent team composition and working arrangements
        • Stable definition of "done" and point estimation
        • Regular, complete data collection practices
    """,
    "weekly_chart_methodology": """
        Weekly velocity charts with predictive forecasting using weighted moving averages.
        
        📊 **Chart Components:**
        • Historical bars: Actual weekly completion rates
        • Forecast bars: Predicted next week performance using PERT methodology  
        • Trend lines: Moving average patterns for visual trend identification
        • Confidence intervals: Error bars showing forecast uncertainty ranges
        
        🔢 **Forecasting Methodology:**
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
        
        📈 **Visual Interpretation:**
        • Solid bars: Confirmed historical performance
        • Patterned bars: Forecasted performance with uncertainty
        • Error bars: Confidence intervals (±25% variance method)
        • Trend direction: Overall velocity acceleration or deceleration patterns
        
        🎯 **Usage Guidelines:**
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

# Combined comprehensive help content for easy access
COMPREHENSIVE_HELP_CONTENT = {
    "forecast": FORECAST_HELP_DETAILED,
    "velocity": VELOCITY_HELP_DETAILED,
    "scope": SCOPE_HELP_DETAILED,
    "statistics": STATISTICS_HELP_DETAILED,
    "charts": CHART_HELP_DETAILED,
    "bug_analysis": BUG_ANALYSIS_TOOLTIPS,
}
