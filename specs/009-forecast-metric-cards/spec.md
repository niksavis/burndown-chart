# Feature Specification: Forecast-Based Metric Cards

**Feature Branch**: `009-forecast-metric-cards`  
**Created**: November 10, 2025  
**Status**: Draft  
**Input**: User description: "Add 4-week weighted forecast benchmarks to Flow and DORA metric cards with trend indicators to provide meaningful context at week start and prevent misleading zero values"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Meaningful Metrics on Monday Morning (Priority: P1)

As a team lead reviewing metrics on Monday morning, I want to see forecast benchmarks on metric cards instead of misleading zero values, so I can understand our expected performance for the week even before any items are completed.

**Why this priority**: Solves the core problem of misleading zero values at week start. Provides immediate value by giving context to early-week metrics. This is the primary pain point driving this feature.

**Independent Test**: Can be fully tested by opening the dashboard on Monday morning and verifying that all Flow and DORA metric cards display a forecast benchmark (e.g., "Forecast: ~13 items/week") alongside the current week's value, even when current value is zero.

**Acceptance Scenarios**:

1. **Given** it is Monday morning with no completed items this week, **When** I view the Flow Velocity card, **Then** I see "0 items completed this week" with "Forecast: ~13 items/week" displayed below, providing context that work is expected
2. **Given** it is Monday morning, **When** I view any Flow or DORA metric card, **Then** I see a forecast value calculated from the last 4 weeks of historical data
3. **Given** it is Monday with zero current metrics, **When** I check the performance badges, **Then** they reflect last week's performance rather than showing misleading "Poor" badges based on current zeros

---

### User Story 2 - Track Progress Against Forecast Mid-Week (Priority: P1)

As a team member checking progress on Tuesday or Wednesday, I want to see trend indicators showing whether we're on track, above, or below our forecast, so I can quickly assess if we need to adjust our approach for the week.

**Why this priority**: Provides actionable insights throughout the week. Enables early course correction if team is falling behind. Core value proposition of the feature.

**Independent Test**: Can be fully tested by completing some items mid-week and verifying that the forecast comparison shows directional trend arrows (↗ → ↘) and percentage deviation (e.g., "↘ -62% vs forecast" when behind, or "↗ +23% above forecast" when ahead).

**Acceptance Scenarios**:

1. **Given** it is Tuesday with 3 items completed and forecast is 13 items/week, **When** I view the Flow Velocity card, **Then** I see "3 items completed this week" with "↘ -77% vs forecast" indicating we're behind pace
2. **Given** it is Wednesday with 16 items completed and forecast is 13 items/week, **When** I view the Flow Velocity card, **Then** I see "16 items completed" with "↗ +23% above forecast" indicating we're exceeding expectations
3. **Given** current metric value is within ±10% of forecast, **When** viewing the trend indicator, **Then** I see a neutral arrow (→) with "On track" status
4. **Given** it is mid-week, **When** I view the Flow Load (WIP) card, **Then** I see a forecast range (e.g., "~15 items (12-18)") rather than a point estimate, since WIP can be too high or too low

---

### User Story 3 - Review Historical Performance Against Forecast (Priority: P2)

As a team lead reviewing past weeks, I want to see how our completed weeks performed against their forecasts, so I can identify trends in our predictability and performance consistency.

**Why this priority**: Enables retrospective analysis and continuous improvement. Helps teams understand their reliability and forecast accuracy over time. Secondary to real-time tracking but valuable for long-term insights.

**Independent Test**: Can be fully tested by selecting a completed historical week and verifying that the metric cards show both the actual achieved value and the forecast that was calculated for that week, with trend indicators showing the deviation.

**Acceptance Scenarios**:

1. **Given** I select Week 2025-W45 (a completed week with 18 items), **When** I view the Flow Velocity card, **Then** I see "18 items completed/week" with "Forecast: ~13 items/week" and "↗ +38% above forecast"
2. **Given** I'm viewing a historical week, **When** I check the performance badge, **Then** it shows the achieved performance tier (Elite/High/Medium/Low) based on actual results, not forecast
3. **Given** a historical week where we underperformed the forecast, **When** viewing the card, **Then** I see the actual value with a downward trend (↘) and percentage below forecast

