# Bug Analysis Dashboard - Developer Quickstart

**Feature**: Bug Analysis Dashboard  
**Last Updated**: October 22, 2025  
**Estimated Setup Time**: 10 minutes

## Prerequisites

Before starting, ensure you have:

- ✅ Python 3.13 installed
- ✅ Virtual environment activated (`.\.venv\Scripts\activate` on Windows)
- ✅ All dependencies installed (`pip install -r requirements.txt`)
- ✅ Existing burndown chart app running successfully

## Quick Setup (5 Minutes)

### 1. Verify Environment

```powershell
# Activate virtual environment (CRITICAL on Windows)
.\.venv\Scripts\activate

# Verify Python version
python --version  # Should show Python 3.13.x

# Verify dependencies
python -c "import dash, plotly, pandas; print('Dependencies OK')"
```

### 2. Enable Bug Analysis Feature

Add bug analysis configuration to `app_settings.json`:

```json
{
  "pert_factor": 1.5,
  "deadline": "2025-12-31",
  "bug_analysis_config": {
    "enabled": true,
    "issue_type_mappings": {
      "Bug": "bug",
      "Defect": "bug",
      "Incident": "bug"
    },
    "default_bug_type": "Bug"
  }
}
```

### 3. Update JIRA Integration

Modify `data/jira_simple.py` to include `issuetype` field:

```python
# Line ~171 in data/jira_simple.py
base_fields = "key,created,resolutiondate,status,issuetype"  # Add issuetype
```

### 4. Verify Setup

```powershell
# Run unit tests to verify setup
.\.venv\Scripts\activate; pytest tests/unit/data/test_jira_simple.py -v

# Start app
.\.venv\Scripts\activate; python app.py
```

Visit `http://localhost:8050` and verify the app loads without errors.

---

## Feature Development Workflow

### Running Bug Analysis in Isolation

For testing bug processing functions without running the full app:

```python
# Create test script: test_bug_analysis.py
from data.bug_processing import filter_bug_issues, calculate_bug_statistics
from data.bug_insights import generate_quality_insights
from tests.utils.mock_data import generate_mock_bug_data
from datetime import datetime, timedelta

# Generate mock data
mock_bugs = generate_mock_bug_data(num_weeks=12, bugs_per_week_range=(5, 15))

# Test bug filtering
bug_type_mappings = {"Bug": "bug", "Defect": "bug"}
bug_issues = filter_bug_issues(mock_bugs, bug_type_mappings)
print(f"Filtered {len(bug_issues)} bugs from {len(mock_bugs)} issues")

# Test statistics calculation
date_from = datetime.now() - timedelta(weeks=12)
date_to = datetime.now()
weekly_stats = calculate_bug_statistics(bug_issues, date_from, date_to)
print(f"Generated {len(weekly_stats)} weeks of statistics")

# Test insights generation
bug_metrics = calculate_bug_metrics_summary(bug_issues, weekly_stats)
insights = generate_quality_insights(bug_metrics, weekly_stats)
print(f"Generated {len(insights)} quality insights")
for insight in insights:
    print(f"  - [{insight['severity'].upper()}] {insight['title']}")
```

Run with:
```powershell
.\.venv\Scripts\activate; python test_bug_analysis.py
```

### Testing with Mock Data

The mock data generator creates realistic bug distributions:

```python
# Generate default mock data (12 weeks, random bug creation)
from tests.utils.mock_data import generate_mock_bug_data

bugs = generate_mock_bug_data()

# Generate custom mock data
bugs = generate_mock_bug_data(
    num_weeks=24,                   # 24 weeks of history
    bugs_per_week_range=(10, 20),   # 10-20 bugs per week
    issue_types=["Bug", "Defect", "Incident", "Critical Bug"]
)

# Mock data includes:
# - Realistic creation/resolution patterns
# - ~70% resolution rate (healthy baseline)
# - Story points distribution (some null, some 1-13)
# - Edge cases (outliers, boundary conditions)
```

### Adding New Quality Insight Rules

To add a new insight rule to `data/bug_insights.py`:

