# Callback Contracts

**Feature**: Unified UX/UI and Architecture Redesign  
**Date**: 2025-10-23  
**Type**: Dash Callback Interface Contracts

## Overview

This document defines the API contracts for all new and modified Dash callbacks in the UX/UI redesign. These contracts ensure predictable behavior, consistent error handling, and clear data flow.

## General Callback Standards

### 1. Signature Standards

```python
@app.callback(
    # Outputs - what component properties are updated
    [Output("component-id", "property"), ...],
    
    # Inputs - what triggers the callback
    [Input("trigger-id", "property"), ...],
    
    # States - additional data read but doesn't trigger callback
    [State("data-id", "property"), ...],
    
    # Prevent initial call unless data loading required
    prevent_initial_call=True|False
)
def callback_name(
    # Input parameters (order matches Input/State order)
    input_param: Type,
    state_param: Type
) -> Union[ReturnType, Tuple[ReturnType, ...]]:
    """
    Callback description.
    
    Args:
        input_param: Description with expected type/format
        state_param: Description with expected type/format
    
    Returns:
        Single value or tuple matching Output declarations
        
    Raises:
        PreventUpdate: When callback should not update any outputs
        
    Behavior:
        - Key behaviors and side effects
        - Caching strategy if applicable
        - Performance considerations
    """
    pass
```

### 2. Error Handling Standards

- Use `raise PreventUpdate` when callback should not fire
- Validate inputs before processing
- Return safe defaults for missing data (e.g., "N/A", empty string, 0)
- Log errors for debugging but don't crash app

### 3. Performance Standards

- Debounce user inputs (500ms default)
- Cache expensive calculations
- Use client-side callbacks for UI-only state
- Background callbacks for long operations (>2 seconds)

---

## Dashboard Callbacks

### DC-001: Update Dashboard Metrics

**Purpose**: Recalculate and display all dashboard metrics when data changes

```python
@app.callback(
    [
        Output("forecast-date", "children"),
        Output("forecast-confidence", "children"),
        Output("forecast-confidence-badge", "color"),
        Output("completion-progress", "value"),
        Output("completion-progress", "label"),
        Output("days-to-completion", "children"),
        Output("days-to-deadline", "children"),
        Output("velocity-items", "children"),
        Output("velocity-points", "children"),
        Output("velocity-trend-icon", "className"),
        Output("velocity-trend-text", "children"),
        Output("remaining-items", "children"),
        Output("remaining-points", "children"),
    ],
    [
        Input("statistics-store", "data"),
        Input("settings-store", "data")
    ]
)
def update_dashboard_metrics(
    statistics: List[Dict[str, Any]],
    settings: Dict[str, Any]
) -> Tuple[str, str, str, float, str, str, str, str, str, str, str, str, str]:
    """
    Update all dashboard metric displays.
    
    Args:
        statistics: List of weekly statistics dictionaries with keys:
            - date (str): Week ending date
            - completed_items (int): Items completed that week
            - completed_points (float): Points completed that week
        settings: App settings dictionary with keys:
            - pert_factor (float): PERT calculation factor
            - deadline (str): Project deadline date
            - total_items (int): Total scope items
            - estimated_items (int): Estimated completion items
            - total_points (float): Total scope points
            - estimated_points (float): Estimated completion points
    
    Returns:
        Tuple of 13 values:
        - forecast_date (str): "YYYY-MM-DD" or "N/A"
        - forecast_confidence (str): "XX%" or "N/A"
        - confidence_badge_color (str): "success", "warning", "danger"
        - completion_progress (float): 0-100
        - completion_progress_label (str): "XX% Complete"
        - days_to_completion (str): "XX days" or "N/A"
        - days_to_deadline (str): "XX days" or "Past deadline"
        - velocity_items (str): "X.X items/week"
        - velocity_points (str): "X.X points/week"
        - velocity_trend_icon (str): Font Awesome class
        - velocity_trend_text (str): "Increasing", "Stable", "Decreasing"
        - remaining_items (str): "XX items"
        - remaining_points (str): "XX.X points"
    
    Raises:
        PreventUpdate: If statistics or settings is None or empty
    
    Behavior:
        - Calculates DashboardMetrics using data/processing.py functions
        - Formats dates using ISO 8601 format
        - Rounds percentages to 1 decimal place
        - Velocity calculated from last 4 weeks
        - Trend determined by comparing recent vs. earlier velocity
        - Confidence based on velocity standard deviation:
            - >80%: success (green badge)
            - 60-80%: warning (yellow badge)
            - <60%: danger (red badge)
    
    Performance:
        - Target execution time: <50ms
        - Results cached in session until data changes
    """
    pass
```

---

### DC-002: Update PERT Timeline

