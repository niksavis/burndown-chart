# Phase 1: Data Model

**Feature**: Unified UX/UI and Architecture Redesign  
**Date**: 2025-10-23  
**Status**: Phase 1 - Data Model Complete

## Overview

This document defines the data entities, structures, and relationships involved in the UX/UI redesign. Since this is primarily a UI refactoring feature, the focus is on UI state entities, configuration structures, and component data interfaces rather than business domain entities (which remain unchanged).

## Entity Categories

### 1. UI State Entities

These entities manage the presentation layer state and user interface configuration.

#### 1.1 ParameterPanelState

**Purpose**: Manages the collapsible parameter control panel state and user preferences.

**Fields**:
- `is_open` (boolean): Whether the parameter panel is expanded or collapsed
- `last_updated` (timestamp): When the state was last modified
- `user_preference` (boolean): Whether user manually set state (vs. default)

**Persistence**: Client-side localStorage via dcc.Store

**Validation Rules**:
- `is_open` must be boolean (default: false)
- `last_updated` optional, ISO 8601 format if present
- `user_preference` must be boolean (default: false)

**State Transitions**:
```
collapsed (is_open=false) 
    -> User clicks expand button 
    -> expanded (is_open=true)

expanded (is_open=true) 
    -> User clicks collapse button 
    -> collapsed (is_open=false)
```

**JSON Schema**:
```json
{
  "is_open": false,
  "last_updated": "2025-10-23T10:30:00Z",
  "user_preference": true
}
```

---

#### 1.2 NavigationState

**Purpose**: Tracks active tab, navigation history, and user's current view context.

**Fields**:
- `active_tab` (string): ID of currently active tab (e.g., "tab-dashboard")
- `tab_history` (array of strings): Last N visited tabs for back navigation
- `previous_tab` (string, optional): Tab user was on before current
- `session_start_tab` (string): First tab loaded in current session

**Persistence**: Session-level dcc.Store (memory storage type)

**Validation Rules**:
- `active_tab` must be valid tab ID from registered tabs
- `tab_history` maximum 10 items, FIFO queue
- Tab IDs must match pattern: `^tab-[a-z-]+$`

**Valid Tab IDs**:
- `tab-dashboard` (new)
- `tab-burndown`
- `tab-items-per-week`
- `tab-points-per-week`
- `tab-scope-tracking`
- `tab-bug-analysis`

**State Transitions**:
```
Initial Load 
    -> active_tab = "tab-dashboard" (new default)
    -> session_start_tab = "tab-dashboard"

User clicks tab 
    -> previous_tab = current active_tab
    -> active_tab = clicked tab ID
    -> append previous_tab to tab_history
```

**JSON Schema**:
```json
{
  "active_tab": "tab-dashboard",
  "tab_history": ["tab-burndown", "tab-items-per-week"],
  "previous_tab": "tab-items-per-week",
  "session_start_tab": "tab-dashboard"
}
```

---

#### 1.3 MobileNavigationState

**Purpose**: Manages mobile-specific navigation drawer and bottom sheet state.

**Fields**:
- `drawer_open` (boolean): Whether mobile navigation drawer is open
- `bottom_sheet_visible` (boolean): Whether parameter bottom sheet is visible
- `swipe_enabled` (boolean): Whether swipe gestures are enabled
- `viewport_width` (integer): Current viewport width in pixels
- `is_mobile` (boolean): Computed flag if viewport < 768px

**Persistence**: Client-side dcc.Store (memory storage, resets on page load)

**Validation Rules**:
- All boolean fields required
- `viewport_width` must be positive integer
- `is_mobile` computed as `viewport_width < 768`

**State Transitions**:
```
Desktop viewport (>=768px)
    -> drawer_open = false (always)
    -> is_mobile = false

Mobile viewport (<768px)
    -> User taps menu icon
    -> drawer_open = true
    
Bottom sheet (mobile only)
    -> User taps FAB button
    -> bottom_sheet_visible = true
    
    -> User swipes down or taps outside
    -> bottom_sheet_visible = false
```

