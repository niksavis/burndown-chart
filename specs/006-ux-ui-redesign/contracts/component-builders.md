# Component Builder Contracts

**Feature**: Unified UX/UI and Architecture Redesign  
**Date**: 2025-10-23  
**Type**: Python Component Interface Contracts

## Overview

This document defines the standardized API contracts for UI component builder functions. All component builders must follow these interfaces to ensure consistency and predictability.

## General Contract Rules

### 1. Function Signature Standards

All component builders must follow this pattern:

```python
def create_[component_name](
    # Required data (specific to component)
    data: Dict[str, Any] | str | int | None,
    
    # Common optional parameters (order matters)
    variant: str = "default",
    size: str = "md",
    id_suffix: str = "",
    
    # Additional kwargs for pass-through
    **kwargs
) -> Union[dbc.Component, html.Div, dcc.Component]:
    """
    Component description.
    
    Args:
        data: Primary data for the component (type varies by component)
        variant: Visual variant (default, primary, secondary, danger, etc.)
        size: Size variant (sm, md, lg, xl)
        id_suffix: Suffix for generating unique component IDs
        **kwargs: Additional properties passed to underlying Dash component
    
    Returns:
        Configured Dash component ready to render
        
    Raises:
        ValueError: If required data is missing or invalid
        TypeError: If data type doesn't match expected type
    
    Examples:
        >>> create_[component_name](data, variant="primary", size="lg")
        >>> create_[component_name](data, id_suffix="main", className="custom")
    """
    pass
```

### 2. Return Type Standards

- Components must return Dash component types (dbc, html, dcc)
- Never return None or primitive types
- For complex components, return container with clear structure
- Include descriptive `id` attributes for all interactive elements

### 3. Error Handling Standards

- Validate required data at function entry
- Raise `ValueError` for invalid data values
- Raise `TypeError` for wrong data types
- Provide clear error messages mentioning parameter name and expected type

### 4. ID Generation Standards

All component IDs must follow pattern: `{component-type}-{purpose}[-{id_suffix}]`

Examples:
- Button: `btn-submit`, `btn-cancel-settings`
- Input: `input-deadline`, `input-pert-factor`
- Card: `card-dashboard-metrics`
- Tab: `tab-dashboard`, `tab-burndown`

### 5. Styling Standards

- Use design tokens from `ui/style_constants.py`
- Accept `className` via kwargs for custom CSS
- Apply Bootstrap classes for standard behaviors
- Use inline styles only for component-specific values (not colors/spacing)

---

## Tier 1: Atom Components

Atoms are the smallest building blocks - individual UI elements.

### Contract 1.1: Button Component

```python
def create_action_button(
    text: str,
    icon: str | None = None,
    variant: str = "primary",
    size: str = "md",
    id_suffix: str = "",
    **kwargs
) -> dbc.Button:
    """
    Create a standardized action button with optional icon.
    
    Args:
        text: Button label text (required)
        icon: Font Awesome icon name (e.g., "save", "trash") without "fa-" prefix
        variant: Button style - "primary", "secondary", "success", "danger", "warning", "info", "light", "dark", "link"
        size: Button size - "sm", "md", "lg"
        id_suffix: Unique identifier suffix for button ID
        **kwargs: Additional props (onClick, disabled, className, etc.)
    
    Returns:
        dbc.Button configured with consistent styling
        
    Raises:
        ValueError: If text is empty or variant is invalid
        
    Examples:
        >>> create_action_button("Save", "save", variant="primary")
        >>> create_action_button("Delete", "trash", variant="danger", size="sm")
        >>> create_action_button("Cancel", variant="secondary", disabled=True)
    
    ID Pattern: btn-{text-slugified}[-{id_suffix}]
    
    Accessibility:
        - Includes aria-label matching text
        - Supports disabled state
        - Minimum 44px touch target on mobile
    """
    pass
```

**Valid Variants**: primary, secondary, success, danger, warning, info, light, dark, link  
**Valid Sizes**: sm, md, lg  
**Design Tokens Used**: COLOR_PRIMARY, COLOR_SECONDARY, etc., SPACING_SM, SPACING_MD

---

### Contract 1.2: Input Field Component

