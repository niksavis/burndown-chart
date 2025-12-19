# Data Model: Enhanced Import/Export Options

**Feature**: 013-import-export-scenarios  
**Date**: December 19, 2025

## Overview

This document defines the data structures, state transitions, and validation rules for the enhanced import/export system. The design extends the existing T009 export infrastructure with three distinct export modes.

---

## Core Entities

### 1. ExportManifest (Extended)

**Purpose**: Metadata for exported profiles with mode selection support

**Schema**:
```python
@dataclass
class ExportManifest:
    """Metadata for exported profiles."""
    
    # Existing fields (from T009)
    version: str                    # Schema version (e.g., "2.0")
    created_at: str                 # ISO 8601 timestamp
    created_by: str                 # User identifier (optional)
    export_type: str                # "backup" | "sharing" | "migration"
    
    # New fields (013)
    export_mode: str                # "CONFIG_ONLY" | "FULL_DATA" | "FULL_DATA_WITH_TOKEN"
    includes_cache: bool            # Derived: True if FULL_DATA*
    includes_queries: bool          # Always True (query defs always included)
    includes_token: bool            # Derived: True if *_WITH_TOKEN
    includes_setup_status: bool     # Existing field preserved
    profiles: List[str]             # Existing field preserved
```

**Validation Rules**:
- `version` must match regex `^\d+\.\d+$` (e.g., "2.0")
- `created_at` must be valid ISO 8601 string
- `export_mode` must be one of enum values
- `includes_*` flags must be consistent with `export_mode`:
  - `CONFIG_ONLY` → `includes_cache=False, includes_token=False`
  - `FULL_DATA` → `includes_cache=True, includes_token=False`
  - `FULL_DATA_WITH_TOKEN` → `includes_cache=True, includes_token=True`

**Example**:
```json
{
  "version": "2.0",
  "created_at": "2025-12-19T10:30:00Z",
  "created_by": "user@example.com",
  "export_type": "sharing",
  "export_mode": "CONFIG_ONLY",
  "includes_cache": false,
  "includes_queries": true,
  "includes_token": false,
  "includes_setup_status": true,
  "profiles": ["default"]
}
```

---

### 2. ExportPackage

**Purpose**: Complete export payload with data and metadata

**Schema**:
```python
@dataclass
class ExportPackage:
    """Complete export package."""
    
    manifest: ExportManifest
    profile_data: Dict[str, Any]    # From profile.json
    query_data: Optional[Dict[str, Any]]  # None if CONFIG_ONLY
```

**Structure**:
```json
{
  "manifest": { /* ExportManifest */ },
  "profile_data": {
    "profile_id": "default",
    "jira_url": "https://example.atlassian.net",
    "jira_email": "user@example.com",
    "jira_token": "...",  // Omitted if !includes_token
    "queries": [
      {
        "query_id": "sprint-123",
        "jql": "project = ACME AND sprint = 123",
        "field_mappings": { /* ... */ }
      }
    ]
  },
  "query_data": {  // Omitted if CONFIG_ONLY
    "sprint-123": {
      "project_data": { /* statistics, scope */ },
      "jira_cache": { /* cached issues */ },
      "metrics_snapshots": { /* weekly snapshots */ }
    }
  }
}
```

**Size Estimates**:
- `CONFIG_ONLY`: ~5-10 KB (profile + query definitions)
- `FULL_DATA`: ~500 KB - 5 MB (includes cached JIRA responses)
- `FULL_DATA_WITH_TOKEN`: Same as FULL_DATA + token field

---

### 3. ImportContext

**Purpose**: State tracking during import process

**Schema**:
```python
@dataclass
class ImportContext:
    """State information during import."""
    
    source_file: str                # Path to uploaded file
    manifest: ExportManifest        # Parsed from file
    validation_status: str          # "pending" | "valid" | "invalid"
    validation_errors: List[str]    # Error messages if invalid
    conflict_resolution: Optional[str]  # "overwrite" | "merge" | "rename"
    target_profile_id: str          # Final profile name after conflict resolution
    requires_token_prompt: bool     # True if !includes_token
```

**State Transitions**:
```
File uploaded → validation_status="pending"
  ↓
Validation passed → validation_status="valid"
  ↓
Profile exists? → YES → prompt conflict_resolution
                  NO → proceed with import
  ↓
Token missing? → YES → requires_token_prompt=True
                 NO → complete import
```

---

### 4. ConflictResolution

**Purpose**: Strategy for handling existing profile with same ID

**Schema**:
```python
class ConflictResolution(Enum):
    """Strategies for profile name conflicts."""
    
    OVERWRITE = "overwrite"  # Delete existing, import new
    MERGE = "merge"          # Combine with precedence rules
    RENAME = "rename"        # Auto-generate unique name
```