**JSON Schema**:
```json
{
  "drawer_open": false,
  "bottom_sheet_visible": false,
  "swipe_enabled": true,
  "viewport_width": 375,
  "is_mobile": true
}
```

---

#### 1.4 LayoutPreferences

**Purpose**: User's preferred layout configuration and display options.

**Fields**:
- `theme` (string): UI theme (currently only "light", future: "dark")
- `compact_mode` (boolean): Whether to use compact spacing
- `show_help_icons` (boolean): Whether to show contextual help icons
- `animation_enabled` (boolean): Whether to enable UI animations
- `preferred_chart_height` (integer): User's preferred chart height in pixels

**Persistence**: Client-side localStorage via dcc.Store

**Validation Rules**:
- `theme` must be "light" or "dark" (default: "light")
- `compact_mode` boolean (default: false)
- `show_help_icons` boolean (default: true)
- `animation_enabled` boolean (default: true)
- `preferred_chart_height` range 300-1200 pixels (default: 600)

**JSON Schema**:
```json
{
  "theme": "light",
  "compact_mode": false,
  "show_help_icons": true,
  "animation_enabled": true,
  "preferred_chart_height": 600
}
```

---

### 2. Component Configuration Entities

These entities define the structure and behavior of UI components.

#### 2.1 DesignTokens

**Purpose**: Centralized design system values for consistent styling.

**Fields**:
- `colors` (object): Color palette tokens
- `spacing` (object): Spacing scale values
- `typography` (object): Font sizes, weights, line heights
- `layout` (object): Border radius, shadows, z-index values
- `animation` (object): Transition timings and easing functions

**Persistence**: Python constants in `ui/style_constants.py`, exported to CSS variables

**Validation Rules**:
- Color values must be valid hex codes or rgba
- Spacing values must be valid CSS units (rem, px, em)
- Font sizes must be positive numbers with units
- Z-index values must be integers

**Structure**:
```python
DESIGN_TOKENS = {
    "colors": {
        "primary": "#0d6efd",
        "secondary": "#6c757d",
        "success": "#198754",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#0dcaf0",
        "light": "#f8f9fa",
        "dark": "#343a40",
    },
    "spacing": {
        "xs": "0.25rem",
        "sm": "0.5rem",
        "md": "1rem",
        "lg": "1.5rem",
        "xl": "2rem",
        "xxl": "3rem"
    },
    "typography": {
        "size": {
            "xs": "0.75rem",
            "sm": "0.875rem",
            "base": "1rem",
            "lg": "1.125rem",
            "xl": "1.25rem"
        },
        "weight": {
            "normal": 400,
            "medium": 500,
            "bold": 700
        },
        "lineHeight": {
            "tight": 1.2,
            "base": 1.5,
            "relaxed": 1.75
        }
    },
    "layout": {
        "borderRadius": {
            "sm": "0.25rem",
            "md": "0.375rem",
            "lg": "0.5rem"
        },
        "shadow": {
            "sm": "0 .125rem .25rem rgba(0,0,0,.075)",
            "md": "0 .5rem 1rem rgba(0,0,0,.15)",
            "lg": "0 1rem 3rem rgba(0,0,0,.175)"
        },
        "zIndex": {
            "sticky": 1020,
            "modal": 1050,
            "tooltip": 1070
        }
    },
    "animation": {
        "duration": {
            "fast": "200ms",
            "base": "300ms",
            "slow": "500ms"
        },
        "easing": {
            "default": "ease-in-out",
            "smooth": "cubic-bezier(0.4, 0.0, 0.2, 1)"
        }
    }
}
```

---

#### 2.2 TabConfiguration

**Purpose**: Defines tab metadata, order, and navigation behavior.

**Fields**:
- `id` (string): Unique tab identifier
- `label` (string): Display text for tab
- `icon` (string): Font Awesome icon class
- `color` (string): Tab accent color (from design tokens)
- `order` (integer): Display order (0-based, 0 = first)
- `requires_data` (boolean): Whether tab needs data loaded
- `help_content_id` (string, optional): ID of help content for tab