```python
def create_input_field(
    label: str,
    input_type: str = "text",
    input_id: str = "",
    placeholder: str = "",
    value: Any = None,
    required: bool = False,
    size: str = "md",
    **kwargs
) -> html.Div:
    """
    Create a labeled input field with validation support.
    
    Args:
        label: Display label for input field (required)
        input_type: HTML input type - "text", "number", "date", "email", "password"
        input_id: Unique ID for input element (if empty, generated from label)
        placeholder: Placeholder text
        value: Initial/current value
        required: Whether field is required
        size: Input size - "sm", "md", "lg"
        **kwargs: Additional props (min, max, step, disabled, invalid, valid, etc.)
    
    Returns:
        html.Div containing dbc.Label and dbc.Input
        
    Raises:
        ValueError: If label is empty or input_type is invalid
        
    Examples:
        >>> create_input_field("Deadline", input_type="date", value="2025-12-31")
        >>> create_input_field("PERT Factor", input_type="number", min=1.0, max=3.0, step=0.1)
        >>> create_input_field("Email", input_type="email", required=True)
    
    ID Pattern: input-{label-slugified} or provided input_id
    
    Accessibility:
        - Label properly associated with input via htmlFor/id
        - Required fields marked with aria-required
        - Invalid state communicated via aria-invalid
    """
    pass
```

**Valid Input Types**: text, number, date, email, password, tel, url  
**Valid Sizes**: sm, md, lg  
**Design Tokens Used**: SPACING_SM, COLOR_DANGER (for validation)

---

### Contract 1.3: Icon Component

```python
def create_icon(
    icon_name: str,
    variant: str = "default",
    size: str = "md",
    **kwargs
) -> html.I:
    """
    Create Font Awesome icon element with consistent sizing.
    
    Args:
        icon_name: Font Awesome icon name (e.g., "chart-line", "save") without "fa-" prefix
        variant: Color variant - "default", "primary", "secondary", "success", "danger", "warning", "muted"
        size: Icon size - "xs", "sm", "md", "lg", "xl", "2x", "3x"
        **kwargs: Additional props (className, style, etc.)
    
    Returns:
        html.I element with icon classes
        
    Raises:
        ValueError: If icon_name is empty
        
    Examples:
        >>> create_icon("chart-line", variant="primary", size="lg")
        >>> create_icon("trash", variant="danger")
        >>> create_icon("info-circle", variant="muted", size="sm")
    
    Accessibility:
        - Decorative icons have aria-hidden="true"
        - Semantic icons require aria-label in kwargs
    """
    pass
```

**Valid Variants**: default, primary, secondary, success, danger, warning, muted  
**Valid Sizes**: xs, sm, md, lg, xl, 2x, 3x  
**Design Tokens Used**: COLOR_* constants for variant colors

---

## Tier 2: Molecule Components

Molecules combine atoms into simple functional units.

### Contract 2.1: Labeled Input Component

```python
def create_labeled_input(
    label: str,
    input_id: str,
    input_type: str = "text",
    value: Any = None,
    help_text: str = "",
    error_message: str = "",
    size: str = "md",
    **kwargs
) -> dbc.FormGroup:
    """
    Create input field with label, help text, and error message support.
    
    Args:
        label: Display label text (required)
        input_id: Unique ID for input (required)
        input_type: HTML input type
        value: Initial value
        help_text: Optional help text displayed below input
        error_message: Error message (shown only if invalid=True in kwargs)
        size: Component size
        **kwargs: Additional props passed to dbc.Input (invalid, valid, disabled, etc.)
    
    Returns:
        dbc.FormGroup containing label, input, help text, and error feedback
        
    Examples:
        >>> create_labeled_input("PERT Factor", "pert-input", input_type="number", 
        ...                      help_text="Typically 1.5-2.0", min=1.0, max=3.0)
        >>> create_labeled_input("Deadline", "deadline-input", input_type="date",
        ...                      error_message="Date must be in future", invalid=True)
    
    Accessibility:
        - Help text linked via aria-describedby
        - Error messages linked via aria-describedby
        - Invalid state properly communicated
    """
    pass
```

---

### Contract 2.2: Info Card Component

