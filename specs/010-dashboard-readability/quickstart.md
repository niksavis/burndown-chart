# Dashboard Testing Quickstart Guide

**Feature**: 010-dashboard-readability  
**Target**: >90% test coverage for dashboard calculations

## Quick Test Commands

### Run All Dashboard Tests

```powershell
# Activate virtual environment and run all dashboard tests
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py -v
```

### Run with Coverage Report

```powershell
# Generate coverage report for dashboard modules
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=term --cov-report=html
```

### View Coverage Report

```powershell
# Open HTML coverage report in browser
htmlcov\index.html
```

---

## Running Specific Tests

### Test Individual Functions

```powershell
# Test calculate_dashboard_metrics()
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py::TestCalculateDashboardMetrics -v

# Test calculate_pert_timeline()
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py::TestCalculatePertTimeline -v

# Test health score calculation
.\.venv\Scripts\activate; pytest tests/unit/ui/test_dashboard_cards.py::TestHealthScore -v

# Test card creation functions
.\.venv\Scripts\activate; pytest tests/unit/ui/test_dashboard_cards.py::TestCardCreation -v
```

### Test Edge Cases Only

```powershell
# Run tests with "edge" in the name
.\.venv\Scripts\activate; pytest tests/unit/ -k "edge or empty or zero or missing" -v
```

### Test Specific Scenario

```powershell
# Example: Test empty statistics handling
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py::test_calculate_dashboard_metrics_empty_statistics -v
```

---

## Coverage Verification Workflow

### Step 1: Run Tests with Coverage

```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=term-missing
```

**Expected Output**:
```
---------- coverage: platform win32, python 3.13.0 -----------
Name                       Stmts   Miss  Cover   Missing
--------------------------------------------------------
data/processing.py           120      8    93%   45-47, 102-105
ui/dashboard_cards.py        156     12    92%   78-82, 145-150, 210
--------------------------------------------------------
TOTAL                        276     20    93%
```

### Step 2: Identify Missing Coverage

Look for functions in the `Missing` column:
- Lines not covered by any test
- Branches not tested (if/else conditions)

### Step 3: Add Tests for Missing Lines

```powershell
# Open the file to see which tests are needed
code data/processing.py:45  # Jump to line 45
```

### Step 4: Re-run Coverage

```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=html
```

### Step 5: Validate >90% Target

Check HTML report for detailed coverage:
```powershell
htmlcov\index.html
```

**Success Criteria** (from spec.md SC-002):
- `data/processing.py`: >90% coverage
- `ui/dashboard_cards.py`: >90% coverage
- All edge cases from contract covered

---

## Test Isolation Validation

### Verify No Side Effects

```powershell
# Run tests in random order to ensure isolation
.\.venv\Scripts\activate; pip install pytest-randomly
.\.venv\Scripts\activate; pytest tests/unit/ --random-order -v
```

### Check for Project Root Pollution

```powershell
# Before running tests
Get-ChildItem -Path . -Filter "*.json" | Select-Object Name, LastWriteTime

# Run tests
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py -v

# After running tests - verify no new files created
Get-ChildItem -Path . -Filter "*.json" | Select-Object Name, LastWriteTime
```

**Expected**: No changes to `app_settings.json`, `project_data.json`, `jira_cache.json`, etc.

**If files changed**: Tests are violating isolation - find and fix using `tempfile` fixtures.

---

## Test Development Workflow

### 1. Create Test File

```powershell
# Example: Create test file for data/processing.py
New-Item -Path "tests\unit\data\test_dashboard_metrics.py" -ItemType File
```

### 2. Write Test with Fixtures

```python
import pytest
import tempfile
import json

@pytest.fixture
def temp_settings_file():
    """Create isolated temporary settings file"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name
    
    yield temp_file
    
    if os.path.exists(temp_file):
        os.unlink(temp_file)

def test_calculate_dashboard_metrics_normal_data(temp_settings_file):
    """Test dashboard metrics calculation with normal data"""
    # Arrange
    statistics = [
        {"date": "2025-01-01", "completed_items": 5, "completed_points": 25},
        {"date": "2025-01-08", "completed_items": 7, "completed_points": 35},
    ]
    settings = {"pert_factor": 1.2, "deadline": "2025-06-01"}
    
    # Act
    result = calculate_dashboard_metrics(statistics, settings)
    
    # Assert
    assert result["completion_percentage"] > 0
    assert result["current_velocity_items"] > 0
    assert result["completion_forecast_date"] is not None
```

### 3. Run Test

```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py::test_calculate_dashboard_metrics_normal_data -v
```

### 4. Check Coverage for That Function

```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py --cov=data.processing --cov-report=term-missing
```

### 5. Iterate Until >90%

Repeat steps 2-4, adding tests for edge cases until coverage target met.

