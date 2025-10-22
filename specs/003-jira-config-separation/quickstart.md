# Quickstart Guide: JIRA Configuration Separation

**Feature**: 003-jira-config-separation  
**Audience**: Developers implementing this feature  
**Estimated Time**: 4-6 hours

---

## Overview

This feature separates JIRA API configuration from the JQL query interface by creating a dedicated configuration modal. The implementation follows the existing Dash/Bootstrap component patterns and extends the JSON-based persistence layer.

---

## Prerequisites

- ✅ Python 3.11+ environment configured
- ✅ Virtual environment activated (`.\.venv\Scripts\activate`)
- ✅ Dependencies installed (`pip install -r requirements.txt`)
- ✅ Familiarity with Dash callbacks and Bootstrap components
- ✅ Understanding of existing `data/persistence.py` patterns

---

## Implementation Phases

### Phase 1: Data Layer (1-2 hours)

#### Step 1.1: Add Configuration Functions to `data/persistence.py`

```python
def load_jira_configuration() -> dict:
    """
    Load JIRA configuration from app_settings.json.
    Automatically migrates legacy configuration if needed.
    
    Returns:
        dict: JIRA configuration with all fields
    """
    app_settings = load_app_settings()
    
    # Migrate legacy configuration if needed
    if "jira_config" not in app_settings:
        app_settings = migrate_jira_config(app_settings)
        save_app_settings(app_settings)
    
    return app_settings.get("jira_config", get_default_jira_config())


def save_jira_configuration(config: dict) -> bool:
    """
    Save JIRA configuration to app_settings.json.
    
    Args:
        config: Configuration dict with base_url, token, etc.
    
    Returns:
        bool: True if save successful
    """
    app_settings = load_app_settings()
    app_settings["jira_config"] = config
    save_app_settings(app_settings)
    return True


def validate_jira_config(config: dict) -> tuple[bool, str]:
    """
    Validate JIRA configuration fields.
    
    Returns:
        (is_valid, error_message)
    """
    # Implement validation rules from data-model.md
    # ... (see data-model.md for complete validation logic)


def migrate_jira_config(app_settings: dict) -> dict:
    """Migrate legacy JIRA settings to new structure."""
    # ... (see research.md for migration logic)
```

**Test**: Unit tests in `tests/unit/data/test_persistence.py`

---

#### Step 1.2: Add Connection Test to `data/jira_simple.py`

```python
def test_jira_connection(base_url: str, token: str, api_version: str = "v3") -> dict:
    """
    Test JIRA connection by calling serverInfo endpoint.
    
    Args:
        base_url: Base JIRA URL (e.g., "https://company.atlassian.net")
        token: Personal access token
        api_version: API version ("v2" or "v3")
    
    Returns:
        dict: {
            "success": bool,
            "message": str,
            "server_info": dict (if successful),
            "error_code": str (if failed),
            "error_details": str (if failed),
            "response_time_ms": int
        }
    """
    # Implement connection test logic from research.md
    # ... (see research.md for complete implementation)


def construct_jira_endpoint(base_url: str, api_version: str = "v3") -> str:
    """Construct full JIRA API endpoint from base URL and version."""
    clean_url = base_url.rstrip('/')
    
    if not clean_url.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")
    
    api_path = "/rest/api/2/search" if api_version == "v2" else "/rest/api/3/search"
    return f"{clean_url}{api_path}"
```

**Test**: Unit tests in `tests/unit/data/test_jira_simple.py`

---

### Phase 2: UI Components (1-2 hours)

#### Step 2.1: Create `ui/jira_config_modal.py`

```python
"""
JIRA Configuration Modal Component

Provides a Bootstrap modal dialog for JIRA API configuration.
"""

import dash_bootstrap_components as dbc
from dash import html, dcc


def create_jira_config_modal():
    """
    Create JIRA configuration modal dialog.
    
    Returns:
        dbc.Modal: Complete modal component with form fields
    """
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("JIRA Configuration")),
        dbc.ModalBody([
            # Form fields implementation from research.md
            # ... (see research.md Section 6 for complete component)
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="jira-config-cancel-button", color="secondary"),
            dbc.Button("Test Connection", id="jira-test-connection-button", color="info", className="me-2"),
            dbc.Button("Save Configuration", id="jira-config-save-button", color="primary")
        ])
    ], id="jira-config-modal", size="lg", is_open=False)


def create_jira_config_button():
    """
    Create button to open JIRA configuration modal.
    
    Returns:
        dbc.Button: Configuration button for Data Source interface
    """
    return dbc.Button(
        [html.I(className="fas fa-cog me-2"), "Configure JIRA"],
        id="jira-config-button",
        color="secondary",
        outline=True,
        className="mb-3"
    )
```

