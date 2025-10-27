# Feature Specification: DORA and Flow Metrics Dashboard

**Feature Branch**: `007-dora-flow-metrics`  
**Created**: October 27, 2025  
**Status**: Draft  
**Input**: User description: "Include DORA and Flow metrics page to the app with configurable Jira custom field mapping"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View DORA Metrics Dashboard (Priority: P1)

As a DevOps manager, I want to view my team's DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, and Mean Time to Recovery) so that I can assess our software delivery performance and identify areas for improvement.

**Why this priority**: DORA metrics are industry-standard KPIs for DevOps performance. This is the core value proposition of the feature and delivers immediate business insight.

**Independent Test**: Can be fully tested by navigating to the DORA metrics tab, viewing pre-calculated metrics from sample Jira data, and verifying that all four DORA metrics display with appropriate visualizations and performance tier indicators (Elite/High/Medium/Low).

**Acceptance Scenarios**:

1. **Given** I have Jira data with deployment and incident issues, **When** I navigate to the DORA Metrics tab, **Then** I see four metric cards displaying Deployment Frequency, Lead Time for Changes, Change Failure Rate, and MTTR with current values and trend indicators
2. **Given** I am viewing DORA metrics, **When** the metrics are calculated, **Then** each metric displays its performance tier (Elite/High/Medium/Low) with color coding (green/yellow/orange/red)
3. **Given** I am viewing DORA metrics, **When** I hover over a metric card, **Then** I see a tooltip explaining the metric definition and how it's calculated
4. **Given** insufficient data exists for a metric, **When** I view the DORA dashboard, **Then** I see a clear message indicating "Insufficient data to calculate [metric name]" with guidance on required Jira fields

---

### User Story 2 - View Flow Metrics Dashboard (Priority: P2)

As a project manager, I want to view Flow metrics (Velocity, Time, Efficiency, Load, Distribution) so that I can understand how work flows through my team's process and identify bottlenecks.

**Why this priority**: Flow metrics provide complementary insights to DORA metrics, focusing on process efficiency and value delivery. Essential for process optimization but secondary to DORA metrics.

**Independent Test**: Can be fully tested by navigating to the Flow Metrics tab and viewing calculated metrics from Jira issues, including work item distribution charts and flow efficiency trends.

**Acceptance Scenarios**:

1. **Given** I have Jira data with completed work items, **When** I navigate to the Flow Metrics tab, **Then** I see metric cards for Flow Velocity, Flow Time, Flow Efficiency, Flow Load, and Flow Distribution
2. **Given** I am viewing Flow Distribution, **When** the data is loaded, **Then** I see a pie chart showing the percentage breakdown of Features, Defects, Risks, and Technical Debt with recommended ranges indicated
3. **Given** I am viewing Flow Efficiency, **When** the metric displays, **Then** I see the percentage of active work time vs total time with a trend chart over the selected time period
4. **Given** I am viewing Flow Load, **When** the data loads, **Then** I see the current work-in-progress count with a historical trend line and capacity indicators

---

### User Story 3 - Configure Jira Field Mappings (Priority: P1)

As a system administrator, I want to configure how Jira custom fields map to the internal fields required for DORA and Flow metrics so that the application works with my organization's specific Jira configuration.

**Why this priority**: This is critical infrastructure that enables the feature to work across different Jira configurations. Without this, the feature is non-functional for most organizations. Elevated to P1 because it's a prerequisite for metrics calculation.

**Independent Test**: Can be fully tested by opening the field mapping configuration interface, mapping sample Jira fields to required metric fields, saving the configuration, and verifying that metrics recalculate using the new mappings.

**Acceptance Scenarios**:

1. **Given** I am on the DORA/Flow Metrics tab, **When** I click "Configure Field Mappings", **Then** I see a modal displaying all required field mappings organized by metric type (DORA vs Flow)
2. **Given** I am in the field mapping configuration, **When** I view a required field (e.g., "Deployment Date"), **Then** I see a dropdown populated with available Jira custom fields from my connected Jira instance
3. **Given** I have selected mappings for required fields, **When** I click "Save Configuration", **Then** the mappings are persisted and metrics recalculate automatically using the new field mappings
4. **Given** I am configuring field mappings, **When** I select a field with an incompatible type (e.g., text field for a date field), **Then** I see a validation error indicating the type mismatch
5. **Given** I have unmapped required fields, **When** I attempt to save configuration, **Then** I see a warning listing which fields are unmapped and which metrics cannot be calculated without them