---

### User Story 4 - Understand WIP Health with Forecast Ranges (Priority: P2)

As a team lead monitoring work in progress, I want to see if current WIP is within a healthy forecast range, so I can identify potential bottlenecks (too high) or underutilization (too low).

**Why this priority**: Flow Load requires special handling (range vs point estimate) because WIP can be problematic in both directions. Important for flow health but secondary to velocity tracking.

**Independent Test**: Can be fully tested by viewing the Flow Load card and verifying it displays a forecast range with upper and lower bounds (e.g., "~15 items (12-18)") and indicates whether current WIP is within, above, or below the healthy range.

**Acceptance Scenarios**:

1. **Given** current WIP is 24 items and forecast range is 12-18 items, **When** I view Flow Load card, **Then** I see "24 items work in progress" with "Forecast: ~15 items (12-18)" and "↗ +60% above normal" with warning styling
2. **Given** current WIP is 14 items and forecast range is 12-18 items, **When** I view Flow Load card, **Then** I see "→ Within normal range ✓" with positive styling
3. **Given** current WIP is 9 items and forecast range is 12-18 items, **When** I view Flow Load card, **Then** I see "↘ -40% below normal" with informational styling suggesting possible underutilization

---

### User Story 5 - Build Baseline During First Weeks (Priority: P3)

As a new team starting to track metrics, I want to see forecast information even when I have less than 4 weeks of historical data, so I can start benefiting from the feature immediately with appropriate caveats.

**Why this priority**: Edge case handling for new teams. Less critical than core functionality but important for good user experience during onboarding. Can be implemented with simple equal-weight averaging.

**Independent Test**: Can be fully tested by starting with a fresh metrics dataset containing only 2-3 weeks of data and verifying that forecasts are shown with a note like "based on 2 weeks" and "Building baseline..." to set appropriate expectations.

**Acceptance Scenarios**:

1. **Given** only 2 weeks of historical data exist, **When** viewing metric cards, **Then** I see forecasts calculated using equal weighting of available weeks with a note "Forecast: ~10 items (based on 2 weeks)"
2. **Given** fewer than 4 weeks of data, **When** viewing any metric card, **Then** I see an informational message "🆕 Building forecast baseline..." indicating the forecast will improve with more data
3. **Given** only 1 week of historical data exists, **When** viewing metric cards, **Then** no forecast is shown, only a message "Insufficient data for forecast"

---

### Edge Cases

- What happens when historical weeks contain zero or null values (e.g., holiday weeks, data gaps)?
  - Filter out invalid weeks before calculating forecast
  - If fewer than 2 valid weeks remain, show "Insufficient data for forecast"
  
- How does the system handle extreme outlier weeks in historical data?
  - Weighted average naturally dampens outliers (most recent week has 40% weight, oldest has 10%)
  - No additional outlier capping needed - weighted average provides sufficient smoothing
  
- What if the current week value is exactly at forecast?
  - Show neutral trend arrow (→) with "On track" status
  - Color: secondary/gray rather than success/danger
  
- What if a metric has no unit (e.g., Flow Efficiency is a percentage)?
  - Forecast displays with appropriate unit: "Forecast: ~45%" for percentages
  - Trend comparison uses same unit: "↗ +10 percentage points above forecast"
  
