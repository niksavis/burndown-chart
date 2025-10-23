# Data Model: Bug Analysis Dashboard

**Feature**: Bug Analysis Dashboard  
**Phase**: 1 - Design & Architecture  
**Date**: October 22, 2025

## Overview

This document defines the data structures used for bug analysis functionality. All entities are designed to integrate seamlessly with the existing unified data structure in `project_data.json`.

---

## Entity Definitions

### 1. Bug Issue

**Purpose**: Represents a single bug/defect from JIRA mapped to the application's internal format.

**Schema**:

```python
class BugIssue(TypedDict):
    """Single bug issue from JIRA."""
    key: str                          # JIRA issue key (e.g., "PROJ-123")
    type: str                         # Mapped issue type ("Bug", "Defect", "Incident")
    original_type: str                # Original JIRA type name
    created_date: datetime            # Creation timestamp
    resolved_date: Optional[datetime] # Resolution timestamp (None if open)
    status: str                       # JIRA status name
    story_points: Optional[int]       # Story points (None if not estimated)
    week_created: str                 # Week identifier (ISO format: "2025-W01")
    week_resolved: Optional[str]      # Week resolved (None if open)
```

**Example**:

```json
{
  "key": "PROJ-456",
  "type": "Bug",
  "original_type": "Defect",
  "created_date": "2025-01-15T10:30:00Z",
  "resolved_date": "2025-01-22T14:20:00Z",
  "status": "Done",
  "story_points": 3,
  "week_created": "2025-W03",
  "week_resolved": "2025-W04"
}
```

**Validation Rules**:
- `key`: Must match pattern `[A-Z]+-\d+`
- `type`: Must be one of configured bug types
- `created_date`: Required, cannot be in the future
- `resolved_date`: Must be after `created_date` if present
- `story_points`: Must be >= 0 if present
- `week_created` / `week_resolved`: Must be valid ISO week format

**Data Sources**:
- Extracted from JIRA issues via `data/jira_simple.py`
- Mapped through issue type configuration in `app_settings.json`

---

### 2. Weekly Bug Statistics

**Purpose**: Aggregated bug metrics for a single week, used for trend visualization.

**Schema**:

```python
class WeeklyBugStatistics(TypedDict):
    """Bug statistics for a single week."""
    week: str                  # ISO week identifier (e.g., "2025-W03")
    week_start_date: str       # ISO date of week start (e.g., "2025-01-13")
    bugs_created: int          # Count of bugs created this week
    bugs_resolved: int         # Count of bugs resolved this week
    bugs_points_created: int   # Story points created this week
    bugs_points_resolved: int  # Story points resolved this week
    net_bugs: int              # bugs_created - bugs_resolved
    net_points: int            # bugs_points_created - bugs_points_resolved
    cumulative_open_bugs: int  # Running total of open bugs
```

**Example**:

```json
{
  "week": "2025-W03",
  "week_start_date": "2025-01-13",
  "bugs_created": 8,
  "bugs_resolved": 5,
  "bugs_points_created": 21,
  "bugs_points_resolved": 13,
  "net_bugs": 3,
  "net_points": 8,
  "cumulative_open_bugs": 15
}
```

**Validation Rules**:
- `week`: Valid ISO week format, must be within project timeline
- All counts: Must be >= 0
- `net_bugs`: Must equal `bugs_created - bugs_resolved`
- `net_points`: Must equal `bugs_points_created - bugs_points_resolved`
- `cumulative_open_bugs`: Must be >= 0

**Calculation**:
- Aggregated from `BugIssue` entities
- Created bugs: Count where `week_created == week`
- Resolved bugs: Count where `week_resolved == week`
- Cumulative open: Running sum of `net_bugs` from project start

**Data Sources**:
- Calculated by `data/bug_processing.py::calculate_bug_statistics()`

---

### 3. Bug Metrics Summary

**Purpose**: High-level summary of bug health metrics across the entire project.

**Schema**:

```python
class BugMetricsSummary(TypedDict):
    """Overall bug health metrics."""
    total_bugs: int                  # Total bugs in project
    open_bugs: int                   # Currently open bugs
    closed_bugs: int                 # Resolved bugs
    resolution_rate: float           # closed_bugs / total_bugs (0.0-1.0)
    avg_resolution_time_days: float  # Average days to close a bug
    bugs_created_last_4_weeks: int   # Recent bug creation rate
    bugs_resolved_last_4_weeks: int  # Recent bug resolution rate
    trend_direction: str             # "improving" | "stable" | "degrading"
    total_bug_points: int            # Total story points for bugs
    open_bug_points: int             # Points for open bugs
    capacity_consumed_by_bugs: float # Percentage of capacity (0.0-1.0)
```

**Example**:

```json
{
  "total_bugs": 150,
  "open_bugs": 23,
  "closed_bugs": 127,
  "resolution_rate": 0.847,
  "avg_resolution_time_days": 5.3,
  "bugs_created_last_4_weeks": 18,
  "bugs_resolved_last_4_weeks": 25,
  "trend_direction": "improving",
  "total_bug_points": 425,
  "open_bug_points": 67,
  "capacity_consumed_by_bugs": 0.28
}
```

