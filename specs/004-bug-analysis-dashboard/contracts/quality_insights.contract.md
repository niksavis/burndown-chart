# Contract: Quality Insights Generation

**Feature**: Bug Analysis Dashboard  
**Module**: `data/bug_insights.py`  
**Phase**: 1 - Design & Architecture

## Function Signature

```python
def generate_quality_insights(
    bug_metrics: BugMetricsSummary,
    weekly_stats: List[WeeklyBugStatistics],
    thresholds: Optional[Dict[str, float]] = None
) -> List[QualityInsight]:
    """
    Generate actionable quality insights based on bug analysis.
    
    Args:
        bug_metrics: Overall bug metrics summary
        weekly_stats: Weekly statistics for trend analysis (min 4 weeks recommended)
        thresholds: Optional custom thresholds (uses defaults if None)
    
    Returns:
        List of quality insights, sorted by severity (critical first)
        
    Raises:
        ValueError: If weekly_stats has < 2 weeks of data
    """
```

## Contract Specification

### Preconditions

- `bug_metrics` must be a valid BugMetricsSummary dictionary
- `weekly_stats` must have at least 2 weeks of data
- `weekly_stats` must be chronologically ordered
- `thresholds` (if provided) must have valid numeric values

### Postconditions

- Returns list of 0-10 insights (avoid overwhelming users)
- Insights sorted by severity: CRITICAL → HIGH → MEDIUM → LOW
- Each insight has unique ID (no duplicates)
- All insights are actionable or informational
- Timestamps reflect generation time

### Input Validation

```python
# Validate bug metrics
assert isinstance(bug_metrics, dict), "bug_metrics must be a dict"
assert "resolution_rate" in bug_metrics, "bug_metrics missing resolution_rate"
assert "total_bugs" in bug_metrics, "bug_metrics missing total_bugs"

# Validate weekly stats
assert isinstance(weekly_stats, list), "weekly_stats must be a list"
assert len(weekly_stats) >= 2, "weekly_stats must have at least 2 weeks"

# Verify chronological order
for i in range(len(weekly_stats) - 1):
    assert weekly_stats[i]["week"] < weekly_stats[i+1]["week"], "weekly_stats must be ordered"

# Validate thresholds
if thresholds:
    assert isinstance(thresholds, dict), "thresholds must be a dict"
    for key, value in thresholds.items():
        assert isinstance(value, (int, float)), f"Threshold {key} must be numeric"
```

### Output Guarantees

```python
# Verify output structure
assert isinstance(result, list), "Result must be a list"
assert len(result) <= 10, "Maximum 10 insights to avoid overwhelming users"

# Verify uniqueness
insight_ids = [insight["id"] for insight in result]
assert len(insight_ids) == len(set(insight_ids)), "Insight IDs must be unique"

# Verify sorting by severity
severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
for i in range(len(result) - 1):
    current_severity = severity_order[result[i]["severity"]]
    next_severity = severity_order[result[i+1]["severity"]]
    assert current_severity <= next_severity, "Insights must be sorted by severity"

# Verify each insight structure
for insight in result:
    assert "id" in insight, "Insight missing id"
    assert "type" in insight, "Insight missing type"
    assert "severity" in insight, "Insight missing severity"
    assert "title" in insight, "Insight missing title"
    assert "message" in insight, "Insight missing message"
    assert len(insight["title"]) <= 60, f"Title too long: {len(insight['title'])} chars"
    assert len(insight["message"]) <= 200, f"Message too long: {len(insight['message'])} chars"
```

### Default Thresholds

```python
DEFAULT_THRESHOLDS = {
    "resolution_rate_warning": 0.70,        # Below this triggers warning
    "resolution_rate_critical": 0.50,       # Below this triggers critical
    "capacity_warning": 0.30,               # Above this triggers warning
    "capacity_critical": 0.40,              # Above this triggers critical
    "avg_resolution_days_warning": 14,      # Above this triggers warning
    "avg_resolution_days_critical": 30,     # Above this triggers critical
    "trend_window_weeks": 4,                # Number of weeks for trend analysis
    "trend_ratio_increasing": 1.2,          # bugs_created / bugs_resolved
    "trend_ratio_stable": 0.9,              # Lower bound for stable
    "positive_resolution_rate": 0.80        # Above this is positive
}
```

### Insight Rules

| Rule ID                 | Trigger Condition                                         | Type           | Severity | Example Message                                             |
| ----------------------- | --------------------------------------------------------- | -------------- | -------- | ----------------------------------------------------------- |
| LOW_RESOLUTION_RATE     | resolution_rate < 0.50                                    | WARNING        | CRITICAL | "Only 45% of bugs resolved - immediate attention needed"    |
| BELOW_TARGET_RESOLUTION | 0.50 <= resolution_rate < 0.70                            | RECOMMENDATION | HIGH     | "Resolution rate of 65% below 70% target"                   |
| HIGH_BUG_CAPACITY       | capacity_consumed_by_bugs >= 0.40                         | WARNING        | CRITICAL | "Bugs consuming 42% of capacity - quality issues detected"  |
| ELEVATED_BUG_CAPACITY   | 0.30 <= capacity_consumed_by_bugs < 0.40                  | RECOMMENDATION | HIGH     | "Bugs using 35% of capacity - monitor closely"              |
| INCREASING_BUG_TREND    | trend_ratio > 1.2                                         | WARNING        | HIGH     | "Bug creation exceeding resolution rate by 25%"             |
| LONG_RESOLUTION_TIME    | avg_resolution_time_days >= 30                            | WARNING        | HIGH     | "Bugs taking 35 days to resolve on average"                 |
| SLOW_RESOLUTION         | 14 <= avg_resolution_time_days < 30                       | RECOMMENDATION | MEDIUM   | "Average resolution time of 18 days - room for improvement" |
| POSITIVE_TREND          | trend_direction == "improving" AND resolution_rate > 0.80 | POSITIVE       | LOW      | "Bug resolution trending positively - keep it up!"          |
| STABLE_QUALITY          | trend_direction == "stable" AND resolution_rate >= 0.70   | POSITIVE       | LOW      | "Quality metrics stable at healthy levels"                  |
| NO_OPEN_BUGS            | open_bugs == 0                                            | POSITIVE       | LOW      | "No open bugs - excellent quality!"                         |