- What if forecast calculation would result in negative values (e.g., for time-based metrics)?
  - Forecast is clamped to minimum of 0
  - Very low forecasts trigger review of historical data quality

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST display forecast benchmarks on all 9 metric cards (4 DORA: Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Recovery; 5 Flow: Flow Velocity, Flow Time, Flow Efficiency, Flow Load, Flow Distribution)
- **FR-002**: System MUST calculate forecasts using 4-week weighted average with weights: 40% (most recent), 30% (2 weeks ago), 20% (3 weeks ago), 10% (4 weeks ago)
- **FR-003**: System MUST display trend indicators (↗ → ↘) comparing current value to forecast on all metric cards
- **FR-004**: System MUST display percentage deviation from forecast (e.g., "+23% above forecast", "-62% vs forecast")
- **FR-005**: System MUST use ±10% threshold for determining trend direction (↗ if >+10%, ↘ if <-10%, → if within ±10%)
- **FR-006**: System MUST display Flow Load forecast as a range (±20%) rather than a point estimate (e.g., "~15 items (12-18)")
- **FR-007**: System MUST color-code forecast trend indicators: green for good (↗ for higher-better metrics, ↘ for lower-better metrics), red for bad, gray for neutral
- **FR-008**: System MUST handle metrics where lower is better (Flow Time, Lead Time, CFR, MTTR) by inverting trend interpretation
- **FR-009**: System MUST filter out null or zero values from historical weeks before calculating forecast. If fewer than 2 valid weeks remain after filtering, return None and display "Insufficient data for forecast"
- **FR-010**: System MUST display appropriate message when fewer than 4 weeks of historical data exist (e.g., "based on 2 weeks", "Building baseline...")
- **FR-011**: System MUST NOT show forecast when fewer than 2 valid historical weeks exist, displaying "Insufficient data for forecast" instead
- **FR-012**: System MUST display forecast information within existing card body structure without changing card header or layout
- **FR-013**: System MUST maintain mobile responsiveness with forecast information visible on screens as small as 320px width
- **FR-014**: System MUST use existing CSS classes and styling patterns (text-center, text-muted, small, mb-1/mb-2) for forecast display
- **FR-015**: System MUST show forecast with appropriate units matching the metric (see Unit Mapping below)
- **FR-016**: System MUST persist forecast data in weekly metric snapshots for historical analysis
- **FR-017**: System MUST maintain backward compatibility with existing metric snapshots that do not contain forecast data
- **FR-018**: Current week cards MUST display last completed week's performance badge rather than badges based on current zeros

**Unit Mapping**:
- Flow Velocity: items/week
- Flow Time: hours or days (based on magnitude)
- Flow Efficiency: % (percentage points)
- Flow Load: items (with range format: "12-18 items")
- Flow Distribution: % (percentage breakdown by type)
- Deployment Frequency: deploys/month or deploys/week
- Lead Time for Changes: hours or days
- Change Failure Rate: %
- Mean Time to Recovery: hours

### Key Entities