**Validation Rules**:
- `id` required, unique, pattern `^tab-[a-z-]+$`
- `label` required, 1-50 characters
- `icon` required, valid Font Awesome class
- `color` must reference design token color
- `order` required, unique integer >= 0
- `requires_data` boolean (default: true)

**Tab Registry**:
```python
TAB_CONFIG = [
    {
        "id": "tab-dashboard",
        "label": "Dashboard",
        "icon": "fa-tachometer-alt",
        "color": "primary",
        "order": 0,
        "requires_data": True,
        "help_content_id": "help-dashboard"
    },
    {
        "id": "tab-burndown",
        "label": "Burndown",
        "icon": "fa-chart-line",
        "color": "info",
        "order": 1,
        "requires_data": True,
        "help_content_id": "help-burndown"
    },
    # ... etc for remaining tabs
]
```

---

#### 2.3 ComponentVariant

**Purpose**: Defines available visual variants for reusable components.

**Fields**:
- `component_type` (string): Type of component (button, card, input, etc.)
- `variant_name` (string): Name of variant (default, primary, secondary, etc.)
- `style_overrides` (object): CSS style properties for variant
- `class_names` (array of strings): Bootstrap/custom classes to apply

**Validation Rules**:
- `component_type` must be registered component type
- `variant_name` required, alphanumeric + hyphen
- `style_overrides` object with valid CSS properties
- `class_names` array of valid CSS class strings

**Example Variants**:
```python
BUTTON_VARIANTS = {
    "primary": {
        "component_type": "button",
        "variant_name": "primary",
        "style_overrides": {},
        "class_names": ["btn-primary"]
    },
    "secondary": {
        "component_type": "button",
        "variant_name": "secondary",
        "style_overrides": {},
        "class_names": ["btn-outline-secondary"]
    },
    "danger": {
        "component_type": "button",
        "variant_name": "danger",
        "style_overrides": {},
        "class_names": ["btn-danger"]
    }
}

CARD_VARIANTS = {
    "default": {
        "component_type": "card",
        "variant_name": "default",
        "style_overrides": {
            "borderRadius": DESIGN_TOKENS["layout"]["borderRadius"]["md"],
            "boxShadow": DESIGN_TOKENS["layout"]["shadow"]["sm"]
        },
        "class_names": ["card"]
    },
    "elevated": {
        "component_type": "card",
        "variant_name": "elevated",
        "style_overrides": {
            "borderRadius": DESIGN_TOKENS["layout"]["borderRadius"]["md"],
            "boxShadow": DESIGN_TOKENS["layout"]["shadow"]["md"]
        },
        "class_names": ["card", "shadow"]
    }
}
```

---

### 3. Dashboard Entities

These entities specifically support the new Dashboard tab functionality.

#### 3.1 DashboardMetrics

**Purpose**: Aggregated project health data displayed on Dashboard.

**Fields**:
- `completion_forecast_date` (date): Predicted completion date
- `completion_confidence` (float): Confidence percentage (0-100)
- `days_to_completion` (integer): Days remaining until forecast date
- `days_to_deadline` (integer): Days remaining until hard deadline
- `completion_percentage` (float): Project completion percentage (0-100)
- `remaining_items` (integer): Total items remaining
- `remaining_points` (float): Total story points remaining
- `current_velocity_items` (float): Recent velocity (items per week)
- `current_velocity_points` (float): Recent velocity (points per week)
- `velocity_trend` (string): Trend direction ("increasing", "stable", "decreasing")
- `last_updated` (timestamp): When metrics were calculated

**Persistence**: Computed on-demand, cached in dcc.Store (session storage)

**Validation Rules**:
- Dates must be valid ISO 8601 format or null
- Percentages must be 0-100 or null
- Counts must be non-negative integers or null
- Velocities must be non-negative floats or null
- `velocity_trend` must be one of: "increasing", "stable", "decreasing", "unknown"

**Calculation Dependencies**:
- Derived from existing `statistics` data (data/processing.py)
- Uses `app_settings` for deadline and scope values
- Uses PERT calculations from existing forecast logic