**Test**: Unit tests in `tests/unit/ui/test_jira_config_modal.py`

---

#### Step 2.2: Modify `ui/cards.py`

**Remove** these fields from Data Source interface:
- JIRA URL input
- JIRA token input  
- Cache size input
- Max results input
- Points field input

**Add** configuration button:

```python
# In create_data_source_card() function
# Replace JIRA configuration fields with:
create_jira_config_button(),
```

**Add** modal component to layout:

```python
# In create_data_source_card() or layout.py
from ui.jira_config_modal import create_jira_config_modal

# Add to component tree
create_jira_config_modal(),
```

---

### Phase 3: Callbacks (1-2 hours)

#### Step 3.1: Create `callbacks/jira_config.py`

```python
"""
JIRA Configuration Callbacks

Handles all callback logic for JIRA configuration modal.
"""

from dash import callback, Output, Input, State, html
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc

from data.persistence import (
    load_jira_configuration,
    save_jira_configuration,
    validate_jira_config
)
from data.jira_simple import test_jira_connection


@callback(
    Output("jira-config-modal", "is_open"),
    Input("jira-config-button", "n_clicks"),
    prevent_initial_call=True
)
def open_jira_config_modal(n_clicks):
    """Open JIRA configuration modal."""
    # Implementation from contracts/dash-callbacks.md


@callback(
    [
        Output("jira-base-url-input", "value"),
        Output("jira-api-version-select", "value"),
        # ... other form fields
    ],
    Input("jira-config-modal", "is_open")
)
def load_jira_config(is_open):
    """Load and display existing JIRA configuration."""
    # Implementation from contracts/dash-callbacks.md


@callback(
    Output("jira-connection-status", "children"),
    Input("jira-test-connection-button", "n_clicks"),
    [
        State("jira-base-url-input", "value"),
        State("jira-token-input", "value"),
        # ... other states
    ],
    prevent_initial_call=True
)
def test_connection(n_clicks, base_url, token, api_version):
    """Test JIRA connection and display result."""
    # Implementation from contracts/dash-callbacks.md


@callback(
    [
        Output("jira-config-modal", "is_open", allow_duplicate=True),
        Output("jira-save-status", "children")
    ],
    Input("jira-config-save-button", "n_clicks"),
    [State(...) for all form fields],
    prevent_initial_call=True
)
def save_configuration(n_clicks, base_url, token, ...):
    """Validate and save JIRA configuration."""
    # Implementation from contracts/dash-callbacks.md


@callback(
    Output("jira-config-modal", "is_open", allow_duplicate=True),
    Input("jira-config-cancel-button", "n_clicks"),
    prevent_initial_call=True
)
def cancel_configuration(n_clicks):
    """Close configuration modal without saving."""
    # Implementation from contracts/dash-callbacks.md
```

---

#### Step 3.2: Register Callbacks in `callbacks/__init__.py`

```python
def register_all_callbacks(app):
    """Register all application callbacks."""
    # ... existing imports ...
    from callbacks import jira_config  # New import
    
    # Callbacks are registered via @callback decorator
    # No additional registration needed
```

---

#### Step 3.3: Update Existing Callbacks in `callbacks/settings.py`

**Modify** callbacks that read JIRA settings to use new configuration structure:

```python
# Old: Direct reads from app_settings
jira_token = app_settings.get("jira_token", "")

# New: Read from jira_config structure
jira_config = app_settings.get("jira_config", {})
jira_token = jira_config.get("token", "")
```

---

### Phase 4: Integration & Testing (1 hour)

#### Step 4.1: Manual Testing Checklist

- [ ] Open app, click "Configure JIRA" button
- [ ] Modal opens with empty form (new user) or pre-filled (existing config)
- [ ] Enter invalid URL → validation error shown
- [ ] Enter valid URL + token, click "Test Connection" → success/failure feedback
- [ ] Click "Save" without testing → configuration saved
- [ ] Close and reopen modal → settings persist
- [ ] Modify token, click "Save" → existing JQL queries unaffected
- [ ] Navigate to Data Source → JIRA config fields removed
- [ ] Test on mobile viewport (375px width) → modal responsive

---

