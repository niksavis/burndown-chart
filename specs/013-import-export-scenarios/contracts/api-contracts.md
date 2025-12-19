# API Contracts: Enhanced Import/Export Options

**Feature**: 013-import-export-scenarios  
**Date**: December 19, 2025

This document defines the function signatures, callback contracts, and UI component interfaces for the import/export feature.

---

## Data Layer API (data/import_export.py)

### 1. strip_credentials

**Purpose**: Remove sensitive authentication fields from profile data

**Signature**:
```python
def strip_credentials(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive fields from profile configuration.
    
    Creates a deep copy of the profile and removes all credential fields.
    Does NOT mutate the input dictionary.
    
    Args:
        profile: Profile configuration dictionary from profile.json
        
    Returns:
        Deep copy of profile with credentials removed
        
    Raises:
        ValueError: If credential patterns detected in output (validation failure)
        
    Example:
        >>> profile = {"jira_token": "secret", "jira_url": "https://example.com"}
        >>> safe = strip_credentials(profile)
        >>> "jira_token" in safe
        False
        >>> "jira_url" in safe
        True
    """
```

**Contract**:
- MUST NOT mutate input dictionary
- MUST remove: `jira_token`, `jira_api_key`, `api_secret`
- MUST validate absence of credential patterns in output
- MUST return deep copy (changes to output don't affect input)

---

### 2. export_profile_with_mode

**Purpose**: Export profile data with selected mode and token option

**Signature**:
```python
def export_profile_with_mode(
    profile_id: str,
    query_id: str,
    export_mode: str,
    include_token: bool = False
) -> Dict[str, Any]:
    """Export profile with mode-specific data inclusion.
    
    Args:
        profile_id: Profile identifier (e.g., "default")
        query_id: Active query identifier (e.g., "sprint-123")
        export_mode: One of "CONFIG_ONLY", "FULL_DATA"
        include_token: Whether to include JIRA token (default: False)
        
    Returns:
        Export package dictionary with structure:
        {
            "manifest": ExportManifest,
            "profile_data": dict,
            "query_data": dict or None  # None if CONFIG_ONLY
        }
        
    Raises:
        ValueError: If profile_id or query_id not found
        ValueError: If export_mode invalid
        FileNotFoundError: If profile/query files missing
        
    Example:
        >>> package = export_profile_with_mode(
        ...     "default", "sprint-123", "CONFIG_ONLY", False
        ... )
        >>> package["manifest"]["export_mode"]
        'CONFIG_ONLY'
        >>> "query_data" in package
        False
    """
```

**Contract**:
- MUST validate profile_id and query_id exist
- MUST validate export_mode in ["CONFIG_ONLY", "FULL_DATA"]
- MUST call `strip_credentials()` if `include_token=False`
- MUST exclude query_data if `export_mode="CONFIG_ONLY"`
- MUST include query_data if `export_mode="FULL_DATA"`
- MUST set manifest flags consistent with mode:
  - `CONFIG_ONLY` → `includes_cache=False, includes_token=False`
  - `FULL_DATA` → `includes_cache=True, includes_token=include_token`

---

### 3. validate_import_data

**Purpose**: Multi-stage validation of imported data

**Signature**:
```python
def validate_import_data(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate imported data for compatibility.
    
    Performs multi-stage validation:
    1. Format validation (JSON structure, required keys)
    2. Version compatibility (major version match)
    3. Schema validation (required profile fields)
    4. Integrity checks (manifest consistency)
    
    Args:
        data: Parsed JSON data from uploaded file
        
    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if all validation stages passed
        - error_messages: List of validation errors (empty if valid)
        
    Example:
        >>> data = {"manifest": {...}, "profile_data": {...}}
        >>> valid, errors = validate_import_data(data)
        >>> if not valid:
        ...     print("Errors:", errors)
    """
```

**Contract**:
- MUST check for required keys: `manifest`, `profile_data`
- MUST validate version compatibility (major version = 2)
- MUST validate profile fields: `profile_id`, `jira_url`, `jira_email`, `queries`
- MUST check manifest consistency (includes_* flags match data presence)
- MUST return (True, []) if all stages pass
- MUST return (False, [error1, error2, ...]) if any stage fails

---

### 4. resolve_profile_conflict

**Purpose**: Handle profile name collision during import

**Signature**:
```python
def resolve_profile_conflict(
    profile_id: str,
    strategy: str,
    imported_data: Dict[str, Any],
    existing_data: Dict[str, Any]
) -> Tuple[str, Dict[str, Any]]:
    """Resolve profile name conflict with user-selected strategy.
    
    Args:
        profile_id: Original profile identifier from import
        strategy: One of "overwrite", "merge", "rename"
        imported_data: Profile data from uploaded file
        existing_data: Existing profile data from filesystem
        
    Returns:
        Tuple of (final_profile_id, merged_data)
        - final_profile_id: Profile ID after resolution (may be renamed)
        - merged_data: Profile data after applying strategy
        
    Raises:
        ValueError: If strategy invalid
        
    Example:
        >>> final_id, merged = resolve_profile_conflict(
        ...     "default", "merge", imported, existing
        ... )
        >>> merged["jira_token"]  # Preserved from existing
        'LOCAL_TOKEN'
        >>> len(merged["queries"])  # Combined from both
        3
    """
```

**Contract**:
- MUST validate strategy in ["overwrite", "merge", "rename"]
- MUST implement overwrite: return (profile_id, imported_data)
- MUST implement merge:
  - Preserve existing: `jira_token`, `jira_email`, `jira_url`
  - Import new: `queries` (deduplicated), `field_mappings`
- MUST implement rename: append timestamp like " (imported 2025-12-19)"
- MUST return consistent data structure regardless of strategy

---

### 5. import_profile_with_validation

**Purpose**: Complete import workflow with validation and conflict resolution

**Signature**:
```python
def import_profile_with_validation(
    file_content: str,
    conflict_strategy: Optional[str] = None,
    token_override: Optional[str] = None
) -> Tuple[bool, str, List[str]]:
    """Import profile from JSON file with full validation.
    
    Orchestrates complete import process:
    1. Parse JSON
    2. Validate data
    3. Check conflicts (apply strategy if provided)
    4. Write profile files
    5. Return result
    
    Args:
        file_content: Raw JSON string from uploaded file
        conflict_strategy: Resolution if profile exists ("overwrite"|"merge"|"rename")
        token_override: JIRA token if not included in import
        
    Returns:
        Tuple of (success, message, warnings)
        - success: True if import completed
        - message: User-facing success/error message
        - warnings: Non-blocking issues (e.g., field mismatches)
        
    Example:
        >>> success, msg, warnings = import_profile_with_validation(
        ...     json_content, conflict_strategy="merge", token_override="ABC123"
        ... )
        >>> if success:
        ...     print(msg)  # "Profile 'default' imported successfully"
    """
```

**Contract**:
- MUST parse JSON and call `validate_import_data()`
- MUST return (False, error_message, []) if validation fails
- MUST detect profile conflict and require strategy if exists
- MUST call `resolve_profile_conflict()` if conflict detected
- MUST prompt for token if `includes_token=False` and `token_override` not provided
- MUST write profile.json and query_data files on success
- MUST return user-friendly messages (not raw exceptions)

---

## Callback Layer API (callbacks/import_export.py)

### 1. export_profile_callback

**Purpose**: Handle export button click and file download trigger

**Signature**:
```python
@callback(
    Output("export-profile-download", "data"),
    Output("app-notifications", "children", allow_duplicate=True),
    Input("export-confirm-button", "n_clicks"),
    State("export-mode-radio", "value"),
    State("include-token-checkbox", "value"),
    prevent_initial_call=True,
)
def export_profile_callback(
    n_clicks: int,
    export_mode: str,
    include_token: bool
) -> Tuple[Dict[str, str], Component]:
    """Export profile with user-selected mode and token option.
    
    Args:
        n_clicks: Export button click count
        export_mode: Selected export mode ("CONFIG_ONLY" or "FULL_DATA")
        include_token: Checkbox state for token inclusion
        
    Returns:
        Tuple of (download_data, notification)
        - download_data: {"content": json_string, "filename": "export_*.json"}
        - notification: Toast notification component
        
    Side Effects:
        - Reads profile and query data from filesystem
        - Logs export operation with mode and size
    """
```

**Contract**:
- MUST check n_clicks > 0 before proceeding
- MUST get active profile_id and query_id from query_manager
- MUST call `data.import_export.export_profile_with_mode()`
- MUST generate filename: `export_{profile}_{query}_{timestamp}.json`
- MUST show success toast with file size
- MUST show error toast if export fails
- MUST return no_update if no active profile/query

---

### 2. import_profile_callback

**Purpose**: Handle file upload and import process

**Signature**:
```python
@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("conflict-modal", "is_open"),
    Output("token-prompt-modal", "is_open"),
    Input("upload-data", "contents"),
    State("upload-data", "filename"),
    prevent_initial_call=True,
)
def import_profile_callback(
    contents: str,
    filename: str
) -> Tuple[Component, bool, bool]:
    """Handle profile import file upload.
    
    Args:
        contents: Base64-encoded file contents
        filename: Original filename
        
    Returns:
        Tuple of (notification, conflict_modal_open, token_modal_open)
        - notification: Toast component
        - conflict_modal_open: True if profile conflict detected
        - token_modal_open: True if token required
        
    Side Effects:
        - Stores import context in dcc.Store for subsequent callbacks
        - Validates imported data
        - May write profile files if no conflicts/prompts needed
    """
```

**Contract**:
- MUST decode base64 contents
- MUST call `data.import_export.validate_import_data()`
- MUST show error toast if validation fails
- MUST check for profile_id conflict
- MUST open conflict modal if conflict detected
- MUST check for token requirement (includes_token=False)
- MUST open token prompt modal if token required
- MUST complete import if no conflicts/prompts needed

---

### 3. resolve_conflict_callback

**Purpose**: Handle user's conflict resolution choice

**Signature**:
```python
@callback(
    Output("app-notifications", "children", allow_duplicate=True),
    Output("conflict-modal", "is_open", allow_duplicate=True),
    Input("conflict-overwrite-button", "n_clicks"),
    Input("conflict-merge-button", "n_clicks"),
    Input("conflict-rename-button", "n_clicks"),
    State("import-context-store", "data"),
    prevent_initial_call=True,
)
def resolve_conflict_callback(
    overwrite_clicks: int,
    merge_clicks: int,
    rename_clicks: int,
    import_context: Dict[str, Any]
) -> Tuple[Component, bool]:
    """Handle conflict resolution selection.
    
    Args:
        overwrite_clicks: Overwrite button clicks
        merge_clicks: Merge button clicks
        rename_clicks: Rename button clicks
        import_context: Stored import state from previous callback
        
    Returns:
        Tuple of (notification, modal_open)
        - notification: Success/error toast
        - modal_open: False (close modal after selection)
        
    Side Effects:
        - Writes profile files with resolved conflict
        - Updates import_context with resolution
    """
```

**Contract**:
- MUST determine which button triggered callback (ctx.triggered_id)
- MUST call `data.import_export.resolve_profile_conflict()` with chosen strategy
- MUST complete import after resolution
- MUST close modal on success
- MUST show toast with resolution details

---

### 4. show_token_warning_callback

**Purpose**: Display security warning when token checkbox checked

**Signature**:
```python
@callback(
    Output("token-warning-modal", "is_open"),
    Input("include-token-checkbox", "value"),
    prevent_initial_call=True,
)
def show_token_warning_callback(include_token: bool) -> bool:
    """Show security warning modal when token inclusion enabled.
    
    Args:
        include_token: Checkbox state
        
    Returns:
        True if checkbox checked (show modal), False otherwise
    """
```

**Contract**:
- MUST return True if include_token is True
- MUST return False if include_token is False
- MUST NOT block export (only show warning)

---

### 5. confirm_token_warning_callback

**Purpose**: Handle user response to token warning modal

**Signature**:
```python
@callback(
    Output("include-token-checkbox", "value", allow_duplicate=True),
    Output("token-warning-modal", "is_open", allow_duplicate=True),
    Input("token-warning-proceed", "n_clicks"),
    Input("token-warning-cancel", "n_clicks"),
    prevent_initial_call=True,
)
def confirm_token_warning_callback(
    proceed_clicks: int,
    cancel_clicks: int
) -> Tuple[bool, bool]:
    """Handle token warning confirmation.
    
    Args:
        proceed_clicks: "I Understand, Proceed" button clicks
        cancel_clicks: "Cancel" button clicks
        
    Returns:
        Tuple of (checkbox_value, modal_open)
        - checkbox_value: True if proceeded, False if canceled
        - modal_open: False (close modal)
    """
```

**Contract**:
- MUST close modal regardless of choice
- MUST keep checkbox checked if proceeded
- MUST uncheck checkbox if canceled

---

## UI Component API (ui/settings.py)

### Export Mode Selector

**Component**:
```python
dbc.RadioItems(
    id="export-mode-radio",
    options=[
        {
            "label": "Configuration Only (settings and queries, no data)",
            "value": "CONFIG_ONLY"
        },
        {
            "label": "Full Profile with Data (includes cached JIRA data)",
            "value": "FULL_DATA"
        },
    ],
    value="CONFIG_ONLY",  # Default to secure option
    className="mb-3"
)
```

**Contract**:
- MUST default to "CONFIG_ONLY"
- MUST show clear descriptions of what's included
- MUST be required (no null value)

---

### Token Inclusion Checkbox

**Component**:
```python
dbc.Checkbox(
    id="include-token-checkbox",
    label="Include JIRA Token (⚠️ Security Risk)",
    value=False,  # Default unchecked
    className="mb-2"
)
```

**Contract**:
- MUST default to False (unchecked)
- MUST show warning icon
- MUST have adjacent tooltip explaining risk

---

### Token Warning Modal

**Component**:
```python
dbc.Modal([
    dbc.ModalHeader("Security Warning"),
    dbc.ModalBody([
        html.P("Including your JIRA token in the export will:"),
        html.Ul([
            html.Li("Allow anyone with the file to access your JIRA instance"),
            html.Li("Expose your credentials if file is shared or leaked"),
            html.Li("Grant full API access until token is revoked"),
        ]),
        html.P("Only proceed if:", className="font-weight-bold"),
        html.Ul([
            html.Li("This is a personal backup on a secure device"),
            html.Li("You will not share this file with others"),
            html.Li("You understand how to revoke the token if needed"),
        ]),
    ]),
    dbc.ModalFooter([
        dbc.Button("Cancel", id="token-warning-cancel", color="secondary"),
        dbc.Button(
            "I Understand, Proceed",
            id="token-warning-proceed",
            color="danger"
        ),
    ]),
], id="token-warning-modal", is_open=False)
```

**Contract**:
- MUST use danger color for proceed button (red)
- MUST list specific consequences
- MUST provide safe-use guidelines
- MUST default to closed (is_open=False)

---

### Conflict Resolution Modal

**Component**:
```python
dbc.Modal([
    dbc.ModalHeader("Profile Already Exists"),
    dbc.ModalBody([
        html.P(f"A profile named '{profile_id}' already exists."),
        html.P("Choose how to handle this conflict:"),
        dbc.RadioItems(
            id="conflict-strategy-radio",
            options=[
                {
                    "label": "Merge (combine with existing, preserve local settings)",
                    "value": "merge"
                },
                {
                    "label": "Overwrite (replace existing with imported)",
                    "value": "overwrite"
                },
                {
                    "label": "Rename (keep both, rename imported)",
                    "value": "rename"
                },
            ],
            value="merge"  # Default to safest option
        ),
    ]),
    dbc.ModalFooter([
        dbc.Button("Cancel", id="conflict-cancel", color="secondary"),
        dbc.Button("Continue", id="conflict-continue", color="primary"),
    ]),
], id="conflict-modal", is_open=False)
```

**Contract**:
- MUST default to "merge" (safest option)
- MUST explain consequences of each choice
- MUST show profile_id in message
- MUST allow cancellation

---

## Success/Error Messages

### Export Success
```python
create_toast(
    "Export Successful",
    f"Profile exported ({file_size_kb} KB). Mode: {export_mode}",
    "success"
)
```

### Export Error
```python
create_toast(
    "Export Failed",
    f"Could not export profile: {error_message}",
    "danger"
)
```

### Import Success
```python
create_toast(
    "Import Successful",
    f"Profile '{profile_id}' imported. {data_status}",
    "success"
)
# data_status examples:
# - "Sync with JIRA to fetch data" (if CONFIG_ONLY)
# - "All data restored" (if FULL_DATA)
```

### Import Validation Error
```python
create_toast(
    "Import Failed",
    f"Invalid file: {', '.join(validation_errors)}",
    "danger"
)
```

### Import Conflict Resolved
```python
create_toast(
    "Conflict Resolved",
    f"Profile imported using '{strategy}' strategy",
    "info"
)
```

---

## File Format Contract

### Export File Naming Convention
```
export_{profile_name}_{query_name}_{timestamp}.json

Examples:
- export_default_sprint-123_20251219_103045.json
- export_acme-team_backlog_20251219_143022.json
```

**Contract**:
- MUST sanitize profile/query names (replace spaces with underscores)
- MUST use ISO 8601 timestamp without separators (YYYYMMDDHHmmss)
- MUST use .json extension

---

### Export File Structure Contract

```json
{
  "manifest": {
    "version": "2.0",
    "created_at": "2025-12-19T10:30:45Z",
    "export_mode": "CONFIG_ONLY" | "FULL_DATA" | "FULL_DATA_WITH_TOKEN",
    "includes_cache": bool,
    "includes_token": bool
  },
  "profile_data": {
    "profile_id": string,
    "jira_url": string,
    "jira_email": string,
    "jira_token": string | omitted,  // Omitted if !includes_token
    "queries": [
      {
        "query_id": string,
        "jql": string,
        "field_mappings": object
      }
    ]
  },
  "query_data": {  // Omitted if CONFIG_ONLY
    "<query_id>": {
      "project_data": object,
      "jira_cache": object,
      "metrics_snapshots": object
    }
  }
}
```

**Contract**:
- MUST include "manifest" and "profile_data" keys
- MUST omit "query_data" if export_mode = "CONFIG_ONLY"
- MUST omit "jira_token" if includes_token = false
- MUST use ISO 8601 timestamps
- MUST use UTF-8 encoding
- MUST use 2-space indentation for readability

---

## Summary

**Defined Contracts**:
- 5 data layer functions with full signatures and contracts
- 5 callback functions with Dash I/O specifications
- 4 UI components with structure and behavior contracts
- File format and naming conventions
- Success/error message templates

**Key Principles**:
- No mutation of input data (deep copy pattern)
- Validation before action (fail early)
- User-friendly error messages (not raw exceptions)
- Consistent return types (tuples for multi-value returns)
- Type hints on all signatures

Ready for quickstart.md (developer onboarding guide).
