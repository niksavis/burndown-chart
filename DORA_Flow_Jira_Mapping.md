# DORA and Flow Metrics: Detailed Description and Jira REST API Mapping Guide

## Overview

This guide provides a comprehensive description of DORA and Flow metrics with practical guidance on how to extract and calculate them from Jira using the REST API, including recommendations for custom fields.

---

## Part 1: DORA Metrics

DORA (DevOps Research and Assessment) metrics comprise four key performance indicators measuring software delivery performance. They are split into two categories: **Velocity metrics** (speed of delivery) and **Stability metrics** (reliability of delivery).

### 1. Deployment Frequency (DF)

**Category:** Velocity Metric

**Description:** Measures how frequently code is successfully deployed to production. It represents the cadence at which teams can deliver value to end users.

**Definition:** Average number of deployments to production per time period (typically per day, week, or month).

**Performance Benchmarks:**
- Elite performers: Multiple deployments per day (on-demand)
- High performers: Once per week to once per month
- Medium performers: Once per month to once every 6 months
- Low performers: Less than once every 6 months

**Jira REST API Mapping:**

Deployment frequency requires tracking deployments, which are typically external to Jira. However, you can model this using Jira by:

1. **Option A: Using Jira Releases**
   - Endpoint: `GET /rest/api/3/projects/{projectIdOrKey}/versions`
   - Extract: `releaseDate` field to count releases per time period
   - API Response includes: `id`, `name`, `released` (boolean), `releaseDate`

2. **Option B: Using Custom Issue Type for Deployments**
   - Create issues with type "Deployment" or "Release"
   - Track status transitions to "Deployed" or "Released"
   - Use changelog endpoint: `GET /rest/api/3/issues/{issueIdOrKey}?expand=changelog`
   - Extract transition timestamps from `changelog.histories[].created`

3. **Option C: Using Custom Fields**
   - Create a custom field: "Deployment Date" (Date/DateTime picker type)
   - Create a custom field: "Environment" (Select list: Dev, Staging, Production)
   - Query: `GET /rest/api/3/issues/search?jql=type=Deployment AND environment=Production AND deploymentDate >= -7d`
   - Calculate: Count issues with deployment date in the period

**Recommended Custom Fields:**
- `Deployment_Date` (DateTime) - Auto-populated when issue transitions to "Deployed"
- `Target_Environment` (Select) - Values: Development, Staging, Production
- `Deployment_Version` (Text) - Release or build version number

**Calculation Formula:**
```
Deployment Frequency = Count(Deployments to Production) / Time Period (days/weeks/months)
```

---

### 2. Lead Time for Changes (LT)

**Category:** Velocity Metric

**Description:** Measures the time elapsed from when a code change is committed to when it is successfully deployed to production. It indicates how quickly the team can move from ideation to delivery.

**Definition:** Average time from code commit to production deployment.

**Performance Benchmarks:**
- Elite performers: Less than 1 hour
- High performers: Between 1 day and 1 week
- Medium performers: Between 1 week and 1 month
- Low performers: Between 1 month and 6 months

**Jira REST API Mapping:**

Lead time for changes spans from the start of development to production. Multiple data sources are needed:

1. **Option A: Issue Creation to Resolution**
   - Start point: When issue is created (`fields.created`)
   - End point: When issue is resolved (`fields.resolutiondate`)
   - Endpoint: `GET /rest/api/3/issues/{issueIdOrKey}?expand=changelog`

2. **Option B: Commit to Deployment (More Accurate)**
   - Requires integration with Git/SCM system
   - Start: First commit date (from Git)
   - End: Deployment date (from CD/CI pipeline or custom Jira field)
   - This typically requires external data sources beyond Jira alone

3. **Option C: Using Status Transitions**
   - Identify "Ready for Development" or "To Do" as start
   - Identify "Done" or "Deployed to Production" as end
   - Parse changelog for these specific transitions
   - API: `GET /rest/api/3/issues/{issueIdOrKey}?expand=changelog`