```python
@app.callback(
    [
        Output("pert-optimistic-date", "children"),
        Output("pert-pessimistic-date", "children"),
        Output("pert-most-likely-date", "children"),
        Output("pert-estimate-date", "children"),
        Output("pert-timeline-figure", "figure"),
    ],
    [
        Input("statistics-store", "data"),
        Input("settings-store", "data")
    ]
)
def update_pert_timeline(
    statistics: List[Dict[str, Any]],
    settings: Dict[str, Any]
) -> Tuple[str, str, str, str, Dict[str, Any]]:
    """
    Update PERT forecast timeline display.
    
    Args:
        statistics: Weekly statistics data
        settings: App settings with pert_factor
    
    Returns:
        Tuple of 5 values:
        - optimistic_date (str): Best case completion date
        - pessimistic_date (str): Worst case completion date
        - most_likely_date (str): Most likely completion date
        - pert_estimate_date (str): PERT weighted average date
        - timeline_figure (dict): Plotly figure for timeline visualization
    
    Raises:
        PreventUpdate: If data insufficient for PERT calculation
    
    Behavior:
        - Calculates PERT scenarios using existing forecast logic
        - Creates horizontal timeline Plotly figure
        - Shows confidence range as shaded area
        - Marks deadline for visual comparison
    
    Performance:
        - Target: <100ms including chart generation
    """
    pass
```

---

## Navigation Callbacks

### NC-001: Handle Tab Change

```python
@app.callback(
    Output("navigation-store", "data"),
    Input("chart-tabs", "active_tab"),
    State("navigation-store", "data")
)
def handle_tab_change(
    active_tab: str,
    current_nav_state: Optional[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Update navigation state when user switches tabs.
    
    Args:
        active_tab: ID of newly activated tab (e.g., "tab-dashboard")
        current_nav_state: Current NavigationState or None on first load
    
    Returns:
        Updated NavigationState dictionary:
        {
            "active_tab": str,
            "previous_tab": str | None,
            "tab_history": List[str],  # Max 10 items
            "session_start_tab": str
        }
    
    Raises:
        ValueError: If active_tab is invalid tab ID
        
    Behavior:
        - On first load (current_nav_state is None):
            - active_tab = provided tab (should be "tab-dashboard")
            - session_start_tab = provided tab
            - tab_history = []
            - previous_tab = None
        - On subsequent tab changes:
            - previous_tab = current active_tab
            - active_tab = new tab
            - Append previous_tab to tab_history (FIFO, max 10)
        - Validates tab ID against TAB_CONFIG registry
    
    Valid Tab IDs:
        - tab-dashboard
        - tab-burndown
        - tab-items-per-week
        - tab-points-per-week
        - tab-scope-tracking
        - tab-bug-analysis
    """
    pass
```

---

### NC-002: Initialize Default Tab

```python
@app.callback(
    Output("chart-tabs", "active_tab"),
    Input("url", "pathname"),
    prevent_initial_call=False  # Must run on page load
)
def initialize_default_tab(pathname: str) -> str:
    """
    Set default active tab on app load.
    
    Args:
        pathname: URL pathname (not currently used, reserved for future deep linking)
    
    Returns:
        Default tab ID: "tab-dashboard"
    
    Behavior:
        - Always returns "tab-dashboard" for now
        - Future enhancement: Parse pathname for deep linking
            - /dashboard → "tab-dashboard"
            - /burndown → "tab-burndown"
            - etc.
    """
    pass
```

---

## Parameter Panel Callbacks

### PC-001: Toggle Parameter Panel (Client-Side)

```javascript
app.clientside_callback(
    """
    function(n_clicks, is_open, viewport_width) {
        // Handle initial load
        if (!n_clicks) {
            const stored = localStorage.getItem('param_panel_open');
            const default_open = stored !== null ? stored === 'true' : false;
            const icon = default_open ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
            return [default_open, icon];
        }
        
        // Toggle state
        const new_state = !is_open;
        localStorage.setItem('param_panel_open', new_state);
        
        // Update icon
        const icon = new_state ? 'fas fa-chevron-up' : 'fas fa-chevron-down';
        
        return [new_state, icon];
    }
    """,
    [
        Output("param-panel-collapse", "is_open"),
        Output("expand-params-btn-icon", "className")
    ],
    Input("expand-params-btn", "n_clicks"),
    State("param-panel-collapse", "is_open"),
    State("viewport-store", "data")  # For future mobile adaptations
)
```

**Type**: Client-side callback (JavaScript)  
**Purpose**: Handle panel toggle without server round-trip  
**Storage**: localStorage key `param_panel_open` (boolean string)  
**Mobile Behavior**: Future enhancement to use bottom sheet on mobile viewports

---

### PC-002: Update Parameter Summary

