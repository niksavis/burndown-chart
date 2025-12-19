# Research: Enhanced Import/Export Options

**Feature**: 013-import-export-scenarios  
**Date**: December 19, 2025

## Research Questions

### 1. How should export modes be structured in the data model?

**Decision**: Extend existing `ExportManifest` dataclass with `export_mode` enum field

**Rationale**:
- Existing T009 implementation already uses dataclass pattern for export metadata
- `ExportManifest` in `data/import_export.py` has `export_type` field ("backup", "sharing", "migration")
- New field `export_mode` with values: "CONFIG_ONLY", "FULL_DATA", "FULL_DATA_WITH_TOKEN"
- Separates transport type (sharing) from payload content (config vs data)

**Alternatives considered**:
- Separate export functions per mode → rejected: violates DRY, harder to maintain
- Boolean flags (include_data, include_token) → rejected: ambiguous combinations, error-prone
- String-based modes without enum → rejected: no type safety, harder to validate

**Implementation approach**:
```python
@dataclass
class ExportManifest:
    version: str
    created_at: str
    export_mode: str  # "CONFIG_ONLY" | "FULL_DATA" | "FULL_DATA_WITH_TOKEN"
    includes_cache: bool  # Derived from mode
    includes_queries: bool  # Always true
    includes_token: bool  # Derived from mode
```

---

### 2. What is the best practice for securely stripping credentials from JSON exports?

**Decision**: Deep copy profile dict, del token key, validate absence before serialization

**Rationale**:
- Python's `copy.deepcopy()` prevents mutation of source data
- Explicit `del profile_copy["jira_token"]` is more readable than dict comprehension
- Final validation step: `assert "jira_token" not in json.dumps(export_data)`
- Follows security best practice: fail-safe defaults (token excluded by default)

**Alternatives considered**:
- JSON serializer hook to skip specific keys → rejected: non-obvious behavior, hard to audit
- Encryption instead of stripping → rejected: over-engineered for sharing use case
- Redaction (replace with "REDACTED") → rejected: could cause parsing errors on import

**Implementation approach**:
```python
def strip_credentials(profile_data: dict) -> dict:
    """Remove sensitive fields from profile configuration."""
    safe_copy = copy.deepcopy(profile_data)
    
    # Strip JIRA credentials
    safe_copy.pop("jira_token", None)  # Safe removal
    safe_copy.pop("jira_api_key", None)  # Future-proof
    
    # Validate no credentials remain
    serialized = json.dumps(safe_copy)
    assert "token" not in serialized.lower(), "Credential leak detected"
    
    return safe_copy
```

**Security validation**:
- Unit test with real token pattern: `test_export_config_only_strips_token()`
- Integration test: export → grep for "token" → assert none found
- Pre-commit hook: scan staged files for token patterns

---

### 3. How to handle profile name conflicts during import?

**Decision**: Detect conflict, prompt user with 3 options: overwrite, merge, rename

**Rationale**:
- User Story 2 edge case: "What happens when user imports configuration-only but profile already exists with same name?"
- Toast notification with 3-button choice matches existing UI pattern
- Merge strategy: preserve local JIRA token + user preferences, import queries/field mappings
- Rename strategy: auto-generate unique name (e.g., "Profile Name (imported 2025-12-19)")

**Alternatives considered**:
- Auto-overwrite → rejected: data loss risk, violates user control principle
- Auto-merge always → rejected: unpredictable results, hard to undo
- Fail with error → rejected: poor UX, requires manual intervention

**Implementation approach**:
```python
def resolve_profile_conflict(profile_id: str, import_data: dict) -> str:
    """Handle profile name collision during import."""
    if not profile_exists(profile_id):
        return profile_id  # No conflict
    
    # Show modal with options (callback triggers this)
    # Return value determines action:
    # - "overwrite" → delete existing, import new
    # - "merge" → combine with precedence rules
    # - "rename" → append timestamp
    
    # Default: rename for safety
    timestamp = datetime.now().strftime("%Y-%m-%d")
    return f"{profile_id} (imported {timestamp})"
```

**UI flow**:
1. Import file uploaded
2. Conflict detected → pause import
3. Modal with radio buttons: Overwrite / Merge / Rename
4. User selects → import continues with chosen strategy
5. Toast notification confirms action taken

---

### 4. What file size optimization techniques are needed for configuration-only exports?

**Decision**: Exclude jira_cache.json and project_data.json, include only profile.json + query definitions

**Rationale**:
- Success criteria SC-002: "90% smaller than full data exports when cache contains >100 issues"
- Typical sizes: profile.json (~5KB), jira_cache.json (~500KB-5MB), project_data.json (~50KB)
- Configuration-only: ~5KB, Full data: ~550KB-5MB → 99% reduction achievable
- Query definitions stored in profile.json under `queries` key

**Alternatives considered**:
- Compression (gzip) → deferred: adds complexity, may implement later if needed
- Binary format (msgpack) → rejected: JSON is human-readable, easier to debug
- Incremental export (only changed data) → rejected: complex versioning, not needed for MVP

**Implementation approach**:
```python
def export_config_only(profile_id: str, include_token: bool) -> dict:
    """Export profile configuration without cached data."""
    profile_path = Path("profiles") / profile_id / "profile.json"
    
    with open(profile_path, "r") as f:
        profile_data = json.load(f)
    
    if not include_token:
        profile_data = strip_credentials(profile_data)
    
    return {
        "export_version": "2.0",
        "export_mode": "CONFIG_ONLY",
        "profile": profile_data,
        # Explicitly omit query_data
    }
```

**Measurement**:
- Unit test: verify exported JSON < 10KB for typical profile
- Integration test: compare config-only vs full export size ratio > 0.9