- **Forecast Data**: Contains weighted forecast value, historical values used in calculation, weights applied, number of weeks used, and forecast range (for Flow Load)
- **Trend Indicator**: Contains direction arrow (↗ → ↘), percentage deviation from forecast, status text, and color classification (success/danger/secondary)
- **Metric Snapshot**: Enhanced with forecast data field containing forecast value, historical basis, and trend information for each metric type

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Team leads can view meaningful forecast context on Monday morning within 2 seconds of opening the dashboard, even when current week values are zero
- **SC-002**: 100% of Flow and DORA metric cards (9 metrics total) display forecast benchmarks when at least 2 weeks of historical data exist
- **SC-003**: Users can determine if current performance is on track (within ±10% of forecast) by viewing trend indicators without manual calculation
- **SC-004**: Metric cards remain readable and functional on mobile devices (320px width) with forecast information displayed
- **SC-005**: Forecast calculation completes within 100ms per metric to avoid impacting dashboard load time
- **SC-006**: Historical week reviews show forecast accuracy, enabling teams to measure forecast reliability over 4+ weeks
- **SC-007**: Flow Load card correctly identifies WIP health status (within range, above, below) 100% of the time when WIP deviates beyond ±20%
- **SC-008**: Zero misleading "Poor" or "Warning" badges appear on Monday morning based on current zeros (badges reflect previous week's actual performance)
- **SC-009**: Forecast data is persisted in snapshots, enabling historical analysis of forecast accuracy without recalculation

### User Experience Outcomes

- **SC-010**: Users report understanding week progress without waiting until Wednesday/Thursday for meaningful metrics
- **SC-011**: Teams can identify underperformance or overperformance trends earlier in the week, enabling course correction
- **SC-012**: New teams with 2-3 weeks of data can still benefit from preliminary forecasts with appropriate baseline-building messaging

## Assumptions

1. **Historical data quality**: Assumes at least 2 weeks of valid historical metrics exist for forecast calculation. Teams with no history will see "Insufficient data" messages.

2. **4-week window consistency**: Assumes 4 weeks is appropriate across all metric types. This matches existing app patterns (velocity charts, bug trends, PERT forecasting).

3. **Weighted average suitability**: Assumes 40/30/20/10 weighting pattern effectively balances recent trends vs historical stability for all metric types.

4. **±10% threshold for trends**: Assumes ±10% deviation is the right threshold for "on track" status across all metrics. May need tuning based on metric-specific variance.

5. **±20% WIP range**: Assumes ±20% deviation defines healthy WIP range for Flow Load. Based on industry flow metrics practices but may need customer-specific tuning.

6. **Snapshot storage capacity**: Assumes adding forecast data to metric snapshots (additional ~200 bytes per metric per week) does not create storage concerns.

7. **Performance impact**: Assumes weighted average calculation overhead (<100ms per metric) is acceptable for dashboard load time.

8. **User interpretation**: Assumes users can interpret directional arrows (↗ → ↘) and percentage deviations without additional training or documentation.

9. **Badge logic**: Assumes using last week's performance badge for current week is less confusing than showing forecast-based badges or zero-based badges.

10. **Metric interpretation**: Assumes users understand which metrics are "higher is better" (velocity, deployment frequency) vs "lower is better" (lead time, MTTR, CFR).

## Dependencies

1. **Existing metric snapshot system**: Feature depends on metrics_snapshots.json structure and weekly metric calculation workflow (calculate_and_save_weekly_metrics)

2. **4-week historical data**: Forecast quality depends on having at least 4 weeks of valid historical metrics. Feature degrades gracefully with fewer weeks.

3. **Metric card UI structure**: Feature must work within existing CardHeader/CardBody/Collapse structure without breaking mobile layout

4. **Weekly metric calculation timing**: Assumes weekly metrics are calculated reliably and snapshots are up-to-date when users view dashboard

5. **Existing CSS framework**: Feature depends on Bootstrap classes (text-center, text-muted, small, text-success/danger/secondary) for styling consistency

## Out of Scope

The following are explicitly NOT part of this feature:

1. **Day-of-week pro-rating**: No "expected by Tuesday" calculations. Only weekly forecasts shown.

2. **Confidence intervals**: No statistical uncertainty ranges or confidence levels displayed with forecasts.

3. **Seasonal adjustments**: No automatic detection or handling of holidays, vacations, or seasonal patterns.

4. **Team size normalization**: No adjustment of forecasts when team size changes.

5. **Smart alerts**: No automatic notifications when metrics deviate significantly from forecast.

6. **Historical forecast accuracy tracking**: No automatic measurement of how accurate past forecasts were (though data is available for manual analysis).

7. **Cross-metric insights**: No automatic correlation analysis (e.g., "high WIP correlates with longer Flow Time").

8. **Configurable weights**: Weights remain fixed at 40/30/20/10. No user configuration of weighting scheme.

9. **Configurable thresholds**: Trend thresholds (±10%) and WIP range (±20%) are fixed. No user configuration in this version.

10. **Custom forecast periods**: Only 4-week forecasts supported. No 2-week, 8-week, or custom period options.

## Technical Constraints

1. **Maintain existing card structure**: Forecast elements must fit within current CardBody without changes to CardHeader or overall layout

2. **Mobile responsiveness**: Cards must remain functional on screens as small as 320px width (iPhone SE)

3. **Performance budget**: Forecast calculation must complete in under 100ms per metric to avoid impacting dashboard load time

4. **CSS constraint**: Must use only existing CSS classes, no new stylesheets or custom classes

5. **Backward compatibility**: Must handle existing metric snapshots without forecast data gracefully

6. **Maximum 6-7 lines in CardBody**: Forecast information must not make cards too tall or cause excessive scrolling on mobile

7. **Font size consistency**: Forecast text must use ~0.85rem to match existing trend indicators and maintain readability

## Risk Assessment

### Low Risk
- Calculation errors in weighted average (simple math, easily testable)
- CSS/styling inconsistencies (can be visually verified)
- Historical data retrieval (existing snapshot system is stable)

### Medium Risk
- Mobile layout breaking with additional card content (requires thorough responsive testing across devices)
- User confusion about forecast interpretation (can be mitigated with clear labeling and help tooltips)
- Performance impact on dashboard load time (weighted average is lightweight but needs measurement)

### High Risk
- Misleading forecasts during atypical weeks (holidays, major disruptions) - weighted average helps but doesn't eliminate this risk. May require future seasonal adjustment features.
- Snapshot storage growth over time - adding ~200 bytes per metric per week compounds over 52 weeks. Current scale (9 metrics) = ~94KB per year, acceptable but should be monitored.

## Success Metrics (Post-Implementation)

After implementation, success will be measured by:

1. **User engagement**: Time spent on dashboard on Mondays increases (users find Monday metrics meaningful)
2. **Early-week course correction**: Teams make mid-week adjustments more frequently when behind forecast
3. **Forecast accuracy**: Historical analysis shows forecasts within ±20% of actual values at least 70% of the time
4. **Badge confusion reduction**: Zero user reports of "misleading zero/poor badges on Monday"
5. **Mobile usage**: No increase in mobile bounce rate or decrease in mobile session duration
6. **Performance**: Dashboard load time remains under 2 seconds with forecast calculations included

## Reference Materials

### Industry Standards and Best Practices

This feature is designed to align with established industry practices for DORA and Flow metrics:

1. **DORA Metrics - Four Keys**  
   **URL**: https://dora.dev/guides/dora-metrics-four-keys/  
   **Purpose**: Official DORA guide defining the four key metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Recovery). Use this to verify metric definitions, thresholds for Elite/High/Medium/Low performance tiers, and best practices for measurement.  
   **Relevance to Feature**: Ensures our forecast calculations and trend indicators align with DORA's intended use of these metrics for software delivery performance.

