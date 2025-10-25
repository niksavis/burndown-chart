# Architecture Guidelines - Feature 006 UX/UI Redesign

## Overview

This document defines the architecture standards for the Burndown Chart Generator application following the completion of Feature 006 UX/UI Redesign. It establishes clear layer boundaries, code organization principles, and callback patterns.

**Last Updated**: 2025-01-09  
**Status**: Phase 6 Implementation (US4 - Architecture Cleanup)

---

## Table of Contents

- [Layer Boundaries](#layer-boundaries)
- [Code Organization](#code-organization)
- [Callback Registration Patterns](#callback-registration-patterns)
- [State Management](#state-management)
- [Design System](#design-system)
- [Testing Standards](#testing-standards)

---

## Layer Boundaries

### 3-Tier Architecture

The application follows a strict 3-tier separation pattern:

```
┌─────────────────────────────────────────────────────┐
│                  UI Layer (ui/)                     │
│  - Component builders (buttons, cards, inputs)      │
│  - Layout composition                               │
│  - Design tokens and styling                        │
│  - NO business logic                                │
│  - NO data persistence                              │
│  - NO calculations                                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│              Callback Layer (callbacks/)            │
│  - Event handling                                   │
│  - State coordination                               │
│  - Delegates to data layer                          │
│  - NO business logic                                │
│  - NO file I/O operations                           │
│  - NO calculations                                  │
└─────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────┐
│               Data Layer (data/)                    │
│  - Business logic (calculations, forecasting)       │
│  - Data persistence (JSON files)                    │
│  - External API integration (JIRA)                  │
│  - Data validation                                  │
│  - State management                                 │
└─────────────────────────────────────────────────────┘
```

### Layer Responsibilities

#### UI Layer (`ui/`)

**Purpose**: Pure presentation components with no business logic.

**Allowed**:
- Component builders (buttons, cards, inputs, charts)
- Layout composition and DOM structure
- Design token usage (`DESIGN_TOKENS` dictionary)
- CSS class application
- Dash component instantiation

**Forbidden**:
- Business logic (calculations, forecasting)
- Data persistence (file I/O, database access)
- External API calls
- State validation logic
- Complex data transformations

**Example - Correct UI Component**:
```python
# ui/button_utils.py
from ui.style_constants import DESIGN_TOKENS

def create_action_button(text: str, icon: str, **kwargs):
    """Pure UI component builder - no business logic."""
    return dbc.Button(
        [html.I(className=f"fas fa-{icon} me-2"), text],
        color=DESIGN_TOKENS["colors"]["primary"],
        **kwargs
    )
```

**Example - Incorrect UI Component** ❌:
```python
# ❌ WRONG: Business logic in UI
def create_metrics_card(statistics_data):
    # ❌ Calculation logic belongs in data layer
    avg_velocity = sum(s["points"] for s in statistics_data) / len(statistics_data)
    
    return dbc.Card([
        html.H3(f"Average: {avg_velocity:.1f}")
    ])
```

#### Callback Layer (`callbacks/`)

**Purpose**: Event handling and state coordination between UI and data layers.

**Allowed**:
- Dash callback decorators (`@callback`)
- State coordination between components
- Calling data layer functions
- Updating UI components with results
- Error handling and user feedback

**Forbidden**:
- Business logic implementation
- File I/O operations (use `data.persistence`)
- Complex calculations (use `data.processing`)
- Direct JSON manipulation
- External API calls (use `data.jira_*`)

**Example - Correct Callback**:
```python
# callbacks/settings.py
from dash import callback, Output, Input
from data.persistence import save_app_settings, calculate_project_scope_from_jira

@callback(
    Output("settings-store", "data"),
    Input("save-button", "n_clicks"),
    State("pert-input", "value")
)
def save_settings(n_clicks, pert_factor):
    """Callback delegates to data layer - no business logic."""
    if n_clicks is None:
        return dash.no_update
    
    # Delegate to data layer
    new_settings = save_app_settings({"pert_factor": pert_factor})
    
    return new_settings
```

**Example - Incorrect Callback** ❌:
```python
# ❌ WRONG: Business logic in callback
@callback(Output("forecast", "children"), Input("data", "data"))
def update_forecast(statistics):
    # ❌ Calculation logic belongs in data layer
    velocities = [s["points"] / s["weeks"] for s in statistics]
    avg_velocity = sum(velocities) / len(velocities)
    
    # ❌ File I/O belongs in data layer
    with open("forecast_cache.json", "w") as f:
        json.dump({"velocity": avg_velocity}, f)
    
    return f"Forecast: {avg_velocity:.1f}"
```

#### Data Layer (`data/`)

**Purpose**: Business logic, data persistence, and external integrations.

**Allowed**:
- Business calculations and forecasting
- File I/O operations (JSON persistence)
- External API integration (JIRA)
- Data validation and transformation
- State management functions
- Caching and performance optimization

**Forbidden**:
- UI component creation
- Direct callback registration
- HTML/CSS generation

**Example - Correct Data Module**:
```python
# data/processing.py
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

def calculate_performance_trend(statistics: List[Dict]) -> Dict:
    """
    Calculate performance trend from statistics data.
    Pure business logic - no UI, no callbacks.
    """
    if not statistics:
        logger.warning("No statistics provided for trend calculation")
        return {"trend": "unknown", "confidence": 0.0}
    
    # Business logic implementation
    velocities = [s.get("velocity", 0) for s in statistics]
    
    # Complex calculations belong here
    trend = "improving" if velocities[-1] > velocities[0] else "declining"
    confidence = calculate_confidence_score(velocities)
    
    return {"trend": trend, "confidence": confidence}

def calculate_confidence_score(velocities: List[float]) -> float:
    """Helper function - business logic implementation."""
    # Implementation details...
    pass
```

### Validated Architecture Compliance

**Status as of 2025-01-09**:

✅ **Callbacks Layer**: 18 imports from `data.persistence` - proper delegation pattern  
✅ **UI Layer**: 0 calculation functions found - clean separation  
✅ **Design System**: 20+ usages of `DESIGN_TOKENS` - consistent styling  
✅ **State Management**: Centralized in `data/state_management.py`

---

## Code Organization

### Directory Structure Standards

```
burndown-chart/
├── ui/                         # Presentation Layer
│   ├── __init__.py             # UI module exports
│   ├── layout.py               # Main app layout
│   ├── style_constants.py      # DESIGN_TOKENS definition
│   ├── button_utils.py         # Button builders
│   ├── cards.py                # Card builders
│   ├── components.py           # Reusable components
│   └── [feature]_*.py          # Feature-specific UI components
│
├── callbacks/                  # Event Handling Layer
│   ├── __init__.py             # Callback registration
│   ├── settings.py             # Settings callbacks
│   ├── visualization.py        # Chart callbacks
│   ├── statistics.py           # Statistics callbacks
│   └── [feature].py            # Feature-specific callbacks
│
├── data/                       # Business Logic Layer
│   ├── __init__.py             # Data module exports
│   ├── persistence.py          # File I/O and persistence
│   ├── processing.py           # Business calculations
│   ├── state_management.py     # State management functions
│   ├── jira_*.py               # JIRA integration
│   └── [domain].py             # Domain-specific logic
│
├── configuration/              # Application Configuration
│   ├── settings.py             # App settings
│   ├── chart_config.py         # Chart configurations
│   └── help_content.py         # Help text content
│
├── assets/                     # Static Assets
│   ├── custom.css              # Global styles
│   ├── *.js                    # Client-side scripts
│   └── manifest.json           # PWA manifest
│
├── tests/                      # Test Suite
│   ├── unit/                   # Fast unit tests
│   ├── integration/            # End-to-end tests
│   └── utils/                  # Test utilities
│
└── specs/                      # Specifications
    └── 006-ux-ui-redesign/     # Feature documentation
        ├── tasks.md            # Task tracking
        ├── data-model.md       # Data structures
        └── docs/               # Architecture docs
```

### Module Organization Principles

1. **One Responsibility Per File**
   - `button_utils.py` → Button components only
   - `cards.py` → Card components only
   - `persistence.py` → File I/O only

2. **Feature Cohesion**
   - Related functionality grouped together
   - `bug_analysis.py` in ui/, callbacks/, data/

3. **Depth Over Width**
   - Use subdirectories for complex features
   - `ui/components/` for shared component builders
   - `data/calculators/` for calculation engines

4. **Clear Naming Conventions**
   - `*_utils.py` → Helper utilities
   - `*_config.py` → Configuration files
   - `*_management.py` → Management/orchestration

### Import Standards

**Import Order** (per PEP 8):
```python
# 1. Standard library imports
import os
import json
from typing import Dict, List

# 2. Third-party imports
import dash
from dash import html, dcc
import plotly.graph_objects as go

# 3. Local application imports
from data.persistence import load_app_settings
from ui.style_constants import DESIGN_TOKENS
```

**Import Principles**:
- Always use absolute imports
- Import functions/classes directly when possible
- Avoid circular imports (use lazy imports if needed)
- Document external dependencies in `requirements.txt`

---

## Callback Registration Patterns

### Centralized Registration

All callbacks are registered through `callbacks/__init__.py`:

```python
# callbacks/__init__.py
"""
Callback Registration Module

This module provides centralized callback registration for the Dash application.
All callback modules must be imported here to ensure proper registration.

Pattern: Import callback modules → Callbacks auto-register via @callback decorator
"""

def register_callbacks(app):
    """
    Register all application callbacks.
    
    Args:
        app: Dash application instance
    
    Note: Individual callback modules use @callback decorator which registers
          callbacks automatically when the module is imported.
    """
    # Import callback modules to trigger registration
    from callbacks import settings
    from callbacks import visualization
    from callbacks import statistics
    from callbacks import jira_config
    from callbacks import dashboard
    from callbacks import scope_metrics
    from callbacks import bug_analysis
    from callbacks import settings_panel
    from callbacks import mobile_navigation
    from callbacks import jql_editor
    
    # Callbacks are now registered via @callback decorator
    pass
```

### Callback Patterns

**Standard Callback Structure**:
```python
from dash import callback, Output, Input, State, no_update
from data.persistence import load_data, save_data
import logging

logger = logging.getLogger(__name__)

@callback(
    Output("result-component", "children"),
    Input("trigger-button", "n_clicks"),
    State("input-field", "value"),
    prevent_initial_call=True
)
def handle_user_action(n_clicks, input_value):
    """
    Handle user action with proper error handling.
    
    Pattern:
    1. Validate inputs
    2. Delegate to data layer
    3. Return UI update
    4. Handle errors gracefully
    """
    # Validate inputs
    if n_clicks is None:
        return no_update
    
    try:
        # Delegate to data layer
        result = process_data(input_value)  # From data.processing
        
        # Return UI update
        return create_result_display(result)  # From ui.components
        
    except Exception as e:
        logger.error(f"Failed to process data: {e}")
        return create_error_message(str(e))  # From ui.error_utils
```

**Multi-Output Callback Pattern**:
```python
@callback(
    [
        Output("data-store", "data"),
        Output("status-message", "children"),
        Output("loading-spinner", "is_open")
    ],
    Input("update-button", "n_clicks"),
    prevent_initial_call=True
)
def update_data_with_feedback(n_clicks):
    """
    Update data with user feedback pattern.
    
    Returns: tuple of (data, status_message, loading_state)
    """
    try:
        # Delegate to data layer
        new_data = fetch_updated_data()
        
        return (
            new_data,
            create_success_message("Data updated successfully"),
            False  # Close loading spinner
        )
    except Exception as e:
        logger.error(f"Update failed: {e}")
        return (
            no_update,
            create_error_message(str(e)),
            False
        )
```

**Background Callback Pattern** (for long-running operations):
```python
@callback(
    Output("result", "children"),
    Input("start-button", "n_clicks"),
    background=True,
    prevent_initial_call=True
)
def process_long_running_task(n_clicks):
    """
    Handle long-running operations without blocking UI.
    
    Best for: JIRA API calls, large data processing
    """
    if n_clicks is None:
        return no_update
    
    # Long-running operation
    result = fetch_large_dataset()  # From data.jira_simple
    
    return create_result_display(result)
```

---

## State Management

### State Container Standards

The application uses standardized `dcc.Store` components defined in `data/state_management.py`.

**State Containers**:

| Store ID                | Storage Type | Purpose                              | Module                  |
| ----------------------- | ------------ | ------------------------------------ | ----------------------- |
| `settings-store`        | `local`      | User preferences, app settings       | `data.persistence`      |
| `statistics-store`      | `memory`     | Project statistics, historical data  | `data.persistence`      |
| `ui-state-store`        | `memory`     | Transient UI state (loading, errors) | `data.state_management` |
| `nav-state-store`       | `memory`     | Navigation and tab state             | `data.state_management` |
| `parameter-panel-state` | `local`      | Panel collapse/expand preference     | `data.state_management` |
| `mobile-nav-state`      | `memory`     | Mobile navigation drawer state       | `data.state_management` |

### State Management Functions

**Navigation State**:
```python
from data.state_management import (
    initialize_navigation_state,
    update_navigation_state,
    validate_navigation_state
)

# Initialize
nav_state = initialize_navigation_state(default_tab="tab-dashboard")

# Update
new_state = update_navigation_state(
    current_state=nav_state,
    new_tab="tab-burndown",
    add_to_history=True
)

# Validate
is_valid, errors = validate_navigation_state(nav_state)
```

**UI State**:
```python
from data.state_management import initialize_ui_state, update_ui_state

# Initialize
ui_state = initialize_ui_state()

# Update loading state
new_state = update_ui_state(
    current_state=ui_state,
    loading=True,
    last_action="Fetching JIRA data"
)
```

**Mobile Navigation State**:
```python
from data.state_management import initialize_mobile_nav_state, update_mobile_nav_state

# Initialize
mobile_state = initialize_mobile_nav_state()

# Update drawer state
new_state = update_mobile_nav_state(
    current_state=mobile_state,
    drawer_open=True,
    active_tab="tab-settings"
)
```

### State Management Best Practices

1. **Immutable Updates**
   - Always return new state dict
   - Never mutate existing state
   - Use spread operator: `{**current_state, "key": new_value}`

2. **Validation**
   - Validate state before updates
   - Log validation errors
   - Return previous state on validation failure

3. **Timestamps**
   - Include `last_updated` field
   - Use ISO format: `datetime.now().isoformat()`

4. **Error Handling**
   - Gracefully handle missing fields
   - Provide default values
   - Log state transitions

---

## Design System

### Design Token Architecture

**Token Definition** (`ui/style_constants.py`):
```python
DESIGN_TOKENS = {
    "colors": {
        "primary": "#0066cc",
        "success": "#28a745",
        "danger": "#dc3545",
        "warning": "#ffc107",
        "info": "#17a2b8",
    },
    "spacing": {
        "xs": "0.25rem",
        "sm": "0.5rem",
        "md": "1rem",
        "lg": "1.5rem",
        "xl": "2rem",
    },
    "typography": {
        "font_family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto",
        "font_size_base": "16px",
        "line_height_base": 1.5,
    },
}
```

**Token Usage**:
```python
from ui.style_constants import DESIGN_TOKENS, get_color, get_spacing

# Direct access
primary_color = DESIGN_TOKENS["colors"]["primary"]

# Helper functions
button_color = get_color("primary")
card_padding = get_spacing("md")
```

**CSS Variables** (`assets/custom.css`):
```css
:root {
    --color-primary: #0066cc;
    --spacing-md: 1rem;
    --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto;
}

.card-consistent {
    padding: var(--spacing-md);
    border: 1px solid var(--color-border);
}
```

### Component Builder Pattern

**Standard Builder**:
```python
from ui.style_constants import DESIGN_TOKENS
import dash_bootstrap_components as dbc
from dash import html

def create_action_button(
    text: str,
    icon: str,
    action_type: str = "primary",
    size: str = "md",
    **kwargs
):
    """
    Create consistent action button using design tokens.
    
    Args:
        text: Button text
        icon: FontAwesome icon name (without 'fa-' prefix)
        action_type: Button style ('primary', 'success', 'danger', etc.)
        size: Button size ('sm', 'md', 'lg')
        **kwargs: Additional button properties
    
    Returns:
        dbc.Button: Configured button component
    """
    return dbc.Button(
        [html.I(className=f"fas fa-{icon} me-2"), text],
        color=action_type,
        size=size,
        className=f"action-btn action-btn-{action_type}",
        **kwargs
    )
```

**Usage in Layouts**:
```python
from ui.button_utils import create_action_button

layout = html.Div([
    create_action_button("Save", "save", id="save-btn"),
    create_action_button("Cancel", "times", action_type="secondary", id="cancel-btn"),
])
```

---

## Testing Standards

### Test Organization

Tests mirror the source code structure:

```
tests/
├── unit/                       # Fast, isolated tests
│   ├── ui/                     # UI component tests
│   ├── data/                   # Business logic tests
│   └── configuration/          # Config tests
│
├── integration/                # End-to-end workflows
│   ├── dashboard/              # Dashboard workflow tests
│   └── jira/                   # JIRA integration tests
│
└── utils/                      # Test helpers and fixtures
```

### Test Isolation Requirements (CRITICAL)

**All tests MUST**:
- Use temporary files/directories (no project root pollution)
- Clean up resources even if test fails
- Pass when run individually, in parallel, or in any order
- Not share state between tests

**Correct Test Pattern**:
```python
import tempfile
import os
import pytest
from unittest.mock import patch

@pytest.fixture
def temp_settings_file():
    """Create isolated temporary file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name
    
    yield temp_file
    
    # Cleanup (runs even if test fails)
    if os.path.exists(temp_file):
        os.unlink(temp_file)

def test_save_settings(temp_settings_file):
    """Test with proper isolation."""
    from data.persistence import save_app_settings
    
    with patch("data.persistence.SETTINGS_FILE", temp_settings_file):
        save_app_settings({"pert_factor": 1.5})
        
        assert os.path.exists(temp_settings_file)
```

### Architecture Testing

**Layer Boundary Tests**:
```python
def test_ui_has_no_business_logic():
    """Verify UI layer contains no calculations."""
    import ast
    import os
    
    ui_files = [
        f for f in os.listdir("ui")
        if f.endswith(".py") and f != "__init__.py"
    ]
    
    forbidden_functions = ["calculate_", "compute_", "process_data"]
    
    for ui_file in ui_files:
        with open(f"ui/{ui_file}", "r") as f:
            tree = ast.parse(f.read())
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for forbidden in forbidden_functions:
                    assert not node.name.startswith(forbidden), \
                        f"Business logic found in UI: {ui_file}::{node.name}"
```

**Callback Delegation Tests**:
```python
def test_callbacks_delegate_to_data_layer():
    """Verify callbacks don't contain business logic."""
    import ast
    
    callback_files = [f for f in os.listdir("callbacks") if f.endswith(".py")]
    
    for callback_file in callback_files:
        with open(f"callbacks/{callback_file}", "r") as f:
            content = f.read()
        
        # Check for imports from data layer
        assert "from data." in content or "import data." in content, \
            f"Callback {callback_file} doesn't import from data layer"
```

---

## Compliance Verification

### Automated Checks

**Run architecture validation**:
```powershell
# Check callback delegation
.\.venv\Scripts\activate; pytest tests/unit/ -k "architecture" -v

# Check UI layer purity
.\.venv\Scripts\activate; pytest tests/unit/ -k "layer_boundaries" -v

# Full test suite
.\.venv\Scripts\activate; pytest tests/ --cov=ui --cov=callbacks --cov=data -v
```

### Manual Review Checklist

Before merging feature branches:

- [ ] All UI components use design tokens (no hardcoded colors)
- [ ] Callbacks delegate to data layer (no inline business logic)
- [ ] No file I/O in callbacks or UI layers
- [ ] State management uses `data/state_management.py` functions
- [ ] All tests pass with proper isolation
- [ ] No files created in project root during testing
- [ ] Documentation updated to reflect changes

---

## Migration from Legacy Code

### Identifying Legacy Patterns

**Red Flags**:
```python
# ❌ Business logic in callback
@callback(Output("result", "children"), Input("data", "data"))
def process_data(data):
    # ❌ Calculation in callback
    velocity = sum(d["points"] for d in data) / len(data)
    return f"Velocity: {velocity}"

# ❌ Hardcoded colors in UI
def create_card():
    return dbc.Card(style={"background-color": "#0066cc"})  # ❌ Hardcoded

# ❌ File I/O in callback
@callback(Output("status", "children"), Input("save-btn", "n_clicks"))
def save_data(n_clicks):
    with open("data.json", "w") as f:  # ❌ File I/O in callback
        json.dump(data, f)
```

### Refactoring Steps

1. **Extract Business Logic**:
   ```python
   # Move from callback to data/processing.py
   def calculate_velocity(statistics: List[Dict]) -> float:
       """Calculate average velocity from statistics."""
       return sum(s["points"] for s in statistics) / len(statistics)
   ```

2. **Use Design Tokens**:
   ```python
   # Replace hardcoded colors
   from ui.style_constants import DESIGN_TOKENS
   
   def create_card():
       return dbc.Card(style={
           "background-color": DESIGN_TOKENS["colors"]["primary"]
       })
   ```

3. **Delegate Persistence**:
   ```python
   # Move file I/O to data/persistence.py
   @callback(Output("status", "children"), Input("save-btn", "n_clicks"))
   def save_data(n_clicks):
       from data.persistence import save_project_data
       save_project_data(data)  # Delegate to data layer
   ```

---

## Conclusion

This architecture establishes clear boundaries between presentation, event handling, and business logic. Following these guidelines ensures:

- **Maintainability**: Changes isolated to specific layers
- **Testability**: Pure functions easy to unit test
- **Scalability**: Clear structure for adding features
- **Consistency**: Standardized patterns across codebase

For questions or clarifications, refer to:
- `data/state_management.py` - State management patterns
- `ui/style_constants.py` - Design token definitions
- `callbacks/__init__.py` - Callback registration
- This document - Architecture standards