**Merge Precedence Rules**:
```python
def merge_profiles(existing: dict, imported: dict) -> dict:
    """Merge profiles with conflict resolution rules."""
    
    # Local takes precedence (do not overwrite)
    merged = {
        "jira_token": existing.get("jira_token"),  # Never overwrite local token
        "jira_email": existing.get("jira_email"),
        "jira_url": existing.get("jira_url"),
    }
    
    # Imported takes precedence (do overwrite)
    merged.update({
        "queries": imported.get("queries"),  # Import new query definitions
        "field_mappings": imported.get("field_mappings"),
    })
    
    # Combine arrays (no duplicates)
    merged["queries"] = deduplicate_queries(
        existing.get("queries", []) + imported.get("queries", [])
    )
    
    return merged
```

---

## Field Mappings

### Profile Configuration Fields

| Field            | Type   | Required | Description               | Export Behavior                   |
| ---------------- | ------ | -------- | ------------------------- | --------------------------------- |
| `profile_id`     | string | Yes      | Unique profile identifier | Always included                   |
| `jira_url`       | string | Yes      | JIRA instance URL         | Always included                   |
| `jira_email`     | string | Yes      | JIRA user email           | Always included                   |
| `jira_token`     | string | Yes      | API token                 | **Stripped if !includes_token**   |
| `queries`        | array  | Yes      | Query definitions         | Always included                   |
| `field_mappings` | object | No       | Custom field mappings     | Always included                   |
| `setup_status`   | object | No       | Wizard progress           | Included if includes_setup_status |

### Query Data Fields

| Field               | Type   | Required | Description           | Export Behavior        |
| ------------------- | ------ | -------- | --------------------- | ---------------------- |
| `project_data`      | object | No       | Statistics, scope     | Included if FULL_DATA* |
| `jira_cache`        | object | No       | Cached JIRA responses | Included if FULL_DATA* |
| `metrics_snapshots` | object | No       | Weekly metric history | Included if FULL_DATA* |

---

## Validation Rules

### Import Validation Pipeline

**Stage 1: Format Validation**
```python
def validate_format(file_content: str) -> Tuple[bool, List[str]]:
    """Validate JSON structure and required keys."""
    errors = []
    
    try:
        data = json.loads(file_content)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON: {e}"]
    
    # Check required top-level keys
    if "manifest" not in data:
        errors.append("Missing 'manifest' key")
    if "profile_data" not in data:
        errors.append("Missing 'profile_data' key")
    
    return len(errors) == 0, errors
```

**Stage 2: Version Compatibility**
```python
def validate_version(manifest: ExportManifest) -> Tuple[bool, List[str]]:
    """Check version compatibility."""
    errors = []
    
    version = manifest.version
    major, minor = version.split(".")
    
    # Support same major version
    if int(major) != 2:
        errors.append(f"Unsupported version {version}. Expected 2.x")
    
    return len(errors) == 0, errors
```

**Stage 3: Schema Validation**
```python
def validate_schema(data: dict) -> Tuple[bool, List[str]]:
    """Validate required profile fields."""
    errors = []
    
    profile = data.get("profile_data", {})
    required_fields = ["profile_id", "jira_url", "jira_email", "queries"]
    
    for field in required_fields:
        if field not in profile:
            errors.append(f"Missing required field: {field}")
    
    # Validate queries structure
    queries = profile.get("queries", [])
    if not isinstance(queries, list):
        errors.append("'queries' must be an array")
    
    for i, query in enumerate(queries):
        if "query_id" not in query or "jql" not in query:
            errors.append(f"Invalid query at index {i}")
    
    return len(errors) == 0, errors
```

**Stage 4: Data Integrity**
```python
def validate_integrity(data: dict) -> Tuple[bool, List[str]]:
    """Check manifest consistency with data."""
    warnings = []
    
    manifest = data["manifest"]
    
    # Check includes_cache consistency
    if manifest.includes_cache:
        if "query_data" not in data:
            warnings.append("Manifest claims includes_cache=true but query_data missing")
    
    # Check includes_token consistency
    if manifest.includes_token:
        profile = data.get("profile_data", {})
        if "jira_token" not in profile or not profile["jira_token"]:
            warnings.append("Manifest claims includes_token=true but token missing")
    
    # Warnings don't block import, but log them
    return True, warnings
```

---

## State Transitions

### Export Workflow

```
User clicks "Export" → Show modal with mode selection
  ↓
User selects mode:
  - CONFIG_ONLY → Checkbox "Include Token" (default: unchecked)
  - FULL_DATA → Checkbox "Include Token" (default: unchecked)
  ↓
User checks "Include Token" → Show security warning modal
  ↓
User confirms in modal → Proceed with export
User cancels → Uncheck "Include Token"
  ↓
Generate ExportPackage based on mode
  ↓
If !includes_token → strip_credentials(profile_data)
  ↓
Serialize to JSON → Download file
```

### Import Workflow

```
User uploads file → Parse JSON
  ↓
Validate format/version/schema → Invalid? → Show error toast
  ↓
Check profile_id conflict → Exists? → Show conflict modal
  ↓
User selects resolution:
  - Overwrite → Delete existing profile
  - Merge → Apply merge rules
  - Rename → Append timestamp to profile_id
  ↓
Check includes_token → False? → Show token input modal
  ↓
User enters token → Validate connection → Invalid? → Retry or cancel
  ↓
Write profile.json (+ query_data if included)
  ↓
Show success toast with summary:
  - "Configuration imported for profile 'X'"
  - "Sync with JIRA to fetch data" (if CONFIG_ONLY)
  - "All data restored" (if FULL_DATA)
```