**Validation Rules**:
- `total_bugs`: Must equal `open_bugs + closed_bugs`
- `resolution_rate`: Must be between 0.0 and 1.0
- `avg_resolution_time_days`: Must be >= 0
- `trend_direction`: Must be one of ["improving", "stable", "degrading"]
- `capacity_consumed_by_bugs`: Must be between 0.0 and 1.0

**Calculation**:
- Aggregated from `BugIssue` and `WeeklyBugStatistics`
- `resolution_rate`: `closed_bugs / total_bugs`
- `avg_resolution_time_days`: Mean of `(resolved_date - created_date).days` for closed bugs
- `trend_direction`: Based on 4-week moving average comparison
- `capacity_consumed_by_bugs`: `total_bug_points / total_project_points`

**Data Sources**:
- Calculated by `data/bug_processing.py::calculate_bug_metrics_summary()`

---

### 4. Quality Insight

**Purpose**: Actionable insight about project quality based on bug analysis.

**Schema**:

```python
class InsightType(Enum):
    """Type of insight."""
    WARNING = "warning"              # Critical issue requiring attention
    RECOMMENDATION = "recommendation" # Suggested improvement
    POSITIVE = "positive"            # Encouraging feedback

class InsightSeverity(Enum):
    """Severity of insight."""
    CRITICAL = "critical"  # Immediate action needed
    HIGH = "high"          # Address soon
    MEDIUM = "medium"      # Monitor
    LOW = "low"            # Informational

class QualityInsight(TypedDict):
    """Single quality insight from bug analysis."""
    id: str                     # Unique insight ID (e.g., "LOW_RESOLUTION_RATE")
    type: InsightType           # Insight type
    severity: InsightSeverity   # Severity level
    title: str                  # Short title (max 60 chars)
    message: str                # Detailed message (max 200 chars)
    metrics: Dict[str, float]   # Supporting metrics
    actionable: bool            # Whether insight has recommended action
    action_text: Optional[str]  # Recommended action (if actionable)
    created_at: datetime        # When insight was generated
```

**Example**:

```json
{
  "id": "LOW_RESOLUTION_RATE",
  "type": "recommendation",
  "severity": "high",
  "title": "Bug Resolution Rate Below Target",
  "message": "Only 65% of bugs are resolved, below the 70% target. Consider allocating more capacity to bug fixing.",
  "metrics": {
    "resolution_rate": 0.65,
    "target_rate": 0.70,
    "open_bugs": 52
  },
  "actionable": true,
  "action_text": "Dedicate 20% of sprint capacity to bug resolution",
  "created_at": "2025-01-22T10:00:00Z"
}
```

**Validation Rules**:
- `id`: Must be unique, uppercase snake_case
- `type`: Must be valid `InsightType`
- `severity`: Must be valid `InsightSeverity`
- `title`: Max 60 characters
- `message`: Max 200 characters
- `actionable`: Must be `true` if `action_text` present

**Data Sources**:
- Generated by `data/bug_insights.py::generate_quality_insights()`

**Insight Rules** (Examples):
- **LOW_RESOLUTION_RATE**: `resolution_rate < 0.70`
- **INCREASING_BUG_TREND**: `bugs_created_last_4_weeks > bugs_resolved_last_4_weeks * 1.2`
- **HIGH_BUG_CAPACITY**: `capacity_consumed_by_bugs > 0.30`
- **LONG_RESOLUTION_TIME**: `avg_resolution_time_days > 14`
- **POSITIVE_TREND**: `trend_direction == "improving" && resolution_rate > 0.80`

---

### 5. Bug Forecast

**Purpose**: Forecast of when open bugs will be resolved based on historical closure rates.

**Schema**:

```python
class BugForecast(TypedDict):
    """Bug resolution timeline forecast."""
    open_bugs: int                    # Current open bug count
    avg_closure_rate: float           # Average bugs closed per week
    optimistic_weeks: Optional[int]   # Best-case weeks to resolution
    pessimistic_weeks: Optional[int]  # Worst-case weeks to resolution
    most_likely_weeks: Optional[int]  # Most likely weeks to resolution
    optimistic_date: Optional[str]    # Best-case completion date (ISO)
    pessimistic_date: Optional[str]   # Worst-case completion date (ISO)
    most_likely_date: Optional[str]   # Most likely completion date (ISO)
    confidence_level: float           # Statistical confidence (0.0-1.0)
    insufficient_data: bool           # True if not enough history
```

**Example**:

```json
{
  "open_bugs": 23,
  "avg_closure_rate": 5.2,
  "optimistic_weeks": 3,
  "pessimistic_weeks": 7,
  "most_likely_weeks": 4,
  "optimistic_date": "2025-02-12",
  "pessimistic_date": "2025-03-12",
  "most_likely_date": "2025-02-19",
  "confidence_level": 0.85,
  "insufficient_data": false
}
```

**Validation Rules**:
- `open_bugs`: Must be >= 0
- `avg_closure_rate`: Must be >= 0
- `optimistic_weeks <= most_likely_weeks <= pessimistic_weeks`
- `confidence_level`: Must be between 0.0 and 1.0
- All date fields: Must be valid ISO dates in the future
- If `insufficient_data == true`, week/date fields should be `null`

