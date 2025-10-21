# Dash Callback Contracts: JIRA Configuration

**Feature**: 003-jira-config-separation  
**Date**: October 21, 2025  
**Framework**: Dash 3.1.1 (Python callbacks, not REST API)

---

## Overview

This document defines the Dash callback contracts for JIRA configuration management. Dash uses server-side Python callbacks triggered by component interactions, not traditional REST APIs.

---

## Callback 1: Open Configuration Modal

**Purpose**: Display JIRA configuration modal when user clicks configuration button.

### Trigger (Input)
```python
Input("jira-config-button", "n_clicks")
```

### Updates (Output)
```python
Output("jira-config-modal", "is_open")
```

### Behavior
- **When**: User clicks "Configure JIRA" button from Data Source interface
- **Then**: Modal dialog opens with current configuration pre-filled (if exists)

### Implementation
```python
@app.callback(
    Output("jira-config-modal", "is_open"),
    Input("jira-config-button", "n_clicks"),
    prevent_initial_call=True
)
def open_jira_config_modal(n_clicks):
    """Open JIRA configuration modal."""
    if n_clicks:
        return True
    return dash.no_update
```

---

## Callback 2: Load Existing Configuration

**Purpose**: Pre-fill configuration form with saved settings when modal opens.

### Trigger (Input)
```python
Input("jira-config-modal", "is_open")
```

### Updates (Outputs)
```python
Output("jira-base-url-input", "value"),
Output("jira-api-version-select", "value"),
Output("jira-token-input", "value"),
Output("jira-cache-size-input", "value"),
Output("jira-max-results-input", "value"),
Output("jira-points-field-input", "value")
```

### Behavior
- **When**: Modal opens (is_open=True)
- **Then**: Load configuration from `app_settings.json` and populate form fields

### Implementation
```python
@app.callback(
    [
        Output("jira-base-url-input", "value"),
        Output("jira-api-version-select", "value"),
        Output("jira-token-input", "value"),
        Output("jira-cache-size-input", "value"),
        Output("jira-max-results-input", "value"),
        Output("jira-points-field-input", "value")
    ],
    Input("jira-config-modal", "is_open")
)
def load_jira_config(is_open):
    """Load and display existing JIRA configuration."""
    if not is_open:
        raise PreventUpdate
    
    config = load_jira_configuration()  # From data.persistence
    
    return (
        config.get("base_url", ""),
        config.get("api_version", "v3"),
        config.get("token", ""),
        config.get("cache_size_mb", 100),
        config.get("max_results_per_call", 100),
        config.get("points_field", "customfield_10016")
    )
```

---

## Callback 3: Test JIRA Connection

**Purpose**: Validate JIRA connection settings before saving.

### Trigger (Input)
```python
Input("jira-test-connection-button", "n_clicks")
```

### State (Current Values)
```python
State("jira-base-url-input", "value"),
State("jira-api-version-select", "value"),
State("jira-token-input", "value")
```

### Updates (Output)
```python
Output("jira-connection-status", "children")
```

### Behavior
- **When**: User clicks "Test Connection" button
- **Then**: Validate URL, construct endpoint, call JIRA serverInfo API
- **Result**: Display success message with server info OR error message with guidance

### Request Flow
```
User clicks "Test Connection"
    ↓
Callback reads form values (State)
    ↓
Validate base URL format
    ↓
Construct endpoint: base_url + /rest/api/2/serverInfo
    ↓
Make HTTP request with token
    ↓
Parse response (10s timeout)
    ↓
Display result feedback
```

### Success Response
```python
dbc.Alert(
    [
        html.Strong("✓ Connection Successful"),
        html.P(f"Server: {server_info['serverTitle']}"),
        html.P(f"Version: {server_info['version']}"),
        html.P(f"Response time: {response_time}ms")
    ],
    color="success"
)
```

### Error Response
```python
dbc.Alert(
    [
        html.Strong("✗ Connection Failed"),
        html.P(error_message),
        html.Small(error_details, className="text-muted")
    ],
    color="danger"
)
```

### Implementation
```python
@app.callback(
    Output("jira-connection-status", "children"),
    Input("jira-test-connection-button", "n_clicks"),
    [
        State("jira-base-url-input", "value"),
        State("jira-api-version-select", "value"),
        State("jira-token-input", "value")
    ],
    prevent_initial_call=True
)
def test_jira_connection(n_clicks, base_url, api_version, token):
    """Test JIRA connection and display result."""
    if not n_clicks:
        raise PreventUpdate
    
    # Validate inputs
    if not base_url or not token:
        return dbc.Alert("Please fill in Base URL and Token", color="warning")
    
    # Call test function from data.jira_simple
    result = test_jira_connection_api(base_url, token, api_version)
    
    if result["success"]:
        return create_success_feedback(result)
    else:
        return create_error_feedback(result)
```

---

## Callback 4: Save Configuration

**Purpose**: Persist JIRA configuration to app_settings.json.

### Trigger (Input)
```python
Input("jira-config-save-button", "n_clicks")
```

### State (Form Values)
```python
State("jira-base-url-input", "value"),
State("jira-api-version-select", "value"),
State("jira-token-input", "value"),
State("jira-cache-size-input", "value"),
State("jira-max-results-input", "value"),
State("jira-points-field-input", "value")
```

### Updates (Outputs)
```python
Output("jira-config-modal", "is_open"),  # Close modal on success
Output("jira-save-status", "children")   # Success/error message
```

### Behavior
- **When**: User clicks "Save Configuration"
- **Then**: Validate all fields, save to app_settings.json, close modal

