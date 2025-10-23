# Contract: Bug Statistics Calculation

**Feature**: Bug Analysis Dashboard  
**Module**: `data/bug_processing.py`  
**Phase**: 1 - Design & Architecture

## Function Signature

```python
def calculate_bug_statistics(
    bug_issues: List[BugIssue],
    date_from: datetime,
    date_to: datetime,
    story_points_field: str = "customfield_10016"
) -> List[WeeklyBugStatistics]:
    """
    Calculate weekly bug creation and resolution statistics.
    
    Args:
        bug_issues: Filtered bug issues from filter_bug_issues()
        date_from: Start date of analysis period
        date_to: End date of analysis period
        story_points_field: JIRA field name for story points
    
    Returns:
        List of weekly statistics, ordered chronologically
        
    Raises:
        ValueError: If date_from >= date_to
        ValueError: If bug_issues is empty
    """
```

## Contract Specification

### Preconditions

- `bug_issues` must be a non-empty list of BugIssue entities
- `date_from` must be before `date_to`
- `date_from` and `date_to` must be aware datetimes or both naive
- Each bug must have valid `created_date` and optional `resolved_date`

### Postconditions

- Returns list of weekly statistics covering full date range
- Each week in range has exactly one statistics entry
- Weeks ordered chronologically (earliest first)
- All counts >= 0
- `net_bugs` equals `bugs_created - bugs_resolved` for each week
- `cumulative_open_bugs` is running sum starting from 0

### Input Validation

```python
# Validate bug issues
assert isinstance(bug_issues, list), "bug_issues must be a list"
assert len(bug_issues) > 0, "bug_issues cannot be empty"

for bug in bug_issues:
    assert "created_date" in bug, f"Bug {bug.get('key')} missing created_date"
    assert isinstance(bug["created_date"], datetime), "created_date must be datetime"

# Validate date range
assert isinstance(date_from, datetime), "date_from must be datetime"
assert isinstance(date_to, datetime), "date_to must be datetime"
assert date_from < date_to, "date_from must be before date_to"
```

### Output Guarantees

```python
# Verify output structure
assert isinstance(result, list), "Result must be a list"
assert len(result) > 0, "Result cannot be empty"

# Verify weekly coverage
weeks = [stat["week"] for stat in result]
assert len(weeks) == len(set(weeks)), "No duplicate weeks allowed"

# Verify ordering
for i in range(len(result) - 1):
    assert result[i]["week"] < result[i+1]["week"], "Weeks must be chronologically ordered"

# Verify calculations
for stat in result:
    assert stat["net_bugs"] == stat["bugs_created"] - stat["bugs_resolved"]
    assert stat["net_points"] == stat["bugs_points_created"] - stat["bugs_points_resolved"]
    assert stat["bugs_created"] >= 0
    assert stat["bugs_resolved"] >= 0

# Verify cumulative logic
cumulative = 0
for stat in result:
    cumulative += stat["net_bugs"]
    assert stat["cumulative_open_bugs"] == cumulative
```

### Example Usage

```python
# Setup
bug_issues = [
    {
        "key": "BUG-1",
        "created_date": datetime(2025, 1, 6),  # Week 2
        "resolved_date": datetime(2025, 1, 13),  # Week 3
        "story_points": 3
    },
    {
        "key": "BUG-2",
        "created_date": datetime(2025, 1, 8),  # Week 2
        "resolved_date": None,  # Open
        "story_points": 5
    },
    {
        "key": "BUG-3",
        "created_date": datetime(2025, 1, 15),  # Week 3
        "resolved_date": datetime(2025, 1, 20),  # Week 3
        "story_points": None  # No points
    }
]

date_from = datetime(2025, 1, 1)
date_to = datetime(2025, 1, 31)

# Execute
stats = calculate_bug_statistics(bug_issues, date_from, date_to)

# Expected result: 5 weeks (Jan has 5 weeks in 2025)
assert len(stats) == 5

# Week 2 (Jan 6-12): 2 bugs created, 0 resolved
week2 = next(s for s in stats if s["week"] == "2025-W02")
assert week2["bugs_created"] == 2
assert week2["bugs_resolved"] == 0
assert week2["bugs_points_created"] == 8  # 3 + 5
assert week2["bugs_points_resolved"] == 0
assert week2["net_bugs"] == 2
assert week2["cumulative_open_bugs"] == 2

# Week 3 (Jan 13-19): 1 bug created, 2 resolved
week3 = next(s for s in stats if s["week"] == "2025-W03")
assert week3["bugs_created"] == 1
assert week3["bugs_resolved"] == 2
assert week3["bugs_points_created"] == 0  # BUG-3 has no points
assert week3["bugs_points_resolved"] == 3  # Only BUG-1
assert week3["net_bugs"] == -1
assert week3["cumulative_open_bugs"] == 1  # 2 + (-1)
```