**Recommended Custom Fields:**
- `Code_Commit_Date` (DateTime) - When first commit was made
- `Deployed_to_Production_Date` (DateTime) - When deployed to prod
- `Lead_Time_Minutes` (Number) - Auto-calculated field
- `First_Commit_SHA` (Text) - Git commit hash for reference

**Data Extraction from Changelog:**
```json
GET /rest/api/3/issues/ABC-123?expand=changelog

Response includes:
{
  "changelog": {
    "histories": [
      {
        "id": "10000",
        "created": "2024-10-01T10:00:00.000+0000",
        "items": [
          {
            "field": "status",
            "fromString": "To Do",
            "toString": "In Progress"
          }
        ]
      }
    ]
  }
}
```

**Calculation Formula:**
```
Lead Time = Deployed_to_Production_Date - Code_Commit_Date
Average Lead Time = Sum(All Lead Times) / Count(Deployments)
```

---

### 3. Change Failure Rate (CFR)

**Category:** Stability Metric

**Description:** Measures the percentage of deployments that result in degraded service or outage in production. It indicates how well changes maintain system stability.

**Definition:** Percentage of deployments that cause incidents or failures in production.

**Performance Benchmarks:**
- Elite performers: 0-15% failure rate
- High performers: 15-30% failure rate
- Medium performers: 30-46% failure rate
- Low performers: 46-60% failure rate

**Jira REST API Mapping:**

This metric requires tracking deployments and their associated incidents:

1. **Option A: Link Incidents to Deployments**
   - Create "Incident" issue type
   - Track which deployment caused the incident
   - Use issue links: `GET /rest/api/3/issues/{issueIdOrKey}` → `fields.issuelinks`
   - Relationship type: "caused by" (deployment causes incident)

2. **Option B: Custom Field on Deployment Issues**
   - Add custom field: "Resulted in Incident" (checkbox or linked issues)
   - Query deployments that resulted in incidents
   - Calculate percentage of total deployments

3. **Option C: Using Labels or Status Categories**
   - Create deployments with label "failed" or status "Deployment Failed"
   - Query: `GET /rest/api/3/issues/search?jql=type=Deployment AND labels=failed`

**Recommended Custom Fields:**
- `Deployment_Successful` (Checkbox) - True/False for success
- `Incident_Related` (Linked Issues) - Link to related incidents
- `Production_Impact` (Select) - Values: None, Minor, Critical
- `Root_Cause` (Text) - Description of what caused failure

**Data Structure Example:**
```json
GET /rest/api/3/issues/search?jql=type=Deployment AND resolution!=Done

Response includes issues with counts
Count Failed = Issues with status "Deployment Failed" OR label "failed"
Count Total = Total deployment issues in period
```

**Calculation Formula:**
```
Change Failure Rate = Count(Failed Deployments) / Count(Total Deployments) × 100
Failed Deployment = Deployment that resulted in incident or rollback
```

---

### 4. Mean Time to Recovery (MTTR)

**Category:** Stability Metric

**Description:** Measures the average time taken to restore service after a production incident or outage. It indicates how quickly the team can respond to and fix issues.

**Definition:** Average time from incident detection to resolution.

**Performance Benchmarks:**
- Elite performers: Less than 1 hour
- High performers: Less than 1 day
- Medium performers: Between 1 day and 1 week
- Low performers: Between 1 week and 1 month

**Jira REST API Mapping:**

This metric tracks incidents from discovery to resolution:

1. **Option A: Using Service Management Issues**
   - Use Jira Service Management incident tracking
   - Start: `fields.created` (when incident created)
   - End: `fields.resolutiondate` (when incident resolved)
   - Calculate time difference

2. **Option B: Using Custom Fields on Incidents**
   - Create "Incident" issue type with custom fields
   - `Incident_Detected_Time` (DateTime)
   - `Incident_Resolved_Time` (DateTime)
   - `MTTR_Minutes` (Number, auto-calculated)

3. **Option C: Parsing Changelog Transitions**
   - Track transition from "New" → "Resolved" or "Closed"
   - Use changelog to find exact timestamps
   - Calculate time between these transitions