**JSON Schema**:
```json
{
  "completion_forecast_date": "2025-12-15",
  "completion_confidence": 75.5,
  "days_to_completion": 53,
  "days_to_deadline": 60,
  "completion_percentage": 68.3,
  "remaining_items": 42,
  "remaining_points": 125.5,
  "current_velocity_items": 8.2,
  "current_velocity_points": 24.7,
  "velocity_trend": "stable",
  "last_updated": "2025-10-23T14:30:00Z"
}
```

---

#### 3.2 PERTTimelineData

**Purpose**: PERT forecast timeline data for Dashboard visualization.

**Fields**:
- `optimistic_date` (date): Best-case completion date
- `pessimistic_date` (date): Worst-case completion date
- `most_likely_date` (date): Most likely completion date
- `pert_estimate_date` (date): PERT weighted average date
- `optimistic_days` (integer): Days for optimistic scenario
- `pessimistic_days` (integer): Days for pessimistic scenario
- `most_likely_days` (integer): Days for most likely scenario
- `confidence_range_days` (integer): Range between optimistic and pessimistic

**Persistence**: Computed on-demand, cached in dcc.Store

**Validation Rules**:
- All dates must be valid ISO 8601 or null
- Days must be non-negative integers
- Pessimistic >= Most Likely >= Optimistic (chronologically)
- Confidence range = pessimistic_days - optimistic_days

**Calculation**:
- Uses existing PERT formula from data/processing.py
- Based on current velocity and remaining work
- Applied PERT factor from app_settings

**JSON Schema**:
```json
{
  "optimistic_date": "2025-11-30",
  "pessimistic_date": "2026-01-15",
  "most_likely_date": "2025-12-15",
  "pert_estimate_date": "2025-12-18",
  "optimistic_days": 38,
  "pessimistic_days": 84,
  "most_likely_days": 53,
  "confidence_range_days": 46
}
```

---

### 4. Existing Entities (No Changes)

These entities are part of the existing data model and will NOT be modified by this feature:

#### 4.1 ProjectData
- Structure: Defined in data/schema.py
- Persistence: project_data.json
- Status: **NO CHANGES**

#### 4.2 AppSettings
- Structure: Defined in data/persistence.py
- Persistence: app_settings.json
- Fields: PERT factor, deadline, scope values, JIRA config
- Status: **NO CHANGES** to structure (may add UI preference fields in future)

#### 4.3 Statistics
- Structure: Weekly statistics data
- Persistence: Computed from ProjectData
- Status: **NO CHANGES**

#### 4.4 JIRACacheData
- Structure: JIRA issue data cache
- Persistence: jira_cache.json
- Status: **NO CHANGES**

---

## Entity Relationships

```
┌─────────────────────┐
│  NavigationState    │
│  (active_tab)       │
└──────────┬──────────┘
           │
           │ determines
           ▼
┌─────────────────────┐         ┌─────────────────────┐
│  TabConfiguration   │         │  LayoutPreferences  │
│  (tab registry)     │         │  (user settings)    │
└──────────┬──────────┘         └──────────┬──────────┘
           │                               │
           │ defines structure             │ influences
           ▼                               ▼
┌─────────────────────┐         ┌─────────────────────┐
│  Dashboard Tab      │ ←───────│  DesignTokens       │
│  (if active)        │ styled  │  (theme values)     │
└──────────┬──────────┘  by     └─────────────────────┘
           │                               ▲
           │ displays                      │
           ▼                               │
┌─────────────────────┐                   │
│  DashboardMetrics   │                   │
│  (computed)         │                   │
└──────────┬──────────┘                   │
           │                               │
           │ calculated from               │ applies styles
           ▼                               │
┌─────────────────────┐         ┌─────────────────────┐
│  Statistics         │         │  ComponentVariant   │
│  (existing data)    │         │  (style variants)   │
└─────────────────────┘         └─────────────────────┘

┌─────────────────────┐
│ ParameterPanelState │
│ (is_open)           │
└──────────┬──────────┘
           │
           │ controls visibility
           ▼
┌─────────────────────┐
│  Parameter Panel    │
│  (input controls)   │
└─────────────────────┘
```

