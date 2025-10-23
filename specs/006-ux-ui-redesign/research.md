# Phase 0: Research & Decisions

**Feature**: Unified UX/UI and Architecture Redesign  
**Date**: 2025-10-23  
**Status**: Phase 0 Complete

## Overview

This document resolves all "NEEDS CLARIFICATION" items identified in the Technical Context and documents architectural decisions for implementing the UX/UI redesign.

## Research Items

### 1. Playwright Integration Status

**Question**: What is the current status of Playwright integration in the test suite?

**Research Findings**:
- Copilot instructions explicitly recommend Playwright over Selenium for new tests
- Existing integration tests may use Selenium via dash.testing utilities
- Playwright requires custom server management (waitress) and text-based selectors
- Pattern exists in project documentation for Playwright implementation

**Decision**: Use Playwright for new integration tests  
**Rationale**: 
- Modern API with better performance (~3x faster than Selenium)
- More reliable element detection and reduced flakiness
- Better async/await support and cleaner syntax
- Recommended approach in project guidelines

**Implementation Notes**:
- Use direct app import with waitress server for testing
- Use text-based selectors (`has_text()`) instead of dynamic React IDs
- Implement custom server management in fixtures
- Add Playwright to test dependencies if not present

**Alternatives Considered**:
- Continue with Selenium: Rejected due to slower execution and higher flakiness
- Use dash.testing utilities: Rejected because they have Selenium dependencies

---

### 2. Component Builder Pattern Standardization

**Question**: What is the exact implementation approach for standardizing component builder patterns?

**Research Findings**:
- Current codebase has inconsistent component creation:
  - Some use inline component definitions in layout.py
  - Some use utility functions in button_utils.py, cards.py
  - Style application is mixed (inline styles vs. CSS classes)
- Project follows Atomic Design System concept (atoms → molecules → organisms)
- style_constants.py exists but may not be fully utilized

**Decision**: Implement three-tier component builder system  
**Rationale**:
- Separates concerns: atoms (basic elements), molecules (simple groups), organisms (complex sections)
- Centralizes styling through style_constants.py design tokens
- Provides consistent API for all component creation
- Reduces code duplication and improves maintainability

**Component Builder Tiers**:

1. **Atoms** (basic UI elements):
   - Functions in `ui/button_utils.py`, `ui/icon_utils.py`
   - Example: `create_action_button(text, icon, variant, size, **kwargs)`
   - Return single Dash component with consistent styling

2. **Molecules** (simple component groups):
   - Functions in `ui/components.py` (existing file)
   - Example: `create_labeled_input(label, input_id, input_type, **kwargs)`
   - Combine atoms into functional units
   - Include internal layout logic

3. **Organisms** (complex UI sections):
   - Functions in `ui/cards.py`, `ui/tabs.py`, new `ui/dashboard.py`
   - Example: `create_dashboard_metrics_card(metrics_data)`
   - Compose molecules and atoms into complete features
   - Manage internal state and interactivity

**Standard Component API Pattern**:
```python
def create_component(
    data: Dict[str, Any],          # Required data
    variant: str = "default",       # Visual variant
    size: str = "md",              # Size option
    id_suffix: str = "",           # For unique IDs
    **kwargs                        # Pass-through to Dash component
) -> dbc.Component:
    """Component description.
    
    Args:
        data: Required data structure
        variant: Visual variant (default, primary, secondary, etc.)
        size: Size (sm, md, lg)
        id_suffix: Suffix for component ID uniqueness
        **kwargs: Additional props passed to underlying component
    
    Returns:
        Configured Dash Bootstrap component
    """
    pass
```

**Implementation Steps**:
1. Audit existing components and categorize by tier
2. Extract all inline styles to style_constants.py
3. Create/enhance builder functions following standard API
4. Refactor layout.py and cards.py to use builders
5. Document builder API in each module

**Alternatives Considered**:
- Class-based components: Rejected - Dash uses functional composition, classes add unnecessary complexity
- Single-file component library: Rejected - Would create large unmaintainable file
- No standardization: Rejected - Perpetuates inconsistency issues

---

### 3. Collapsible Parameter Panel Implementation

**Question**: How should the collapsible parameter control panel be implemented technically?

**Research Findings**:
- Bootstrap provides Collapse component via dash-bootstrap-components
- Dash callbacks can manage collapse state
- Client-side callbacks could improve responsiveness
- Need persistent state across tab changes

**Decision**: Use dbc.Collapse with client-side callback and dcc.Store  
**Rationale**:
- No server round-trip for collapse/expand improves UX
- dcc.Store with localStorage preserves user preference
- Bootstrap Collapse provides smooth animations
- Works seamlessly with existing Dash architecture

**Technical Design**:

**Component Structure**:
```python
dbc.Container([
    # Collapsed state - always visible sticky bar
    dbc.Row([
        dbc.Col([
            html.Div([
                html.Span("Current Settings: ", className="text-muted"),
                html.Strong(id="param-summary"),  # Shows key values
                dbc.Button(
                    html.I(className="fas fa-chevron-down"),
                    id="expand-params-btn",
                    size="sm",
                    color="link"
                )
            ], className="param-bar-collapsed")
        ])
    ], className="sticky-top bg-light border-bottom"),
    
    # Expanded state - reveals all controls
    dbc.Collapse([
        dbc.Row([
            # Parameter input fields
            dbc.Col([...], md=3),
            dbc.Col([...], md=3),
            dbc.Col([...], md=3),
            dbc.Col([...], md=3),
        ])
    ], id="param-panel-collapse", is_open=False)
], id="parameter-control-panel")
```

**Callback Strategy**:
```python
# Client-side callback for instant toggle (no server round-trip)
app.clientside_callback(
    """
    function(n_clicks, is_open) {
        // Toggle collapse state
        const new_state = !is_open;
        // Store preference
        localStorage.setItem('param_panel_open', new_state);
        // Update icon
        const icon = new_state ? 'fa-chevron-up' : 'fa-chevron-down';
        return [new_state, icon];
    }
    """,
    [Output("param-panel-collapse", "is_open"),
     Output("expand-params-btn", "children")],
    Input("expand-params-btn", "n_clicks"),
    State("param-panel-collapse", "is_open")
)

# Server-side callback for parameter summary
@app.callback(
    Output("param-summary", "children"),
    [Input("pert-input", "value"),
     Input("deadline-input", "value"),
     Input("total-items-input", "value")]
)
def update_param_summary(pert, deadline, items):
    return f"PERT: {pert} | Deadline: {deadline} | Items: {items}"
```

**Mobile Adaptation**:
- On mobile (<768px), collapsed bar shows minimal info with expand button
- Expanded panel uses full-width single-column layout
- Bottom sheet alternative can be Phase 2 enhancement

**Alternatives Considered**:
- Sidebar panel: Rejected - Takes horizontal space away from charts
- Modal dialog: Rejected - Completely obscures charts, poor UX
- Tabs for parameters: Rejected - Adds navigation complexity
- Always-visible controls: Rejected - Consumes vertical space, user's primary complaint

---

### 4. Dashboard Tab Implementation

**Question**: How should the Dashboard be implemented as a new first tab?

**Research Findings**:
- Current dashboard content exists in `create_project_summary_card()` in ui/cards.py
- Tab system defined in ui/tabs.py
- Tab registration in ui/layout.py
- Need to extract dashboard metrics from existing statistics and settings

**Decision**: Create dedicated Dashboard module with metrics composition  
**Rationale**:
- Separates dashboard concerns from general card utilities
- Allows dashboard-specific layouts and interactivity
- Simplifies future dashboard enhancements
- Follows organism-level component pattern

**Technical Design**:

**New Module**: `ui/dashboard.py`
```python
def create_dashboard_tab() -> dbc.Tab:
    """Create Dashboard tab with project metrics."""
    return dbc.Tab(
        label="Dashboard",
        tab_id="tab-dashboard",
        children=dbc.Container([
            dbc.Row([
                dbc.Col([create_completion_forecast_card()], md=4),
                dbc.Col([create_velocity_metrics_card()], md=4),
                dbc.Col([create_remaining_work_card()], md=4),
            ], className="mb-3"),
            dbc.Row([
                dbc.Col([create_pert_timeline_card()], md=6),
                dbc.Col([create_scope_health_card()], md=6),
            ]),
        ], fluid=True, className="dashboard-container")
    )

def create_completion_forecast_card() -> dbc.Card:
    """Forecast completion date and confidence."""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-calendar-check me-2"),
            "Completion Forecast"
        ]),
        dbc.CardBody([
            html.H3(id="forecast-date", className="text-primary"),
            html.P(id="forecast-confidence", className="text-muted"),
            dbc.Progress(id="completion-progress", className="mt-2"),
        ]),
        dbc.CardFooter([
            dbc.Button("View Details", id="goto-burndown", size="sm", color="link")
        ])
    ])
```

**Tab Registration Update** in `ui/tabs.py`:
```python
def create_tab_navigation() -> dbc.Tabs:
    """Create main tab navigation."""
    tabs = [
        create_dashboard_tab(),          # NEW - First tab
        create_burndown_tab(),
        create_items_per_week_tab(),
        create_points_per_week_tab(),
        create_scope_tracking_tab(),
        create_bug_analysis_tab(),
    ]
    return dbc.Tabs(tabs, id="chart-tabs", active_tab="tab-dashboard")
```