**Recommended Custom Fields:**
- `Incident_Severity` (Select) - Critical, High, Medium, Low
- `Incident_Detected_At` (DateTime) - When incident was first detected
- `Incident_Resolved_At` (DateTime) - When incident was fully resolved
- `Resolution_Time_Minutes` (Number) - Auto-calculated
- `Mitigation_Actions` (Text) - What was done to resolve

**Data Extraction:**
```json
GET /rest/api/3/issues/search?jql=type=Incident AND resolved >= -30d

For each incident:
resolved_time = fields.resolutiondate
created_time = fields.created
mttr = (resolved_time - created_time) in minutes/hours
```

**Calculation Formula:**
```
MTTR = Sum(Time to Resolve for All Incidents) / Count(Incidents)
MTTR = (Incident_Resolved_At - Incident_Detected_At) per incident
Average MTTR = Sum of all MTTRs / Number of incidents in period
```

---

## Part 2: Flow Metrics

Flow metrics measure how efficiently business value moves through the software development process. They categorize work into four types: **Features**, **Defects**, **Risks**, and **Technical Debt**.

### 1. Flow Velocity

**Description:** Measures the quantity of work items completed within a specific time period. It shows how much work the team can deliver and indicates productivity trends over time.

**Definition:** Number of work items (of all types) completed per time period.

**Business Relevance:** Higher velocity indicates faster value delivery to customers.

**Jira REST API Mapping:**

1. **Basic Query - Count Completed Items:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND resolution!=UNRESOLVED AND resolved>=-7d
   
   This counts all resolved issues in the last 7 days
   ```

2. **Segmented by Work Type:**
   - Create custom field: `Flow_Item_Type` (Select)
   - Values: Feature, Defect, Risk, Technical_Debt
   - Query for each type separately
   
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND flowItemType=Feature AND resolved>=-7d
   GET /rest/api/3/issues/search?jql=project=PROJ AND flowItemType=Defect AND resolved>=-7d
   GET /rest/api/3/issues/search?jql=project=PROJ AND flowItemType=Risk AND resolved>=-7d
   GET /rest/api/3/issues/search?jql=project=PROJ AND flowItemType=Debt AND resolved>=-7d
   ```

3. **Advanced - Using Issue Count from JQL Search:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status=Done AND updated>=-7d

   Response includes "total" field = Flow Velocity count
   ```

**Recommended Custom Fields:**
- `Flow_Item_Type` (Select) - Feature, Defect, Risk, Technical_Debt
- `Business_Value_Points` (Number) - Optional weighting system
- `Completed_Date` (DateTime) - When work item was marked complete

**Calculation Formula:**
```
Flow Velocity = Count(Completed Work Items) / Time Period
Flow Velocity by Type = Count(Completed [Type] Items) / Time Period

Example:
- 45 features completed in one month = 45 story points of feature velocity
- 12 defects fixed in one month = 12 story points of defect velocity
```

**Typical Use:**
- Track velocity over multiple sprints/months to identify trends
- Compare velocity across teams
- Forecast future delivery based on historical velocity

---

### 2. Flow Time

**Description:** Measures the total elapsed time from when a work item starts in the development process until it reaches production. This includes both active work time and waiting time.

**Definition:** Calendar time from work item approval/start to production completion.

**Business Relevance:** Shorter flow time means faster time-to-market and reduced cost of delay.

**Jira REST API Mapping:**

1. **Simple Calculation - Created to Done:**
   ```
   GET /rest/api/3/issues/{issueIdOrKey}
   
   Flow Time = fields.resolutiondate - fields.created
   ```

2. **More Precise - Using Custom Start/End Points:**
   - Custom field: `Approval_Date` (DateTime) - When work approved to start
   - Custom field: `Production_Ready_Date` (DateTime) - When deployed to production
   
   ```
   GET /rest/api/3/issues/{issueIdOrKey}
   
   Flow Time = production_ready_date - approval_date
   ```

3. **Batch Query for Reporting:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status=Done AND updated>=-30d&expand=changelog
   
   For each issue:
     - created = fields.created
     - resolved = fields.resolutiondate
     - flow_time_days = (resolved - created) / 86400
   ```