```python
# Step 1: Define rule ID constant
RULE_CRITICAL_BUGS_OPEN = "CRITICAL_BUGS_OPEN"

# Step 2: Add rule function
def check_critical_bugs_open(bug_issues: List[BugIssue]) -> Optional[QualityInsight]:
    """Check for critical bugs that remain open."""
    critical_open = [
        bug for bug in bug_issues
        if bug.get("severity") == "Critical" and bug["resolved_date"] is None
    ]
    
    if len(critical_open) > 0:
        return QualityInsight(
            id=RULE_CRITICAL_BUGS_OPEN,
            type=InsightType.WARNING,
            severity=InsightSeverity.CRITICAL,
            title=f"{len(critical_open)} Critical Bugs Open",
            message=f"There are {len(critical_open)} critical bugs still open. Prioritize resolution.",
            metrics={"critical_bugs_open": len(critical_open)},
            actionable=True,
            action_text="Review critical bugs and assign to sprint",
            created_at=datetime.now()
        )
    return None

# Step 3: Register rule in generate_quality_insights()
def generate_quality_insights(bug_metrics, weekly_stats, thresholds=None):
    insights = []
    
    # ... existing rules ...
    
    # Add new rule
    critical_insight = check_critical_bugs_open(bug_issues)
    if critical_insight:
        insights.append(critical_insight)
    
    # ... sort and return ...
```

Test the new rule:

```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_bug_insights.py::test_critical_bugs_open_rule -v
```

---

## Project Structure

Understanding the modular architecture:

```text
data/                              # Data processing layer
├── bug_processing.py              # Bug filtering, statistics, forecasting
├── bug_insights.py                # Quality insights engine
├── jira_simple.py                 # JIRA API integration (MODIFIED)
└── processing.py                  # General statistics (REUSED)

ui/                                # UI components layer
├── bug_analysis.py                # Bug analysis tab UI
├── bug_charts.py                  # Bug-specific visualizations
└── tabs.py                        # Tab navigation (MODIFIED)

callbacks/                         # Dash callback layer
├── bug_analysis.py                # Bug analysis callbacks
└── __init__.py                    # Callback registration (MODIFIED)

tests/                             # Test suite
├── unit/data/
│   ├── test_bug_processing.py     # Bug processing unit tests
│   ├── test_bug_insights.py       # Insights engine unit tests
│   └── test_jira_issue_types.py   # JIRA integration tests
├── integration/
│   └── test_bug_analysis_workflow.py  # End-to-end tests
└── utils/
    └── mock_data.py               # Mock bug data generator
```

### Key Integration Points

1. **JIRA Integration** (`data/jira_simple.py`):
   - Fetches `issuetype` field alongside existing fields
   - No breaking changes to existing functionality

2. **Data Persistence** (`data/persistence.py`):
   - Extends `project_data.json` with `bug_analysis` section
   - Backward compatible (older projects work without bug data)

3. **Callback Registration** (`callbacks/__init__.py`):
   - Registers new bug analysis callbacks
   - Follows existing pattern

4. **Tab System** (`ui/tabs.py`):
   - Adds "Bug Analysis" tab to navigation
   - Conditionally shown based on `bug_analysis_config.enabled`

---

## Testing Your Changes

### Unit Tests

Test individual functions in isolation:

```powershell
# Test bug processing module
.\.venv\Scripts\activate; pytest tests/unit/data/test_bug_processing.py -v

# Test insights engine
.\.venv\Scripts\activate; pytest tests/unit/data/test_bug_insights.py -v

# Test specific function
.\.venv\Scripts\activate; pytest tests/unit/data/test_bug_processing.py::test_filter_bug_issues -v

# Run with coverage
.\.venv\Scripts\activate; pytest tests/unit/data/ --cov=data.bug_processing --cov=data.bug_insights
```

### Integration Tests

Test complete workflows with Playwright:

```powershell
# Run bug analysis workflow tests
.\.venv\Scripts\activate; pytest tests/integration/test_bug_analysis_workflow.py -v -s

# Run specific workflow
.\.venv\Scripts\activate; pytest tests/integration/test_bug_analysis_workflow.py::test_bug_tab_navigation -v
```

### Performance Tests

Verify performance targets:

