"""Forecast and velocity help content.

Comprehensive help text for forecast methodology and velocity metrics.
"""

FORECAST_HELP_DETAILED = {
    "pert_methodology": """
        PERT (Program Evaluation and Review Technique) uses three-point estimation
        for probabilistic forecasting:
        
        [Stats] **Formula Components:**
        • Optimistic (O): Best-case scenario from top velocity periods
        • Most Likely (ML): Current average velocity from recent data
        • Pessimistic (P): Worst-case scenario from lowest velocity periods
        • Expected (E): Weighted average = (O + 4×ML + P) ÷ 6
        
        [Calc] **Mathematical Foundation:**
        The formula weights the Most Likely estimate 4x more heavily than
        extreme scenarios,
        following beta distribution principles for realistic project estimation.
        
        [Trend] **Confidence Intervals (Statistical Percentiles):**
        • 50% (Median): The PERT forecast itself - 50% chance of completion by this date
                • 80% (Good Confidence): PERT + 0.84 standard deviations - 80% chance
                    of completion
                • 95% (High Confidence): PERT + 1.65 standard deviations - 95% chance
                    of completion
        
        Wider ranges indicate higher velocity uncertainty; narrower ranges show
        more predictable delivery.
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
        
        [Note] **Interpretation:** Most reliable single-point forecast for
        project planning.
    """,
    "three_point_estimation": """
        Three-point estimation technique provides forecast ranges instead of
        single points.
        
        [Tip] **Mathematical Advantage:**
        Single estimates ignore uncertainty; ranges acknowledge project variability.
        
        [Trend] **Confidence Calculation:**
        Uncertainty bands calculated from variance between optimistic and
        pessimistic scenarios.
        Wider bands = higher uncertainty, narrower bands = more predictable outcomes.
        
        [Apply] **Practical Application:**
        Use ranges for risk planning, resource allocation, and stakeholder
        communication.
        The expected value provides planning target while ranges show risk boundaries.
    """,
    "project_overview": """
        Project Overview provides a comprehensive dashboard of your project's
        current state and progress metrics.
        
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
        Different completion rates for items vs points can indicate scope or
        estimation changes.
        
        [Note] **Interpretation Guide:**
        Items and points completion percentages may differ due to:
        • Variable item complexity (some items worth more points)
        • Scope changes affecting total estimates
        • Estimation refinements during development
    """,
    "forecast_graph_overview": """
        Interactive forecast visualization showing project completion timeline
        with uncertainty ranges.
        
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
        Comprehensive PERT (Program Evaluation and Review Technique) analysis
        using statistical forecasting.
        
        [Calc] **Three-Point Calculation Method:**
        
        **Data Collection Process:**
        • Optimistic (O): Average of top 25% velocity periods from your historical data
                • Most Likely (ML): Simple arithmetic mean of all recent data points
                    (typically 8-12 weeks)
                • Pessimistic (P): Average of bottom 25% velocity periods from your
                    historical data
        
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
                • **Beta Distribution**: Mathematically models project uncertainty
                    patterns naturally
                • **4× Most Likely Weighting**: Statistically optimal balance (proven
                    by decades of project data)
                • **Confidence Intervals**: Calculated using coefficient of variation
                    (CV = std/mean) applied to forecast
          - 50th percentile: The PERT forecast (median)
          - 80th percentile: PERT + 0.84 × forecast_std
          - 95th percentile: PERT + 1.65 × forecast_std
        
        [Link] **Related Topics:**
        See also: Weekly Velocity Calculation, Forecast Graph Overview,
        Input Parameters Guide
        
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
        Input Parameters control forecast calculations and scope definitions
        for your project.
        
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
        Weekly velocity represents your team's average completion rate
        calculated over the last 10 weeks of data.
        
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
        Percentage change = ((Current Period - Previous Period) ÷
        Previous Period) × 100%
        
        [Stats] **Visual Meanings:**
        • [UP] Green Up Arrow: >5% improvement (acceleration)
        • [DOWN] Red Down Arrow: >5% decline (deceleration)
        • [STABLE] Gray Stable: ±5% variation (consistent)
        
        [Note] **Interpretation Guide:**
        Consistent upward trends may indicate team learning or process improvements.
        Consistent downward trends may indicate technical debt, scope creep,
        or team changes.
        Stable trends indicate predictable delivery capacity.
    """,
    "data_quality_impact": """
        Data quality and quantity directly affect forecast accuracy and
        confidence levels.
        
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
        Average Velocity calculation using arithmetic mean for consistent
        baseline forecasting.
        
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
                • **Outlier Sensitivity**: Week 4 (18 items) and Week 3 (8 items)
                    both pull the average
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
                • **Choose Median** when dealing with frequent scope changes or
                    capacity variations
        
        [Link] **Related Topics:**
        See also: Median Velocity Calculation, PERT Analysis Detailed,
        Velocity Trend Indicators
    """,
    "velocity_median_calculation": """
        Median Velocity calculation using middle value for outlier-resistant
        forecasting.
        
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
    "scope_growth_methodology": """
        Scope Growth measures new work added vs baseline or completed work.
        
        [Calc] **Two Key Metrics:**
        1. Items Scope Growth = (Created ÷ Baseline) × 100%
        2. Scope Growth Rate = (Created ÷ Completed) × 100%
        
        [Stats] **Example:**
        • Baseline: 500 items, Created: 250, Completed: 200
        • Items Scope Growth: (250 ÷ 500) = 50% (baseline expansion)
        • Scope Growth Rate: (250 ÷ 200) = 125% (adding faster than completing)
        
        [Tip] **Agile Context:**
        Scope changes are normal in agile, representing discovery, feedback,
        and adaptation.
        
        [Trend] **Healthy Ranges:**
        • <20%: Stable scope
        • 20-50%: Active adaptation
        • >50%: High volatility, review planning
    """,
    "adaptability_index": """
        Adaptability Index measures how well your team balances scope changes
        with delivery consistency.
        
        [Calc] **Calculation Method:**
        Adaptability = 1 - (Standard Deviation of Weekly Scope Changes ÷
        Mean Weekly Scope Changes)
        
        [Stats] **Interpretation Scale:**
        • 0.8-1.0: Highly adaptable (excellent scope management)
        • 0.5-0.8: Good adaptability (normal agile patterns)
        • 0.2-0.5: Moderate adaptability (some instability)
        • 0.0-0.2: Low adaptability (high scope volatility)
        
        [Tip] **Agile Context:**
        Low values (0.2-0.5) are NORMAL for responsive agile teams!
        This indicates healthy adaptation to changing requirements.
        Very high values might suggest insufficient customer feedback or market
        responsiveness.
        
        [Note] **Action Insights:**
        Use trends over time rather than absolute values for decision making.
    """,
    "throughput_ratio": """
        Throughput Ratio compares work creation to completion rate.
        
        [Calc] **Formula:**
        Throughput Ratio = Created ÷ Completed
        
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