**Recommended Custom Fields:**
- `Work_Started_Date` (DateTime) - When work actually started
- `Work_Completed_Date` (DateTime) - When work moved to done status
- `Flow_Time_Days` (Number) - Auto-calculated field
- `Work_Item_Type` (Select) - Feature, Defect, Risk, Debt

**Data Extraction Example:**
```json
GET /rest/api/3/issues/ABC-100?expand=changelog

Response:
{
  "key": "ABC-100",
  "fields": {
    "created": "2024-10-01T10:00:00.000Z",
    "resolutiondate": "2024-10-08T15:30:00.000Z"
  }
}

Calculation:
Flow Time = (Oct 8 15:30 - Oct 1 10:00) = 5 days 5 hours 30 minutes
```

**Calculation Formula:**
```
Flow Time (per item) = Work_Completed_Date - Work_Started_Date
Average Flow Time = Sum(All Flow Times) / Count(Work Items Completed)

Example: If 10 items took [2, 3, 2, 4, 1, 5, 3, 2, 2, 3] days
Average Flow Time = 27 days / 10 items = 2.7 days per item
```

**Typical Use:**
- Measure time-to-market efficiency
- Identify items that spend excessive time waiting
- Compare flow times across different work types

---

### 3. Flow Efficiency

**Description:** Measures the proportion of time spent actively working on an item versus total time in the system (including waiting, blocked time, rework). Highlights process waste.

**Definition:** Active working time / Total flow time, expressed as percentage.

**Business Relevance:** Higher efficiency indicates less waste and better process design. Typical healthy efficiency is 25-40%.

**Jira REST API Mapping:**

1. **Using Status Duration Tracking:**
   - Track time in "Active" statuses vs "Waiting" statuses
   - Active statuses: In Progress, In Review, Testing
   - Waiting statuses: Backlog, Blocked, Waiting for Approval

   ```
   GET /rest/api/3/issues/{issueIdOrKey}?expand=changelog
   
   Parse changelog to find:
   - Time in "In Progress" status = active time
   - Time in "Blocked" status = waiting time
   - Time in "Backlog" status = waiting time
   ```

2. **Using Custom Fields:**
   - `Active_Work_Hours` (Number) - Sum of time spent actively working
   - `Total_Flow_Hours` (Number) - Total time from start to finish
   - `Flow_Efficiency_Percent` (Number) - Auto-calculated

   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND resolved>=-30d
   
   For each issue:
     - flow_efficiency = (active_work_hours / total_flow_hours) × 100
   ```

3. **Advanced - Parsing All Status Transitions:**
   ```
   Process changelog.histories to:
   1. Identify all status transitions with timestamps
   2. Categorize each status as "active" or "waiting"
   3. Calculate cumulative time in each category
   4. flow_efficiency = active_time / (active_time + waiting_time)
   ```

**Recommended Custom Fields:**
- `Status_Entry_Timestamp` (DateTime) - When item entered current status (auto via automation)
- `Active_Work_Time_Hours` (Number) - Manually tracked or calculated
- `Waiting_Time_Hours` (Number) - Calculated from status transitions
- `Flow_Efficiency_Percent` (Number) - Auto-calculated = (active / total) × 100
- `Blocker_Reason` (Text) - Reason if item was blocked

**Data Extraction Example:**
```
Changelog shows status transitions:
- 2024-10-01 10:00 → "In Progress" (ACTIVE)
- 2024-10-01 14:00 → "Blocked" (WAITING) [4 hours active]
- 2024-10-02 10:00 → "In Progress" (ACTIVE) [20 hours waiting]
- 2024-10-03 15:00 → "In Review" (ACTIVE) [29 hours active]
- 2024-10-04 16:00 → "Done" (END) [25 hours active]

Total active time = 4 + 29 + 25 = 58 hours
Total waiting time = 20 hours
Total flow time = 58 + 20 = 78 hours
Flow Efficiency = 58 / 78 × 100 = 74.4%
```

**Calculation Formula:**
```
Flow Efficiency = (Active Working Time / Total Flow Time) × 100

