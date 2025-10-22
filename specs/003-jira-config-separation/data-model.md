# Data Model: JIRA Configuration Separation

**Feature**: 003-jira-config-separation  
**Date**: October 21, 2025  
**Source**: Extracted from spec.md functional requirements

---

## Entity: JIRA Configuration

**Purpose**: Represents the complete JIRA connection setup that enables API communication.

### Attributes

| Attribute              | Type             | Required | Default             | Validation                                             | Description                                                    |
| ---------------------- | ---------------- | -------- | ------------------- | ------------------------------------------------------ | -------------------------------------------------------------- |
| `base_url`             | string           | Yes      | ""                  | Must start with http:// or https://, no trailing slash | Base JIRA instance URL (e.g., "https://company.atlassian.net") |
| `api_version`          | enum("v2", "v3") | Yes      | "v3"                | Must be "v2" or "v3"                                   | JIRA REST API version to use                                   |
| `token`                | string           | Yes      | ""                  | Non-empty string                                       | Personal access token for authentication                       |
| `cache_size_mb`        | integer          | Yes      | 100                 | Range: 10-1000                                         | Maximum cache size in megabytes                                |
| `max_results_per_call` | integer          | Yes      | 100                 | Range: 10-500                                          | Maximum number of issues returned per API call                 |
| `points_field`         | string           | No       | "customfield_10016" | Pattern: customfield_\d+                               | JIRA custom field name for story points                        |
| `configured`           | boolean          | Yes      | false               | true/false                                             | Whether initial configuration is complete                      |
| `last_test_timestamp`  | datetime         | No       | null                | ISO 8601 format                                        | When connection was last tested                                |
| `last_test_success`    | boolean          | No       | null                | true/false/null                                        | Result of last connection test                                 |

### State Transitions

```
[Not Configured] 
    ↓ (User fills form + saves)
[Configured - Untested]
    ↓ (User clicks "Test Connection")
[Configured - Testing]
    ↓ (Success)
[Configured - Verified] ← stable state
    ↓ (Failure)
[Configured - Invalid]
    ↓ (User updates settings)
[Configured - Untested]
```

### Business Rules

1. **Configuration is required** before JQL queries can be executed
2. **Token is sensitive data** and should be masked in UI (password field)
3. **Base URL must be normalized**: Remove trailing slashes, validate protocol
4. **API version determines endpoint**: v2 → `/rest/api/2/search`, v3 → `/rest/api/3/search`
5. **Cache size impacts disk usage**: Warn if set above 500MB
6. **Max results affects query performance**: Higher values = fewer API calls but slower responses
7. **Points field is optional**: Not all JIRA instances use story points

### Relationships

- **Has Many**: JQL Query Profiles (existing entity, not modified in this feature)
- **Independent of**: Statistics, Project Scope, Forecast Settings

---

## Entity: Connection Test Result

**Purpose**: Represents the outcome of a JIRA connection validation attempt.

### Attributes

| Attribute          | Type     | Required | Description                             |
| ------------------ | -------- | -------- | --------------------------------------- |
| `success`          | boolean  | Yes      | Whether connection test succeeded       |
| `message`          | string   | Yes      | User-friendly status message            |
| `timestamp`        | datetime | Yes      | When test was performed (ISO 8601)      |
| `response_time_ms` | integer  | No       | API response time in milliseconds       |
| `server_info`      | object   | No       | JIRA server information (if successful) |
| `error_code`       | string   | No       | Error category (if failed)              |
| `error_details`    | string   | No       | Technical error details (if failed)     |

### Example Successful Result

```json
{
  "success": true,
  "message": "Connection successful",
  "timestamp": "2025-10-21T12:30:45Z",
  "response_time_ms": 234,
  "server_info": {
    "version": "9.4.0",
    "serverTitle": "My Company JIRA",
    "baseUrl": "https://mycompany.atlassian.net"
  }
}
```

### Example Failed Result