### Example Usage

```python
# Setup
bug_metrics = {
    "total_bugs": 100,
    "open_bugs": 45,
    "closed_bugs": 55,
    "resolution_rate": 0.55,  # Below target
    "avg_resolution_time_days": 18,
    "bugs_created_last_4_weeks": 20,
    "bugs_resolved_last_4_weeks": 15,
    "trend_direction": "degrading",
    "capacity_consumed_by_bugs": 0.35,  # Elevated
    "total_bug_points": 300,
    "open_bug_points": 135
}

weekly_stats = [
    {"week": "2025-W01", "bugs_created": 5, "bugs_resolved": 4, ...},
    {"week": "2025-W02", "bugs_created": 6, "bugs_resolved": 3, ...},
    {"week": "2025-W03", "bugs_created": 4, "bugs_resolved": 5, ...},
    {"week": "2025-W04", "bugs_created": 5, "bugs_resolved": 3, ...}
]

# Execute
insights = generate_quality_insights(bug_metrics, weekly_stats)

# Expected insights (sorted by severity)
assert len(insights) >= 2  # At least resolution rate + capacity warnings
assert insights[0]["severity"] in ["critical", "high"]  # Most severe first

# Check for specific insights
insight_ids = [i["id"] for i in insights]
assert "BELOW_TARGET_RESOLUTION" in insight_ids  # resolution_rate = 0.55
assert "ELEVATED_BUG_CAPACITY" in insight_ids   # capacity = 0.35
assert "INCREASING_BUG_TREND" in insight_ids    # 20 created > 15 resolved

# Verify actionable insights
resolution_insight = next(i for i in insights if i["id"] == "BELOW_TARGET_RESOLUTION")
assert resolution_insight["actionable"] is True
assert "action_text" in resolution_insight
assert "capacity" in resolution_insight["action_text"].lower()
```

### Edge Cases

| Case                 | Input                                     | Expected Output         | Handling                     |
| -------------------- | ----------------------------------------- | ----------------------- | ---------------------------- |
| Perfect metrics      | resolution_rate = 1.0, open_bugs = 0      | POSITIVE insights only  | Return 1-2 positive insights |
| All zeros            | total_bugs = 0                            | Empty list              | No insights if no data       |
| Insufficient history | 1 week of data                            | Raise ValueError        | Need 2+ weeks                |
| Custom thresholds    | Lower threshold values                    | More insights triggered | Apply custom rules           |
| No trend             | stable metrics over time                  | STABLE_QUALITY insight  | Positive feedback            |
| Conflicting signals  | Good resolution rate but increasing trend | Both insights           | Don't filter contradictions  |

### Performance Requirements

- **Time Complexity**: O(n) where n = number of weekly stats
- **Space Complexity**: O(1) - Maximum 10 insights
- **Benchmark**: Generate insights for 52 weeks in < 20ms

### Insight Prioritization

When multiple insights are generated, prioritize by:

1. **Severity**: CRITICAL > HIGH > MEDIUM > LOW
2. **Type**: WARNING > RECOMMENDATION > POSITIVE
3. **Actionability**: Actionable insights before informational
4. **Impact**: Metrics with largest deviation from targets

```python
def calculate_insight_priority(insight: QualityInsight) -> int:
    """Calculate numeric priority for sorting (lower = higher priority)."""
    severity_weight = {"critical": 0, "high": 100, "medium": 200, "low": 300}
    type_weight = {"warning": 0, "recommendation": 10, "positive": 20}
    actionable_weight = 0 if insight["actionable"] else 5
    
    return severity_weight[insight["severity"]] + type_weight[insight["type"]] + actionable_weight
```

### Error Messages

```python
# Error message templates
ERROR_INSUFFICIENT_DATA = "Cannot generate insights with < 2 weeks of data (got {weeks} weeks)"
ERROR_INVALID_METRICS = "bug_metrics missing required field: {field}"
ERROR_INVALID_THRESHOLD = "Threshold {name} must be numeric, got {type}"
ERROR_UNORDERED_STATS = "weekly_stats must be chronologically ordered"
```

### Testing Requirements

- ✅ Unit test each insight rule independently
- ✅ Unit test with perfect metrics (all positive)
- ✅ Unit test with poor metrics (all warnings)
- ✅ Unit test with mixed signals
- ✅ Unit test with custom thresholds
- ✅ Unit test with minimum data (2 weeks)
- ✅ Unit test insight prioritization
- ✅ Unit test message length constraints
- ✅ Property test with random metrics
- ✅ Integration test with real bug data

---

## Contract Verification

This contract will be verified by:

1. **Type Checking**: MyPy static analysis with Enum types
2. **Unit Tests**: pytest with 100% rule coverage
3. **Property Testing**: Hypothesis with random metric values
4. **Threshold Testing**: Verify all threshold boundaries trigger correctly
5. **Message Testing**: Validate all messages are clear and actionable

**Contract Status**: ✅ **APPROVED** - Ready for implementation