Active Working Time = Time in Progress + Time in Review + Time in Testing
Total Flow Time = Created Date to Resolution Date
Waiting Time = Time in Backlog + Time Blocked + Time Waiting for Approval
```

---

### 4. Flow Load

**Description:** Measures the number of work items currently in progress or in the development pipeline at any given time. Indicates team capacity and WIP (Work In Progress) levels.

**Definition:** Number of items currently "in progress" or "active" in the workflow.

**Business Relevance:** Lower WIP typically leads to faster delivery and fewer context switches. Healthy WIP limit is usually 3-5 items per developer.

**Jira REST API Mapping:**

1. **Current Snapshot - Items Currently in Progress:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status="In Progress"
   
   Response "total" field = current Flow Load
   ```

2. **Items in Active Workflow States:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status IN ("To Do", "In Progress", "In Review", "Testing")
   
   This gives broader WIP definition
   ```

3. **Tracking Over Time:**
   - Query daily/weekly to build Flow Load trend
   - Store results with timestamp
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status!="Done" AND created<-365d
   
   Group by date to see historical WIP trends
   ```

4. **Per Developer/Team:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status="In Progress" AND assignee=USERNAME
   
   This gives Flow Load per individual
   ```

**Recommended Custom Fields:**
- `Team_Member` (User) - For per-person WIP tracking
- `Work_Type` (Select) - Feature, Defect, Risk, Debt
- `Priority_Level` (Select) - Critical, High, Medium, Low

**Data Extraction Example:**
```
Current state query:
GET /rest/api/3/issues/search?jql=project=PROJ AND status IN ("To Do", "In Progress", "In Review")

Response:
{
  "total": 47,
  "issues": [
    ... array of 47 issues currently in active workflow states
  ]
}

Flow Load = 47 items currently in progress
```

**Calculation Formula:**
```
Flow Load (current) = Count(Issues with status NOT IN ["Done", "Backlog"])
Flow Load (average) = Sum(Daily Flow Load counts) / Number of days

Example: If daily WIP counts are [45, 48, 50, 47, 49, 46, 44]
Average Flow Load = 329 / 7 = 47 items average in progress
```

**Typical Use:**
- Identify if team is overloaded
- Balance new work intake
- Correlate high WIP with increased Flow Time

---

### 5. Flow Distribution

**Description:** Measures the ratio of work types (Features, Defects, Risks, Technical Debt) completed during a time period. Ensures balanced investment across different work types.

**Definition:** Percentage breakdown of completed work by type.

**Business Relevance:** 
- Too many features (>70%) risks product quality and sustainability
- Too many defects (>30%) indicates quality issues
- Too little debt repayment (<10%) leads to velocity degradation

**Recommended Distribution (Healthy Balance):**
- Features: 40-50% (new business value)
- Defects: 15-25% (quality fixes)
- Risks: 10-15% (security, compliance)
- Technical Debt: 20-25% (sustainability)

**Jira REST API Mapping:**

1. **Basic Query by Issue Type:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status=Done AND resolved>=-30d
   
   Then categorize by issue type or custom field
   ```

2. **Using Custom Flow Item Type Field:**
   ```
   GET /rest/api/3/issues/search?jql=project=PROJ AND status=Done AND resolved>=-30d AND flowItemType=Feature
   GET /rest/api/3/issues/search?jql=project=PROJ AND status=Done AND resolved>=-30d AND flowItemType=Defect
   GET /rest/api/3/issues/search?jql=project=PROJ AND status=Done AND resolved>=-30d AND flowItemType=Risk
   GET /rest/api/3/issues/search?jql=project=PROJ AND status=Done AND resolved>=-30d AND flowItemType=Debt
   
   Count results for each query
   ```

3. **Categorizing by Issue Type and Labels:**
   - Features: Issue Type = "Story" or "Epic"
   - Defects: Issue Type = "Bug"
   - Risks: Label = "security" OR label = "compliance"
   - Debt: Label = "technical-debt" OR component = "Refactoring"

   ```
   Get count for each category by separate queries
   ```