2. **Flow Framework - Discover Phase**  
   **URL**: https://flowframework.org/ffc-discover/  
   **Purpose**: Flow Framework documentation covering Flow Velocity, Flow Time, Flow Efficiency, Flow Load, and Flow Distribution metrics. Provides context on how these metrics work together to measure value stream health.  
   **Relevance to Feature**: Validates our approach to Flow Load (WIP) using ranges instead of point estimates, and confirms the importance of tracking these metrics weekly for team predictability.

3. **2025 State of AI-Assisted Software Development**  
   **URL**: https://services.google.com/fh/files/misc/2025_state_of_ai_assisted_software_development.pdf  
   **Purpose**: Google research on software delivery performance (see especially the beginning sections before AI discussion). Contains statistical analysis of DORA metrics across thousands of teams, showing distribution patterns and performance correlations.  
   **Relevance to Feature**: Provides empirical data on metric variability and typical week-to-week fluctuations, supporting our choice of ±10% threshold for "on track" status and ±20% range for healthy WIP levels.

### How to Use These References

**During Implementation**:
- Verify metric units and terminology match industry standards
- Confirm performance tier thresholds (Elite/High/Medium/Low) align with DORA benchmarks
- Validate that Flow Load range calculation (±20%) reflects typical WIP variance observed in research

**During Validation**:
- Compare forecast accuracy against industry norms for week-to-week metric stability
- Ensure trend indicators reflect whether teams are moving toward Elite performance
- Test that edge cases (outliers, holidays) are handled consistently with Flow Framework guidance

**For User Communication**:
- Link to these resources in help documentation to explain why specific thresholds are used
- Use industry terminology consistently (e.g., "Lead Time for Changes" not "deployment lead time")
- Reference benchmark data when setting team expectations for forecast accuracy
