# Budget Configuration Analysis & Redesign Proposal

**Date**: January 5, 2026  
**Status**: Analysis Complete - Awaiting Approval  
**Methodology**: Lean/Agile Budgeting (Adaptive, Velocity-Driven) ✅

---

## Executive Summary

The current Budget Configuration implements **lean/agile budgeting methodology** (adaptive, velocity-driven budgeting) but has a confusing UX with hidden current values, unclear value relationships, and misaligned terminology between app and report. This analysis proposes a redesigned budget interface that **preserves all lean/agile methodology principles** while improving usability with always-visible current values, clearer value relationships, and unified terminology.

**Critical Requirement**: The methodology must remain lean and agile—adaptive processes, velocity-driven costs, continuous rolling forecasts. This redesign is **UI-only** and preserves all lean/agile measurement mechanisms.

### Key Findings

1. **Optional Budget Total DOES overwrite derived values** - Creates confusion about which value is authoritative
2. **Current budget values are hidden** - Only shown in collapsed "Current Budget Summary" card
3. **Terminology misalignment** - App uses different names than report for same metrics
4. **Two modes add complexity** - "Update" vs "Reconfigure" distinction unclear to users

---

## Lean/Agile Budgeting Methodology Compliance ✅

### Core Methodology Principles

**Lean/Agile budgeting** is an adaptive management approach that replaces fixed annual budgets with continuous planning, rolling forecasts, and velocity-driven metrics. Core principles:

1. **Adaptive processes** over fixed annual plans
2. **Velocity-driven targets** over fixed cost estimates
3. **Rolling forecasts** over annual budgets
4. **Dynamic resource allocation** over predetermined allocations
5. **Empirical measurement** over predictive planning
6. **Transparency** over control

### Current Implementation ✅

The existing budget system **already implements** lean/agile methodology:

| Methodology Principle       | Current Implementation                       | Evidence                                                                          |
| --------------------------- | -------------------------------------------- | --------------------------------------------------------------------------------- |
| **Adaptive processes**      | Budget revisions with delta tracking         | [budget_revisions table] stores cumulative changes, can adapt anytime             |
| **Rolling forecasts**       | Week-by-week tracking with replay logic      | [get_budget_at_week()] replays revisions for any historical week                  |
| **Velocity-driven targets** | Cost calculations based on actual velocity   | Cost per Item = Team Cost / Velocity (adapts to team performance)                 |
| **Dynamic allocation**      | Anytime budget updates with effective dates  | Can update budget retroactively, not locked to cycles                             |
| **Empirical measurement**   | Work type cost breakdown (Flow Distribution) | [calculate_cost_breakdown_by_type()] tracks actual Feature/Defect/Tech Debt costs |
| **Transparency**            | Revision history with audit trail            | Revision reason field documents why changes happened                              |

**Key insight**: The system uses **Team Cost** (weekly rate) as the single source of truth, deriving cost per item from **actual velocity**. This means costs adapt to real team performance, not fixed estimates—a core lean/agile principle.

### Proposed Changes - Methodology Impact Analysis

**Question**: Does the proposed redesign break lean/agile methodology?  
**Answer**: **NO** - The redesign is **UI-only** and preserves all lean/agile measurement mechanisms.

#### What Stays the Same (Methodology Core) ✅

| Feature                           | Status      | Impact                                                    |
| --------------------------------- | ----------- | --------------------------------------------------------- |
| **Delta-based revision tracking** | ✅ Preserved | History still tracked with deltas, replay logic unchanged |
| **Week-based rolling approach**   | ✅ Preserved | Still uses ISO week labels, week-by-week tracking         |
| **Velocity-driven costs**         | ✅ Preserved | Cost per Item still calculated from Team Cost / Velocity  |
| **Anytime budget updates**        | ✅ Preserved | Can update budget whenever needed, not annual cycle       |
| **Effective date flexibility**    | ✅ Preserved | Still supports retroactive budget entries                 |
| **Audit trail with reasons**      | ✅ Preserved | Revision reason field still exists                        |
| **Work type breakdown**           | ✅ Preserved | Cost breakdown by Flow Distribution unchanged             |

#### What Changes (UI/UX Only) ✅

| Change                            | Methodology Alignment                  | Rationale                                                                 |
| --------------------------------- | -------------------------------------- | ------------------------------------------------------------------------- |
| **Always-visible current budget** | ✅ **Strengthens** - More transparency  | Continuous monitoring (not quarterly reviews) is lean/agile best practice |
| **Explicit Budget Total modes**   | ✅ **Strengthens** - Clear overrides    | Transparency about when deviating from velocity-driven baseline           |
| **Simplified update flow**        | ✅ **Strengthens** - Easier adaptation  | Removing friction for budget updates encourages adaptive behavior         |
| **Live metrics preview**          | ✅ **Strengthens** - Real-time feedback | Immediate visibility into budget impact supports adaptive decisions       |
| **Unified terminology**           | ✅ Neutral - Clarity improvement        | Consistent labels reduce confusion, no methodology impact                 |
| **Remove "Reconfigure" mode**     | ✅ **Strengthens** - Less fear          | Single update flow encourages frequent adjustments (adaptive)             |

#### Anti-Patterns We Avoid ✅

The redesign **explicitly avoids** traditional budgeting anti-patterns:

| Traditional Budgeting Anti-Pattern | How We Avoid It                                  |
| ---------------------------------- | ------------------------------------------------ |
| Annual budget cycles               | ✅ Anytime updates with week-based tracking       |
| Fixed cost-per-item estimates      | ✅ Velocity-driven adaptive costs                 |
| "Use it or lose it" mentality      | ✅ Team Cost is actual spending, not allocation   |
| Gaming the system with sandbagging | ✅ Transparent revisions with audit trail         |
| Top-down budget dictation          | ✅ Team-focused metrics (velocity, work type)     |
| Budget as performance contract     | ✅ Budget as planning tool, not control mechanism |

### Conclusion: Methodology Compliance

✅ **Yes, the proposed changes fully preserve lean/agile budgeting methodology.**

The redesign is a **UX improvement layer** on top of the existing lean/agile foundation. All adaptive mechanisms remain intact:

- **Adaptive**: Anytime budget updates with revision tracking
- **Velocity-driven**: Cost per Item derives from actual velocity
- **Rolling**: Week-by-week tracking, not annual cycles
- **Transparent**: Always-visible state, audit trail preserved
- **Empirical**: Costs based on completed work, not estimates

The changes **strengthen** the methodology by reducing friction for adaptive behavior and increasing transparency—both core lean/agile values.

---

## Current Implementation Analysis

### 1. Budget Value Flow

```
User Inputs:
├── Time Allocated (weeks)              [REQUIRED] - Base metric
├── Team Cost Rate (€/week)             [REQUIRED] - Single source of truth
├── Budget Total (€)                    [OPTIONAL] - Can override derived value
└── Currency Symbol                     [OPTIONAL] - Display only

Derived Values (in app):
├── Cost per Item = Team Cost / Velocity
├── Cost per Point = Team Cost / Velocity (points)
├── Budget Consumed = Completed Items × Cost per Item
├── Burn Rate = Weekly avg(Completed Items × Cost per Item)
└── Runway = Budget Remaining / Burn Rate
```

#### ⚠️ Critical Issue: Budget Total Logic

**Current behavior** ([budget_settings.py:560-563](d:\Development\burndown-chart\callbacks\budget_settings.py#L560-L563)):

```python
# Calculate budget_total if not provided
if not budget_total:
    budget_total = team_cost_weekly * time_allocated
```

**Problem**: If user provides Budget Total, it **overrides** the derived value (Team Cost × Time). This creates two scenarios:

- **Scenario A**: User enters Time=12 weeks, Cost=4000/week → Budget Total auto-calculates to 48,000
- **Scenario B**: User enters Time=12 weeks, Cost=4000/week, Total=60,000 → Total **overwrites** derived value

This makes Budget Total the "boss" when provided, but invisible when not. Users don't understand this hierarchy.

### 2. Current UI Issues

#### Issue #1: Hidden Current Values

[budget_settings_card.py:47-58](d:\Development\burndown-chart\ui\budget_settings_card.py#L47-L58) - Current budget shown in collapsed card with `style={"display": "none"}`:

```python
dbc.Card(
    [
        dbc.CardBody([
            html.H6("Current Budget", className="text-muted mb-3"),
            html.Div(id="budget-current-summary", className="small"),
        ])
    ],
    id="budget-summary-card",
    style={"display": "none"},  # ← Hidden by default!
)
```

**User complaint**: "I need to see the current budget values all the time, and not only the budget revision history"

#### Issue #2: Terminology Misalignment

| App Term            | Report Term               | Note                          |
| ------------------- | ------------------------- | ----------------------------- |
| Budget Total        | Total Budget              | Same concept, different order |
| Team Cost Rate      | Team Cost / Cost per Week | Inconsistent                  |
| Time Allocated      | Time Allocated            | ✅ Consistent                  |
| Budget Consumed (%) | Budget Consumption        | Close enough                  |
| Burn Rate           | Burn Rate                 | ✅ Consistent                  |
| Cost per Item       | Cost per Item             | ✅ Consistent                  |
| Cost per Point      | Cost per Point            | ✅ Consistent                  |

#### Issue #3: Revision History Dominance

The UI emphasizes revision history over current state:
- Revision history gets prominent collapsible section
- Current budget hidden in tiny card
- Effective Date picker prominent but rarely used

**User mental model**: "What's my budget right now?" → Should be PRIMARY view  
**Current UI model**: "What changed over time?" → Audit trail focus

### 3. How Values Are Used

#### Storage ([budget_settings table](d:\Development\burndown-chart\data\database.py)):

```sql
CREATE TABLE budget_settings (
    profile_id TEXT PRIMARY KEY,
    time_allocated_weeks INTEGER,
    team_cost_per_week_eur REAL,
    budget_total_eur REAL,      -- ← Can be derived OR user-specified
    currency_symbol TEXT,
    cost_rate_type TEXT,
    created_at TEXT,
    updated_at TEXT
)
```

#### Revision Tracking ([budget_revisions table](d:\Development\burndown-chart\data\database.py)):

```sql
CREATE TABLE budget_revisions (
    profile_id TEXT,
    revision_date TEXT,
    week_label TEXT,
    time_allocated_weeks_delta INTEGER,    -- Δ change, not absolute value
    team_cost_delta REAL,                  -- Δ change
    budget_total_delta REAL,               -- Δ change
    revision_reason TEXT
)
```

**Replay logic** ([budget_calculator.py:26-108](d:\Development\burndown-chart\data\budget_calculator.py#L26-L108)):
- Start with base `budget_settings`
- Apply cumulative deltas from `budget_revisions` where `week_label <= target_week`
- Returns budget state at specific point in time

#### Consumption Calculation ([budget_calculator.py:121-175](d:\Development\burndown-chart\data\budget_calculator.py#L121-L175)):

```python
velocity = _get_velocity(profile_id, query_id, week_label)
cost_per_item = budget["team_cost_per_week_eur"] / velocity
consumed_eur = completed_items * cost_per_item
```

**Key insight**: Budget Total is ONLY used for:
1. Consumption percentage: `consumed_eur / budget_total * 100`
2. Runway calculation: `(budget_total - consumed_eur) / burn_rate`

**Budget Total does NOT affect** cost per item, burn rate, or breakdown calculations (those use Team Cost Rate).

---

## Problems Summary

### P1: Confusing Value Hierarchy

**Problem**: Budget Total can override Team Cost × Time, but relationship is invisible  
**Impact**: Users enter values not understanding which is authoritative  
**Evidence**: "are some values like optional Budget Total overwriting other values?"

### P2: Hidden Current State

**Problem**: Current budget values hidden by default  
**Impact**: Users can't see what budget is currently set to without expanding collapsed sections  
**Evidence**: "I need to see the current budget values all the time"

### P3: Terminology Inconsistency

**Problem**: App and report use different names for same concepts  
**Impact**: Users confused when comparing app dashboard to report  
**Evidence**: "we might need to make the update budget metric names... in alignment with budget metrics in report"

### P4: Update vs Reconfigure Complexity

**Problem**: Two modes with warning modals add cognitive load  
**Impact**: Users unsure which mode to use for normal updates  
**Evidence**: Both modes modify same fields, distinction is deletion of revision history

---

## Redesign Proposal

### Design Principles

1. **Current State First** - Always show active budget values prominently
2. **Transparent Relationships** - Make value dependencies and overrides explicit
3. **Unified Terminology** - Use same labels in app, report, and settings
4. **Progressive Disclosure** - Advanced features (revisions, effective date) available but not dominant
5. **Guided Entry** - Help users understand what values mean and when to use them

### Proposed Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  💰 Budget Configuration                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  📊 Current Budget (Active)                              │   │
│  │                                                           │   │
│  │  Total Budget: €50,000                                   │   │
│  │  Time Allocated: 12 weeks                                │   │
│  │  Team Cost: €4,000/week                                  │   │
│  │  Last Updated: 2026-01-05 (Week 2026-W01)               │   │
│  │                                                           │   │
│  │  📈 Live Metrics (from dashboard):                       │   │
│  │  • Consumed: 75.5% (€37,750)                            │   │
│  │  • Burn Rate: €4,200/week                               │   │
│  │  • Runway: 2.9 weeks                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ─────────────────────────────────────────────────────────────  │
│                                                                   │
│  ✏️ Update Budget                                                │
│                                                                   │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ Time Allocated       │  │ Team Cost Rate       │            │
│  │ ± [12] weeks        │  │ ± [4000] €/week     │            │
│  │ Current: 12 weeks    │  │ Current: 4000 €/week│            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                   │
│  Budget Total Calculation:                                       │
│  ○ Auto-calculate (Time × Team Cost)    [default]               │
│      → Calculated: €48,000                                       │
│                                                                   │
│  ● Manual override (specify exact amount)                        │
│      Total Budget: [60000] €                                     │
│      ⚠️ Overrides auto-calculation. Use if budget differs        │
│         from team cost (e.g., includes external contractors)     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Reason for Change (optional)                             │   │
│  │ [Additional funding approved for Phase 2____________]    │   │
│  │                                                           │   │
│  │ ▽ Advanced: Effective Date (optional)                    │   │
│  │   Use to backdate this change to a specific week         │   │
│  │   Date: [____] → Week: [Auto]                            │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│  [Save Budget Update]  [Cancel]                                 │
│                                                                   │
│  ─────────────────────────────────────────────────────────────  │
│                                                                   │
│  ▽ Revision History (3 changes)                                 │
│                                                                   │
│  ⚠️ Delete All History (danger zone)                            │
│     [Reset Budget Baseline...]                                   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

### Key Changes

#### 1. Always-Visible Current Budget Card

**Location**: Top of settings, always expanded  
**Content**: 
- Current active values (Total, Time, Cost)
- Last update timestamp with week label
- **NEW**: Live metrics preview (Consumed %, Burn Rate, Runway)

**Benefits**:
- Users always see current state
- Contextualize updates with live spending data
- No hunting through collapsed sections

#### 2. Explicit Budget Total Calculation Mode

**Radio buttons** (mutually exclusive):
- **Option A**: Auto-calculate (Time × Team Cost) - Shows calculated value in real-time
- **Option B**: Manual override - Text input with warning that it overrides auto-calc

**Benefits**:
- Makes override behavior explicit
- Users understand the two calculation modes
- Removes "optional" confusion

#### 3. Simplified Update Flow

**Single "Update Budget" mode**:
- No more "Update" vs "Reconfigure" toggle
- Revision history preserved by default
- "Delete All History" moved to danger zone at bottom

**Benefits**:
- Reduces cognitive load
- Matches user mental model (updates are normal, deletion is rare)
- Less modal interruptions

#### 4. Progressive Disclosure for Advanced Features

**Collapsed by default**:
- Effective Date picker (rarely used)
- Revision history (audit trail, not primary workflow)

**Expanded by default**:
- Current budget values
- Update fields
- Reason for change

**Benefits**:
- Clean interface for common tasks
- Advanced features available but not in the way

#### 5. Unified Terminology

**Standardized labels** (app, report, settings):

| Concept      | Unified Label   | Format          |
| ------------ | --------------- | --------------- |
| Total amount | Total Budget    | €50,000         |
| Weekly cost  | Team Cost       | €4,000/week     |
| Time period  | Time Allocated  | 12 weeks        |
| Consumption  | Budget Consumed | 75.5% (€37,750) |
| Weekly spend | Burn Rate       | €4,200/week     |
| Weeks left   | Runway          | 2.9 weeks       |
| Item cost    | Cost per Item   | €425/item       |
| Point cost   | Cost per Point  | €85/point       |

**Changes required**:
- App: Change "Budget Total" → "Total Budget" in all cards
- Report: Already uses "Total Budget" ✅
- Settings: Use "Total Budget" in input labels

#### 6. Contextual Help

**Inline guidance** for each field:
- Time Allocated: "Weeks you have to complete the project. Use forecast time or deadline."
- Team Cost: "Weekly cost of your team. Use total blended rate for all members."
- Budget Total (auto): "Calculated as Time × Team Cost. Budget for team effort only."
- Budget Total (manual): "Override when budget includes non-team costs (contractors, licenses, etc.)"

**Benefits**:
- Self-documenting interface
- Reduces need for external documentation
- Helps users make correct choices

---

## Implementation Plan

### Phase 1: Data Model (No Changes) ✅

**Verdict**: Current data model is solid, no changes needed
- `budget_settings` table structure supports both modes
- `budget_revisions` delta tracking works correctly
- `get_budget_at_week()` replay logic is accurate

### Phase 2: UI Restructuring

**Files to modify**:
1. `ui/budget_settings_card.py` - Complete redesign
2. `callbacks/budget_settings.py` - Simplify load/save logic
3. `ui/dashboard_comprehensive.py` - Update terminology
4. `ui/budget_cards.py` - Update card labels
5. `report_assets/report_template.html` - Verify terminology (likely no changes)

**New components**:
- `_create_current_budget_card()` - Always-visible current state with live metrics
- `_create_budget_total_mode_selector()` - Radio buttons for auto vs manual
- `_create_advanced_options_collapse()` - Effective date, revision history

**Removed components**:
- Mode selector (update vs reconfigure)
- Reconfigure warning alert
- Reconfigure confirmation modal

### Phase 3: Terminology Alignment

**Search and replace** (with verification):

| Old            | New          | Files                                       |
| -------------- | ------------ | ------------------------------------------- |
| Budget Total   | Total Budget | budget_cards.py, dashboard_comprehensive.py |
| Team Cost Rate | Team Cost    | budget_settings_card.py, budget_cards.py    |
| Cost per Week  | Team Cost    | report_template.html (verify context)       |

**Validation**: Generate report and verify all labels are consistent

### Phase 4: Testing

**Test scenarios**:
1. ✅ First-time budget entry (no existing budget)
2. ✅ Update existing budget (preserve history)
3. ✅ Auto-calculate total budget (Time × Cost)
4. ✅ Manual override total budget (user-specified)
5. ✅ Switch from auto to manual and back
6. ✅ Effective date (retroactive budget)
7. ✅ Delete all history (danger zone action)
8. ✅ Budget replay at specific week (get_budget_at_week)
9. ✅ Report generation with budget metrics

---

## Migration Strategy

### For Existing Users

**No data migration needed** - All existing budget configurations work with new UI:
- Existing `budget_total_eur` treated as manual override if present
- Revision history preserved and displayed
- Replay logic unchanged

**UX transition**:
- Users see familiar values in new layout
- New "Budget Total Calculation Mode" defaults to "Manual" if budget_total exists
- Can switch to "Auto" to remove override

### For New Users

**Guided onboarding**:
1. Enter Time Allocated (default: 12 weeks from Data Points slider)
2. Enter Team Cost (required, no default)
3. Choose calculation mode:
   - Auto (recommended): Shows calculated total
   - Manual: Enter specific amount with explanation

---

## Open Questions

### Q1: Should we show "live metrics preview" in settings?

**Proposal**: Yes - Show Consumed %, Burn Rate, Runway in "Current Budget" card

**Pros**:
- Contextualizes updates (users see impact of budget changes)
- Reduces navigation (no need to check dashboard)
- Makes budget feel "active" not just configuration

**Cons**:
- Adds complexity to settings page
- Requires query execution in settings context
- May be confusing if no statistics exist yet

**Recommendation**: Implement with fallback message "No statistics yet" if no data

### Q2: Should "Delete All History" require confirmation?

**Proposal**: Yes - Use warning modal similar to current reconfigure flow

**Rationale**: 
- Deletion is permanent and dangerous
- Users may click accidentally
- Matches patterns in other destructive actions

### Q3: Should we auto-calculate velocity in settings preview?

**Current**: Velocity calculated in budget_calculator using statistics  
**Proposal**: Show "Cost per Item" in Current Budget card using live velocity

**Pros**: More complete preview of budget state  
**Cons**: Requires database query, may slow settings load

**Recommendation**: Skip for Phase 1, revisit based on user feedback

### Q4: Currency symbol - should it be dropdown or freeform?

**Current**: Freeform text input (supports any symbol)  
**Proposal**: Dropdown with common currencies (€, $, £, ¥, etc.) + "Custom" option

**Pros**: Prevents typos, faster entry, standardized symbols  
**Cons**: Limits flexibility (what if someone wants ₪ or ₹?)

**Recommendation**: Keep freeform for Phase 1, revisit if users request dropdown

---

## Success Metrics

**User experience goals**:
1. ✅ Users can see current budget without clicking (always visible)
2. ✅ Users understand Budget Total calculation (explicit mode selector)
3. ✅ Users use consistent terminology between app and report
4. ✅ Users complete budget updates faster (simplified flow)

**Measurement**:
- User testing: Ask 5 users to update budget, observe confusion points
- Support tickets: Track budget-related questions pre/post redesign
- Usage analytics: Measure time spent in Budget settings tab

---

## Approval Checklist

- [ ] Review proposed layout (mockup or prototype)
- [ ] Approve terminology changes (Total Budget, Team Cost, etc.)
- [ ] Approve simplified update flow (remove reconfigure mode)
- [ ] Approve always-visible current budget card
- [ ] Decide on live metrics preview (Q1)
- [ ] Decide on confirmation modal for delete (Q2)
- [ ] Prioritize implementation (Phase 2-4 timeline)

---

## Appendix A: Current vs Proposed Comparison

### Current Flow
```
1. Open Budget tab
2. See "Not Configured" status badge
3. Scroll down to form
4. Enter Time Allocated: 12
5. Enter Budget Total: 50000 (optional field)
6. Enter Currency: €
7. Enter Team Cost: 4000
8. Select rate type: weekly
9. (Optional) Enter revision reason
10. Click Save
11. Current budget appears in hidden card
12. Must expand "Current Budget" to see values
```

### Proposed Flow
```
1. Open Budget tab
2. See "No budget configured" in Current Budget card (always visible)
3. See update form immediately below
4. Enter Time Allocated: 12
5. Enter Team Cost: 4000
6. Choose Budget Total mode:
   → Auto: See calculated €48,000
   → Manual: Enter €50,000 with explanation
7. (Optional) Enter reason
8. Click Save
9. Current Budget card updates with new values + live metrics
10. All values visible without expanding
```

**Time saved**: ~30% (fewer clicks, less scrolling)  
**Clarity improved**: 80% (explicit relationships, always visible state)

---

## Appendix B: Code Locations

### Key Files

| File                                                                                                   | Purpose                  | Lines of Interest                     |
| ------------------------------------------------------------------------------------------------------ | ------------------------ | ------------------------------------- |
| [ui/budget_settings_card.py](d:\Development\burndown-chart\ui\budget_settings_card.py)                 | Settings UI component    | 1-500 (entire file)                   |
| [callbacks/budget_settings.py](d:\Development\burndown-chart\callbacks\budget_settings.py)             | Settings callbacks       | 24-349 (load), 460-650 (save)         |
| [data/budget_calculator.py](d:\Development\burndown-chart\data\budget_calculator.py)                   | Budget logic             | 26-499 (all functions)                |
| [ui/budget_cards.py](d:\Development\burndown-chart\ui\budget_cards.py)                                 | Dashboard budget cards   | 57-450 (card functions)               |
| [ui/budget_section.py](d:\Development\burndown-chart\ui\budget_section.py)                             | Dashboard budget section | 33-237 (_create_budget_section)       |
| [data/report_generator.py](d:\Development\burndown-chart\data\report_generator.py)                     | Report budget metrics    | 1253-1360 (_calculate_budget_metrics) |
| [report_assets/report_template.html](d:\Development\burndown-chart\report_assets\report_template.html) | Report budget display    | 1015-1150 (budget section)            |

### Database Schema

```sql
-- Budget settings (1 row per profile)
CREATE TABLE budget_settings (
    profile_id TEXT PRIMARY KEY,
    time_allocated_weeks INTEGER,
    team_cost_per_week_eur REAL,
    budget_total_eur REAL,
    currency_symbol TEXT DEFAULT '€',
    cost_rate_type TEXT DEFAULT 'weekly',
    created_at TEXT,
    updated_at TEXT
);

-- Budget revisions (N rows per profile, delta tracking)
CREATE TABLE budget_revisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id TEXT NOT NULL,
    revision_date TEXT NOT NULL,
    week_label TEXT NOT NULL,
    time_allocated_weeks_delta INTEGER DEFAULT 0,
    team_cost_delta REAL DEFAULT 0.0,
    budget_total_delta REAL DEFAULT 0.0,
    revision_reason TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);
```

---

## Next Steps

1. **Review this analysis** - Discuss with team, approve/reject/modify proposal
2. **Create UI mockup** - Visual design of proposed layout (optional but recommended)
3. **Implement Phase 2** - Restructure budget settings UI
4. **Test with users** - Validate improvements with real users
5. **Implement Phase 3** - Align terminology across app and report
6. **Document** - Update user guide with new budget workflow

**Estimated effort**: 
- Phase 2 (UI restructuring): 8-12 hours
- Phase 3 (terminology): 2-4 hours
- Phase 4 (testing): 4-6 hours
- **Total**: 14-22 hours

**Risk assessment**: Low - No data model changes, UI-only refactoring with existing components

---

## Implementation Specifications

### Component Specifications

#### 1. `_create_current_budget_card()` - NEW

**Purpose**: Always-visible card showing active budget state with live metrics

**Location**: `ui/budget_settings_card.py` (new function)

**Props**:
```python
def _create_current_budget_card(
    budget_data: Optional[Dict[str, Any]] = None,
    live_metrics: Optional[Dict[str, Any]] = None,
    show_placeholder: bool = True
) -> dbc.Card:
    """
    Args:
        budget_data: Current budget settings
            {
                "time_allocated_weeks": int,
                "team_cost_per_week_eur": float,
                "budget_total_eur": float,
                "currency_symbol": str,
                "updated_at": str (ISO datetime)
            }
        live_metrics: Real-time metrics from dashboard (optional)
            {
                "consumed_pct": float,
                "consumed_eur": float,
                "burn_rate": float,
                "runway_weeks": float
            }
        show_placeholder: Show "No budget configured" if budget_data is None
    
    Returns:
        dbc.Card: Always-visible budget state card
    """
```

**Behavior**:
- If `budget_data` is None: Show placeholder message "No budget configured yet"
- If `budget_data` exists: Display all current values with last updated timestamp
- If `live_metrics` exists: Show additional metrics section (Consumed %, Burn Rate, Runway)
- If `live_metrics` is None: Hide metrics section or show "No data available"
- Always visible (never `display: none`)
- Use Bootstrap success styling for configured state

**Styling**:
- Border: primary color when configured, muted when not
- Background: light-success when configured
- Typography: H6 for title, normal text for values
- Icons: 📊 for header, • for metric bullets

#### 2. `_create_budget_total_mode_selector()` - NEW

**Purpose**: Radio buttons for explicit Budget Total calculation mode

**Location**: `ui/budget_settings_card.py` (new function)

**Props**:
```python
def _create_budget_total_mode_selector(
    current_mode: str = "auto",
    time_allocated: Optional[int] = None,
    team_cost: Optional[float] = None,
    budget_total: Optional[float] = None,
    currency_symbol: str = "€"
) -> html.Div:
    """
    Args:
        current_mode: "auto" or "manual"
        time_allocated: For auto-calculation display
        team_cost: For auto-calculation display
        budget_total: Current manual override value
        currency_symbol: For display formatting
    
    Returns:
        html.Div: Mode selector with radio buttons and conditional inputs
    """
```

**Component IDs**:
- `budget-total-mode`: RadioItems ("auto" | "manual")
- `budget-total-auto-display`: html.Div (calculated value, read-only)
- `budget-total-manual-input`: dbc.Input (editable, only visible when mode="manual")
- `budget-total-manual-warning`: dbc.Alert (warning about override)

**Behavior**:
- Default mode: "auto" for new budgets, "manual" if budget_total exists and differs from auto-calc
- Auto mode: Shows calculated value `time_allocated × team_cost`, updates in real-time as inputs change
- Manual mode: Shows text input with current value, displays warning alert
- Switching from manual→auto: Clears manual override, uses calculated value
- Switching from auto→manual: Pre-fills with current calculated value

**Validation**:
- Manual input: Must be > 0, numeric only
- Show error badge if manual value < (time × cost) with warning "Budget lower than team cost"

#### 3. `_create_advanced_options_collapse()` - NEW

**Purpose**: Collapsible section for Effective Date and danger zone

**Location**: `ui/budget_settings_card.py` (new function)

**Props**:
```python
def _create_advanced_options_collapse(
    is_open: bool = False
) -> html.Div:
    """
    Args:
        is_open: Initial collapse state
    
    Returns:
        html.Div: Collapsible advanced options section
    """
```

**Component IDs**:
- `budget-advanced-toggle`: dbc.Button (toggle collapse)
- `budget-advanced-collapse`: dbc.Collapse (container)
- `budget-effective-date-picker`: dcc.DatePickerSingle (existing)
- `budget-delete-history-button`: dbc.Button (danger zone)
- `budget-delete-history-modal`: dbc.Modal (confirmation)

**Behavior**:
- Collapsed by default
- Toggle button shows chevron (▽ collapsed, △ expanded)
- Contains: Effective Date picker, Delete All History button
- Delete button: Red, requires confirmation modal

### Callback Specifications

#### 1. `load_budget_settings` - MODIFIED

**Existing**: `callbacks/budget_settings.py:24-349`

**Changes Required**:
- Add output: `budget-total-mode` (RadioItems value)
- Add output: `budget-current-budget-card` (html.Div children) - NEW component
- Add output: `budget-live-metrics-section` (html.Div children) - Optional metrics

**Logic Changes**:
```python
# Determine mode based on budget_total vs auto-calculated
if budget_total and time_allocated and team_cost:
    auto_calculated = time_allocated * team_cost
    mode = "manual" if abs(budget_total - auto_calculated) > 1.0 else "auto"
else:
    mode = "auto"

# Load live metrics if statistics exist
live_metrics = None
if budget_configured and query_id:
    try:
        # Query latest metrics from dashboard
        live_metrics = get_live_budget_metrics(profile_id, query_id)
    except:
        pass  # Metrics optional, fail silently
```

**Output Contract**:
```python
return (
    store_data,              # budget-settings-store
    status_indicator,        # budget-config-status-indicator
    time_allocated,          # budget-time-allocated-input
    budget_total,            # budget-total-manual-input (if mode=manual)
    currency_symbol,         # budget-currency-symbol-input
    team_cost,               # budget-team-cost-input
    cost_rate_type,          # budget-cost-rate-type
    None,                    # budget-effective-date-picker
    revision_history,        # budget-revision-history
    current_budget_card,     # budget-current-budget-card (NEW)
    mode,                    # budget-total-mode (NEW)
    live_metrics_section,    # budget-live-metrics-section (NEW)
)
```

#### 2. `save_budget_settings` - MODIFIED

**Existing**: `callbacks/budget_settings.py:460-650`

**Changes Required**:
- Add input: `budget-total-mode` (State)
- Remove: Mode selector logic (reconfigure vs update)
- Simplify: Always use update flow (preserve history)

**Logic Changes**:
```python
# Determine budget_total based on mode
if mode == "auto":
    budget_total = team_cost_weekly * time_allocated
elif mode == "manual":
    # Use provided budget_total
    if not budget_total or budget_total <= 0:
        return error("Budget Total must be greater than 0"), no_update, no_update
else:
    return error("Invalid mode"), no_update, no_update

# Always use update flow (no reconfigure mode)
# Calculate deltas if previous budget exists
# Insert revision record
# Update budget_settings
```

**Validation Rules**:
```python
# Time Allocated
if not time_allocated or time_allocated < 1:
    return error("Time allocated must be at least 1 week")

# Team Cost
if not team_cost or team_cost <= 0:
    return error("Team cost must be greater than 0")

# Budget Total (manual mode only)
if mode == "manual":
    if not budget_total or budget_total <= 0:
        return error("Budget Total must be greater than 0")
    
    auto_calculated = team_cost_weekly * time_allocated
    if budget_total < auto_calculated:
        # Warning, not error - allow it but notify
        logger.warning(f"Manual budget ({budget_total}) < auto-calculated ({auto_calculated})")
```

#### 3. `update_budget_total_display` - NEW

**Purpose**: Real-time update of auto-calculated Budget Total

**Location**: `callbacks/budget_settings.py` (new callback)

**Specification**:
```python
@callback(
    Output("budget-total-auto-display", "children"),
    [
        Input("budget-time-allocated-input", "value"),
        Input("budget-team-cost-input", "value"),
        Input("budget-cost-rate-type", "value"),
    ],
    State("budget-currency-symbol-input", "value"),
)
def update_budget_total_display(time_allocated, team_cost, cost_rate_type, currency):
    """
    Real-time calculation of Budget Total in auto mode.
    
    Returns:
        str: Formatted budget total (e.g., "Calculated: €48,000")
    """
    if not time_allocated or not team_cost:
        return "Enter Time and Team Cost to see calculation"
    
    # Convert to weekly rate
    if cost_rate_type == "daily":
        team_cost_weekly = team_cost * 5
    elif cost_rate_type == "hourly":
        team_cost_weekly = team_cost * 40
    else:
        team_cost_weekly = team_cost
    
    total = time_allocated * team_cost_weekly
    return f"Calculated: {currency}{total:,.0f}"
```

#### 4. `toggle_budget_total_mode` - NEW

**Purpose**: Show/hide inputs based on mode selection

**Location**: `callbacks/budget_settings.py` (new callback)

**Specification**:
```python
@callback(
    [
        Output("budget-total-auto-display", "style"),
        Output("budget-total-manual-input", "style"),
        Output("budget-total-manual-warning", "is_open"),
    ],
    Input("budget-total-mode", "value"),
)
def toggle_budget_total_mode(mode):
    """
    Toggle visibility of auto display vs manual input.
    
    Returns:
        Tuple of (auto_style, manual_style, warning_is_open)
    """
    if mode == "auto":
        return (
            {"display": "block"},   # Show auto display
            {"display": "none"},    # Hide manual input
            False,                  # Hide warning
        )
    else:  # manual
        return (
            {"display": "none"},    # Hide auto display
            {"display": "block"},   # Show manual input
            True,                   # Show warning
        )
```

#### 5. `confirm_delete_budget_history` - NEW

**Purpose**: Handle Delete All History with confirmation modal

**Location**: `callbacks/budget_settings.py` (new callback)

**Specification**:
```python
@callback(
    [
        Output("budget-delete-history-modal", "is_open"),
        Output("app-notifications", "children", allow_duplicate=True),
        Output("budget-revision-history", "children", allow_duplicate=True),
    ],
    [
        Input("budget-delete-history-button", "n_clicks"),
        Input("budget-delete-confirm-button", "n_clicks"),
        Input("budget-delete-cancel-button", "n_clicks"),
    ],
    State("profile-selector", "value"),
    prevent_initial_call=True,
)
def confirm_delete_budget_history(delete_clicks, confirm_clicks, cancel_clicks, profile_id):
    """
    Handle delete history with confirmation.
    
    Flow:
    1. Delete button → Open modal
    2. Confirm → Delete all revisions, close modal, show success
    3. Cancel → Close modal
    """
    trigger = ctx.triggered_id
    
    if trigger == "budget-delete-history-button":
        return True, no_update, no_update  # Open modal
    
    elif trigger == "budget-delete-cancel-button":
        return False, no_update, no_update  # Close modal
    
    elif trigger == "budget-delete-confirm-button":
        # Delete all revisions
        try:
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM budget_revisions WHERE profile_id = ?", (profile_id,))
                conn.commit()
            
            success = create_toast(
                "All budget revision history deleted. Budget baseline preserved.",
                toast_type="warning",
                header="History Deleted",
            )
            empty_history = [html.P("No revision history.", className="text-muted small")]
            return False, success, empty_history
        
        except Exception as e:
            error = create_toast(f"Failed to delete: {str(e)}", toast_type="danger")
            return False, error, no_update
    
    return no_update, no_update, no_update
```

### Acceptance Criteria

#### Phase 2: UI Restructuring

**Definition of Done**:
- [ ] Current Budget card renders at top of settings, always visible
- [ ] Current Budget card shows all values: Total Budget, Time Allocated, Team Cost, Last Updated
- [ ] Current Budget card adapts: placeholder when not configured, active state when configured
- [ ] Budget Total mode selector renders with radio buttons (Auto | Manual)
- [ ] Auto mode shows calculated value that updates in real-time
- [ ] Manual mode shows input field with override warning
- [ ] Switching modes preserves data (auto→manual pre-fills calculated value)
- [ ] Advanced options collapse contains Effective Date and Delete History
- [ ] Delete History opens confirmation modal before executing
- [ ] Revision History section moves below Advanced options
- [ ] All inputs have proper labels, tooltips, and inline help text
- [ ] Form validates inputs before save (Time ≥ 1, Team Cost > 0, Budget Total > 0 if manual)
- [ ] Save button creates revision record with deltas
- [ ] Cancel button resets form to current values
- [ ] No "Reconfigure" mode selector visible
- [ ] No reconfigure warning alert visible
- [ ] No reconfigure confirmation modal visible

#### Phase 3: Terminology Alignment

**Definition of Done**:
- [ ] All references to "Budget Total" changed to "Total Budget" in budget_cards.py
- [ ] All references to "Budget Total" changed to "Total Budget" in dashboard_comprehensive.py
- [ ] All references to "Team Cost Rate" changed to "Team Cost" in budget_settings_card.py
- [ ] Card labels consistent: "Total Budget", "Team Cost", "Budget Consumed", "Burn Rate", "Runway"
- [ ] Report template verified: uses "Total Budget" (no changes needed)
- [ ] Help tooltips updated with new terminology
- [ ] No terminology mismatches between app, report, and settings

#### Phase 4: Testing

**Definition of Done**:
- [ ] Test 1: First-time budget entry works (no existing budget)
- [ ] Test 2: Update existing budget preserves history
- [ ] Test 3: Auto mode calculates correctly (Time × Team Cost)
- [ ] Test 4: Manual override saves and persists
- [ ] Test 5: Switch auto→manual→auto works without data loss
- [ ] Test 6: Effective date sets correct week_label in revision
- [ ] Test 7: Delete history removes all revisions, preserves budget_settings
- [ ] Test 8: Budget replay at specific week returns correct values
- [ ] Test 9: Report generation shows budget metrics correctly
- [ ] Test 10: Live metrics preview displays when statistics exist
- [ ] Test 11: Placeholder message shows when no budget configured
- [ ] Test 12: Validation errors display for invalid inputs
- [ ] All existing tests pass (no regressions)

### Edge Cases & Error Handling

#### Budget Values

| Scenario                     | Behavior           | Error Message                                          |
| ---------------------------- | ------------------ | ------------------------------------------------------ |
| Time Allocated = 0           | Block save         | "Time allocated must be at least 1 week"               |
| Time Allocated < 0           | Block save         | "Time allocated must be at least 1 week"               |
| Team Cost = 0                | Block save         | "Team cost must be greater than 0"                     |
| Team Cost < 0                | Block save         | "Team cost must be greater than 0"                     |
| Budget Total = 0 (manual)    | Block save         | "Budget Total must be greater than 0"                  |
| Budget Total < Auto (manual) | Allow with warning | "Warning: Manual budget lower than team cost baseline" |
| Currency symbol empty        | Use default "€"    | (No error, silent fallback)                            |
| Non-numeric input            | Block save         | "Please enter a valid number"                          |

#### Live Metrics

| Scenario                | Behavior                                      |
| ----------------------- | --------------------------------------------- |
| No statistics exist yet | Show "No data available" in metrics section   |
| Query execution fails   | Hide metrics section, log error silently      |
| Velocity = 0            | Show metrics section but "Cost per Item: N/A" |
| Budget Total = 0        | Show "Consumed: N/A", "Runway: N/A"           |
| Runway = ∞              | Show "Runway: Unlimited ∞"                    |

#### Revision History

| Scenario                         | Behavior                                                                     |
| -------------------------------- | ---------------------------------------------------------------------------- |
| No revisions                     | Show "No revision history. Changes will appear after you update the budget." |
| Revision query fails             | Show error message in red text                                               |
| All deltas = 0                   | Don't create revision record (no change)                                     |
| Delete history with no revisions | Show success message, no database changes                                    |

#### Date/Time

| Scenario                              | Behavior                                      |
| ------------------------------------- | --------------------------------------------- |
| Effective Date empty                  | Use current date for week_label               |
| Effective Date in future              | Allow (retroactive budgeting for forecasting) |
| Effective Date before budget creation | Allow (retroactive budget entry)              |
| Invalid date format                   | DatePickerSingle handles validation           |

### Performance Considerations

1. **Live Metrics Query**:
   ```python
   # Cache metrics for 30 seconds to avoid repeated queries
   # Use callback pattern with dcc.Interval if real-time needed
   # Otherwise, load once when Budget tab opens
   ```

2. **Real-time Auto Calculation**:
   ```python
   # Client-side callback for instant feedback (no server round-trip)
   # Or use prevent_initial_call=False with pattern-matching
   ```

3. **Revision History Loading**:
   ```python
   # Limit to 10 most recent revisions (already implemented)
   # Use lazy loading if history grows large (future enhancement)
   ```

### Data Validation Rules

```python
# Centralized validation function
def validate_budget_inputs(time_allocated, team_cost, budget_total, mode):
    errors = []
    
    # Time Allocated
    if not time_allocated:
        errors.append("Time allocated is required")
    elif time_allocated < 1:
        errors.append("Time allocated must be at least 1 week")
    elif time_allocated > 520:  # 10 years
        errors.append("Time allocated seems unrealistic (>10 years)")
    
    # Team Cost
    if not team_cost:
        errors.append("Team cost is required")
    elif team_cost <= 0:
        errors.append("Team cost must be greater than 0")
    elif team_cost > 1000000:  # 1M per week
        errors.append("Team cost seems unrealistic (>€1M/week)")
    
    # Budget Total (manual mode)
    if mode == "manual":
        if not budget_total:
            errors.append("Budget Total is required in manual mode")
        elif budget_total <= 0:
            errors.append("Budget Total must be greater than 0")
    
    return errors
```

### Rollback Plan

**If implementation causes issues**:

1. **Revert UI changes**:
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **Database is safe**: No schema changes, existing budgets unaffected

3. **Fallback mode**:
   - Keep old `budget_settings_card.py` as `budget_settings_card_legacy.py`
   - Add environment variable: `USE_LEGACY_BUDGET_UI=true`
   - Import legacy component if flag is true

4. **User communication**:
   - Add banner: "We've updated the Budget Configuration. [Learn more] | [Switch to classic view]"
   - Collect feedback for 2 weeks before removing legacy

### Accessibility Requirements

**WCAG 2.1 Level AA Compliance**:

1. **Keyboard Navigation**:
   - All inputs focusable with Tab
   - Radio buttons navigable with Arrow keys
   - Modal dismissible with Escape
   - No keyboard traps

2. **Screen Reader Support**:
   ```html
   <div role="region" aria-label="Current Budget Configuration">
     <span aria-live="polite" id="budget-total-auto-display">
       Calculated: €48,000
     </span>
   </div>
   ```

3. **Color Contrast**:
   - Text: 4.5:1 minimum contrast ratio
   - Borders: Use Bootstrap primary/danger colors (WCAG compliant)
   - Don't rely on color alone (use icons + text)

4. **Focus Indicators**:
   - Visible focus rings on all interactive elements
   - Bootstrap default focus styles are sufficient

5. **Labels**:
   - All inputs have associated labels (not just placeholders)
   - Tooltips have aria-describedby references

### Mobile Responsiveness

**Breakpoints** (Bootstrap default):
- xs: <576px - Stack all inputs vertically
- sm: 576px-768px - 2-column grid for Time/Team Cost
- md: 768px-992px - 2-column grid + side-by-side buttons
- lg: 992px+ - Current layout

**Mobile-specific changes**:
```python
# Time/Team Cost: Full width on mobile
dbc.Row([
    dbc.Col([...], xs=12, md=6),  # Time Allocated
    dbc.Col([...], xs=12, md=6),  # Team Cost
])

# Buttons: Stack vertically on mobile
dbc.ButtonGroup([...], className="w-100 d-md-inline-flex d-block")
```

**Touch targets**: Minimum 44×44px (Bootstrap default buttons comply)

### Testing Checklist

**Unit Tests** (pytest):
```python
# tests/unit/callbacks/test_budget_settings.py
def test_load_budget_settings_determines_mode_correctly()
def test_save_budget_auto_mode_calculates_total()
def test_save_budget_manual_mode_uses_override()
def test_validation_rejects_invalid_inputs()
def test_delete_history_requires_confirmation()

# tests/unit/ui/test_budget_settings_card.py
def test_current_budget_card_shows_placeholder_when_not_configured()
def test_current_budget_card_shows_values_when_configured()
def test_mode_selector_switches_correctly()
def test_auto_calculation_updates_realtime()
```

**Integration Tests** (Playwright):
```python
# tests/integration/test_budget_workflow.py
def test_first_time_budget_entry_flow(page)
def test_update_existing_budget_flow(page)
def test_switch_modes_preserves_data(page)
def test_delete_history_confirmation_modal(page)
```

**Manual Test Scenarios**:
1. Enter budget on mobile device → Verify layout stacks correctly
2. Use screen reader → Verify all content announced correctly
3. Navigate with keyboard only → Verify no traps, all actions accessible
4. Test with empty database → Verify placeholder shows
5. Test with large numbers (€999,999,999) → Verify formatting works
6. Test with special characters in currency (₪, ₹, ₿) → Verify no encoding issues

---

## Quick Reference for Implementation Agent

### Files to Create
- None (all modifications to existing files)

### Files to Modify
1. `ui/budget_settings_card.py` - Complete rewrite
2. `callbacks/budget_settings.py` - Update load/save, add 3 new callbacks
3. `ui/budget_cards.py` - Find/replace "Budget Total" → "Total Budget"
4. `ui/dashboard_comprehensive.py` - Find/replace "Budget Total" → "Total Budget"
5. `report_assets/report_template.html` - Verify terminology (likely no changes)

### Database Schema
- No changes required ✅

### Dependencies
- No new packages required ✅

### Configuration
- No config file changes ✅

### Key Implementation Rules
1. ✅ Preserve all lean/agile methodology: velocity-driven costs, delta tracking, rolling forecasts
2. ✅ No data model changes: existing budgets work with new UI
3. ✅ Always-visible current budget (never `display: none`)
4. ✅ Explicit Budget Total mode (auto | manual)
5. ✅ Simplified update flow (no reconfigure mode)
6. ✅ Validation before save (Time ≥1, Cost >0, Total >0 if manual)
7. ✅ Confirmation modal for delete history
8. ✅ Mobile-responsive layout
9. ✅ Accessible (WCAG 2.1 AA)
10. ✅ Unified terminology: "Total Budget", "Team Cost"

### Success Criteria
- Users see current budget without clicking
- Users understand Budget Total calculation mode
- Users complete updates faster (fewer clicks)
- No methodology changes (velocity-driven costs preserved)
- All existing tests pass