**Recommended Custom Fields:**
- `Flow_Item_Type` (Select) - Must have - Feature, Defect, Risk, Technical_Debt
- `Business_Value_Score` (Number) - Optional weighting
- `Strategic_Category` (Select) - For business alignment reporting

**Data Extraction Example:**
```
Period: Last 30 days, Project: ABC

Query results:
- Features completed: 45
- Defects fixed: 18
- Risk/Security items: 12
- Technical debt items: 25
- Total completed: 100 items

Flow Distribution:
- Features: 45/100 = 45%
- Defects: 18/100 = 18%
- Risks: 12/100 = 12%
- Debt: 25/100 = 25%

Status: BALANCED (within recommended ranges)
```

**Calculation Formula:**
```
Flow Distribution (by type) = Count(Completed Items of Type) / Count(Total Completed Items) × 100

Total = Features + Defects + Risks + Debt

Example:
Feature % = 45 / 100 × 100 = 45%
Defect % = 18 / 100 × 100 = 18%
Risk % = 12 / 100 × 100 = 12%
Debt % = 25 / 100 × 100 = 25%
```

**Typical Use:**
- Quarterly planning to align with business goals
- Identify drift from intended distribution
- Alert when defect or debt percentages exceed thresholds

---

## Part 3: Custom Fields Summary for Jira

### Required Custom Fields for DORA Metrics

| Field Name                  | Type         | Description                       | Automation                              |
| --------------------------- | ------------ | --------------------------------- | --------------------------------------- |
| Deployment_Date             | DateTime     | When deployed to production       | Auto-set on status change to "Deployed" |
| Target_Environment          | Select       | Dev/Staging/Production            | Manual selection                        |
| Code_Commit_Date            | DateTime     | When code was first committed     | Manual or API-set                       |
| Deployed_to_Production_Date | DateTime     | Actual production deployment time | Auto-set on production release          |
| Production_Impact           | Select       | None/Minor/Critical               | Manual after incident                   |
| Deployment_Successful       | Checkbox     | Success or failure flag           | Auto-calculated from incidents          |
| Incident_Related            | Linked Issue | Link to related incident          | Manual or automation rule               |
| Incident_Severity           | Select       | Critical/High/Medium/Low          | Manual on incident creation             |
| Incident_Detected_At        | DateTime     | When incident was discovered      | Auto-set on creation                    |
| Incident_Resolved_At        | DateTime     | When incident was fully resolved  | Auto-set on resolution                  |
| Resolution_Time_Minutes     | Number       | MTTR in minutes                   | Auto-calculated                         |

### Required Custom Fields for Flow Metrics

| Field Name              | Type     | Description                       | Automation                              |
| ----------------------- | -------- | --------------------------------- | --------------------------------------- |
| Flow_Item_Type          | Select   | Feature/Defect/Risk/Debt          | Manual or rule-based                    |
| Approval_Date           | DateTime | When work was approved to start   | Auto-set on transition to "Ready"       |
| Work_Started_Date       | DateTime | When active work began            | Auto-set on transition to "In Progress" |
| Work_Completed_Date     | DateTime | When work was marked complete     | Auto-set on transition to "Done"        |
| Status_Entry_Timestamp  | DateTime | Entry time for current status     | Auto via automation rule                |
| Active_Work_Hours       | Number   | Hours spent actively working      | Calculated from timestamps              |
| Flow_Time_Days          | Number   | Total days from start to complete | Auto-calculated                         |
| Flow_Efficiency_Percent | Number   | Active time / Total time × 100    | Auto-calculated                         |
| Business_Value_Points   | Number   | Optional weighting factor         | Manual or automated                     |
| Blocker_Reason          | Text     | Why item is blocked/waiting       | Manual when blocking occurs             |

### Setting Up Automation for Timestamp Fields

**Jira Automation Rule Example:**