---

### User Story 4 - Select Time Period for Metrics (Priority: P2)

As a user viewing metrics, I want to select different time periods (last 7 days, 30 days, 90 days, custom range) so that I can analyze trends and compare performance across different timeframes.

**Why this priority**: Time period selection enables trend analysis and historical comparison, which are important for understanding metric trends but not essential for initial value delivery.

**Independent Test**: Can be fully tested by selecting different time periods from a dropdown, verifying that all metrics recalculate for the selected period, and checking that trend charts adjust appropriately.

**Acceptance Scenarios**:

1. **Given** I am viewing DORA or Flow metrics, **When** I select "Last 30 days" from the time period selector, **Then** all metrics recalculate to show data for the past 30 days only
2. **Given** I select a custom date range, **When** I apply the range, **Then** metrics display for exactly that period with the date range shown clearly in the dashboard header
3. **Given** I change the time period, **When** insufficient data exists for the new period, **Then** I see appropriate "insufficient data" messages for affected metrics

---

### User Story 5 - View Metric Trends Over Time (Priority: P3)

As a manager, I want to see trend charts for each metric over time so that I can identify improvements or degradations in team performance.

**Why this priority**: Trend visualization adds analytical depth but is not essential for basic metric viewing. Can be implemented after core metrics display works.

**Independent Test**: Can be fully tested by viewing a metric card, clicking "Show Trend", and verifying that a line chart displays the metric's value over the selected time period with week-over-week or month-over-month data points.

**Acceptance Scenarios**:

1. **Given** I am viewing a DORA metric, **When** I click "Show Trend" on a metric card, **Then** I see a line chart showing the metric's value over time with data points for each week
2. **Given** I am viewing a trend chart, **When** I hover over a data point, **Then** I see the exact value for that time period and the date range it represents
3. **Given** I am viewing Flow Distribution trends, **When** the chart renders, **Then** I see a stacked area chart showing how the distribution of work types has changed over time

---

### User Story 6 - Export Metrics Data (Priority: P3)

As a stakeholder, I want to export metrics data to CSV or JSON format so that I can include it in reports or analyze it with external tools.

**Why this priority**: Export functionality is valuable for reporting and external analysis but not essential for core metric viewing. Nice-to-have feature.

**Independent Test**: Can be fully tested by clicking an "Export" button, selecting a format (CSV/JSON), and verifying that a file downloads with all current metric values and metadata.

**Acceptance Scenarios**:

1. **Given** I am viewing metrics, **When** I click "Export Data" and select CSV format, **Then** a CSV file downloads containing all current metric values with timestamps and configuration metadata
2. **Given** I export metrics, **When** I open the exported file, **Then** I see column headers clearly labeled and data formatted appropriately for the selected format

---

### Edge Cases

- What happens when Jira fields are mapped but no data exists in those fields for the selected time period? **System displays "No data available" with guidance on which Jira fields need to be populated**
- How does the system handle Jira instances where required custom fields don't exist? **Configuration UI warns user which fields are missing and provides instructions for creating them in Jira**
- What happens when a user changes field mappings while viewing metrics? **System prompts to recalculate metrics and shows a loading state during recalculation**
- How does the system handle very large datasets (e.g., 10,000+ issues)? **System implements pagination and client-side aggregation to maintain performance; shows progress indicator during long calculations**
- What happens when Jira API rate limits are reached during metric calculation? **System displays rate limit warning, caches partial results, and provides option to retry or wait**
- How are metrics calculated when issues have incomplete data (e.g., missing resolution date)? **System excludes incomplete issues from calculations and displays count of excluded items with explanation**
- What happens when a user's Jira permissions don't allow access to required fields? **System displays permission error with specific field names that are inaccessible**

## Requirements *(mandatory)*

### Functional Requirements

#### Metrics Display Requirements

- **FR-001**: System MUST display all four DORA metrics (Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Recovery) with current values, performance tier indicators (Elite/High/Medium/Low), and color coding
- **FR-002**: System MUST display all five Flow metrics (Velocity, Time, Efficiency, Load, Distribution) with current values and trend indicators
- **FR-003**: System MUST provide performance tier benchmarking for each DORA metric based on industry standards (Elite: < 1 hour lead time, High: 1 day - 1 week, Medium: 1 week - 1 month, Low: > 1 month)
- **FR-004**: System MUST display Flow Distribution as a pie chart showing percentage breakdown of Features, Defects, Risks, and Technical Debt
- **FR-005**: System MUST show recommended distribution ranges for Flow Distribution (Features: 40-50%, Defects: 15-25%, Risks: 10-15%, Debt: 20-25%)