### Validation Flow
```
User clicks "Save"
    ↓
Validate all fields (client-side + server-side)
    ↓
If invalid: Show error, keep modal open
    ↓
If valid: Save to app_settings.json
    ↓
Update "configured" flag to true
    ↓
Close modal, show success toast
```

### Implementation
```python
@app.callback(
    [
        Output("jira-config-modal", "is_open", allow_duplicate=True),
        Output("jira-save-status", "children")
    ],
    Input("jira-config-save-button", "n_clicks"),
    [
        State("jira-base-url-input", "value"),
        State("jira-api-version-select", "value"),
        State("jira-token-input", "value"),
        State("jira-cache-size-input", "value"),
        State("jira-max-results-input", "value"),
        State("jira-points-field-input", "value")
    ],
    prevent_initial_call=True
)
def save_jira_configuration(n_clicks, base_url, api_version, token, 
                           cache_size, max_results, points_field):
    """Validate and save JIRA configuration."""
    if not n_clicks:
        raise PreventUpdate
    
    # Build configuration object
    config = {
        "base_url": base_url.strip(),
        "api_version": api_version,
        "token": token.strip(),
        "cache_size_mb": int(cache_size),
        "max_results_per_call": int(max_results),
        "points_field": points_field.strip(),
        "configured": True
    }
    
    # Validate
    is_valid, error_msg = validate_jira_config(config)
    if not is_valid:
        return (dash.no_update, dbc.Alert(error_msg, color="danger"))
    
    # Save to app_settings.json
    save_jira_configuration_to_file(config)
    
    # Close modal and show success
    return (False, dbc.Alert("Configuration saved successfully!", color="success"))
```

---

## Callback 5: Cancel Configuration

**Purpose**: Close modal without saving changes.

### Trigger (Input)
```python
Input("jira-config-cancel-button", "n_clicks")
```

### Updates (Output)
```python
Output("jira-config-modal", "is_open")
```

### Behavior
- **When**: User clicks "Cancel"
- **Then**: Close modal, discard unsaved changes

### Implementation
```python
@app.callback(
    Output("jira-config-modal", "is_open", allow_duplicate=True),
    Input("jira-config-cancel-button", "n_clicks"),
    prevent_initial_call=True
)
def cancel_jira_config(n_clicks):
    """Close configuration modal without saving."""
    if n_clicks:
        return False
    return dash.no_update
```

---

## Callback 6: Check Configuration Status (Gatekeeper)

**Purpose**: Redirect unconfigured users to configuration modal before allowing JQL queries.

### Trigger (Input)
```python
Input("url", "pathname")  # Page load/navigation
```

### Updates (Output)
```python
Output("jira-config-required-modal", "is_open")
```

### Behavior
- **When**: User navigates to Data Source page
- **Then**: Check if JIRA is configured
- **If not configured**: Show modal prompting configuration
- **If configured**: Allow normal operation

### Implementation
```python
@app.callback(
    Output("jira-config-required-modal", "is_open"),
    Input("url", "pathname")
)
def check_jira_configuration_status(pathname):
    """Check if JIRA configuration exists, prompt if not."""
    if pathname == "/data-source":  # Or however Data Source page is identified
        config = load_jira_configuration()
        if not config.get("configured"):
            return True  # Show "configuration required" modal
    return False
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    User Interface                            │
│  [Configure JIRA Button] → [Modal Dialog]                   │
│       ↓                         ↓                            │
│   Open Modal              Fill Form Fields                   │
│       ↓                         ↓                            │
│   Load Config            [Test Connection]                   │
│       ↓                         ↓                            │
│  Display Values          Validate & Test                     │
│                                 ↓                            │
│                          Show Result                         │
│                                 ↓                            │
│                          [Save] or [Cancel]                  │
│                                 ↓                            │
│                          Save to JSON File                   │
│                                 ↓                            │
│                          Close Modal                         │
└─────────────────────────────────────────────────────────────┘
         ↓                                      ↓
┌────────────────────┐              ┌──────────────────────┐
│  app_settings.json │              │  JIRA API            │
│  (Local Storage)   │              │  (Remote Service)    │
└────────────────────┘              └──────────────────────┘
```

---

## Error Handling Contract

All callbacks must handle these error scenarios:

| Error Scenario         | Callback Behavior                   | User Feedback                          |
| ---------------------- | ----------------------------------- | -------------------------------------- |
| Empty required field   | Prevent save, show validation error | "Base URL is required"                 |
| Invalid URL format     | Prevent save, show format error     | "URL must start with https://"         |
| Connection timeout     | Allow retry, log error              | "Connection timeout - try again"       |
| Authentication failure | Allow retry, suggest token check    | "Invalid token - check JIRA settings"  |
| File write failure     | Show error, keep data in memory     | "Could not save configuration - retry" |
| Unexpected exception   | Log error, show generic message     | "Unexpected error - see logs"          |

---

## Performance Requirements

| Callback        | Target Response Time | Notes                        |
| --------------- | -------------------- | ---------------------------- |
| Open Modal      | < 100ms              | Instant feedback             |
| Load Config     | < 200ms              | Read from local file         |
| Test Connection | < 10s                | Network request with timeout |
| Save Config     | < 500ms              | Write to local file          |
| Cancel          | < 100ms              | Instant close                |
| Status Check    | < 100ms              | Read from local file         |

---

## Summary

**Total Callbacks**: 6  
**Primary Callback**: Save Configuration (most complex validation)  
**External API Call**: Test Connection (only callback making network request)  
**Data Persistence**: JSON file operations (no database)

Ready to proceed to quickstart guide.
