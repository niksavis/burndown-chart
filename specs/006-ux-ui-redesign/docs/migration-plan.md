# Migration Plan: Old Components to New Design System

**Date Created**: 2025-10-24  
**Specification**: 006-ux-ui-redesign  
**Status**: Planning Phase

---

## Executive Summary

**Current State**:
- ✅ **New Dashboard tab** (User Story 2) - Fully functional and working
- ⚠️ **New Parameter Panel** (User Story 1) - UI implemented but callbacks not fully connected
- 📦 **Old "Input Parameters" card** - Still functional and in use
- 📦 **Old "Project Dashboard" card** - Still functional, now redundant with new Dashboard tab

**Migration Goal**: Remove old components once new ones achieve feature parity and are proven stable.

---

## Component Inventory

### 1. New Dashboard Tab (✅ Ready)
**Location**: `ui/dashboard.py`, `callbacks/dashboard.py`  
**Status**: ✅ **Fully functional**  
**Features**:
- Items forecast card
- Points forecast card  
- Project deadline card
- Completion forecast card
- Weekly velocity metrics
- Updates with parameter changes

**Old Equivalent**: "Project Dashboard" card in `ui/layout.py` (lines 220-240)

---

### 2. New Parameter Panel (⚠️ Partially Ready)
**Location**: `ui/components.py` (create_parameter_panel), `callbacks/settings.py`  
**Status**: ⚠️ **UI complete, callbacks incomplete**  
**Features Implemented**:
- Sticky positioning below header
- Collapsible with expand/collapse animation
- Shows summary values when collapsed
- All input fields present (PERT factor, deadline, scope metrics)
- State persistence (expand/collapse state)

**Features NOT Connected**:
- Parameter changes don't update calculations yet
- Need to wire new input IDs to existing calculation callbacks
- Need to verify all parameters flow through to charts

**Old Equivalent**: "Input Parameters" card in `ui/layout.py` (lines 221-227)

---

### 3. Old Components to Remove

#### A. Old "Input Parameters" Card
**Location**: `ui/layout.py` lines 221-227  
**Function**: `create_input_parameters_card()` in `ui/cards.py`  
**Currently Used By**:
- Main layout (always visible)
- All parameter adjustment workflows
- Settings callbacks

**Dependencies**:
- `callbacks/settings.py` - parameter input callbacks
- Chart update workflows
- PERT calculations

#### B. Old "Project Dashboard" Card  
**Location**: `ui/layout.py` lines 228-238  
**Function**: `create_project_summary_card()` in `ui/cards.py`  
**Currently Used By**:
- Main layout (always visible)
- Summary metrics display

**Dependencies**:
- Minimal - mostly display logic
- No critical callbacks depend on it

---

## Migration Strategy

### Phase 1: Complete New Parameter Panel (CURRENT PRIORITY)
**Timeline**: Next 1-2 days  
**Status**: 🔄 IN PROGRESS

**Tasks**:
1. ✅ T022 verification: Check if parameter callbacks are connected
2. 🔄 Wire new parameter input IDs to existing callbacks:
   - `param-panel-pert-factor` → PERT calculation
   - `param-panel-deadline` → deadline calculations
   - `param-panel-scope-*` → scope calculations
3. 🔄 Test parameter changes trigger chart updates
4. 🔄 Verify feature parity with old parameter card
5. ✅ Validate no regressions in calculations

**Acceptance Criteria**:
- [ ] All parameters in new panel update charts immediately
- [ ] PERT factor changes recalculate forecasts
- [ ] Deadline changes update timeline visualizations
- [ ] Scope changes (completed/remaining items/points) reflect in charts
- [ ] Parameter summary in collapsed state shows current values
- [ ] No errors in browser console
- [ ] All existing features work identically to old card

**Code Changes Required**:
```python
# In callbacks/settings.py - Update input IDs
# OLD IDs:
Input("pert-factor-input", "value")
Input("deadline-input", "value")
Input("completed-items-input", "value")
# etc.

# NEW IDs (from parameter panel):
Input("param-panel-pert-factor", "value")
Input("param-panel-deadline", "value")
Input("param-panel-completed-items", "value")
# etc.
```