#### Field Mapping Requirements

- **FR-006**: System MUST provide a configuration interface for mapping Jira custom fields to internal metric calculation fields
- **FR-007**: System MUST fetch and display available custom fields from the connected Jira instance via REST API
- **FR-008**: System MUST validate that mapped Jira fields are compatible with required internal field types (DateTime maps to DateTime, Number maps to Number, etc.)
- **FR-009**: System MUST persist field mapping configuration in application settings (app_settings.json)
- **FR-010**: System MUST support mapping configurations for the following DORA fields: Deployment_Date, Target_Environment, Code_Commit_Date, Deployed_to_Production_Date, Incident_Detected_At, Incident_Resolved_At, Deployment_Successful, Production_Impact
- **FR-011**: System MUST support mapping configurations for the following Flow fields: Flow_Item_Type, Work_Started_Date, Work_Completed_Date, Status_Entry_Timestamp, Active_Work_Hours, Flow_Time_Days
- **FR-012**: System MUST allow users to mark certain mappings as "optional" when the corresponding Jira field doesn't exist
- **FR-013**: System MUST warn users which metrics cannot be calculated when required field mappings are missing

#### Data Processing Requirements

- **FR-014**: System MUST calculate Deployment Frequency as: Count(Deployments to Production) / Time Period
- **FR-015**: System MUST calculate Lead Time for Changes as: Average(Deployed_to_Production_Date - Code_Commit_Date) for all completed deployments
- **FR-016**: System MUST calculate Change Failure Rate as: Count(Failed Deployments) / Count(Total Deployments) × 100
- **FR-017**: System MUST calculate MTTR as: Average(Incident_Resolved_At - Incident_Detected_At) for all resolved incidents
- **FR-018**: System MUST calculate Flow Velocity as: Count(Completed Work Items) / Time Period, segmented by work type
- **FR-019**: System MUST calculate Flow Time as: Average(Work_Completed_Date - Work_Started_Date) for all completed items
- **FR-020**: System MUST calculate Flow Efficiency as: (Active Working Time / Total Flow Time) × 100
- **FR-021**: System MUST calculate Flow Load as: Count(Issues with active status) at the current point in time
- **FR-022**: System MUST calculate Flow Distribution as: Percentage breakdown of work types based on Flow_Item_Type field values

#### User Interface Requirements

- **FR-023**: System MUST add a new top-level navigation tab labeled "DORA & Flow Metrics"
- **FR-024**: System MUST organize the metrics page into two collapsible sections: "DORA Metrics" and "Flow Metrics"
- **FR-025**: System MUST provide a time period selector with options: Last 7 days, Last 30 days, Last 90 days, Custom Range
- **FR-026**: System MUST display metric cards in a responsive grid layout (2 columns on desktop, 1 column on mobile)
- **FR-027**: System MUST show loading indicators during metric calculation
- **FR-028**: System MUST display helpful tooltips for each metric explaining its definition and calculation method
- **FR-029**: System MUST provide a "Configure Field Mappings" button prominently displayed at the top of the metrics page

#### Data Caching Requirements

- **FR-030**: System MUST cache calculated metrics for the selected time period with a TTL (time-to-live) of 1 hour
- **FR-031**: System MUST invalidate metric cache when field mappings are changed
- **FR-032**: System MUST provide a "Refresh Metrics" button to manually trigger recalculation

### Key Entities *(mandatory)*