## Data Flow Patterns

### Pattern 1: Dashboard Metrics Calculation

```
User loads Dashboard tab
    ↓
Callback triggered: update_dashboard_metrics
    ↓
Read from stores:
  - statistics-store (existing weekly data)
  - settings-store (PERT factor, deadline, scope)
    ↓
Calculate DashboardMetrics:
  - completion_forecast_date (from velocity + remaining)
  - completion_confidence (from velocity consistency)
  - remaining work (from scope - completed)
    ↓
Calculate PERTTimelineData:
  - optimistic/pessimistic/most_likely dates
  - PERT weighted estimate
    ↓
Update Dashboard card outputs:
  - forecast-date (display element)
  - velocity-metric (display element)
  - completion-progress (progress bar)
    ↓
User sees updated Dashboard
```

### Pattern 2: Parameter Panel State Management

```
User clicks expand/collapse button
    ↓
Client-side callback: toggle_param_panel
    ↓
Read current state: ParameterPanelState.is_open
    ↓
Calculate new state: !is_open
    ↓
Update outputs:
  - param-panel-collapse.is_open (Bootstrap Collapse)
  - expand-params-btn children (icon direction)
    ↓
Store preference: localStorage.setItem('param_panel_open', new_state)
    ↓
Panel animates open/closed (Bootstrap CSS transition)
```

### Pattern 3: Tab Navigation Flow

```
User clicks tab
    ↓
Callback triggered: handle_tab_change
    ↓
Read current NavigationState
    ↓
Update NavigationState:
  - previous_tab = active_tab
  - active_tab = new_tab_id
  - append previous_tab to tab_history
    ↓
Store updated NavigationState
    ↓
Dash renders new tab content
    ↓
If tab requires data:
  - Trigger data loading callbacks
  - Show loading spinner
  - Render chart/content when ready
```

## Validation & Business Rules

### Rule 1: Tab Navigation

- Dashboard tab must always be first in order (order = 0)
- Active tab must be a valid registered tab ID
- Tab history limited to 10 most recent tabs
- Session start tab defaults to "tab-dashboard" on fresh load

### Rule 2: Parameter Panel

- Panel state persists across tab changes within session
- Panel must be collapsible via button click
- Panel must show summary of key values when collapsed
- On mobile (<768px), panel uses bottom sheet alternative

### Rule 3: Dashboard Metrics

- Metrics computed on-demand when Dashboard tab active
- Metrics cached until statistics or settings change
- Invalid/missing data shows "N/A" or error state, not broken UI
- Confidence percentage calculated from velocity standard deviation

### Rule 4: Design Tokens

- All components must use design tokens, not inline hardcoded values
- Color values must come from COLOR_* constants
- Spacing values must come from SPACING_* constants
- Custom styles only when design tokens insufficient (document reason)

### Rule 5: Responsive Behavior

- Mobile layout: < 768px (single column, bottom sheet for params)
- Tablet layout: 768px - 992px (hybrid, collapsible sidebar)
- Desktop layout: >= 992px (multi-column, sticky param panel)
- Touch targets on mobile must be minimum 44px × 44px

## Data Migration

**Migration Required**: None - this feature adds new UI state entities but doesn't modify existing data structures.

**Backward Compatibility**:
- All existing data files (project_data.json, app_settings.json, jira_cache.json) remain unchanged
- New UI state stored separately in browser storage (dcc.Store)
- Existing callbacks preserve signatures (new callbacks additive only)

**Rollback Strategy**:
- UI state stored client-side only - no server state migration needed
- Rolling back to previous version simply ignores new localStorage keys
- No data loss risk since business data untouched

## Performance Considerations

### Caching Strategy

**Client-Side Cache** (dcc.Store with localStorage):
- ParameterPanelState: 1 KB, persistent
- LayoutPreferences: 2 KB, persistent
- NavigationState: 1 KB, session-only

