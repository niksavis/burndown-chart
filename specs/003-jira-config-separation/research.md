# Research & Design Decisions: JIRA Configuration Separation

**Feature**: 003-jira-config-separation  
**Date**: October 21, 2025  
**Status**: Complete

---

## Overview

This document captures research findings and design decisions for separating JIRA API configuration from the JQL query interface. The goal is to simplify the user workflow by creating a dedicated configuration interface for one-time JIRA setup.

---

## Research Tasks

### 1. Modal vs. Separate Page for Configuration

**Decision**: Use Bootstrap Modal Dialog (dbc.Modal)

**Rationale**:
- **User Context**: Configuration is infrequent (once during initial setup, occasionally for updates). Modal keeps users in context without navigation.
- **Existing Patterns**: Application already uses modals for help system (`.ui.help_system`), establishing consistent UX pattern.
- **Mobile Compatibility**: Bootstrap modals are responsive and work well on mobile devices with proper touch targets.
- **Implementation Simplicity**: Dash Bootstrap Components (dbc.Modal) is already in tech stack, no new dependencies.

**Alternatives Considered**:
- **Separate Page/Tab**: Rejected because it requires navigation away from the Data Source interface, breaking user flow. Configuration is not frequent enough to warrant dedicated tab.
- **Collapsible Panel**: Rejected because it still clutters the Data Source interface and doesn't provide clear visual separation.

---

### 2. Configuration Data Storage Strategy

**Decision**: Extend existing `app_settings.json` with new JIRA configuration fields

**Rationale**:
- **Consistency**: Application already uses `app_settings.json` for app-level configuration (PERT factor, deadline, toggles).
- **Backward Compatibility**: Existing `jira_token` field is already in `app_settings.json` - extending this structure is natural.
- **Simple Migration**: Existing settings can be preserved, new fields added incrementally.
- **No Database Overhead**: JSON file storage is sufficient for single-user desktop application.

**Data Structure**:
```json
{
  "jira_config": {
    "base_url": "https://mycompany.atlassian.net",
    "api_version": "v3",
    "token": "encrypted_or_masked_value",
    "cache_size_mb": 100,
    "max_results_per_call": 100,
    "points_field": "customfield_10016",
    "configured": true,
    "last_test_timestamp": "2025-10-21T12:00:00Z",
    "last_test_success": true
  },
  "pert_factor": 3,
  "deadline": "2025-12-31",
  ...
}
```

**Alternatives Considered**:
- **Separate `jira_config.json` file**: Rejected because it fragments configuration across multiple files, increasing complexity.
- **Environment variables only**: Rejected because it requires technical knowledge (editing .env files) and doesn't support GUI configuration.
- **Encrypted database**: Rejected as overkill for single-user application with no multi-user requirements.

---

### 3. API Endpoint Construction Logic

**Decision**: Server-side endpoint construction in `data.jira_simple.py`

**Rationale**:
- **Single Source of Truth**: Endpoint construction logic centralized in one module.
- **Validation at Source**: URL validation happens where API calls are made, ensuring consistency.
- **Future-Proofing**: If JIRA introduces API v4, only one function needs updating.

**Implementation Pattern**:
```python
def construct_jira_endpoint(base_url: str, api_version: str = "v3") -> str:
    """
    Construct full JIRA API endpoint from base URL and version.
    
    Args:
        base_url: Base JIRA URL (e.g., "https://company.atlassian.net")
        api_version: API version ("v2" or "v3")
    
    Returns:
        Full endpoint URL (e.g., "https://company.atlassian.net/rest/api/3/search")
    """
    # Remove trailing slashes
    clean_url = base_url.rstrip('/')
    
    # Validate URL format
    if not clean_url.startswith(('http://', 'https://')):
        raise ValueError("URL must start with http:// or https://")
    
    # Construct endpoint
    api_path = "/rest/api/2/search" if api_version == "v2" else "/rest/api/3/search"
    return f"{clean_url}{api_path}"
```

**Alternatives Considered**:
- **Client-side (JavaScript) construction**: Rejected because it duplicates logic and complicates debugging.
- **User provides full endpoint**: Rejected per spec requirement - users should only provide base URL.

---

### 4. Connection Test Implementation

**Decision**: Synchronous connection test with JIRA serverInfo endpoint

**Rationale**:
- **Fast Feedback**: JIRA `/rest/api/2/serverInfo` endpoint is lightweight and doesn't require authentication, perfect for connectivity check.
- **Clear Success/Failure**: Returns server information on success, clear error messages on failure.
- **User Expectations**: Users expect immediate feedback (< 10 seconds) for connection tests, synchronous is acceptable.