```python
def create_info_card(
    title: str,
    value: str | int | float,
    icon: str = "",
    subtitle: str = "",
    variant: str = "default",
    clickable: bool = False,
    click_id: str = "",
    size: str = "md",
    **kwargs
) -> dbc.Card:
    """
    Create information display card for metrics/statistics.
    
    Args:
        title: Card title/label (required)
        value: Primary value to display (required)
        icon: Optional Font Awesome icon name
        subtitle: Optional subtitle/description
        variant: Color variant - "default", "primary", "success", "warning", "danger"
        clickable: Whether card should be interactive
        click_id: ID for click callback (required if clickable=True)
        size: Card size - "sm", "md", "lg"
        **kwargs: Additional props (className, style, etc.)
    
    Returns:
        dbc.Card with standardized info display layout
        
    Raises:
        ValueError: If title or value is empty, or clickable=True but click_id empty
        
    Examples:
        >>> create_info_card("Days to Completion", 53, icon="calendar-check", 
        ...                  subtitle="Based on current velocity", variant="primary")
        >>> create_info_card("Remaining Items", 42, icon="tasks", 
        ...                  clickable=True, click_id="goto-burndown")
    
    ID Pattern: card-{title-slugified}[-{click_id}]
    
    Layout:
        - Header: icon + title
        - Body: large value + subtitle
        - Footer: optional action link (if clickable)
    """
    pass
```

**Valid Variants**: default, primary, success, warning, danger  
**Valid Sizes**: sm, md, lg  
**Design Tokens Used**: Card border radius, shadow, padding from DESIGN_TOKENS

---

### Contract 2.3: Tab Item Component

```python
def create_tab_item(
    label: str,
    tab_id: str,
    icon: str = "",
    content: Any = None,
    requires_data: bool = True,
    **kwargs
) -> dbc.Tab:
    """
    Create a tab item for navigation.
    
    Args:
        label: Tab display label (required)
        tab_id: Unique tab identifier (required, pattern: tab-*)
        icon: Font Awesome icon name for tab
        content: Tab content (Dash components) or None for lazy loading
        requires_data: Whether tab needs data loaded before display
        **kwargs: Additional props (disabled, className, etc.)
    
    Returns:
        dbc.Tab configured for navigation system
        
    Raises:
        ValueError: If label or tab_id empty, or tab_id doesn't match pattern
        
    Examples:
        >>> create_tab_item("Dashboard", "tab-dashboard", icon="tachometer-alt",
        ...                 content=dashboard_layout)
        >>> create_tab_item("Burndown", "tab-burndown", icon="chart-line",
        ...                 requires_data=True)
    
    ID Pattern: Must be "tab-{name}"
    
    Behavior:
        - If content is None, children rendered by callback when tab active
        - If requires_data=True, shows loading spinner until data ready
    """
    pass
```

---

## Tier 3: Organism Components

Organisms are complex UI sections composed of molecules and atoms.

### Contract 3.1: Dashboard Metrics Card

```python
def create_dashboard_metrics_card(
    metrics: Dict[str, Any],
    card_type: str = "forecast",
    variant: str = "primary",
    size: str = "md",
    **kwargs
) -> dbc.Card:
    """
    Create dashboard metric display card with rich formatting.
    
    Args:
        metrics: Dictionary containing metric data (structure varies by card_type)
        card_type: Type of metrics card - "forecast", "velocity", "remaining", "pert", "scope"
        variant: Color variant for card accent
        size: Card size
        **kwargs: Additional props
    
    Returns:
        dbc.Card with dashboard-specific metric layout
        
    Raises:
        ValueError: If metrics is empty or card_type invalid
        KeyError: If metrics missing required fields for card_type
        
    Examples:
        >>> metrics = {
        ...     "completion_forecast_date": "2025-12-15",
        ...     "completion_confidence": 75.5,
        ...     "days_to_completion": 53
        ... }
        >>> create_dashboard_metrics_card(metrics, card_type="forecast", variant="primary")
    
    Required Fields by Card Type:
        - forecast: completion_forecast_date, completion_confidence, days_to_completion
        - velocity: current_velocity_items, current_velocity_points, velocity_trend
        - remaining: remaining_items, remaining_points, completion_percentage
        - pert: optimistic_date, pessimistic_date, most_likely_date
        - scope: (scope-specific fields from ScopeMetrics)
    
    ID Pattern: card-dashboard-{card_type}
    
    Layout:
        - CardHeader: Icon + Title + Help Icon
        - CardBody: Primary metric (large) + Supporting metrics (small) + Progress/Chart
        - CardFooter: Action buttons or navigation links
    """
    pass
```