---

### 5. How to validate imported data for compatibility?

**Decision**: Multi-stage validation: schema version check → field mapping validation → JQL syntax validation

**Rationale**:
- Edge case: "What happens when imported configuration references custom JIRA fields that don't exist on recipient's JIRA instance?"
- Edge case: "How does system handle version incompatibility (importing newer format into older app version)?"
- Fail early with actionable error messages

**Alternatives considered**:
- Best-effort import with warnings → rejected: silent failures confuse users
- Lazy validation (on first use) → rejected: unexpected errors during operation
- No validation → rejected: violates data integrity principle

**Implementation approach**:
```python
def validate_import_data(import_data: dict) -> Tuple[bool, List[str]]:
    """Validate imported data for compatibility.
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # Stage 1: Version check
    export_version = import_data.get("export_version")
    if not export_version or export_version < "1.0":
        errors.append("Unsupported export version")
    
    # Stage 2: Schema validation
    required_keys = ["profile", "export_mode"]
    missing_keys = [k for k in required_keys if k not in import_data]
    if missing_keys:
        errors.append(f"Missing keys: {missing_keys}")
    
    # Stage 3: Field mapping validation (warning, not error)
    profile = import_data.get("profile", {})
    field_mappings = profile.get("field_mappings", {})
    # Note: Actual field existence validated on first JIRA sync
    
    return (len(errors) == 0, errors)
```

**User experience**:
- Invalid file → toast notification with specific error
- Warning (field mismatch) → allow import, show warning banner
- Success → toast with "Configuration imported. Sync with JIRA to validate fields."

---

### 6. What security warnings are effective for token inclusion?

**Decision**: Two-tier warning: inline tooltip + modal confirmation with consequences list

**Rationale**:
- FR-005: "System MUST display security warning near Include JIRA Token checkbox"
- SC-007: "95% of users understand token inclusion implications before making export choice"
- Progressive disclosure: light warning always visible, severe warning on explicit opt-in

**Alternatives considered**:
- Checkbox only → rejected: insufficient awareness, accidental exposure risk
- Always show modal → rejected: warning fatigue for config-only exports
- Red text only → rejected: users skip text warnings

**Implementation approach**:

**Inline warning (always visible)**:
```python
dbc.Tooltip(
    "Including token allows recipient to access your JIRA instance. "
    "Only enable for personal backups.",
    target="include-token-checkbox"
)
```

**Modal confirmation (shown when checked)**:
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
        dbc.Button("Cancel", id="token-warning-cancel"),
        dbc.Button("I Understand, Proceed", id="token-warning-proceed", color="danger"),
    ]),
])
```

**Metrics**:
- Track: % exports with token included (should be <5%)
- Track: % users who see modal and cancel (indicates warning effectiveness)

---

## Technology Decisions

### Export File Format

**Decision**: JSON (unchanged from existing implementation)

**Justification**:
- Human-readable for debugging
- Native Python support
- Existing T009 implementation uses JSON
- No breaking changes required

---

### UI Component Library

**Decision**: Dash Bootstrap Components (existing)

**Justification**:
- Already used throughout app (dbc.Modal, dbc.RadioItems, dbc.Checkbox)
- Consistent styling with existing UI
- Mobile-responsive out of the box

---

### Testing Strategy

**Decision**: Three-tier testing (unit → integration → browser)

**Justification**:
- Unit tests: Export mode logic, credential stripping, file size validation
- Integration tests: End-to-end export/import flows with temp files
- Browser tests (Playwright): UI interactions, modal workflows

**Test file structure**:
```
tests/
├── unit/data/test_import_export.py       # Mode logic, stripping
├── integration/test_import_export_scenarios.py  # E2E flows
└── visual/test_export_ui.py              # Playwright tests
```

---

## Dependencies

### Existing (no additions needed)
- `json` (stdlib)
- `pathlib` (stdlib)
- `copy.deepcopy` (stdlib)
- `dash-bootstrap-components` (already installed)
- `pytest` (already installed)
- `playwright` (already installed)

### No new dependencies required

---

## Performance Considerations

### Export Performance Target: <3 seconds

**Approach**:
- Configuration-only: No I/O on cache files → <100ms
- Full data: Single query only (not all queries) → bounds data size
- Stream large files instead of loading into memory

**Optimization**:
```python
def export_full_data(profile_id: str, query_id: str) -> dict:
    """Export with selected query data only (not all queries)."""
    # Only load specified query's cache
    query_cache = load_query_cache(profile_id, query_id)  # Scoped read
    
    # Avoid loading other queries' data
    return {
        "profile": load_profile(profile_id),
        "query_data": {query_id: query_cache}  # Single query
    }
```

---

## Open Questions

1. **Should we support bulk export (multiple profiles at once)?**
   - Decision: Deferred to future feature (not in spec)
   - Current scope: Single profile per export

2. **Should we compress exports automatically?**
   - Decision: No (not in requirements)
   - JSON remains human-readable for debugging
   - Future enhancement if user requests

3. **Should we support incremental imports (append queries vs replace)?**
   - Decision: Use conflict resolution (overwrite/merge/rename)
   - Incremental append could be future enhancement

---

## Summary

All research questions resolved. Key decisions:
1. Extend `ExportManifest` with `export_mode` field
2. Deep copy + explicit deletion for credential stripping
3. Three-way conflict resolution (overwrite/merge/rename)
4. Exclude cache files for 90%+ size reduction
5. Multi-stage validation (version → schema → fields)
6. Two-tier security warnings (tooltip + modal)

No blockers identified. No new dependencies required. Ready for Phase 1 (data model design).