---

### Phase 2: Side-by-Side Testing
**Timeline**: 1 day after Phase 1 completion  
**Status**: ⏳ PENDING

**Tasks**:
1. Run application with both old and new components visible
2. Test all parameter combinations:
   - Adjust PERT factor: verify both cards show same results
   - Change deadline: verify both update identically
   - Modify scope values: verify calculations match
3. Compare performance (load times, responsiveness)
4. Test mobile responsiveness of new panel
5. Gather user feedback if available

**Acceptance Criteria**:
- [ ] New parameter panel shows identical values to old card
- [ ] All calculations produce same results
- [ ] New panel performs as fast or faster than old card
- [ ] Mobile experience is improved or equivalent
- [ ] No visual glitches or layout issues

---

### Phase 3: Remove Old "Project Dashboard" Card (SAFE TO DO FIRST)
**Timeline**: Can be done immediately  
**Status**: ⏳ READY (low risk)

**Rationale**: 
- New Dashboard tab is fully functional
- Old dashboard card is now redundant
- Low risk - no critical dependencies
- Users prefer dedicated Dashboard tab

**Tasks**:
1. Remove old dashboard card from layout
2. Update layout grid (no longer need two-column layout)
3. Remove unused functions if no other references
4. Test application still loads correctly
5. Verify all metrics available in Dashboard tab

**Code Changes**:
```python
# In ui/layout.py - REMOVE lines 220-240:
create_two_column_layout(
    left_content=create_input_parameters_card(...),
    right_content=create_project_summary_card(...),  # <- REMOVE THIS
    ...
)

# Replace with single column for parameters only:
create_full_width_layout(
    create_input_parameters_card(...),  # Keep until Phase 4
    row_class="mb-4",
)
```

**Acceptance Criteria**:
- [ ] Application loads without old dashboard card
- [ ] All dashboard metrics available in Dashboard tab
- [ ] Layout looks clean without two-column section
- [ ] No broken references or import errors

---

### Phase 4: Remove Old "Input Parameters" Card (AFTER PHASE 1)
**Timeline**: After new parameter panel fully working  
**Status**: ⏳ BLOCKED (waiting on Phase 1)

**Rationale**:
- New parameter panel provides better UX (sticky, collapsible)
- Old card takes up valuable screen space
- Redundant once new panel is working

**Tasks**:
1. Remove old input parameters card from layout
2. Remove `create_input_parameters_card()` function (or mark as deprecated)
3. Clean up unused imports
4. Update any documentation
5. Test all parameter workflows work with new panel only

**Code Changes**:
```python
# In ui/layout.py - REMOVE:
create_full_width_layout(
    create_input_parameters_card(...),  # <- REMOVE THIS
    row_class="mb-4",
)

# Keep only:
html.Div(
    create_parameter_panel(settings, is_open=False),
    className="param-panel-sticky",
),
```

**Acceptance Criteria**:
- [ ] Application loads with only new parameter panel
- [ ] All parameter adjustments work correctly
- [ ] Charts update as expected
- [ ] No regressions in any workflows
- [ ] Layout feels cleaner and more modern

---

### Phase 5: Code Cleanup
**Timeline**: After all removals complete  
**Status**: ⏳ PENDING

**Tasks**:
1. Remove unused functions:
   - `create_input_parameters_card()` in `ui/cards.py`
   - `create_project_summary_card()` if only used by old layout
2. Remove unused imports
3. Update tests to use new component IDs
4. Update documentation and screenshots
5. Archive old code in git history (no need to keep commented out)

**Code Audit**:
```powershell
# Check for references to old functions
Select-String -Path "*.py" -Pattern "create_input_parameters_card|create_project_summary_card"

# Check for old input IDs
Select-String -Path "callbacks\*.py" -Pattern "pert-factor-input|deadline-input"
```