---

## Relationships

```
ExportPackage
  ├── manifest: ExportManifest
  │     └── export_mode: determines includes_*
  ├── profile_data: Dict
  │     ├── queries: List[QueryDefinition]
  │     └── jira_token: Optional (stripped if !includes_token)
  └── query_data: Optional[Dict]  (None if CONFIG_ONLY)
        └── {query_id}: Dict
              ├── project_data
              ├── jira_cache
              └── metrics_snapshots

ImportContext
  ├── manifest: ExportManifest (from uploaded file)
  ├── validation_errors: List[str]
  └── conflict_resolution: ConflictResolution (if conflict)
```

---

## Examples

### Example 1: Config-Only Export (No Token)

**Input**:
- User selects "CONFIG_ONLY" mode
- "Include Token" unchecked

**Output**:
```json
{
  "manifest": {
    "version": "2.0",
    "export_mode": "CONFIG_ONLY",
    "includes_cache": false,
    "includes_token": false
  },
  "profile_data": {
    "profile_id": "default",
    "jira_url": "https://acme.atlassian.net",
    "jira_email": "user@acme.com",
    "queries": [
      {
        "query_id": "sprint-123",
        "jql": "project = ACME AND sprint = 123"
      }
    ]
  }
}
```

**File size**: ~5 KB

---

### Example 2: Full Data Export (With Token)

**Input**:
- User selects "FULL_DATA" mode
- "Include Token" checked (after warning)

**Output**:
```json
{
  "manifest": {
    "version": "2.0",
    "export_mode": "FULL_DATA_WITH_TOKEN",
    "includes_cache": true,
    "includes_token": true
  },
  "profile_data": {
    "profile_id": "default",
    "jira_url": "https://acme.atlassian.net",
    "jira_email": "user@acme.com",
    "jira_token": "ATATT3xFfGF0...",  // Token included
    "queries": [ /* ... */ ]
  },
  "query_data": {
    "sprint-123": {
      "project_data": { /* 50 KB */ },
      "jira_cache": { /* 500 KB */ },
      "metrics_snapshots": { /* 10 KB */ }
    }
  }
}
```

**File size**: ~560 KB

---

### Example 3: Import with Conflict (Merge)

**Existing profile**:
```json
{
  "profile_id": "default",
  "jira_token": "LOCAL_TOKEN_123",
  "queries": [
    {"query_id": "sprint-122", "jql": "old query"}
  ]
}
```

**Imported profile**:
```json
{
  "profile_id": "default",
  "queries": [
    {"query_id": "sprint-123", "jql": "new query"}
  ]
}
```

**Merged result**:
```json
{
  "profile_id": "default",
  "jira_token": "LOCAL_TOKEN_123",  // Preserved from local
  "queries": [
    {"query_id": "sprint-122", "jql": "old query"},
    {"query_id": "sprint-123", "jql": "new query"}  // Added from import
  ]
}
```

---

## Security Considerations

### Credential Stripping Implementation

```python
def strip_credentials(profile: dict) -> dict:
    """Remove sensitive fields from profile.
    
    Returns a deep copy with credentials removed.
    Does NOT mutate the input.
    """
    import copy
    
    safe_profile = copy.deepcopy(profile)
    
    # Remove all credential fields
    SENSITIVE_FIELDS = ["jira_token", "jira_api_key", "api_secret"]
    for field in SENSITIVE_FIELDS:
        safe_profile.pop(field, None)
    
    # Validate no credentials remain
    serialized = json.dumps(safe_profile).lower()
    FORBIDDEN_PATTERNS = ["token", "secret", "password", "api_key"]
    
    for pattern in FORBIDDEN_PATTERNS:
        if pattern in serialized:
            logger.warning(f"Potential credential leak: '{pattern}' found in export")
    
    return safe_profile
```

### Token Presence Validation

```python
def validate_token_consistency(package: ExportPackage) -> None:
    """Verify token presence matches manifest."""
    
    profile = package.profile_data
    manifest = package.manifest
    
    has_token = "jira_token" in profile and bool(profile["jira_token"])
    
    if manifest.includes_token and not has_token:
        raise ValueError("Manifest claims includes_token=True but token missing")
    
    if not manifest.includes_token and has_token:
        raise ValueError("Token present but manifest claims includes_token=False")
```

---

## Summary

**Key Data Structures**:
1. `ExportManifest` - Extended with `export_mode` and consistency flags
2. `ExportPackage` - Complete payload with conditional query_data
3. `ImportContext` - State tracking for validation and conflict resolution
4. `ConflictResolution` - Three-way merge strategy

**Validation Pipeline**:
Format → Version → Schema → Integrity → Conflict → Token prompt

**Security**:
- Deep copy before credential stripping
- Validation of token absence in exports
- Two-tier warnings for token inclusion

Ready for contract definition (API/callback signatures) in Phase 1 contracts/.