#### Step 4.2: Unit Tests

```powershell
# Run unit tests for new modules
.\.venv\Scripts\activate; pytest tests/unit/data/test_persistence.py -v
.\.venv\Scripts\activate; pytest tests/unit/data/test_jira_simple.py -v
.\.venv\Scripts\activate; pytest tests/unit/ui/test_jira_config_modal.py -v
```

---

#### Step 4.3: Integration Tests (Optional - Final Validation)

Create Playwright test in `tests/integration/test_jira_configuration.py`:

```python
def test_jira_configuration_workflow(dash_duo):
    """Test complete JIRA configuration workflow."""
    app = import_app("app")
    dash_duo.start_server(app)
    
    # Click configuration button
    dash_duo.find_element("#jira-config-button").click()
    
    # Verify modal opens
    modal = dash_duo.find_element("#jira-config-modal")
    assert modal.is_displayed()
    
    # Fill form fields
    dash_duo.find_element("#jira-base-url-input").send_keys("https://test.atlassian.net")
    dash_duo.find_element("#jira-token-input").send_keys("test-token")
    
    # Test connection (with mocked API)
    dash_duo.find_element("#jira-test-connection-button").click()
    
    # Save configuration
    dash_duo.find_element("#jira-config-save-button").click()
    
    # Verify modal closes
    assert not modal.is_displayed()
```

---

## File Changes Summary

### New Files (3)
1. `ui/jira_config_modal.py` - Configuration modal component
2. `callbacks/jira_config.py` - Configuration callbacks
3. `tests/unit/ui/test_jira_config_modal.py` - Component tests

### Modified Files (3)
1. `ui/cards.py` - Remove JIRA fields, add config button
2. `data/persistence.py` - Add configuration functions
3. `data/jira_simple.py` - Add connection test function

### Modified Files (Optional)
4. `callbacks/settings.py` - Update JIRA config reads
5. `tests/integration/test_jira_configuration.py` - Integration tests

---

## Common Pitfalls & Solutions

| Problem                   | Solution                                                             |
| ------------------------- | -------------------------------------------------------------------- |
| Modal doesn't open        | Check `n_clicks` is not None in callback                             |
| Form fields empty on load | Ensure `load_jira_config` callback returns values in correct order   |
| Connection test times out | Verify timeout parameter (10s) in requests.get()                     |
| Save doesn't persist      | Check file permissions on app_settings.json                          |
| Validation errors unclear | Use specific error messages from data-model.md                       |
| Mobile modal too wide     | Ensure modal size="lg" and Bootstrap CSS loaded                      |
| Callbacks conflict        | Use `allow_duplicate=True` for outputs updated by multiple callbacks |

---

## Performance Checklist

- [ ] Configuration load < 200ms (JSON file read)
- [ ] Modal open/close < 100ms (instant feedback)
- [ ] Connection test < 10s (with timeout)
- [ ] Configuration save < 500ms (JSON file write)
- [ ] No blocking operations in callbacks

---

## Accessibility Checklist

- [ ] All inputs have `<label>` elements with `html_for` attribute
- [ ] Modal can be closed with Escape key
- [ ] Tab order is logical (URL → Version → Token → Cache → Max Results → Points)
- [ ] Focus management: modal receives focus on open
- [ ] Error messages associated with inputs via ARIA
- [ ] "Test Connection" button has clear loading state

---

## Deployment Checklist

- [ ] All unit tests passing
- [ ] Manual testing completed on desktop
- [ ] Manual testing completed on mobile (375px)
- [ ] Migration tested with existing configurations
- [ ] No console errors in browser
- [ ] No Python exceptions in terminal
- [ ] Git commit with clear message
- [ ] Branch ready for merge to main

---

## Next Steps After Implementation

1. Run `/speckit.tasks` to generate detailed task breakdown
2. Implement tasks in priority order (P1 → P2 → P3)
3. Write tests during implementation (per constitutional amendment)
4. Add Playwright integration tests as final validation
5. Merge to main when all tests pass

---

## Reference Documents

- [spec.md](./spec.md) - Feature specification
- [research.md](./research.md) - Design decisions
- [data-model.md](./data-model.md) - Entity definitions
- [contracts/dash-callbacks.md](./contracts/dash-callbacks.md) - Callback contracts

---

**Estimated Total Time**: 4-6 hours  
**Complexity**: Medium (familiar patterns, clear requirements)  
**Risk Level**: Low (no breaking changes, graceful migration)