```python
@app.callback(
    Output("param-summary", "children"),
    [
        Input("pert-factor-input", "value"),
        Input("deadline-input", "value"),
        Input("total-items-input", "value"),
        Input("estimated-items-input", "value"),
    ]
)
def update_parameter_summary(
    pert_factor: float,
    deadline: str,
    total_items: int,
    estimated_items: int
) -> str:
    """
    Update collapsed parameter bar summary text.
    
    Args:
        pert_factor: PERT calculation factor (1.0-3.0)
        deadline: Deadline date string (YYYY-MM-DD)
        total_items: Total scope items
        estimated_items: Estimated completion items
    
    Returns:
        Formatted summary string, e.g.:
        "PERT: 1.5 | Deadline: 2025-12-31 | Items: 35/100"
    
    Raises:
        PreventUpdate: Never - always returns safe string
    
    Behavior:
        - Formats values into compact summary
        - Handles None values gracefully ("N/A")
        - Truncates long values for mobile display
    """
    pass
```

---

## Mobile Navigation Callbacks

### MN-001: Detect Viewport Size

```javascript
app.clientside_callback(
    """
    function() {
        const width = window.innerWidth;
        const is_mobile = width < 768;
        return JSON.stringify({
            viewport_width: width,
            is_mobile: is_mobile,
            drawer_open: false,
            bottom_sheet_visible: false,
            swipe_enabled: is_mobile
        });
    }
    """,
    Output("mobile-nav-store", "data"),
    Input("interval-viewport-check", "n_intervals")  # Checks every 500ms
)
```

**Type**: Client-side callback  
**Purpose**: Detect viewport size changes (resize, rotation)  
**Frequency**: Every 500ms via dcc.Interval  
**Storage**: Updates MobileNavigationState in dcc.Store

---

### MN-002: Toggle Mobile Drawer

```python
@app.callback(
    [
        Output("mobile-drawer", "is_open"),
        Output("drawer-overlay", "style")
    ],
    Input("mobile-menu-btn", "n_clicks"),
    State("mobile-drawer", "is_open")
)
def toggle_mobile_drawer(
    n_clicks: int,
    is_open: bool
) -> Tuple[bool, Dict[str, str]]:
    """
    Toggle mobile navigation drawer.
    
    Args:
        n_clicks: Number of menu button clicks
        is_open: Current drawer state
    
    Returns:
        Tuple of:
        - new_is_open (bool): Toggled drawer state
        - overlay_style (dict): Overlay visibility style
    
    Raises:
        PreventUpdate: On initial load (n_clicks is None)
    
    Behavior:
        - Toggle drawer state on click
        - Show overlay when drawer open
        - Hide overlay when drawer closed
    """
    pass
```

---

## Settings Callbacks (Modified)

### SC-001: Update App Settings

```python
@app.callback(
    [
        Output("settings-store", "data"),
        Output("settings-save-feedback", "children"),
        Output("settings-save-feedback", "color")
    ],
    Input("save-settings-btn", "n_clicks"),
    [
        State("pert-factor-input", "value"),
        State("deadline-input", "value"),
        State("total-items-input", "value"),
        State("estimated-items-input", "value"),
        State("total-points-input", "value"),
        State("estimated-points-input", "value"),
    ],
    prevent_initial_call=True
)
def update_app_settings(
    n_clicks: int,
    pert_factor: float,
    deadline: str,
    total_items: int,
    estimated_items: int,
    total_points: float,
    estimated_points: float
) -> Tuple[Dict[str, Any], str, str]:
    """
    Save updated app settings and persist to file.
    
    Args:
        n_clicks: Save button clicks
        pert_factor: PERT factor value
        deadline: Deadline date
        total_items: Total scope items
        estimated_items: Estimated completion items
        total_points: Total scope points
        estimated_points: Estimated completion points
    
    Returns:
        Tuple of:
        - updated_settings (dict): New settings for store
        - feedback_message (str): Success/error message
        - feedback_color (str): "success" or "danger"
    
    Raises:
        PreventUpdate: If n_clicks is None
    
    Behavior:
        - Validates all inputs
        - Calls data.persistence.save_app_settings()
        - Returns success message on save
        - Returns error message on validation failure
        - Updates settings-store to trigger dependent callbacks
    
    Validation Rules:
        - pert_factor: 1.0 <= value <= 3.0
        - deadline: Valid date in future
        - total_items: >= estimated_items > 0
        - total_points: >= estimated_points > 0
    """
    pass
```

**NOTE**: This callback exists but will be modified to work with new parameter panel structure

---

## Data Loading Callbacks (Existing, No Changes)

These callbacks remain unchanged but are documented for completeness:

### DL-001: Load Statistics Data

```python
@app.callback(
    Output("statistics-store", "data"),
    Input("load-data-trigger", "n_clicks")
)
def load_statistics_data(n_clicks: int) -> List[Dict[str, Any]]:
    """
    Load or refresh statistics data.
    
    **STATUS**: Existing callback, NO CHANGES
    
    Returns:
        List of weekly statistics dictionaries
    """
    pass
```

