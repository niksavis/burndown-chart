# Quickstart: Smooth Statistical Health Score Formula

**Feature**: 014-smooth-health-formula  
**Status**: Implementation Ready  
**Estimated Time**: 4-6 hours

## For Developers: 5-Minute Setup

### 1. Get the Code

```powershell
git checkout 014-smooth-health-formula
git pull origin 014-smooth-health-formula
```

### 2. Review Key Documents

Read in this order (15 minutes total):
1. [spec.md](spec.md) - User stories and requirements (5 min)
2. [research.md](research.md) - Technical decisions and formulas (5 min)
3. [contracts/health_score_calculation.contract.md](contracts/health_score_calculation.contract.md) - Function behavior (5 min)

### 3. Understand the Change

**Problem**: Health scores stuck at 25-50% due to:
- Incomplete current week deflating velocity by 40-60%
- Threshold-based penalties (0 → -12 → -25 points) hiding gradual changes

**Solution**: Replace with smooth continuous formula:
- Filter incomplete weeks before velocity calculations
- Use tanh/linear functions instead of thresholds
- All components contribute (no arbitrary defaults)

### 4. Key Files to Modify

| File                                    | Change                              | Lines |
| --------------------------------------- | ----------------------------------- | ----- |
| `ui/dashboard_cards.py`                 | Replace `_calculate_health_score()` | ~100  |
| `tests/unit/ui/test_dashboard_cards.py` | Update 12 tests + add 10 new        | ~300  |
| `docs/dashboard_metrics.md`             | Update formula docs                 | ~50   |

### 5. Run Tests

```powershell
.\.venv\Scripts\activate
pytest tests/unit/ui/test_dashboard_cards.py::TestHealthScore -v
```

## Implementation Checklist

### Phase 1: Core Function (2-3 hours)

- [ ] Create `filter_complete_weeks()` helper function
- [ ] Implement new `_calculate_health_score()` with 4 components:
  - [ ] Progress component (linear scaling)
  - [ ] Schedule component (tanh sigmoid)
  - [ ] Stability component (CV linear decay)
  - [ ] Trend component (velocity % change linear)
- [ ] Add validation for component ranges
- [ ] Update function docstring

### Phase 2: Testing (2-3 hours)

- [ ] Update existing tests (12 tests in TestHealthScore class)
- [ ] Add edge case tests:
  - [ ] Incomplete week filtering (Wednesday vs Sunday)
  - [ ] Zero velocity (division by zero)
  - [ ] Missing deadline (neutral schedule)
  - [ ] Small project (4 weeks)
  - [ ] Extreme values (CV>2, buffer>±60 days)
- [ ] Add validation tests:
  - [ ] Component ranges
  - [ ] Sum validation
  - [ ] Deterministic (same input → same output)
- [ ] Performance test (<50ms for 52 weeks)

### Phase 3: Documentation (<1 hour)

- [ ] Update `docs/dashboard_metrics.md` Section 1
- [ ] Update `configuration/help_content.py` health score text
- [ ] Update `docs/METRICS_EXPLANATION.md` statistical notes

## Code Examples

### Example 1: New Health Score Function Structure

```python
def _calculate_health_score(metrics: Dict[str, Any], statistics_df: pd.DataFrame) -> int:
    """Calculate smooth continuous health score (0-100)."""
    score = 0.0
    
    # Component 1: Progress (0-30 points)
    completion_pct = metrics.get("completion_percentage", 0)
    progress_score = (completion_pct / 100) * 30
    score += progress_score
    
    # Component 2: Schedule (0-30 points) - tanh sigmoid
    # ... implementation
    
    # Filter incomplete current week
    filtered_df = filter_complete_weeks(statistics_df.copy())
    
    # Component 3: Stability (0-20 points) - CV linear decay
    # ... implementation
    
    # Component 4: Trend (0-20 points) - velocity change linear
    # ... implementation
    
    return int(round(max(0, min(100, score))))
```

### Example 2: Week Filtering Helper

```python
def filter_complete_weeks(df: pd.DataFrame) -> pd.DataFrame:
    """Remove incomplete current week from DataFrame."""
    if df.empty:
        return df
    
    last_date = pd.to_datetime(df['date'].iloc[-1])
    today = datetime.now()
    days_apart = (today.date() - last_date.date()).days
    
    # Same week (≤6 days) and not Sunday end-of-day
    if days_apart <= 6:
        is_sunday = today.weekday() == 6
        is_end_of_day = today.hour >= 23
        if not (is_sunday and is_end_of_day):
            return df.iloc[:-1]  # Remove last row
    
    return df
```

### Example 3: Test Case Structure

```python
def test_incomplete_week_filtering():
    """Test that incomplete current week is excluded from velocity calcs."""
    # Given: 12 weeks, last week is current (incomplete)
    metrics = {
        "completion_percentage": 70.0,
        "days_to_completion": 30,
        "days_to_deadline": 45
    }
    
    # Mock today as Wednesday
    with patch('datetime.datetime') as mock_dt:
        mock_dt.now.return_value = datetime(2025, 1, 15, 10, 0)  # Wed
        mock_dt.weekday.return_value = 2  # Wednesday
        
        # When: Calculate health
        health = _calculate_health_score(metrics, statistics_df)
        
        # Then: Score should not be deflated by incomplete week
        assert health >= 65  # Not artificially low
```