**Dashboard Callbacks** in `callbacks/dashboard.py` (new file):
```python
@app.callback(
    [Output("forecast-date", "children"),
     Output("forecast-confidence", "children"),
     Output("completion-progress", "value")],
    [Input("statistics-store", "data"),
     Input("settings-store", "data")]
)
def update_dashboard_metrics(statistics, settings):
    """Update dashboard metrics when data changes."""
    # Calculate metrics from statistics and settings
    forecast_date = calculate_forecast_date(statistics, settings)
    confidence = calculate_confidence_level(statistics)
    progress = calculate_completion_percentage(statistics, settings)
    
    return (
        forecast_date.strftime("%Y-%m-%d"),
        f"{confidence}% confidence",
        progress
    )
```

**Alternatives Considered**:
- Reuse existing summary card: Rejected - Dashboard needs richer interactivity
- Dashboard as modal: Rejected - Should be primary view, not secondary
- Merge with existing tab: Rejected - Each tab should have single focus

---

### 5. Responsive Breakpoint Strategy

**Question**: Should we customize Bootstrap breakpoints or use defaults?

**Research Findings**:
- Bootstrap 5 defaults: xs <576px, sm 576px, md 768px, lg 992px, xl 1200px, xxl 1400px
- Project specification mentions: mobile <768px, tablet 768-992px, desktop ≥992px
- Current code uses dbc components which respect Bootstrap breakpoints
- Mobile navigation already implemented with 768px breakpoint

**Decision**: Use Bootstrap 5 standard breakpoints with semantic mappings  
**Rationale**:
- Maintains consistency with existing mobile navigation
- Avoids custom CSS media query complexity
- Works seamlessly with dbc.Col responsive props
- Industry-standard breakpoints familiar to developers

**Breakpoint Mappings**:
- **Mobile**: < 768px (Bootstrap xs, sm) - single-column layouts
- **Tablet Portrait**: 768px - 992px (Bootstrap md) - hybrid layouts
- **Tablet Landscape / Small Desktop**: 992px - 1200px (Bootstrap lg) - multi-column
- **Desktop**: ≥ 1200px (Bootstrap xl, xxl) - full multi-column

**Usage Pattern**:
```python
dbc.Row([
    dbc.Col([component], xs=12, md=6, lg=4),  # Full on mobile, half on tablet, third on desktop
])
```

**Touch Target Strategy**:
- All buttons/inputs use Bootstrap size="lg" on mobile (automatic via CSS)
- Custom CSS for minimum 44px touch targets where needed
- Verified via integration tests on 375px viewport (iPhone SE)

**Alternatives Considered**:
- Custom breakpoints: Rejected - Unnecessary complexity, breaks dbc components
- Only mobile/desktop binary: Rejected - Poor tablet experience
- CSS-only responsive: Rejected - Bootstrap props handle this elegantly

---

### 6. Design Token System

**Question**: What design tokens need to be standardized and how should they be organized?

**Research Findings**:
- style_constants.py exists with some constants
- Bootstrap theme is FLATLY with primary blue #0d6efd
- Inline styles scattered across component files
- CSS custom properties could provide runtime theming

**Decision**: Centralized Python design tokens with CSS variable export  
**Rationale**:
- Python constants provide type safety and IDE support
- Can generate CSS variables for consistency
- Single source of truth for all styling values
- Supports future theming capabilities

**Design Token Categories**:

**1. Colors** (from Bootstrap FLATLY theme):
```python
# Primary palette
COLOR_PRIMARY = "#0d6efd"
COLOR_SECONDARY = "#6c757d"
COLOR_SUCCESS = "#198754"
COLOR_WARNING = "#ffc107"
COLOR_DANGER = "#dc3545"
COLOR_INFO = "#0dcaf0"

# Neutrals
COLOR_LIGHT = "#f8f9fa"
COLOR_DARK = "#343a40"
COLOR_WHITE = "#ffffff"
COLOR_BLACK = "#000000"

# Interactive states
COLOR_PRIMARY_HOVER = "#0b5ed7"
COLOR_PRIMARY_ACTIVE = "#0a58ca"
COLOR_FOCUS_SHADOW = "rgba(13, 110, 253, 0.25)"
```

**2. Spacing** (Bootstrap spacing scale):
```python
SPACING_XS = "0.25rem"  # 4px
SPACING_SM = "0.5rem"   # 8px
SPACING_MD = "1rem"     # 16px
SPACING_LG = "1.5rem"   # 24px
SPACING_XL = "2rem"     # 32px
SPACING_XXL = "3rem"    # 48px
```