---

## Risk Assessment

### High Risk: Parameter Panel Migration (Phase 1 & 4)
**Risk**: Breaking parameter adjustments would break core functionality  
**Mitigation**:
- Keep old card active until new panel proven working
- Extensive testing of all parameter combinations
- Verify callbacks are properly wired before removal
- Monitor browser console for errors
- Have rollback plan ready

### Low Risk: Dashboard Card Removal (Phase 3)
**Risk**: Minimal - new Dashboard tab is fully functional  
**Mitigation**:
- Already tested and working
- Can be done independently
- Easy to rollback if needed

---

## Rollback Plan

If issues arise after removal:

### Emergency Rollback
```powershell
# Revert the commit
git log --oneline | Select-Object -First 5  # Find commit hash
git revert <commit-hash>

# Or restore specific file
git checkout HEAD~1 ui/layout.py
```

### Gradual Rollback
1. Re-add old component to layout
2. Update callbacks to listen to old input IDs
3. Mark new components as "beta" or hidden
4. Investigate and fix issues
5. Try migration again

---

## Testing Checklist

### Before Removing Old Components
- [ ] New parameter panel expand/collapse works
- [ ] All parameter inputs present and visible
- [ ] Parameter changes trigger chart updates
- [ ] PERT calculations correct with new inputs
- [ ] Deadline updates affect timeline
- [ ] Scope changes reflect in forecasts
- [ ] Summary values show in collapsed state
- [ ] Mobile experience acceptable
- [ ] No console errors
- [ ] Performance acceptable (no lag)

### After Removing Old Dashboard Card
- [ ] Application loads successfully
- [ ] Dashboard tab shows all metrics
- [ ] Cards are clickable and navigate correctly
- [ ] Layout looks clean and professional
- [ ] No broken references

### After Removing Old Parameter Card
- [ ] Application loads successfully
- [ ] New parameter panel is only parameter control
- [ ] All parameters adjustable
- [ ] Charts update correctly
- [ ] No regressions in calculations
- [ ] Mobile experience improved

---

## Recommended Timeline

### ✨ Optimal Migration Schedule

**Week 1: Complete Parameter Panel**
- Days 1-2: Wire parameter panel callbacks (Phase 1)
- Days 3-4: Side-by-side testing (Phase 2)
- Day 5: Fix any issues found

**Week 2: Remove Old Components**
- Day 1: Remove old dashboard card (Phase 3) - LOW RISK
- Day 2-3: Final parameter panel validation
- Day 4: Remove old parameter card (Phase 4)
- Day 5: Code cleanup (Phase 5)

**Total Time**: ~2 weeks for safe, tested migration

---

## Quick Win Option (Lower Risk)

**You can remove the old Project Dashboard card TODAY** since:
1. ✅ New Dashboard tab is fully functional
2. ✅ No critical dependencies on old card
3. ✅ Easy to rollback if needed
4. ✅ Immediate UX improvement (less clutter)

**How to do it**:
1. Comment out old dashboard card in `ui/layout.py`
2. Test application loads and Dashboard tab works
3. If everything works, delete the commented code
4. Commit with clear message: "Remove redundant old dashboard card, replaced by Dashboard tab (User Story 2)"

---

## Conclusion

**Current Priority**: 🎯 **Phase 1 - Complete New Parameter Panel**

**Optimal Time to Remove**:
- **Old Dashboard Card**: ✅ NOW (safe, new Dashboard tab works)
- **Old Parameter Card**: ⏳ AFTER new parameter panel callbacks are connected and tested (Phase 1 complete)

**Estimated Time to Full Migration**: 1-2 weeks with proper testing

**Next Step**: Wire parameter panel input IDs to existing callbacks (T022 completion)

---

**Questions? Decisions Needed?**
1. Do you want to remove old dashboard card now (quick win)?
2. Should we prioritize completing parameter panel callbacks before other work?
3. Any specific testing scenarios you want validated?