**Server-Side Cache** (dcc.Store with memory):
- DashboardMetrics: 5 KB, recalculated on statistics change
- PERTTimelineData: 3 KB, recalculated on settings change

**Total Storage Impact**: ~12 KB per user (client-side + session)

### Computation Performance

**Dashboard Metrics Calculation**:
- Input: Statistics array (typically 10-50 weeks)
- Complexity: O(n) linear scan for averages
- Target: < 50ms calculation time
- Caching: Results cached until data changes

**Component Rendering**:
- Design token lookups: O(1) dictionary access
- Style application: Minimal overhead vs. inline styles
- Target: No measurable rendering delay

## Testing Strategy

### Unit Tests

**UI State Entities**:
- Test state transitions (collapsed ↔ expanded)
- Test validation rules (valid tab IDs, value ranges)
- Test default values and initialization

**Design Tokens**:
- Test all token values are valid CSS
- Test no hardcoded colors/spacing in components
- Test helper functions return correct styles

**Dashboard Metrics**:
- Test calculation with mock statistics data
- Test edge cases (no data, zero velocity, past deadline)
- Test PERT timeline calculations

### Integration Tests

**Navigation Flow**:
- Test Dashboard loads as default tab
- Test tab switching updates NavigationState
- Test tab history tracking

**Parameter Panel**:
- Test expand/collapse functionality
- Test state persistence across tab changes
- Test mobile bottom sheet alternative

**Dashboard Display**:
- Test metrics update when statistics change
- Test metrics update when settings change
- Test error states for missing data

### Performance Tests

- Benchmark Dashboard metrics calculation (target: < 50ms)
- Verify no performance regression vs. current version (±10% threshold)
- Test component rendering time with design tokens

## Future Extensibility

### Potential Enhancements

**Theme Support**:
- LayoutPreferences.theme already defined for "dark" mode
- Design tokens structured to support theme variants
- CSS variables export enables runtime theme switching

**Dashboard Customization**:
- Add `dashboard_card_order` to LayoutPreferences
- Allow users to show/hide specific metrics
- Add custom dashboard cards via plugin system

**Advanced Navigation**:
- Add `favorite_tabs` to NavigationState
- Implement quick-switch hotkeys
- Add breadcrumb navigation for drilldowns

**Component Library**:
- Export component builders as standalone package
- Version component API contracts
- Support custom component themes

## Appendix: JSON Schemas

### Complete Schema: NavigationState

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["active_tab", "session_start_tab"],
  "properties": {
    "active_tab": {
      "type": "string",
      "pattern": "^tab-[a-z-]+$"
    },
    "tab_history": {
      "type": "array",
      "items": {
        "type": "string",
        "pattern": "^tab-[a-z-]+$"
      },
      "maxItems": 10
    },
    "previous_tab": {
      "type": "string",
      "pattern": "^tab-[a-z-]+$"
    },
    "session_start_tab": {
      "type": "string",
      "pattern": "^tab-[a-z-]+$"
    }
  }
}
```

### Complete Schema: DashboardMetrics

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "completion_forecast_date": {
      "type": ["string", "null"],
      "format": "date"
    },
    "completion_confidence": {
      "type": ["number", "null"],
      "minimum": 0,
      "maximum": 100
    },
    "days_to_completion": {
      "type": ["integer", "null"],
      "minimum": 0
    },
    "days_to_deadline": {
      "type": ["integer", "null"]
    },
    "completion_percentage": {
      "type": ["number", "null"],
      "minimum": 0,
      "maximum": 100
    },
    "remaining_items": {
      "type": ["integer", "null"],
      "minimum": 0
    },
    "remaining_points": {
      "type": ["number", "null"],
      "minimum": 0
    },
    "current_velocity_items": {
      "type": ["number", "null"],
      "minimum": 0
    },
    "current_velocity_points": {
      "type": ["number", "null"],
      "minimum": 0
    },
    "velocity_trend": {
      "type": "string",
      "enum": ["increasing", "stable", "decreasing", "unknown"]
    },
    "last_updated": {
      "type": "string",
      "format": "date-time"
    }
  }
}
```