## Testing Strategy

### Test Pyramid

```
      /\        Integration (2 tests)
     /  \       - Dashboard callback integration
    /----\      - UI display correctness
   /      \     
  /--------\    Unit (22 tests)
 /          \   - Component calculations
/____________\  - Edge cases
                - Validation
```

### Key Test Scenarios

| Test Type                  | Count | Coverage                |
| -------------------------- | ----- | ----------------------- |
| Excellent projects (>90%)  | 1     | Full range high end     |
| Critical projects (<10%)   | 1     | Full range low end      |
| Typical projects (60-75%)  | 3     | Middle range variations |
| Small projects (4 weeks)   | 2     | Minimum viable dataset  |
| Edge cases (zero, extreme) | 6     | Boundary conditions     |
| Incomplete week filtering  | 3     | Sawtooth bug fix        |
| Validation                 | 6     | Component ranges, sum   |

## Common Issues & Solutions

### Issue 1: Tests Fail with "statistics_df not found"

**Symptom**: `NameError: name 'statistics_df' is not defined`

**Solution**: Update function signature to accept statistics_df parameter:
```python
# Old
def _calculate_health_score(metrics: Dict[str, Any]) -> int:

# New
def _calculate_health_score(metrics: Dict[str, Any], statistics_df: pd.DataFrame) -> int:
```

Update all call sites to pass statistics_df.

### Issue 2: Health Score Always Returns 35

**Symptom**: Score never varies from 35 (0 + 15 + 10 + 10)

**Solution**: Check that statistics_df is being passed correctly and is not empty. Verify filter_complete_weeks() is not removing all data.

### Issue 3: "tanh not found"

**Symptom**: `NameError: name 'tanh' is not defined`

**Solution**: Add import at top of file:
```python
import math
```

Use as: `math.tanh(normalized)`

### Issue 4: Float Precision Issues in Tests

**Symptom**: Test expects 68 but gets 67 or 69

**Solution**: Use range assertions instead of exact values:
```python
# Instead of:
assert health == 68

# Use:
assert 67 <= health <= 69
```

## Performance Validation

### Benchmark Script

```python
import time
import pandas as pd
from ui.dashboard_cards import _calculate_health_score

# Create 52-week dataset
statistics_df = pd.DataFrame({
    'date': pd.date_range('2024-01-01', periods=52, freq='W-MON'),
    'completed_items': [10] * 52,
    'completed_points': [50.0] * 52
})

metrics = {
    "completion_percentage": 70.0,
    "days_to_completion": 30,
    "days_to_deadline": 45
}

# Benchmark
iterations = 1000
start = time.perf_counter()
for _ in range(iterations):
    _ = _calculate_health_score(metrics, statistics_df)
end = time.perf_counter()

avg_time_ms = ((end - start) / iterations) * 1000
print(f"Average time: {avg_time_ms:.2f}ms")
assert avg_time_ms < 50, f"Performance degraded: {avg_time_ms}ms > 50ms"
```

**Expected**: 5-10ms average (well under 50ms budget)

## Deployment Checklist

Before marking feature complete:

- [ ] All 22 unit tests pass
- [ ] Performance <50ms validated
- [ ] Code coverage >95% for modified function
- [ ] Documentation updated
- [ ] Manual smoke test on dashboard
- [ ] No errors in `get_errors` tool
- [ ] Git commit messages follow conventional commits
- [ ] PR description references spec.md

## Getting Help

### Resources

1. **Spec Questions**: See [spec.md](spec.md) User Stories section
2. **Formula Questions**: See [research.md](research.md) mathematical verification
3. **API Questions**: See [contracts/health_score_calculation.contract.md](contracts/health_score_calculation.contract.md)
4. **Constitution Compliance**: See [.specify/memory/constitution.md](../../.specify/memory/constitution.md)

### Contact Points

- **Feature Owner**: Reference issue #014
- **Technical Questions**: Check research.md Q&A section first
- **Test Failures**: Compare with contract test cases

## Success Metrics

Feature is complete when:

1. ✅ Health score changes <3% when checked mid-week vs Sunday (no sawtooth)
2. ✅ 1-day schedule buffer change produces 0.5-2% health change (smooth)
3. ✅ Excellent projects score ≥90%, critical projects score ≤10%
4. ✅ 4-week projects calculate all components (no arbitrary defaults)
5. ✅ Performance <50ms for 52-week datasets
6. ✅ All tests pass, coverage >95%

## Next Steps After Implementation

This feature is Phase 1. Future enhancements (not in scope):

- Show component breakdown in UI tooltip
- Track health score history over time
- Customizable component weights
- Alerting on health score drops
- Export health metrics to reports

## Estimated Timeline

| Phase         | Time          | Completion Criteria                                 |
| ------------- | ------------- | --------------------------------------------------- |
| Core function | 2-3 hours     | Function implements 4 components, passes smoke test |
| Testing       | 2-3 hours     | 22 tests pass, coverage >95%                        |
| Documentation | <1 hour       | 3 doc files updated, help text revised              |
| **Total**     | **4-7 hours** | All acceptance criteria met                         |

---

**Ready to start?** Begin with Phase 1: Core Function. Read the contract first, then implement one component at a time with immediate testing.