**Valid Card Types**: forecast, velocity, remaining, pert, scope  
**Valid Variants**: primary, success, warning, danger, info  
**Design Tokens Used**: Full design token system (colors, spacing, typography, shadows)

---

### Contract 3.2: Parameter Control Panel

```python
def create_parameter_panel(
    current_values: Dict[str, Any],
    is_open: bool = False,
    variant: str = "light",
    **kwargs
) -> html.Div:
    """
    Create collapsible parameter control panel.
    
    Args:
        current_values: Dictionary of current parameter values (pert_factor, deadline, etc.)
        is_open: Initial panel state (expanded or collapsed)
        variant: Background variant - "light", "white", "secondary"
        **kwargs: Additional props
    
    Returns:
        html.Div containing collapsed bar and expandable panel
        
    Raises:
        ValueError: If current_values is empty or missing required parameters
        
    Examples:
        >>> values = {
        ...     "pert_factor": 1.5,
        ...     "deadline": "2025-12-31",
        ...     "total_items": 100,
        ...     "estimated_items": 35
        ... }
        >>> create_parameter_panel(values, is_open=False, variant="light")
    
    Required current_values Keys:
        - pert_factor (float)
        - deadline (str, date format)
        - total_items (int)
        - estimated_items (int)
        - total_points (float)
        - estimated_points (float)
    
    Structure:
        - Collapsed Bar: 50px height, shows key values, expand button
        - Expanded Panel: Full controls, responsive grid layout
    
    IDs Generated:
        - param-bar-collapsed: Collapsed summary bar
        - param-panel-collapse: Expandable section (dbc.Collapse)
        - expand-params-btn: Toggle button
        - param-summary: Summary text display
        - Plus individual input field IDs
    
    Behavior:
        - Client-side callback handles expand/collapse
        - State persists in localStorage
        - Mobile: alternative bottom sheet layout (<768px)
    """
    pass
```

---

### Contract 3.3: Dashboard Tab Layout

```python
def create_dashboard_tab() -> dbc.Tab:
    """
    Create complete Dashboard tab with all metrics and layout.
    
    Args:
        None (loads data from stores via callbacks)
    
    Returns:
        dbc.Tab containing full dashboard layout
        
    Examples:
        >>> dashboard_tab = create_dashboard_tab()
        >>> tabs = dbc.Tabs([dashboard_tab, burndown_tab, ...])
    
    Structure:
        - Container (fluid)
            - Row 1: Completion Forecast + Velocity + Remaining Work (3 columns)
            - Row 2: PERT Timeline + Scope Health (2 columns)
            - Row 3: Quick Actions / Recent Activity
    
    IDs Generated:
        - tab-dashboard: Tab component ID
        - dashboard-container: Main container
        - card-dashboard-forecast: Forecast metrics card
        - card-dashboard-velocity: Velocity metrics card
        - card-dashboard-remaining: Remaining work card
        - card-dashboard-pert: PERT timeline card
        - card-dashboard-scope: Scope health card
    
    Responsive Behavior:
        - Desktop (≥992px): 3-column top row, 2-column bottom row
        - Tablet (768-992px): 2-column grid
        - Mobile (<768px): Single column, stacked vertically
    
    Data Dependencies:
        - statistics-store: Weekly statistics data
        - settings-store: App settings (PERT factor, deadline, scope)
        - Metrics computed by dashboard callbacks
    """
    pass
```

---

## Callback Contracts

### Callback Contract 1: Dashboard Metrics Update

```python
@app.callback(
    [
        Output("forecast-date", "children"),
        Output("forecast-confidence", "children"),
        Output("completion-progress", "value"),
        Output("velocity-metric-items", "children"),
        Output("velocity-metric-points", "children"),
        Output("velocity-trend-icon", "className"),
        Output("remaining-items-value", "children"),
        Output("remaining-points-value", "children"),
    ],
    [
        Input("statistics-store", "data"),
        Input("settings-store", "data")
    ]
)
def update_dashboard_metrics(
    statistics: List[Dict[str, Any]],
    settings: Dict[str, Any]
) -> Tuple[str, str, float, str, str, str, str, str]:
    """
    Update all dashboard metric displays when data changes.
    
    Args:
        statistics: Weekly statistics data from store
        settings: App settings including PERT factor, deadline, scope
    
    Returns:
        Tuple of formatted strings/values for each output:
        - forecast_date (str): Formatted completion date
        - forecast_confidence (str): Confidence percentage with label
        - completion_progress (float): Progress bar value 0-100
        - velocity_items (str): Formatted items/week velocity
        - velocity_points (str): Formatted points/week velocity
        - velocity_trend_icon (str): Icon class for trend direction
        - remaining_items (str): Formatted remaining items count
        - remaining_points (str): Formatted remaining points count
    
    Raises:
        PreventUpdate: If statistics or settings are empty/invalid
        
    Behavior:
        - Calculates DashboardMetrics from inputs
        - Formats values for display (dates, percentages, counts)
        - Returns "N/A" for unavailable metrics
        - Caches results in session store
    """
    pass
```