---

### DL-002: Load JIRA Data

```python
@app.callback(
    [
        Output("jira-cache-status", "children"),
        Output("statistics-store", "data")
    ],
    Input("update-data-unified", "n_clicks"),
    [
        State("jira-url", "value"),
        State("jira-token", "value"),
        State("jira-jql-query", "value")
    ]
)
def load_jira_data(
    n_clicks: int,
    jira_url: str,
    jira_token: str,
    jql_query: str
) -> Tuple[str, List[Dict[str, Any]]]:
    """
    Fetch data from JIRA and update statistics.
    
    **STATUS**: Existing callback, NO CHANGES
    
    Returns:
        Tuple of status message and updated statistics
    """
    pass
```

---

## Callback Dependency Graph

```
Page Load
    ↓
initialize_default_tab
    ↓
active_tab = "tab-dashboard"
    ↓
handle_tab_change (updates NavigationState)
    ↓
Dashboard Tab Visible
    ↓
update_dashboard_metrics (triggered by statistics-store, settings-store)
    ├─→ update_pert_timeline
    └─→ Dashboard displays updated

Parameter Panel Interaction
    ↓
User clicks expand button
    ↓
toggle_param_panel (client-side)
    ↓
Panel expands/collapses
    ↓
User changes parameter value
    ↓
update_parameter_summary
    ↓
Summary bar updates
    ↓
User clicks save
    ↓
update_app_settings
    ↓
settings-store updates
    ↓
update_dashboard_metrics re-triggered
    ↓
Dashboard reflects new parameters

Mobile Navigation
    ↓
Viewport resize detected
    ↓
detect_viewport_size (client-side)
    ↓
mobile-nav-store updates
    ↓
Layout adapts (CSS + conditional rendering)
```

## Callback Performance Requirements

| Callback                 | Max Execution Time | Complexity           | Cacheable     |
| ------------------------ | ------------------ | -------------------- | ------------- |
| update_dashboard_metrics | 50ms               | O(n) where n = weeks | Yes (session) |
| update_pert_timeline     | 100ms              | O(n) + chart render  | Yes (session) |
| handle_tab_change        | 10ms               | O(1)                 | No            |
| toggle_param_panel       | 5ms (client-side)  | O(1)                 | No            |
| update_parameter_summary | 5ms                | O(1)                 | No            |
| update_app_settings      | 200ms (I/O)        | O(1)                 | No            |

## Testing Requirements

### Unit Tests

Each callback requires unit tests covering:

1. **Happy path**: Valid inputs produce expected outputs
2. **Edge cases**: Empty data, None values, boundary values
3. **Error handling**: Invalid inputs raise appropriate errors
4. **Performance**: Execution time within requirements

Example:
```python
def test_update_dashboard_metrics_valid_data():
    """Test dashboard metrics with valid statistics."""
    statistics = [
        {"date": "2025-01-01", "completed_items": 5, "completed_points": 25},
        {"date": "2025-01-08", "completed_items": 7, "completed_points": 35},
    ]
    settings = {"pert_factor": 1.5, "deadline": "2025-12-31", 
                "total_items": 100, "estimated_items": 50}
    
    results = update_dashboard_metrics(statistics, settings)
    
    assert results[0] != "N/A"  # forecast_date
    assert "%" in results[1]     # confidence
    assert 0 <= results[3] <= 100  # progress value
```

### Integration Tests

Each user workflow requires integration test:

1. **Dashboard load**: Verify metrics display on page load
2. **Tab navigation**: Verify Dashboard is default, switching works
3. **Parameter update**: Verify parameter changes update Dashboard
4. **Mobile navigation**: Verify mobile drawer/bottom sheet behavior

Example (Playwright):
```python
def test_dashboard_loads_first(live_server):
    """Test Dashboard is default tab."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(live_server)
        
        # Wait for tabs to load
        page.wait_for_selector("#chart-tabs", timeout=5000)
        
        # Verify Dashboard tab is active
        dashboard_tab = page.locator("#chart-tabs .nav-link").filter(has_text="Dashboard")
        assert "active" in (dashboard_tab.get_attribute("class") or "")
        
        # Verify Dashboard content visible
        forecast_card = page.locator("#card-dashboard-forecast")
        assert forecast_card.is_visible()
        
        browser.close()
```

## Callback Migration Checklist

When modifying existing callbacks:

- [ ] Document changes in callback docstring
- [ ] Update contracts in this file
- [ ] Verify backward compatibility with existing data
- [ ] Update unit tests for new behavior
- [ ] Update integration tests for new workflows
- [ ] Performance test to ensure no regression
- [ ] Update quickstart.md with new callback patterns

## Version History

**v1.0.0** (2025-10-23): Initial callback contracts for UX/UI redesign
