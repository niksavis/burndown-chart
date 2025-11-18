# DORA Calculator Refactoring Plan - Feature 012 T007

## Objective
Integrate VariableExtractor into DORA calculator while maintaining 100% backward compatibility with existing field_mappings system.

## Current State Analysis

**File**: `data/dora_calculator.py` (2816 lines)

**Functions to Refactor**:
1. `calculate_deployment_frequency()` - Lines 381-605 (225 lines)
2. `calculate_lead_time_for_changes()` - Lines 610-808 (199 lines)
3. `calculate_change_failure_rate()` - Lines 814-999 (186 lines)
4. `calculate_mean_time_to_recovery()` - Lines 1005-1204 (200 lines)

**Total Refactoring Scope**: ~810 lines across 4 functions

## Refactoring Strategy

### Phase 1: Dual-Mode Support (Current Approach)
Add variable extraction alongside existing field_mappings without breaking changes.

**Implementation**:
```python
def calculate_deployment_frequency(
    issues: List[Dict[str, Any]],
    field_mappings: Optional[Dict[str, str]] = None,  # Now optional
    variable_mappings: Optional[VariableMappingCollection] = None,  # NEW
    time_period_days: int = 30,
    ...
) -> Dict[str, Any]:
    # Determine mode
    use_variable_extraction = variable_mappings is not None
    
    if use_variable_extraction:
        # NEW: Extract variables from each issue
        extractor = VariableExtractor(variable_mappings)
        for issue in issues:
            vars = _extract_variables_from_issue(
                issue, ["deployment_event", "deployment_timestamp"], extractor
            )
            # Use vars["deployment_event"], vars["deployment_timestamp"]
    else:
        # LEGACY: Use existing field_mappings logic (unchanged)
        deployment_date_field = field_mappings["deployment_date"]
        # ... existing code
```

**Advantages**:
- ✅ Zero breaking changes
- ✅ Both systems work simultaneously
- ✅ Gradual migration path
- ✅ Easy to test and validate

**Disadvantages**:
- ❌ Code duplication (temporary)
- ❌ Increased function complexity
- ❌ Larger file size

### Phase 2: Deprecation (Future)
Mark field_mappings as deprecated, encourage variable_mappings usage.

### Phase 3: Migration (Far Future)
Remove legacy field_mappings support after all users migrated.

## Implementation Plan - T007

### Step 1: Add Optional Parameter ✅ DONE
- [x] Import VariableExtractor and DEFAULT_VARIABLE_COLLECTION
- [x] Add `_extract_variables_from_issue()` helper function
- [x] Unit tests for helper function (6 tests passing)

### Step 2: Refactor calculate_deployment_frequency()
**Complexity**: Medium (225 lines, moderate logic)

**Key Changes**:
1. Add `variable_mappings` optional parameter
2. Add mode detection logic
3. Implement variable extraction path:
   - Extract `deployment_event` (boolean)
   - Extract `deployment_timestamp` (datetime string)
   - Extract `deployment_successful` (boolean) - for filtering
4. Keep legacy field_mappings path unchanged
5. Update error messages for both modes

**Variables Needed**:
- `deployment_event`: Is this a deployment?
- `deployment_timestamp`: When did deployment occur?
- `deployment_successful`: Was deployment successful? (optional filter)

**Testing Strategy**:
- Unit test with variable_mappings → verify extraction works
- Unit test with field_mappings → verify legacy still works
- Unit test with both → verify variable_mappings takes precedence
- Integration test with realistic JIRA data

### Step 3: Refactor calculate_lead_time_for_changes()
**Complexity**: Medium (199 lines)

**Variables Needed**:
- `commit_timestamp`: When was code committed?
- `deployment_timestamp`: When was code deployed?

### Step 4: Refactor calculate_change_failure_rate()
**Complexity**: High (186 lines, complex incident linking logic)

**Variables Needed**:
- `deployment_event`: Identify deployments
- `deployment_timestamp`: When deployment occurred
- `is_incident`: Is this issue an incident?
- `related_deployment`: Link to causing deployment (complex)

**Challenge**: Incident-deployment linking requires careful variable design

### Step 5: Refactor calculate_mean_time_to_recovery()
**Complexity**: Medium (200 lines)

**Variables Needed**:
- `is_incident`: Identify incidents
- `incident_start_timestamp`: When incident detected
- `incident_resolved_timestamp`: When incident resolved

### Step 6: Update Unit Tests
**Affected Test Files**:
- `tests/unit/data/test_dora_calculator.py`
- Need to add tests for variable_mappings mode

### Step 7: Integration Testing
- Test with DEFAULT_VARIABLE_COLLECTION
- Test with custom variable mappings
- Test backward compatibility with existing code

## Risk Mitigation

### Risk 1: Breaking Existing Functionality
**Mitigation**: 
- Keep legacy code path 100% unchanged
- Comprehensive regression testing
- Feature flag for gradual rollout

### Risk 2: Performance Degradation
**Mitigation**:
- Variable extraction uses caching
- Benchmark before/after
- Monitor production metrics

### Risk 3: Test Coverage Gaps
**Mitigation**:
- Add tests for both modes
- Test edge cases (missing fields, null values)
- Integration tests with real JIRA data

## Success Criteria

**T007 Complete When**:
- ✅ All 4 DORA functions support variable_mappings parameter
- ✅ Legacy field_mappings mode still works (0 regressions)
- ✅ New variable extraction mode works correctly
- ✅ Unit tests pass for both modes
- ✅ Integration tests validate realistic scenarios
- ✅ Performance is acceptable (<10% overhead)
- ✅ Documentation updated

## Timeline Estimate

- Step 2 (deployment_frequency): 2-3 hours
- Step 3 (lead_time): 1-2 hours
- Step 4 (change_failure_rate): 3-4 hours (complex)
- Step 5 (mttr): 1-2 hours
- Step 6 (unit tests): 2-3 hours
- Step 7 (integration): 1-2 hours

**Total**: 10-16 hours of focused work

## Alternative Approach: New Functions

Instead of modifying existing functions, create new versions:
- `calculate_deployment_frequency_v3()` with variable extraction
- Keep `calculate_deployment_frequency()` unchanged

**Pros**:
- Zero risk to existing code
- Easier to test in isolation
- Clean separation of concerns

**Cons**:
- Code duplication
- Need to deprecate old functions
- More complex migration path

**Decision**: Use dual-mode approach (current plan) for cleaner API and easier migration.

## Next Immediate Steps

1. Start with `calculate_deployment_frequency()` refactoring
2. Create comprehensive unit tests
3. Validate with integration tests
4. Iterate on remaining functions
5. Document learnings for T008 (Flow calculator)