---

### Callback Contract 2: Parameter Panel Toggle

```python
app.clientside_callback(
    """
    function(n_clicks, is_open) {
        if (!n_clicks) {
            // Initial load - check localStorage
            const stored = localStorage.getItem('param_panel_open');
            return [stored === 'true', stored === 'true' ? 'fa-chevron-up' : 'fa-chevron-down'];
        }
        
        // Toggle state
        const new_state = !is_open;
        localStorage.setItem('param_panel_open', new_state);
        
        // Update icon
        const icon = new_state ? 'fa-chevron-up' : 'fa-chevron-down';
        
        return [new_state, icon];
    }
    """,
    [
        Output("param-panel-collapse", "is_open"),
        Output("expand-params-btn-icon", "className")
    ],
    Input("expand-params-btn", "n_clicks"),
    State("param-panel-collapse", "is_open")
)
```

**Purpose**: Handle parameter panel expand/collapse without server round-trip  
**Client-Side**: Yes (JavaScript executed in browser)  
**Storage**: localStorage for persistence across sessions  

---

### Callback Contract 3: Tab Navigation Handler

```python
@app.callback(
    Output("navigation-store", "data"),
    Input("chart-tabs", "active_tab"),
    State("navigation-store", "data")
)
def handle_tab_change(
    active_tab: str,
    current_nav_state: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update navigation state when user switches tabs.
    
    Args:
        active_tab: ID of newly activated tab
        current_nav_state: Current NavigationState from store
    
    Returns:
        Updated NavigationState dictionary
    
    Raises:
        PreventUpdate: If active_tab unchanged
        ValueError: If active_tab is invalid tab ID
        
    Behavior:
        - Updates active_tab in state
        - Records previous_tab
        - Appends to tab_history (max 10 items)
        - Returns updated state for storage
    """
    pass
```

---

## Testing Contracts

### Unit Test Contract

All component builders must have corresponding unit tests:

```python
def test_create_[component_name]_default():
    """Test component creation with default parameters."""
    component = create_[component_name](required_data)
    assert component is not None
    assert component.id.startswith("[component-type]-")

def test_create_[component_name]_variants():
    """Test all valid variants render without error."""
    for variant in VALID_VARIANTS:
        component = create_[component_name](required_data, variant=variant)
        assert component is not None

def test_create_[component_name]_sizes():
    """Test all valid sizes render without error."""
    for size in VALID_SIZES:
        component = create_[component_name](required_data, size=size)
        assert component is not None

def test_create_[component_name]_validation():
    """Test validation errors for invalid inputs."""
    with pytest.raises(ValueError):
        create_[component_name](invalid_data)
    with pytest.raises(TypeError):
        create_[component_name](wrong_type_data)

def test_create_[component_name]_accessibility():
    """Test accessibility attributes present."""
    component = create_[component_name](required_data)
    # Verify aria-labels, roles, etc.
```

---

## Implementation Checklist

When implementing a component builder, verify:

- [ ] Function signature matches contract
- [ ] All parameters documented in docstring
- [ ] Examples provided in docstring
- [ ] Required data validation at function entry
- [ ] Design tokens used (not hardcoded values)
- [ ] Component ID follows naming pattern
- [ ] Accessibility attributes included
- [ ] Return type is Dash component
- [ ] Error handling for invalid inputs
- [ ] Unit tests cover all variants and sizes
- [ ] Integration test for user workflow
- [ ] Mobile responsiveness verified

---

## Version History

**v1.0.0** (2025-10-23): Initial contract definitions for UX/UI redesign feature
