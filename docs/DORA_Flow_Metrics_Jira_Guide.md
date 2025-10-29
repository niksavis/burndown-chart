# Querying Apache Jira REST API for DORA and Flow Metrics

## Overview

This guide provides a comprehensive mapping of **Jira REST API fields and endpoints** to **DORA (DevOps Research and Assessment) metrics** and **Flow metrics**, enabling you to extract data from public Jira instances (like Apache's Kafka project) for software delivery performance analysis.

---

## Part 1: Understanding DORA and Flow Metrics

### DORA Metrics (Four Key Metrics)

| Metric | Definition | Purpose |
|--------|-----------|---------|
| **Deployment Frequency** | How often code is successfully deployed to production | Measures team velocity and delivery cadence |
| **Lead Time for Changes** | Time from code commit to production deployment | Measures efficiency of the development pipeline |
| **Change Failure Rate** | Percentage of deployments causing incidents in production | Measures quality and stability |
| **Mean Time to Recovery (MTTR)** | Time to restore service after an incident | Measures resilience and incident response capability |

### Flow Metrics (Extended Framework)

| Metric | Definition | Jira Relevance |
|--------|-----------|-----------------|
| **Flow Time (Lead Time)** | Time from approval/planning to production delivery | Includes pre-development stages |
| **Flow Velocity (Throughput)** | Number of items delivered per time period | Measures completion rate |
| **Flow Efficiency** | Percentage of time spent actively working vs. waiting | Requires custom workflow analysis |
| **Flow Load** | Amount of work in progress (WIP) | Observable through status transitions |
| **Flow Distribution** | Mix of work types being completed | Categorization by issue type |

---

## Part 2: Jira REST API Endpoints for Data Extraction

### Base URL for Apache Jira
```
https://issues.apache.org/jira/rest/api/2
```

### Primary Endpoints

#### 1. Search Issues (Main Endpoint for Metrics)
**GET** `/rest/api/2/search`

**Example Query:**
```bash
curl -u username:password \
  "https://issues.apache.org/jira/rest/api/2/search?jql=project=KAFKA&fields=key,summary,created,updated,status,resolution,resolutiondate,issuetype,fixVersions,changelog&maxResults=100&startAt=0"
```

**Query Parameters:**
- `jql`: JQL (Jira Query Language) query string
- `fields`: Comma-separated list of fields to return
- `startAt`: Pagination starting point (for large result sets)
- `maxResults`: Maximum results per request (default 50, max 100)
- `expand`: Additional data to include (e.g., `changelog`, `names`)

#### 2. Get Individual Issue with Changelog
**GET** `/rest/api/2/issue/{issueKey}`

**Example:**
```bash
curl -u username:password \
  "https://issues.apache.org/jira/rest/api/2/issue/KAFKA-12345?expand=changelog"
```

This endpoint retrieves the complete history of an issue, including all status transitions with timestamps.

#### 3. Get Changelog Directly
**GET** `/rest/api/3/issue/{issueIdOrKey}/changelog` (Jira Cloud only)

For Jira Server/Data Center, use the expand parameter in the GET issue endpoint above.

---

## Part 3: Key Jira Fields for DORA Metrics

### System Fields (Available in All Jira Instances)

| Field ID | Display Name | JSON Key | Data Type | DORA/Flow Metric Use |
|----------|--------------|----------|-----------|----------------------|
| `key` | Issue Key | `key` | String | Unique identifier for tracking |
| `created` | Created Date | `created` | DateTime | Start point for Lead Time, Flow Time |
| `updated` | Updated Date | `updated` | DateTime | Last activity timestamp |
| `resolutiondate` | Resolution Date | `resolutiondate` | DateTime | Resolution point, indicator of completion |
| `status` | Status | `status.name` | String | Workflow state, essential for throughput |
| `resolution` | Resolution | `resolution.name` | String | Completion status (Fixed, Won't Fix, etc.) |
| `issuetype` | Issue Type | `issuetype.name` | String | Flow Distribution categorization |
| `priority` | Priority | `priority.name` | String | Optional: prioritization analysis |
| `fixVersions` | Fix Version/Release | `fixVersions[].name` | Array | Deployment tracking |
| `changelog` | Change Log | `changelog.histories[]` | Object | Status transitions, timing |

### Changelog Structure (Critical for DORA)

```json
{
  "changelog": {
    "histories": [
      {
        "id": "10001",
        "author": {
          "name": "username",
          "accountId": "user-id"
        },
        "created": "2024-01-15T10:30:00.000+0000",
        "items": [
          {
            "field": "status",
            "fieldtype": "jira",
            "from": "10000",
            "fromString": "Open",
            "to": "3",
            "toString": "In Progress"
          },
          {
            "field": "resolution",
            "fieldtype": "jira",
            "from": null,
            "fromString": null,
            "to": "10000",
            "toString": "Fixed"
          }
        ]
      }
    ]
  }
}
```

### Time Tracking Fields

| Field | JSON Key | Use Case |
|-------|----------|----------|
| Original Estimate | `timetracking.originalestimate` | Effort planning |
| Remaining Estimate | `timetracking.remainingestimate` | Active work tracking |
| Time Spent | `timetracking.timespent` | Actual effort (requires worklogs) |
| Worklog | `worklog.worklogs[]` | Detailed time tracking with `started`, `timeSpentSeconds` |

---

## Part 4: JQL Queries for Metric Extraction

### Query to Get All Issues in a Project with Full History
```jql
project = KAFKA AND type != Epic ORDER BY updated DESC
```

### Query for Issues Changed in Last 30 Days
```jql
project = KAFKA AND (created >= -30d OR updated >= -30d)
```

### Query for Released/Fixed Issues (For Deployment Frequency)
```jql
project = KAFKA AND resolution = Fixed AND fixVersion is not EMPTY AND resolutiondate >= -30d
```

### Query for Issues by Status (For Throughput/Velocity)
```jql
project = KAFKA AND status in (Closed, Done, Resolved) AND updated >= -7d
```

### Query for Issues with Active Work (WIP - For Flow Load)
```jql
project = KAFKA AND status not in (Closed, Done, Open, Backlog)
```

### Query Combining Filters (POST Method for Large Queries)
```bash
curl -X POST -u username:password \
  -H "Content-Type: application/json" \
  -d '{
    "jql": "project = KAFKA AND type in (Bug, Task, Story) AND updated >= -30d",
    "fields": ["key", "created", "updated", "resolutiondate", "status", "resolution", "fixVersions"],
    "startAt": 0,
    "maxResults": 100
  }' \
  https://issues.apache.org/jira/rest/api/2/search
```

---

## Part 5: Mapping Jira Data to DORA Metrics

### 1. Deployment Frequency

**Definition:** Number of deployments per day/week/month to production

**Jira Implementation:**
```
SELECT COUNT(DISTINCT fixVersions) as deployments
FROM issues
WHERE project = 'KAFKA'
  AND status = 'Done'
  AND resolutiondate >= date_range_start
  AND fixVersions IS NOT NULL
GROUP BY DATE(resolutiondate)
```

**API Fields Used:**
- `fixVersions`: Identifies released versions
- `resolutiondate`: Timestamp of deployment
- `status`: Confirmation of completion

**JQL Query:**
```jql
project = KAFKA AND fixVersion in (projectReleases()) AND resolutiondate >= -30d
```

**Calculation:**
```
Deployment Frequency = COUNT(DISTINCT fixVersions with resolutiondate) / days_in_period
```

### 2. Lead Time for Changes

**Definition:** Time from code commit (issue creation/planned) to production deployment (resolution)

**Jira Implementation:**

**Option A: Created to Resolution Date**
```
Lead Time = resolutiondate - created
```

**Option B: In Development to Released** (More Accurate)
- Track status transitions from "In Development" to "Done"
- Use changelog to find exact transition times

**API Fields Used:**
- `created`: When work was introduced
- `resolutiondate`: When work was completed/deployed
- `changelog.histories`: Detailed transition timeline

**Calculation Algorithm:**
```
1. Get issue created timestamp
2. Get resolutiondate timestamp
3. Calculate difference in hours/days
4. Average across issues in time period
```

**Example JSON Extraction:**
```json
{
  "issue": "KAFKA-12345",
  "created": "2024-01-01T08:00:00Z",
  "resolutiondate": "2024-01-03T14:00:00Z",
  "lead_time_hours": 54,
  "status_transitions": [
    {
      "from": "Open",
      "to": "In Development",
      "timestamp": "2024-01-01T09:00:00Z"
    },
    {
      "from": "In Development",
      "to": "Review",
      "timestamp": "2024-01-02T10:00:00Z"
    },
    {
      "from": "Review",
      "to": "Done",
      "timestamp": "2024-01-03T14:00:00Z"
    }
  ]
}
```

### 3. Change Failure Rate

**Definition:** Percentage of deployments causing production incidents

**Jira Implementation:**

This requires linking issues to incidents. Strategies:

**Option A: Issue Links**
- Use `issuelinks` field to find related issues
- Filter for links labeled "causes", "caused by", or "relates to"
- Look for "Bug" type issues created after a deployment

**Option B: Custom Field**
- Create a custom field like "Deployed Successfully"
- Track rollback or failure statuses

**Option C: Labels/Components**
- Use labels like "production-issue" or "regression"
- Components indicating failure domains

**Calculation:**
```
Change Failure Rate = (Issues with type=Bug AND created within 24h of deployment) / Total Deployments
```

**JQL Query to Find Potential Failures:**
```jql
project = KAFKA 
  AND type = Bug 
  AND created >= -24h 
  AND labels in ("regression", "production-issue")
```

### 4. Mean Time to Recovery (MTTR)

**Definition:** Time to resolve an incident from detection to restoration

**Jira Implementation:**

**Option A: Incident Type Issues**
```
MTTR = resolution_time - creation_time
WHERE issue_type = "Incident" OR labels contains "incident"
```

**Option B: Severity-Based**
```
MTTR = resolution_time - creation_time
WHERE priority = "Highest" OR "High"
  AND resolution = "Fixed"
```

**Calculation:**
```
1. Identify incident issues (by type, label, or priority)
2. Calculate: resolutiondate - created for each
3. Average across incidents in time period
4. Calculate median for statistical robustness
```

**JQL Query:**
```jql
project = KAFKA 
  AND type = Incident 
  AND resolution = Fixed 
  AND resolutiondate >= -30d
```

---

## Part 6: Mapping Jira Data to Flow Metrics

### 1. Flow Time (Lead Time)

**Same as DORA Lead Time for Changes**

**Extended Calculation (Including Pre-Development):**
```
Flow Time = Approval Date → Production
Components:
  - Planning/Design Phase (until status = "In Development")
  - Development Phase (status = "In Development")
  - Review/Testing Phase (until status = "Ready for Release")
  - Deployment Phase (until status = "Done")
```

**Jira Mapping:**
- `Approval Date`: Custom field or first status transition
- `In Development`: First transition to active development status
- `Done`: Final status or resolutiondate

### 2. Flow Velocity (Throughput)

**Definition:** Number of work items completed per time unit

**Calculation:**
```
Flow Velocity = COUNT(issues WHERE status = 'Done' OR resolution = 'Fixed') / time_period
```

**JQL Query:**
```jql
project = KAFKA 
  AND resolution in (Fixed, Resolved, Won't Fix) 
  AND resolutiondate >= -7d
```

**By Flow Item Type:**
```jql
project = KAFKA 
  AND resolution = Fixed 
  AND issuetype in (Story, Bug, Task)
  AND resolutiondate >= -7d
```

### 3. Flow Efficiency

**Definition:** Percentage of time spent actively working vs. waiting

**Calculation:**
```
Flow Efficiency = Active Work Time / Total Flow Time
```

**Jira Approximation:**
```
Active Work Time ≈ SUM(time_spent_in_development_status)
Total Flow Time = resolutiondate - created
```

**Implementation:**
- Track time in "In Development", "In Review" statuses
- Use changelog to calculate duration in each status
- Sum active work statuses / total duration

### 4. Flow Load (Work in Progress)

**Definition:** Number of items currently in progress

**JQL Query for Current WIP:**
```jql
project = KAFKA 
  AND status in (In Development, In Review, Testing, QA)
  AND resolution IS EMPTY
```

**Calculation:**
```
Flow Load = COUNT(issues WHERE status NOT IN (Open, Done, Closed))
```

### 5. Flow Distribution

**Definition:** Mix of work types (features, bugs, technical debt)

**Calculation:**
```
Distribution = {
  "features": COUNT(issuetype = Story),
  "bugs": COUNT(issuetype = Bug),
  "tasks": COUNT(issuetype = Task),
  "debt": COUNT(labels contains "technical-debt")
}
```

**JQL Query:**
```jql
project = KAFKA 
  AND resolutiondate >= -7d
  GROUP BY issuetype
```

---

## Part 7: Complete Implementation Example

### Python Script Template

```python
import requests
import json
from datetime import datetime, timedelta
from collections import defaultdict

class JiraMetricsCollector:
    def __init__(self, base_url, project_key, username, password):
        self.base_url = base_url
        self.project_key = project_key
        self.auth = (username, password)
        
    def get_issues_with_changelog(self, days_back=30):
        """Fetch issues with full changelog for metrics calculation"""
        jql = f"project = {self.project_key} AND updated >= -{days_back}d"
        
        all_issues = []
        start_at = 0
        max_results = 100
        
        while True:
            url = f"{self.base_url}/search"
            params = {
                "jql": jql,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": "key,created,updated,resolutiondate,status,resolution,issuetype,fixVersions,changelog",
                "expand": "changelog"
            }
            
            response = requests.get(url, params=params, auth=self.auth)
            response.raise_for_status()
            
            data = response.json()
            all_issues.extend(data['issues'])
            
            if data['startAt'] + data['maxResults'] >= data['total']:
                break
            start_at += max_results
        
        return all_issues
    
    def calculate_lead_time(self, issues):
        """Calculate DORA Lead Time metric"""
        lead_times = []
        
        for issue in issues:
            created = datetime.fromisoformat(
                issue['fields']['created'].replace('Z', '+00:00')
            )
            
            resolution_date = issue['fields'].get('resolutiondate')
            if resolution_date:
                resolved = datetime.fromisoformat(
                    resolution_date.replace('Z', '+00:00')
                )
                lead_time_hours = (resolved - created).total_seconds() / 3600
                lead_times.append(lead_time_hours)
        
        avg_lead_time = sum(lead_times) / len(lead_times) if lead_times else 0
        return {
            "avg_lead_time_hours": avg_lead_time,
            "avg_lead_time_days": avg_lead_time / 24,
            "issues_sampled": len(lead_times)
        }
    
    def calculate_deployment_frequency(self, issues, days=30):
        """Calculate DORA Deployment Frequency metric"""
        deployments = set()
        
        for issue in issues:
            fix_versions = issue['fields'].get('fixVersions', [])
            if fix_versions and issue['fields'].get('resolutiondate'):
                for version in fix_versions:
                    deployments.add(version['name'])
        
        frequency_per_day = len(deployments) / days
        return {
            "deployments_per_day": frequency_per_day,
            "deployments_per_week": frequency_per_day * 7,
            "deployments_per_month": frequency_per_day * 30,
            "unique_versions": len(deployments)
        }
    
    def calculate_flow_metrics(self, issues):
        """Calculate Flow metrics"""
        completed_issues = [i for i in issues 
                          if i['fields'].get('resolution')]
        
        by_type = defaultdict(int)
        for issue in completed_issues:
            issue_type = issue['fields']['issuetype']['name']
            by_type[issue_type] += 1
        
        return {
            "flow_velocity": len(completed_issues) / 7,  # per week
            "flow_distribution": dict(by_type),
            "total_completed": len(completed_issues)
        }

# Usage
collector = JiraMetricsCollector(
    "https://issues.apache.org/jira/rest/api/2",
    "KAFKA",
    "username",
    "password"
)

issues = collector.get_issues_with_changelog(days_back=30)

metrics = {
    "lead_time": collector.calculate_lead_time(issues),
    "deployment_frequency": collector.calculate_deployment_frequency(issues),
    "flow_metrics": collector.calculate_flow_metrics(issues)
}

print(json.dumps(metrics, indent=2))
```

---

## Part 8: Custom Fields for Enhanced Metrics

### Recommended Custom Fields to Create

| Field Name | Type | Purpose |
|-----------|------|---------|
| `Release/Deployment Date` | Date | Override or supplement resolutiondate |
| `Incident Type` | Single Select | Categorize incident issues for MTTR |
| `Flow Stage` | Single Select | Track workflow stages for Flow Efficiency |
| `Root Cause` | Text | Analysis field for failed changes |
| `Rollback Required` | Yes/No | Track change failures |
| `Production Impact` | Single Select | Severity categorization |

### Field ID Retrieval

```bash
curl -u username:password \
  "https://issues.apache.org/jira/rest/api/2/fields"
```

Custom fields are prefixed with `customfield_` followed by ID in API calls.

---

## Part 9: Query Performance and Pagination

### Handling Large Datasets

```bash
# Initial query to get total count
curl -u username:password \
  "https://issues.apache.org/jira/rest/api/2/search?jql=project=KAFKA&maxResults=0"

# Response includes 'total' field
# Calculate required iterations: total / maxResults

# Use pagination to retrieve all
for start in {0..10000..100}; do
  curl -u username:password \
    "https://issues.apache.org/jira/rest/api/2/search?jql=project=KAFKA&startAt=$start&maxResults=100"
done
```

### Performance Tips

1. **Limit fields returned**: Only request fields needed
2. **Use maxResults=100**: Optimal balance (default 50)
3. **Filter by date**: Use `updated >= -30d` to reduce dataset
4. **Avoid expand changelog on initial query**: Get issue keys first, then fetch changelog for filtered subset
5. **Implement caching**: Store API responses to reduce calls

---

## Part 10: Limitations and Considerations

### Jira Server-Specific Limitations

| Limitation | Impact | Workaround |
|-----------|--------|-----------|
| `created` and `updated` are read-only | Can't set historical dates | Use import tools for data migration |
| No built-in "deployment" field | Requires mapping to fixVersions or custom field | Standardize on fixVersions |
| Worklog time may not sync with status duration | Time tracking ≠ status transition time | Use changelog for accurate timing |
| Private issues hidden in queries | Can't query all project issues | Ensure API user has project access |
| No native incident linking | MTTR harder to calculate | Create custom linking strategy |

### Data Quality Issues

- **Status workflow variations**: Different projects may have different status names
- **Incomplete resolutiondate**: Not all issues have completion dates
- **Changelog gaps**: Very old issues may have truncated history
- **Custom field inconsistency**: Custom fields may not be used uniformly

---

## Summary Table: Key API Fields to Query

```
CORE FIELDS FOR DORA METRICS:
┌─────────────────┬──────────────┬──────────────────────┐
│ Metric          │ Required     │ API Field Path       │
├─────────────────┼──────────────┼──────────────────────┤
│ Deployment Freq │ fixVersions  │ fields.fixVersions[] │
│                 │ resolutiondt │ fields.resolutiondate│
├─────────────────┼──────────────┼──────────────────────┤
│ Lead Time       │ created      │ fields.created       │
│                 │ resolutiondt │ fields.resolutiondate│
├─────────────────┼──────────────┼──────────────────────┤
│ Change Failure  │ issuelinks   │ fields.issuelinks[]  │
│ Rate            │ labels       │ fields.labels[]      │
├─────────────────┼──────────────┼──────────────────────┤
│ MTTR            │ created      │ fields.created       │
│                 │ resolutiondt │ fields.resolutiondate│
│                 │ type/labels  │ issuetype/labels     │
├─────────────────┼──────────────┼──────────────────────┤
│ Flow Metrics    │ All of above + changelog for duration analysis   │
└─────────────────┴──────────────┴──────────────────────┘
```

---

## Additional Resources

- **Jira REST API Documentation**: https://docs.atlassian.com/software/jira/docs/api/REST/latest/
- **JQL Reference**: https://confluence.atlassian.com/jirasoftware/advanced-searching-39339948.html
- **DORA Framework**: https://www.devops-research.com/research.html
- **Flow Metrics Framework**: https://flowframework.atlassian.net/

---

**Document Version:** 1.0  
**Last Updated:** October 2025  
**Applicable To:** Apache Jira, Jira Server, Jira Cloud, Jira Data Center