**Calculation**:
- `avg_closure_rate`: Mean closure rate from last 8 weeks
- `optimistic_weeks`: `ceil(open_bugs / (avg + 1 * std_dev))`
- `pessimistic_weeks`: `ceil(open_bugs / max(avg - 1 * std_dev, 0.1))`
- `most_likely_weeks`: `ceil(open_bugs / avg)`
- `insufficient_data`: `true` if fewer than 4 weeks of history

**Data Sources**:
- Calculated by `data/bug_processing.py::forecast_bug_resolution()`

---

## Unified Data Structure Extension

The bug analysis data extends the existing `project_data.json` structure:

```python
class ProjectData(TypedDict):
    """Extended unified data structure."""
    # Existing fields
    project_scope: Dict
    statistics: List[Dict]  # Existing weekly statistics
    metadata: Dict
    
    # NEW: Bug analysis fields
    bug_analysis: BugAnalysisData

class BugAnalysisData(TypedDict):
    """Bug analysis data container."""
    enabled: bool                                  # Feature toggle
    bug_issues: List[BugIssue]                    # All bug issues
    weekly_bug_statistics: List[WeeklyBugStatistics]  # Weekly aggregates
    bug_metrics_summary: BugMetricsSummary        # Overall metrics
    quality_insights: List[QualityInsight]        # Current insights
    bug_forecast: BugForecast                     # Resolution forecast
    last_updated: str                             # ISO timestamp
```

**Example**:

```json
{
  "project_scope": { "...": "..." },
  "statistics": [ "..." ],
  "metadata": { "...": "..." },
  "bug_analysis": {
    "enabled": true,
    "bug_issues": [ "..." ],
    "weekly_bug_statistics": [ "..." ],
    "bug_metrics_summary": { "...": "..." },
    "quality_insights": [ "..." ],
    "bug_forecast": { "...": "..." },
    "last_updated": "2025-01-22T15:30:00Z"
  }
}
```

**Backward Compatibility**:
- `bug_analysis` field is optional (absent in projects without bug analysis)
- Existing code continues to work without modifications
- Bug analysis code checks for `bug_analysis.enabled` before processing

---

## Data Flow Diagram

```text
JIRA API
   │
   │ fetch_all_issues()
   ▼
[Raw JIRA Issues]
   │
   │ filter_bug_issues()
   ▼
[Bug Issues] ──────────────────────┐
   │                                │
   │ calculate_bug_statistics()     │
   ▼                                │
[Weekly Bug Statistics]             │
   │                                │
   ├─────────────────────┐          │
   │                     │          │
   │                     ▼          ▼
   │          calculate_bug_metrics_summary()
   │                     │
   │                     ▼
   │          [Bug Metrics Summary]
   │                     │
   ├─────────────────────┤
   │                     │
   ▼                     ▼
forecast_bug_resolution()  generate_quality_insights()
   │                     │
   ▼                     ▼
[Bug Forecast]    [Quality Insights]
   │                     │
   └──────────┬──────────┘
              ▼
       [Unified Data Structure]
              │
              ▼
        project_data.json
```

---

## Schema Validation

All data structures will be validated using the following patterns:

```python
# Example validation function
def validate_bug_issue(issue: Dict) -> bool:
    """Validate a bug issue matches schema."""
    required_fields = ["key", "type", "created_date", "status"]
    
    # Check required fields exist
    if not all(field in issue for field in required_fields):
        return False
    
    # Validate key format
    if not re.match(r"[A-Z]+-\d+", issue["key"]):
        return False
    
    # Validate dates
    try:
        created = datetime.fromisoformat(issue["created_date"])
        if created > datetime.now():
            return False
    except ValueError:
        return False
    
    # Additional validations...
    
    return True
```

---

## Migration Strategy

For projects without bug analysis data:

1. **Detection**: Check if `project_data.json` contains `bug_analysis` field
2. **Initialization**: Create empty bug analysis structure with `enabled: false`
3. **Population**: Run bug analysis on next JIRA data fetch
4. **Versioning**: Add `schema_version` to metadata for future migrations

```python
def migrate_to_bug_analysis(project_data: Dict) -> Dict:
    """Migrate existing project data to include bug analysis."""
    if "bug_analysis" not in project_data:
        project_data["bug_analysis"] = {
            "enabled": False,
            "bug_issues": [],
            "weekly_bug_statistics": [],
            "bug_metrics_summary": {},
            "quality_insights": [],
            "bug_forecast": {},
            "last_updated": datetime.now().isoformat()
        }
    
    return project_data
```

---

## Phase 1 Completion

**Status**: Ready for contract definition

All entities are defined with:
- ✅ Complete schemas with field types
- ✅ Validation rules specified
- ✅ Example data provided
- ✅ Calculation methods documented
- ✅ Data flow diagram created
- ✅ Backward compatibility addressed
- ✅ Migration strategy defined

**Next Step**: Create API contracts in `contracts/` directory