### Edge Cases

| Case                     | Input                        | Expected Output                            | Handling                    |
| ------------------------ | ---------------------------- | ------------------------------------------ | --------------------------- |
| Single week              | date_to - date_from < 7 days | Single week stats                          | Bin all bugs to that week   |
| No resolutions           | All bugs still open          | bugs_resolved = 0 for all weeks            | Normal processing           |
| No creations in week     | Week has no new bugs         | bugs_created = 0, but week still in output | Include all weeks           |
| Bug created before range | created_date < date_from     | Exclude from bugs_created                  | Don't count pre-period bugs |
| Bug resolved after range | resolved_date > date_to      | Count in cumulative_open_bugs              | Still open in period        |
| Null story points        | story_points is None         | Treat as 0 points                          | Normal aggregation          |
| Week boundary edge       | Bug created at 23:59:59      | Assigned to correct week                   | Use ISO week calculation    |

### Performance Requirements

- **Time Complexity**: O(n * w) where n = bugs, w = weeks
- **Space Complexity**: O(w) where w = number of weeks
- **Benchmark**: Process 1000 bugs over 52 weeks in < 100ms

### Calculation Details

**Week Assignment**:
```python
def get_iso_week(date: datetime) -> str:
    """Get ISO week identifier (e.g., '2025-W03')."""
    iso_calendar = date.isocalendar()
    return f"{iso_calendar[0]}-W{iso_calendar[1]:02d}"

def get_week_start_date(iso_week: str) -> str:
    """Get Monday date for ISO week (e.g., '2025-01-13')."""
    year, week = iso_week.split("-W")
    return datetime.strptime(f"{year}-W{week}-1", "%Y-W%W-%w").date().isoformat()
```

**Aggregation Logic**:
```python
# Initialize all weeks to 0
for week in week_range:
    weekly_stats[week] = {
        "week": week,
        "week_start_date": get_week_start_date(week),
        "bugs_created": 0,
        "bugs_resolved": 0,
        "bugs_points_created": 0,
        "bugs_points_resolved": 0,
        "net_bugs": 0,
        "net_points": 0,
        "cumulative_open_bugs": 0
    }

# Aggregate bugs into weeks
for bug in bug_issues:
    created_week = get_iso_week(bug["created_date"])
    if created_week in weekly_stats:
        weekly_stats[created_week]["bugs_created"] += 1
        weekly_stats[created_week]["bugs_points_created"] += bug.get("story_points", 0) or 0
    
    if bug["resolved_date"]:
        resolved_week = get_iso_week(bug["resolved_date"])
        if resolved_week in weekly_stats:
            weekly_stats[resolved_week]["bugs_resolved"] += 1
            weekly_stats[resolved_week]["bugs_points_resolved"] += bug.get("story_points", 0) or 0

# Calculate derived fields
cumulative = 0
for week in sorted(weekly_stats.keys()):
    stat = weekly_stats[week]
    stat["net_bugs"] = stat["bugs_created"] - stat["bugs_resolved"]
    stat["net_points"] = stat["bugs_points_created"] - stat["bugs_points_resolved"]
    cumulative += stat["net_bugs"]
    stat["cumulative_open_bugs"] = cumulative
```

### Error Messages

```python
# Error message templates
ERROR_EMPTY_BUGS = "Cannot calculate statistics from empty bug list"
ERROR_INVALID_DATE_RANGE = "date_from ({from_date}) must be before date_to ({to_date})"
ERROR_MISSING_CREATED_DATE = "Bug {key} missing required 'created_date' field"
ERROR_INVALID_DATE_TYPE = "Bug {key} has invalid created_date type: {type}"
```

### Testing Requirements

- ✅ Unit test with bugs across multiple weeks
- ✅ Unit test with single week
- ✅ Unit test with no resolutions (all open)
- ✅ Unit test with bugs created before range
- ✅ Unit test with bugs resolved after range
- ✅ Unit test with mixed story points (some null, some values)
- ✅ Unit test cumulative calculation accuracy
- ✅ Property test with random bug dates
- ✅ Integration test with real timeline filtering

---

## Contract Verification

This contract will be verified by:

1. **Type Checking**: MyPy static analysis with datetime types
2. **Unit Tests**: pytest with 100% branch coverage
3. **Property Testing**: Hypothesis with random date ranges and bug distributions
4. **Performance Testing**: Benchmark with 1000 bugs over 52 weeks

**Contract Status**: ✅ **APPROVED** - Ready for implementation