```
Rule: Auto-timestamp when entering "In Progress"

Trigger: Issue Transitioned TO "In Progress"

Conditions: 
  - Project = [Your Project]
  - Issue Type = Story OR Bug

Actions:
  - Edit Issue
  - Field: Status_Entry_Timestamp
  - Value: {{now}}
```

**Date Format in Jira REST API:**
- Format: ISO 8601 with timezone
- Example: `"2024-10-15T14:30:00.000+0000"`
- When creating/updating: `"customfield_XXXXX": "2024-10-15T14:30:00.000+0000"`

---

## Part 4: Data Collection and Calculation Strategies

### Recommended ETL Pipeline

```
1. Data Extraction (Jira REST API)
   ├── Extract issues: GET /rest/api/3/issues/search
   ├── Extract changelog: GET /rest/api/3/issues/{key}?expand=changelog
   ├── Extract transitions: Parse changelog.histories[]
   └── Extract deployments: GET /rest/api/3/projects/{key}/versions (if using releases)

2. Data Transformation
   ├── Parse timestamps
   ├── Calculate time differences
   ├── Categorize work items (Features/Defects/Risk/Debt)
   ├── Filter by status and date ranges
   └── Aggregate by time period and team

3. Metric Calculation
   ├── DORA metrics (DF, LT, CFR, MTTR)
   ├── Flow metrics (Velocity, Time, Efficiency, Load, Distribution)
   └── Benchmarking against performance tiers

4. Visualization/Reporting
   ├── Dashboards with trend charts
   ├── Performance benchmarks
   ├── Team comparisons
   └── Bottleneck identification
```

### Sample REST API Queries for Weekly Reporting

**Weekly Deployments (Deployment Frequency):**
```
GET /rest/api/3/issues/search?jql=type=Deployment 
  AND deploymentDate >= -7d 
  AND deploymentDate < 0d 
  AND targetEnvironment=Production
```

**Lead Time Data:**
```
GET /rest/api/3/issues/search?jql=type=Story 
  AND status=Done 
  AND resolved >= -7d 
  AND resolved < 0d 
  &expand=changelog
```

**Incident Recovery Time:**
```
GET /rest/api/3/issues/search?jql=type=Incident 
  AND created >= -7d 
  AND status=Resolved
```

**Flow Velocity (Items Completed):**
```
GET /rest/api/3/issues/search?jql=project=PROJ 
  AND resolution!=UNRESOLVED 
  AND resolved >= -7d 
  &expand=changelog
```

---

## Part 5: Implementation Recommendations

### Phase 1: Foundation (Weeks 1-2)
1. Create custom field: `Flow_Item_Type` (Select)
2. Create custom field: `Deployment_Date` (DateTime)
3. Set up automation rule for timestamp capture
4. Document field mapping in Jira

### Phase 2: DORA Metrics (Weeks 3-4)
1. Create deployment tracking issue type or enhance releases
2. Create incident issue type
3. Add DORA-specific custom fields
4. Build first DORA dashboard

### Phase 3: Flow Metrics (Weeks 5-6)
1. Create Flow-specific custom fields
2. Set up automation for status timestamps
3. Build Flow metrics dashboard
4. Train team on categorization

### Phase 4: Integration & Automation (Weeks 7-8)
1. Connect CI/CD pipeline data (if possible)
2. Create automated daily metric calculations
3. Set up alerting for anomalies
4. Integrate with business goals

### Best Practices

- **Consistency:** Enforce mandatory custom field values through field configuration schemes
- **Data Quality:** Use automation to minimize manual data entry errors
- **Privacy:** Map only necessary fields; don't expose sensitive data
- **Scalability:** Design queries with date filters to avoid performance issues
- **Governance:** Document all custom fields and their usage
- **Training:** Educate team on proper categorization (Feature vs Defect vs Debt)

---

## Conclusion

DORA and Flow metrics provide complementary perspectives on software delivery:
- **DORA** focuses on deployment speed and reliability
- **Flow** focuses on value delivery and process efficiency

Proper Jira configuration with custom fields, automation, and REST API data extraction enables comprehensive metric tracking for data-driven continuous improvement.