```powershell
# Run with duration tracking
.\.venv\Scripts\activate; pytest tests/unit/data/ --durations=10

# Specific performance test
.\.venv\Scripts\activate; pytest tests/unit/data/test_bug_processing.py::test_statistics_performance -v
```

---

## Common Development Tasks

### Task 1: Modify Bug Type Mappings

Update `app_settings.json`:

```json
{
  "bug_analysis_config": {
    "enabled": true,
    "issue_type_mappings": {
      "Bug": "bug",
      "Defect": "bug",
      "Incident": "bug",
      "Critical Bug": "bug",      // Add custom type
      "Production Issue": "bug"   // Add another custom type
    }
  }
}
```

### Task 2: Adjust Quality Insight Thresholds

Modify `data/bug_insights.py`:

```python
DEFAULT_THRESHOLDS = {
    "resolution_rate_warning": 0.65,  # Changed from 0.70
    "capacity_warning": 0.25,         # Changed from 0.30
    # ... other thresholds
}
```

### Task 3: Add New Bug Metric to Summary

Extend `BugMetricsSummary` in `data-model.md`, then implement in `data/bug_processing.py`:

```python
def calculate_bug_metrics_summary(bug_issues, weekly_stats):
    # ... existing calculations ...
    
    # Add new metric: average severity
    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    for bug in bug_issues:
        severity = bug.get("severity", "Medium")
        severity_counts[severity] += 1
    
    summary["severity_distribution"] = severity_counts
    return summary
```

### Task 4: Customize Bug Chart

Modify `ui/bug_charts.py`:

```python
def create_bug_trend_chart(bug_stats, viewport_size="mobile"):
    # Customize colors
    colors = {
        "bugs_created": "#ff6b6b",  # Red for created
        "bugs_resolved": "#51cf66",  # Green for resolved
    }
    
    # Customize layout
    layout = {
        "title": "Bug Creation vs Resolution",
        "xaxis": {"title": "Week"},
        "yaxis": {"title": "Bug Count"},
        "template": "plotly_dark",  # Dark theme
    }
    
    # ... rest of implementation
```

---

## Debugging Tips

### Enable Debug Logging

```python
# Add to app.py or test scripts
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("data.bug_processing")
logger.setLevel(logging.DEBUG)
```

### Inspect Data Structures

```python
# Pretty print bug data
import json

with open("project_data.json", "r") as f:
    data = json.load(f)
    bug_data = data.get("bug_analysis", {})
    print(json.dumps(bug_data, indent=2))
```

### Common Issues

| Issue                 | Symptom                                       | Solution                                  |
| --------------------- | --------------------------------------------- | ----------------------------------------- |
| Import errors         | `ModuleNotFoundError: No module named 'dash'` | Activate virtual environment              |
| Missing issuetype     | `KeyError: 'issuetype'`                       | Update `data/jira_simple.py` field list   |
| No insights generated | `insights = []`                               | Check thresholds and bug metrics values   |
| Chart not rendering   | Blank space where chart should be             | Check browser console for JS errors       |
| Tests fail on CI      | Pass locally, fail in CI                      | Ensure test isolation (no file pollution) |

---

## Next Steps

After completing the quickstart:

1. **Read the contracts**: Review `contracts/*.contract.md` for detailed API specifications
2. **Review the data model**: Study `data-model.md` for entity relationships
3. **Run the test suite**: Verify all tests pass before making changes
4. **Start with unit tests**: Write tests first (TDD approach)
5. **Implement incrementally**: Follow Phase 2 milestones in `plan.md`

---

## Getting Help

- **Documentation**: Check `specs/004-bug-analysis-dashboard/` for detailed specs
- **Code examples**: Look at existing processing in `data/processing.py`
- **Test examples**: Review existing tests in `tests/unit/data/`
- **Copilot instructions**: See `.github/copilot-instructions.md` for patterns

---

## Performance Targets

Keep these targets in mind during development:

- **Page load**: < 2 seconds
- **Chart rendering**: < 500ms
- **Bug statistics calculation**: < 100ms for 1000 bugs
- **Insights generation**: < 20ms for 52 weeks
- **Unit test execution**: < 5 seconds for full suite

---

**Happy coding! 🐛 → ✅**