**Implementation Approach**:
```python
def test_jira_connection(base_url: str, token: str, api_version: str = "v3") -> dict:
    """
    Test JIRA connection by hitting serverInfo endpoint.
    
    Returns:
        {
            "success": bool,
            "message": str,
            "server_info": dict (if successful),
            "error_details": str (if failed)
        }
    """
    try:
        endpoint = construct_jira_endpoint(base_url, api_version)
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{base_url}/rest/api/2/serverInfo",
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            return {
                "success": True,
                "message": "Connection successful",
                "server_info": response.json()
            }
        else:
            return {
                "success": False,
                "message": f"Connection failed: {response.status_code}",
                "error_details": response.text
            }
    except requests.exceptions.Timeout:
        return {"success": False, "message": "Connection timeout (>10s)"}
    except requests.exceptions.ConnectionError:
        return {"success": False, "message": "Cannot reach JIRA server"}
    except Exception as e:
        return {"success": False, "message": f"Unexpected error: {str(e)}"}
```

**Alternatives Considered**:
- **Async/Background testing**: Rejected as unnecessary complexity for 10-second operation.
- **Full JQL query test**: Rejected because it's slower and requires valid JQL, adding complexity.
- **Ping/health endpoint**: Rejected because JIRA doesn't have universal health endpoint; serverInfo is closest equivalent.

---

### 5. Migration Strategy for Existing Configurations

**Decision**: Automatic migration on first load with backward compatibility

**Rationale**:
- **Zero Data Loss**: Existing `jira_token` and other settings preserved during migration.
- **Seamless Upgrade**: Users don't need to reconfigure after upgrade.
- **Backward Compatibility**: Old code can still read settings until fully migrated.

**Migration Logic**:
```python
def migrate_jira_config_if_needed(app_settings: dict) -> dict:
    """
    Migrate legacy JIRA configuration to new structure.
    Preserves existing values, adds new fields with defaults.
    """
    if "jira_config" not in app_settings:
        # Migrate from legacy structure
        app_settings["jira_config"] = {
            "base_url": os.getenv("JIRA_URL", ""),  # From environment
            "api_version": "v3",  # Default to v3
            "token": app_settings.get("jira_token", ""),  # From legacy field
            "cache_size_mb": 100,  # Default
            "max_results_per_call": 100,  # Default
            "points_field": "customfield_10016",  # Common default
            "configured": bool(app_settings.get("jira_token")),
            "last_test_timestamp": None,
            "last_test_success": None
        }
        
        # Keep legacy field temporarily for backward compatibility
        # Can be removed in future version after transition period
    
    return app_settings
```

**Alternatives Considered**:
- **Breaking change (force reconfiguration)**: Rejected because it's user-hostile and unnecessary.
- **Manual migration script**: Rejected because automatic migration is simpler and less error-prone.

---

### 6. UI Component Library Patterns

**Decision**: Use Dash Bootstrap Components (dbc) consistent with existing codebase

**Rationale**:
- **Consistency**: Application uses `dbc.Input`, `dbc.Button`, `dbc.Modal` throughout - maintain same patterns.
- **Mobile-Responsive**: Bootstrap components are mobile-first by default.
- **Accessibility**: Bootstrap provides good baseline ARIA support out of the box.

**Component Structure**:
```python
def create_jira_config_modal():
    """Create JIRA configuration modal dialog."""
    return dbc.Modal([
        dbc.ModalHeader(dbc.ModalTitle("JIRA Configuration")),
        dbc.ModalBody([
            # Base URL input
            dbc.Label("JIRA Base URL", html_for="jira-base-url-input"),
            dbc.Input(
                id="jira-base-url-input",
                type="url",
                placeholder="https://mycompany.atlassian.net",
                className="mb-3"
            ),
            
            # API version selector
            dbc.Label("API Version", html_for="jira-api-version-select"),
            dbc.Select(
                id="jira-api-version-select",
                options=[
                    {"label": "API v3 (Recommended)", "value": "v3"},
                    {"label": "API v2 (Legacy)", "value": "v2"}
                ],
                value="v3",
                className="mb-3"
            ),
            
            # Token input (password field for security)
            dbc.Label("Personal Access Token", html_for="jira-token-input"),
            dbc.Input(
                id="jira-token-input",
                type="password",
                placeholder="Enter your JIRA token",
                className="mb-3"
            ),
            
            # Cache settings
            dbc.Label("Cache Size Limit (MB)", html_for="jira-cache-size-input"),
            dbc.Input(
                id="jira-cache-size-input",
                type="number",
                value=100,
                min=10,
                max=1000,
                className="mb-3"
            ),
            
            # Max results
            dbc.Label("Max Results Per API Call", html_for="jira-max-results-input"),
            dbc.Input(
                id="jira-max-results-input",
                type="number",
                value=100,
                min=10,
                max=500,
                className="mb-3"
            ),
            
            # Points field
            dbc.Label("Story Points Field", html_for="jira-points-field-input"),
            dbc.Input(
                id="jira-points-field-input",
                type="text",
                placeholder="customfield_10016",
                className="mb-3"
            ),
            
            # Test connection button
            dbc.Button(
                "Test Connection",
                id="jira-test-connection-button",
                color="info",
                className="me-2"
            ),
            
            # Connection status feedback
            html.Div(id="jira-connection-status", className="mt-2")
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="jira-config-cancel-button", color="secondary"),
            dbc.Button("Save Configuration", id="jira-config-save-button", color="primary")
        ])
    ], id="jira-config-modal", size="lg", is_open=False)
```