- **DORA Metric Configuration**: Stores field mappings for DORA metrics including Deployment_Date, Code_Commit_Date, Deployed_to_Production_Date, Incident_Detected_At, Incident_Resolved_At, Deployment_Successful, Production_Impact, Target_Environment
- **Flow Metric Configuration**: Stores field mappings for Flow metrics including Flow_Item_Type, Work_Started_Date, Work_Completed_Date, Status_Entry_Timestamp, Active_Work_Hours, Flow_Time_Days
- **Metric Value**: Represents a calculated metric with attributes: metric_name, metric_type (DORA/Flow), value, unit, performance_tier, calculation_timestamp, time_period_start, time_period_end
- **Field Mapping**: Associates a Jira custom field (custom field ID, field name, field type) with an internal metric field name; includes validation status
- **Jira Custom Field**: Represents available fields from Jira instance with attributes: field_id, field_name, field_type (datetime/number/text/select), is_custom
- **Metric Cache Entry**: Stores cached metric values with time period, field mapping hash, calculation timestamp, and TTL expiration

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can view all four DORA metrics within 5 seconds of navigating to the DORA & Flow Metrics tab (assuming cached data or < 1000 Jira issues)
- **SC-002**: Users can successfully configure field mappings for their Jira instance and see metrics recalculate within 10 seconds
- **SC-003**: System correctly categorizes DORA metric performance into Elite/High/Medium/Low tiers based on industry benchmarks with 100% accuracy
- **SC-004**: Flow Distribution calculations match expected percentages within 1% margin of error when validated against manual calculations
- **SC-005**: 95% of users can complete field mapping configuration without consulting documentation or support
- **SC-006**: Metric calculations complete successfully for datasets containing up to 5,000 Jira issues within 15 seconds
- **SC-007**: System handles missing or incomplete Jira data gracefully, displaying clear messages for 100% of edge cases without crashes or errors
- **SC-008**: Users can switch between different time periods and see metrics update within 3 seconds
- **SC-009**: Exported metric data contains all required fields and matches displayed values with 100% accuracy
- **SC-010**: Mobile users can view and interact with all metrics functionality without horizontal scrolling or layout issues

## Assumptions

1. **Jira API Access**: Users have already configured Jira API credentials and have access to custom fields via the Jira REST API
2. **Jira Field Types**: Jira administrators have created or will create appropriate custom fields with correct types (DateTime for date fields, Number for numeric fields, Select for categorical fields)
3. **Work Item Categorization**: Organizations using this feature will categorize their work items into Features, Defects, Risks, and Technical Debt (either via Jira issue types or custom fields)
4. **Deployment Tracking**: Organizations track deployments either through Jira releases, dedicated deployment issue types, or custom fields
5. **Incident Tracking**: Organizations track production incidents in Jira with appropriate timestamps for detection and resolution
6. **Reasonable Data Volume**: Typical usage involves querying 100-5,000 Jira issues per time period; extreme volumes (>10,000 issues) may require performance optimization
7. **Browser Compatibility**: Users access the application via modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)
8. **Existing Architecture**: The feature integrates with existing Jira caching mechanisms (jira_cache.json) and settings persistence (app_settings.json)
9. **Default Mappings**: If users don't configure mappings, system attempts to use common Jira field names (e.g., "customfield_10002" for story points) but displays warnings for unmapped fields
10. **Metric Definitions**: Industry-standard DORA and Flow metric definitions are used as documented in the DORA_Flow_Jira_Mapping.md reference document

## Dependencies

- **Jira REST API**: Requires GET /rest/api/3/issues/search, GET /rest/api/3/issues/{key}?expand=changelog, GET /rest/api/3/field endpoints
- **Existing Jira Integration**: Depends on current Jira authentication and data fetching mechanisms in data/jira_simple.py
- **Settings Persistence**: Depends on existing configuration storage in data/persistence.py and app_settings.json
- **Charting Library**: Depends on Plotly library for trend charts and distribution visualizations
- **UI Framework**: Depends on Dash Bootstrap Components for responsive layout and modal dialogs

## Out of Scope

- **Automated Field Detection**: System will NOT automatically detect which Jira fields should be used for metrics; users must manually configure mappings
- **Jira Custom Field Creation**: System will NOT create custom fields in Jira; users must create required fields via Jira admin interface
- **Real-Time Metrics**: Metrics are calculated on-demand or from cache; system does NOT provide real-time streaming updates
- **Multi-Project Aggregation**: Initial version calculates metrics for a single Jira project; cross-project aggregation is out of scope
- **Predictive Analytics**: System displays historical and current metrics but does NOT provide forecasting or predictive capabilities
- **Third-Party Integrations**: System does NOT integrate with CI/CD tools (Jenkins, GitLab, GitHub Actions) for deployment data; all data must come from Jira
- **Custom Metric Definitions**: Users cannot define custom metrics beyond the standard DORA and Flow metrics
- **Advanced Filtering**: Metrics are calculated for all issues in the selected time period; advanced filtering by team, component, or label is out of scope
- **Alerting/Notifications**: System does NOT send alerts when metrics cross thresholds or degrade
- **Historical Trend Analysis**: While trend charts are included (P3), advanced statistical analysis (moving averages, anomaly detection) is out of scope