```json
{
  "success": false,
  "message": "Authentication failed - invalid token",
  "timestamp": "2025-10-21T12:30:45Z",
  "response_time_ms": null,
  "error_code": "authentication_failed",
  "error_details": "401 Unauthorized: Invalid or expired token"
}
```

### Error Categories

| Error Code                | User Message                                           | Typical Cause                                        |
| ------------------------- | ------------------------------------------------------ | ---------------------------------------------------- |
| `invalid_url_format`      | "Please enter a valid JIRA URL starting with https://" | Malformed URL, missing protocol                      |
| `connection_timeout`      | "Connection timeout - check network and try again"     | Network issues, firewall, VPN                        |
| `authentication_failed`   | "Invalid token - please verify in JIRA settings"       | Wrong token, expired token, insufficient permissions |
| `server_unreachable`      | "Cannot reach JIRA server - verify URL"                | Wrong URL, server down, DNS issues                   |
| `api_version_unsupported` | "Selected API version not supported by this server"    | Old JIRA instance without v3 API                     |
| `unexpected_error`        | "Unexpected error - see details below"                 | Catch-all for unknown failures                       |

---

## Entity: JQL Query Profile (Existing - Reference Only)

**Purpose**: Saved JQL queries with metadata. This entity exists and should remain independent of JIRA configuration changes.

### Key Constraint

**FR-017 Requirement**: JQL Query Profiles must survive configuration changes without data loss.

**Implementation Note**: JQL queries reference JIRA configuration but don't embed it. When configuration changes (e.g., API version, endpoint), queries should continue working without modification.

---

## Data Persistence Schema

### app_settings.json Structure

```json
{
  "jira_config": {
    "base_url": "https://mycompany.atlassian.net",
    "api_version": "v3",
    "token": "xxxxxxxxxxxxxxxxxxxxxx",
    "cache_size_mb": 100,
    "max_results_per_call": 100,
    "points_field": "customfield_10016",
    "configured": true,
    "last_test_timestamp": "2025-10-21T12:30:45Z",
    "last_test_success": true
  },
  "pert_factor": 3,
  "deadline": "2025-12-31",
  "show_items_forecast": true,
  "show_points_forecast": true
}
```

### Migration from Legacy Structure

**Legacy fields** (will be preserved temporarily):
- `jira_token` (string) → migrated to `jira_config.token`
- Environment variable `JIRA_URL` → migrated to `jira_config.base_url`

**Migration function** will run automatically on first load, preserving all existing data.

---

## Validation Rules by Entity

### JIRA Configuration Validation

```python
def validate_jira_config(config: dict) -> tuple[bool, str]:
    """
    Validate JIRA configuration object.
    
    Returns:
        (is_valid, error_message)
    """
    # Base URL validation
    if not config.get("base_url"):
        return (False, "Base URL is required")
    
    if not config["base_url"].startswith(("http://", "https://")):
        return (False, "Base URL must start with http:// or https://")
    
    # API version validation
    if config.get("api_version") not in ["v2", "v3"]:
        return (False, "API version must be 'v2' or 'v3'")
    
    # Token validation
    if not config.get("token"):
        return (False, "Personal access token is required")
    
    # Cache size validation
    cache_size = config.get("cache_size_mb", 100)
    if not (10 <= cache_size <= 1000):
        return (False, "Cache size must be between 10 and 1000 MB")
    
    # Max results validation
    max_results = config.get("max_results_per_call", 100)
    if not (10 <= max_results <= 500):
        return (False, "Max results must be between 10 and 500")
    
    # Points field validation (optional)
    points_field = config.get("points_field", "")
    if points_field and not points_field.startswith("customfield_"):
        return (False, "Points field must start with 'customfield_' (e.g., customfield_10016)")
    
    return (True, "")
```

---

## Summary

**Entities Defined**: 2 new (JIRA Configuration, Connection Test Result), 1 referenced (JQL Query Profile)  
**Storage**: JSON file persistence (app_settings.json)  
**Validation**: Comprehensive rules for all configuration fields  
**Migration**: Automatic from legacy structure with zero data loss

Ready to proceed to API contracts definition.