---

## Common Testing Patterns

### Pattern 1: Arrange-Act-Assert

```python
def test_function_name():
    # Arrange: Set up test data
    input_data = {"key": "value"}
    
    # Act: Call function under test
    result = function_to_test(input_data)
    
    # Assert: Verify expected behavior
    assert result["expected_key"] == "expected_value"
```

### Pattern 2: Parameterized Tests (Multiple Scenarios)

```python
@pytest.mark.parametrize("score,expected_color,expected_label", [
    (85, "#198754", "Excellent"),
    (70, "#0dcaf0", "Good"),
    (50, "#ffc107", "Fair"),
    (30, "#fd7e14", "Needs Attention"),
])
def test_health_color_tiers(score, expected_color, expected_label):
    color, label = _get_health_color_and_label(score)
    assert color == expected_color
    assert label == expected_label
```

### Pattern 3: Edge Case Testing

```python
def test_edge_case_empty_data():
    # Arrange
    empty_statistics = []
    settings = {"pert_factor": 1.2}
    
    # Act
    result = calculate_dashboard_metrics(empty_statistics, settings)
    
    # Assert: Should return safe defaults, not crash
    assert result["current_velocity_items"] == 0
    assert result["completion_forecast_date"] is None
```

---

## Debugging Failed Tests

### View Detailed Test Output

```powershell
# Run with full output (no truncation)
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py -v -s
```

### Use pytest Debugging

```powershell
# Drop into debugger on failure
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py --pdb
```

### Print Coverage Missing Lines

```powershell
# Show exactly which lines are not covered
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py --cov=data.processing --cov-report=term-missing
```

---

## Integration with Development Workflow

### Before Committing

```powershell
# 1. Run all tests
.\.venv\Scripts\activate; pytest tests/unit/ -v

# 2. Check coverage
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=term

# 3. Verify no project root pollution
Get-ChildItem -Path . -Filter "*.json" | Select-Object Name, LastWriteTime

# 4. If all pass, commit
git add tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py
git commit -m "test: add comprehensive dashboard metrics tests (>90% coverage)"
```

### Pre-Merge Validation

```powershell
# Run full test suite with coverage report
.\.venv\Scripts\activate; pytest tests/ --cov=data --cov=ui --cov=visualization --cov-report=html --cov-report=term

# Open report to verify all modules >90%
htmlcov\index.html
```

---

## Test Organization

### File Structure

```
tests/
├── unit/
│   ├── data/
│   │   └── test_dashboard_metrics.py       # Tests for data/processing.py functions
│   └── ui/
│       └── test_dashboard_cards.py         # Tests for ui/dashboard_cards.py functions
└── conftest.py                             # Shared fixtures (if needed)
```

### Test Class Organization

```python
# tests/unit/data/test_dashboard_metrics.py

class TestCalculateDashboardMetrics:
    """Tests for calculate_dashboard_metrics() function"""
    
    def test_normal_data(self):
        """Normal operation with 10 weeks of data"""
        pass
    
    def test_empty_statistics(self):
        """Edge case: empty statistics array"""
        pass
    
    def test_zero_velocity(self):
        """Edge case: all completed_items == 0"""
        pass

class TestCalculatePertTimeline:
    """Tests for calculate_pert_timeline() function"""
    
    def test_pert_formula(self):
        """Validate PERT weighted average calculation"""
        pass
```

---

## Performance Testing (Optional)

### Benchmark Test Execution Time

```powershell
# Show 10 slowest tests
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --durations=10
```

**Expected**: All tests should complete in <1 second (unit tests are fast).

---

## Continuous Integration (Future)

When CI is set up, these commands will run automatically:

```yaml
# Example GitHub Actions workflow
- name: Run Dashboard Tests
  run: |
    .\.venv\Scripts\activate
    pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=xml --cov-fail-under=90
```

---

## Success Checklist

Before marking this feature complete, verify:

- [ ] All 61 tests from test-coverage-contract.md implemented
- [ ] `pytest` passes with 0 failures
- [ ] Coverage >90% for `data/processing.py` dashboard functions
- [ ] Coverage >90% for `ui/dashboard_cards.py` functions
- [ ] No files created in project root during tests
- [ ] Tests pass with `--random-order` (isolation validated)
- [ ] HTML coverage report shows all edge cases covered
- [ ] All FR-006 through FR-016 requirements validated by tests

**Command to Validate All**:
```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_dashboard_metrics.py tests/unit/ui/test_dashboard_cards.py --cov=data.processing --cov=ui.dashboard_cards --cov-report=html --cov-fail-under=90 -v
```

If this command exits with code 0, all success criteria met! 🎉

---

**Version**: 1.0 (2025-11-12)  
**Next Steps**: See `contracts/test-coverage-contract.md` for detailed test requirements.