**3. Typography**:
```python
FONT_SIZE_XS = "0.75rem"   # 12px
FONT_SIZE_SM = "0.875rem"  # 14px
FONT_SIZE_BASE = "1rem"    # 16px
FONT_SIZE_LG = "1.125rem"  # 18px
FONT_SIZE_XL = "1.25rem"   # 20px

FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_BOLD = 700

LINE_HEIGHT_TIGHT = 1.2
LINE_HEIGHT_BASE = 1.5
LINE_HEIGHT_RELAXED = 1.75
```

**4. Layout**:
```python
BORDER_RADIUS_SM = "0.25rem"
BORDER_RADIUS_MD = "0.375rem"
BORDER_RADIUS_LG = "0.5rem"

SHADOW_SM = "0 .125rem .25rem rgba(0,0,0,.075)"
SHADOW_MD = "0 .5rem 1rem rgba(0,0,0,.15)"
SHADOW_LG = "0 1rem 3rem rgba(0,0,0,.175)"

Z_INDEX_STICKY = 1020
Z_INDEX_MODAL = 1050
Z_INDEX_TOOLTIP = 1070
```

**5. Animation**:
```python
TRANSITION_FAST = "200ms"
TRANSITION_BASE = "300ms"
TRANSITION_SLOW = "500ms"

EASING_DEFAULT = "ease-in-out"
EASING_SMOOTH = "cubic-bezier(0.4, 0.0, 0.2, 1)"
```

**Implementation Strategy**:
1. Consolidate all existing inline styles to style_constants.py
2. Create helper functions for common style combinations:
   ```python
   def get_card_style(variant="default"):
       return {
           "borderRadius": BORDER_RADIUS_MD,
           "boxShadow": SHADOW_SM,
           "padding": SPACING_MD,
           "backgroundColor": COLOR_WHITE if variant == "default" else COLOR_LIGHT
       }
   ```
3. Export CSS variables in custom.css for JavaScript access:
   ```css
   :root {
       --color-primary: #0d6efd;
       --spacing-md: 1rem;
       /* ... etc ... */
   }
   ```

**Alternatives Considered**:
- CSS-only tokens: Rejected - Python components need direct access
- Separate config file: Rejected - Increases complexity
- No standardization: Rejected - Perpetuates inconsistency

---

## Summary of Decisions

| Decision Area            | Choice                                             | Impact                                 |
| ------------------------ | -------------------------------------------------- | -------------------------------------- |
| Testing Framework        | Playwright for new integration tests               | Better performance and reliability     |
| Component Builders       | Three-tier system (atoms/molecules/organisms)      | Consistent API and reduced duplication |
| Parameter Panel          | dbc.Collapse with client-side callback             | No server latency, smooth UX           |
| Dashboard Implementation | Dedicated ui/dashboard.py module                   | Clear separation, extensible           |
| Responsive Breakpoints   | Bootstrap 5 defaults (768px, 992px, 1200px)        | Standard behavior, dbc compatibility   |
| Design Tokens            | Centralized Python constants in style_constants.py | Single source of truth                 |

## Technology Selections

**UI Framework**: Dash 3.1.1 + dash-bootstrap-components 2.0.2 (no change)  
**Styling Approach**: Bootstrap 5 FLATLY theme + custom design tokens  
**State Management**: dcc.Store (client-side for UI state, server-side for data)  
**Animation**: Bootstrap Collapse + CSS transitions  
**Testing**: pytest + Playwright for integration tests  
**Browser Support**: Modern browsers (Chrome, Firefox, Safari, Edge) - last 2 years

## Implementation Phases

**Phase 1**: Foundation (Week 1)
- Standardize design tokens in style_constants.py
- Create component builder utilities
- Implement collapsible parameter panel

**Phase 2**: Dashboard & Navigation (Week 2)
- Create Dashboard tab module
- Reorganize tab order
- Implement dashboard callbacks
- Update navigation styling

**Phase 3**: Consistency & Polish (Week 3)
- Refactor all components to use builders
- Apply consistent styling across all views
- Enhance responsive behaviors
- Update mobile navigation

**Phase 4**: Testing & Documentation (Week 4)
- Add Playwright integration tests
- Update unit tests for new components
- Document component APIs
- Performance validation

## Risks & Mitigations

| Risk                              | Impact | Mitigation                                              |
| --------------------------------- | ------ | ------------------------------------------------------- |
| Breaking existing callbacks       | High   | Comprehensive integration tests before refactoring      |
| Performance regression            | Medium | Benchmark before/after, maintain < 10% degradation rule |
| Mobile compatibility issues       | Medium | Test on real devices, use 375px viewport baseline       |
| Design token migration complexity | Low    | Incremental migration, one module at a time             |

## Open Questions for Implementation

None remaining - all technical decisions resolved.

## Next Steps

Proceed to Phase 1: Data Model and Contracts generation.