**Alternatives Considered**:
- **Custom React components**: Rejected because it adds complexity and breaks from Dash patterns.
- **Separate page with custom navigation**: Rejected per earlier decision - modal is better UX.

---

### 7. Form Validation Strategy

**Decision**: Client-side validation with HTML5 + server-side validation in callback

**Rationale**:
- **Fast Feedback**: HTML5 validation (required, type="url", min/max) provides instant feedback.
- **Security**: Server-side validation in Python callback ensures data integrity regardless of client tampering.
- **User Experience**: Progressive disclosure - show errors as user types, prevent invalid submissions.

**Validation Rules**:
- **Base URL**: Must start with http:// or https://, no trailing slash required (will be normalized)
- **API Version**: Must be "v2" or "v3"
- **Token**: Required, non-empty string
- **Cache Size**: Integer between 10-1000 MB
- **Max Results**: Integer between 10-500
- **Points Field**: Optional, alphanumeric with underscores (customfield_XXXXX pattern)

**Alternatives Considered**:
- **Client-side only**: Rejected due to security concerns.
- **Server-side only**: Rejected because it's slower and provides poor UX.

---

### 8. Error Handling & User Feedback

**Decision**: Contextual error messages with actionable guidance

**Rationale**:
- **User-Friendly**: Non-technical users need clear explanation of what went wrong and how to fix it.
- **Common Scenarios**: Handle the most common failure modes (typos in URL, expired token, network issues).

**Error Message Patterns**:
```python
ERROR_MESSAGES = {
    "invalid_url_format": {
        "title": "Invalid URL Format",
        "message": "Please enter a valid JIRA URL starting with https://",
        "example": "Example: https://mycompany.atlassian.net"
    },
    "connection_timeout": {
        "title": "Connection Timeout",
        "message": "Could not reach JIRA server within 10 seconds. Check your network connection or try again.",
        "action": "Verify the URL and check your internet connection."
    },
    "authentication_failed": {
        "title": "Authentication Failed",
        "message": "Invalid personal access token. Please verify your token is correct and has not expired.",
        "action": "Generate a new token in JIRA settings: Profile > Personal Access Tokens"
    },
    "server_unreachable": {
        "title": "Server Unreachable",
        "message": "Cannot connect to JIRA server. The URL may be incorrect or the server may be down.",
        "action": "Double-check the base URL and try again."
    }
}
```

**Alternatives Considered**:
- **Generic "Error occurred" messages**: Rejected because they're not actionable.
- **Technical error codes only**: Rejected because non-technical users won't understand them.

---

## Summary of Design Decisions

| Decision Area             | Choice                                | Key Rationale                                                              |
| ------------------------- | ------------------------------------- | -------------------------------------------------------------------------- |
| **UI Pattern**            | Bootstrap Modal                       | Maintains context, consistent with existing help modals, mobile-responsive |
| **Data Storage**          | Extend app_settings.json              | Consistent with existing patterns, simple migration                        |
| **Endpoint Construction** | Server-side in data.jira_simple.py    | Single source of truth, validation at API call point                       |
| **Connection Test**       | Synchronous serverInfo call           | Fast feedback, clear success/failure, user expectations                    |
| **Migration Strategy**    | Automatic with backward compatibility | Zero data loss, seamless upgrade                                           |
| **UI Components**         | Dash Bootstrap Components             | Consistency, mobile-first, good accessibility baseline                     |
| **Validation**            | HTML5 + server-side                   | Fast feedback + security                                                   |
| **Error Handling**        | Contextual messages with guidance     | User-friendly, actionable                                                  |

---

## Open Questions (None)

All design decisions have been made. Ready to proceed to Phase 1 (Data Model & Contracts).
