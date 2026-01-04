# Quick Start Guide: Enhanced Import/Export Options

**Feature**: 013-import-export-scenarios  
**For**: Developers implementing this feature  
**Estimated Time**: 2-3 hours for core implementation

---

## Prerequisites

- Python 3.13 environment activated
- Existing codebase with T009 import/export foundation
- Understanding of Dash callbacks and layered architecture

---

## Implementation Checklist

### Phase 1: Data Layer (1 hour)

- [ ] **Extend ExportManifest** in `data/import_export.py`
  - Add `export_mode` field
  - Add derived flags: `includes_cache`, `includes_token`
  
- [ ] **Implement strip_credentials()**
  - Deep copy profile dict
  - Remove: `jira_token`, `jira_api_key`, `api_secret`
  - Validate no credential patterns remain
  - Add unit test with real token pattern

- [ ] **Implement export_profile_with_mode()**
  - Accept: `profile_id`, `query_id`, `export_mode`, `include_token`
  - Validate mode in ["CONFIG_ONLY", "FULL_DATA"]
  - Conditionally load query_data based on mode
  - Load budget_data (budget_settings and budget_revisions) if present
  - Call `strip_credentials()` if `include_token=False`
  - Return ExportPackage dict with budget_data included

- [ ] **Implement validate_import_data()**
  - Stage 1: Format validation (JSON structure)
  - Stage 2: Version compatibility (major = 2)
  - Stage 3: Schema validation (required fields)
  - Stage 4: Integrity checks (manifest consistency)
  - Return (bool, List[str])

- [ ] **Implement resolve_profile_conflict()**
  - Accept: `profile_id`, `strategy`, `imported_data`, `existing_data`
  - Implement overwrite: return imported_data as-is
  - Implement merge: preserve local token, import queries
  - Implement rename: append timestamp
  - Return (final_profile_id, merged_data)

---

### Phase 2: UI Components (30 minutes)

- [ ] **Add Export Mode Selector** in `ui/settings.py`
  ```python
  dbc.RadioItems(
      id="export-mode-radio",
      options=[
          {"label": "Configuration Only", "value": "CONFIG_ONLY"},
          {"label": "Full Profile with Data", "value": "FULL_DATA"},
      ],
      value="CONFIG_ONLY"
  )
  ```

- [ ] **Add Token Checkbox** in `ui/settings.py`
  ```python
  dbc.Checkbox(
      id="include-token-checkbox",
      label="Include JIRA Token (⚠️ Security Risk)",
      value=False
  )
  ```

- [ ] **Add Token Warning Modal** in `ui/settings.py`
  - Modal with security consequences
  - "Cancel" and "I Understand, Proceed" buttons
  - Danger-colored proceed button

- [ ] **Add Conflict Resolution Modal** in `ui/settings.py`
  - Radio options: Merge, Overwrite, Rename
  - Default to "Merge"
  - "Cancel" and "Continue" buttons

---

### Phase 3: Callbacks (1 hour)

- [ ] **Update export_profile_callback()** in `callbacks/import_export.py`
  - Add State inputs: `export-mode-radio`, `include-token-checkbox`
  - Call `data.import_export.export_profile_with_mode()`
  - Generate filename with mode indicator
  - Show success toast with file size

- [ ] **Update import_profile_callback()** in `callbacks/import_export.py`
  - Call `validate_import_data()` on upload
  - Show error toast if invalid
  - Check for profile conflict → open conflict modal
  - Check for token requirement → open token prompt modal
  - Import budget_data if present (budget_settings and budget_revisions)
  - Update budget revision timestamps to import time
  - Store import context in dcc.Store

- [ ] **Add show_token_warning_callback()** in `callbacks/import_export.py`
  - Trigger: `include-token-checkbox` value change
  - Output: `token-warning-modal` is_open
  - Show modal when checked

- [ ] **Add confirm_token_warning_callback()** in `callbacks/import_export.py`
  - Inputs: proceed button, cancel button
  - Outputs: checkbox value, modal is_open
  - Uncheck if canceled, keep checked if proceeded

- [ ] **Add resolve_conflict_callback()** in `callbacks/import_export.py`
  - Inputs: overwrite, merge, rename buttons
  - State: import context store
  - Call `resolve_profile_conflict()` with chosen strategy
  - Complete import after resolution

---

### Phase 4: Testing (30 minutes)

- [ ] **Unit Tests** in `tests/unit/data/test_import_export.py`
  - `test_strip_credentials_removes_token()`
  - `test_strip_credentials_preserves_other_fields()`
  - `test_export_config_only_excludes_query_data()`
  - `test_export_full_data_includes_query_data()`
  - `test_validate_import_data_format_errors()`
  - `test_validate_import_data_version_incompatible()`
  - `test_resolve_conflict_merge_preserves_token()`
  - `test_resolve_conflict_rename_appends_timestamp()`

- [ ] **Integration Tests** in `tests/integration/test_import_export_scenarios.py`
  - `test_config_only_import_prompts_for_token()`
  - `test_full_data_import_no_token_prompt()`
  - `test_export_config_only_smaller_than_full()`
  - `test_import_with_conflict_merge_strategy()`

---

## Development Workflow

### 1. Start with Data Layer

```bash
# Activate environment
.\.venv\Scripts\activate

# Edit data/import_export.py
code data/import_export.py

# Run unit tests as you implement
pytest tests/unit/data/test_import_export.py -v
```

**Key functions to implement**:
1. `strip_credentials()` - Start here, easiest to test
2. `export_profile_with_mode()` - Core export logic
3. `validate_import_data()` - Import validation pipeline
4. `resolve_profile_conflict()` - Conflict resolution

---

### 2. Add UI Components

```bash
# Edit ui/settings.py
code ui/settings.py
```

**Add to export panel**:
1. Export mode radio buttons
2. Token inclusion checkbox
3. Token warning modal
4. Conflict resolution modal

**Tips**:
- Reuse existing modal styling from other settings
- Place radio buttons above existing export button
- Add tooltips for clarity

---

### 3. Wire Up Callbacks

```bash
# Edit callbacks/import_export.py
code callbacks/import_export.py
```

**Update existing callbacks**:
1. `export_profile_callback()` - Add mode/token parameters
2. `import_profile_callback()` - Add validation and conflict detection

**Add new callbacks**:
3. `show_token_warning_callback()` - Show warning on checkbox
4. `confirm_token_warning_callback()` - Handle warning response
5. `resolve_conflict_callback()` - Handle conflict resolution

**Remember**: Callbacks MUST delegate to data layer. No business logic in callbacks.

---

### 4. Run Tests

```bash
# Run all import/export tests
pytest tests/unit/data/test_import_export.py -v
pytest tests/integration/test_import_export_scenarios.py -v

# Check coverage
pytest tests/unit/data/test_import_export.py --cov=data.import_export --cov-report=html

# Run full test suite
pytest tests/ -v
```

---

### 5. Manual Testing Checklist

- [ ] **Export Config Only (No Token)**
  - Select "Configuration Only"
  - Ensure "Include Token" unchecked
  - Click export
  - Verify file size < 10 KB
  - Open file in text editor
  - Search for "token" → should not find any

- [ ] **Export Config Only (With Token)**
  - Select "Configuration Only"
  - Check "Include Token"
  - Verify security warning modal appears
  - Click "I Understand, Proceed"
  - Click export
  - Open file in text editor
  - Search for "jira_token" → should find it

- [ ] **Export Full Data (No Token)**
  - Select "Full Profile with Data"
  - Ensure "Include Token" unchecked
  - Click export
  - Verify file size > 100 KB (if cache has data)
  - Open file in text editor
  - Verify "query_data" key exists
  - Search for "token" → should not find any

- [ ] **Import Config Only**
  - Export config-only file
  - Upload file
  - Verify token prompt modal appears
  - Enter token
  - Verify import succeeds
  - Check profile has no cached data
  - Click "Update Data" to fetch from JIRA

- [ ] **Import Full Data**
  - Export full-data file
  - Upload file
  - Verify NO token prompt (data includes token OR no token needed)
  - Verify import succeeds
  - Check charts render immediately (no "Update Data" needed)

- [ ] **Import with Conflict (Merge)**
  - Create profile "test-profile"
  - Export it
  - Modify local profile (change token)
  - Import exported file
  - Verify conflict modal appears
  - Select "Merge"
  - Verify local token preserved
  - Verify queries combined

- [ ] **Import with Conflict (Overwrite)**
  - Create profile "test-profile"
  - Export it
  - Modify local profile
  - Import exported file
  - Select "Overwrite"
  - Verify local profile replaced completely

- [ ] **Import with Conflict (Rename)**
  - Create profile "test-profile"
  - Export it
  - Import exported file
  - Select "Rename"
  - Verify new profile created with timestamp suffix
  - Verify both profiles exist

---

## Common Pitfalls

### ❌ Mutating Input Data

**Problem**: `strip_credentials()` modifies the original profile dict

**Solution**:
```python
import copy

def strip_credentials(profile: dict) -> dict:
    safe_profile = copy.deepcopy(profile)  # Create copy first!
    safe_profile.pop("jira_token", None)
    return safe_profile
```

---

### ❌ Inconsistent Manifest Flags

**Problem**: `includes_token=True` but token actually stripped

**Solution**:
```python
manifest = ExportManifest(
    export_mode=export_mode,
    includes_token=include_token,  # Use parameter value
    includes_cache=(export_mode == "FULL_DATA")  # Derive from mode
)

if not include_token:
    profile_data = strip_credentials(profile_data)  # Strip if flag says so
```

---

### ❌ Callback Logic Violation

**Problem**: Implementing file validation in callback

**Solution**:
```python
# ❌ BAD: Logic in callback
@callback(...)
def import_callback(contents):
    data = json.loads(contents)
    if "manifest" not in data:  # Logic!
        return error_toast
    
# ✅ GOOD: Delegate to data layer
@callback(...)
def import_callback(contents):
    valid, errors = validate_import_data(contents)  # Delegate!
    if not valid:
        return create_toast("Import Failed", ", ".join(errors))
```

---

### ❌ Large File Memory Issues

**Problem**: Loading 5MB cache file into memory at once

**Solution**:
```python
# For this feature, loading full file is acceptable (bounded by single query)
# Future optimization: stream large files if needed
```

---

### ❌ Token Leak in Logs

**Problem**: Logging profile dict with token

**Solution**:
```python
# ❌ BAD
logger.info(f"Exporting profile: {profile}")  # Token in logs!

# ✅ GOOD
logger.info(f"Exporting profile: {profile.get('profile_id')}")
```

---

## File Structure Reference

```
data/
└── import_export.py
    ├── ExportManifest (extended)
    ├── strip_credentials()
    ├── export_profile_with_mode()
    ├── validate_import_data()
    └── resolve_profile_conflict()

callbacks/
└── import_export.py
    ├── export_profile_callback() (updated)
    ├── import_profile_callback() (updated)
    ├── show_token_warning_callback() (new)
    ├── confirm_token_warning_callback() (new)
    └── resolve_conflict_callback() (new)

ui/
└── settings.py
    ├── export_mode_radio (new)
    ├── include_token_checkbox (new)
    ├── token_warning_modal (new)
    └── conflict_modal (new)

tests/
├── unit/data/test_import_export.py (extended)
└── integration/test_import_export_scenarios.py (new)
```

---

## Debugging Tips

### Export Not Including Query Data

**Check**:
1. Is `export_mode="FULL_DATA"`?
2. Does query_id exist in `profiles/{profile}/queries/`?
3. Does `project_data.json` exist for that query?

**Debug**:
```python
print(f"Export mode: {export_mode}")
print(f"Query path exists: {query_dir.exists()}")
print(f"Files: {list(query_dir.iterdir())}")
```

---

### Import Validation Always Failing

**Check**:
1. Is file valid JSON?
2. Does it have "manifest" and "profile_data" keys?
3. Is version "2.x"?

**Debug**:
```python
data = json.loads(file_content)
print(f"Keys: {data.keys()}")
print(f"Version: {data.get('manifest', {}).get('version')}")
valid, errors = validate_import_data(data)
print(f"Errors: {errors}")
```

---

### Token Warning Not Showing

**Check**:
1. Is `show_token_warning_callback()` registered?
2. Is modal ID correct: `token-warning-modal`?
3. Is checkbox ID correct: `include-token-checkbox`?

**Debug**:
```python
# In callback
print(f"Checkbox value: {include_token}")
print(f"Returning modal open: {include_token}")
```

---

## Performance Validation

### Export Speed Test

```python
import time

start = time.time()
package = export_profile_with_mode("default", "sprint-123", "FULL_DATA")
end = time.time()

print(f"Export took {end - start:.2f} seconds")  # Should be < 3s
```

**Target**: <3 seconds regardless of cache size

---

### File Size Test

```python
config_size = len(json.dumps(export_profile_with_mode(
    "default", "sprint-123", "CONFIG_ONLY"
)))

full_size = len(json.dumps(export_profile_with_mode(
    "default", "sprint-123", "FULL_DATA"
)))

reduction = 1 - (config_size / full_size)
print(f"Size reduction: {reduction * 100:.1f}%")  # Should be > 90%
```

**Target**: Config-only 90% smaller than full data

---

## Next Steps After Implementation

1. **Run full test suite**: `pytest tests/ -v`
2. **Check code coverage**: `pytest --cov=data.import_export --cov=callbacks.import_export`
3. **Verify zero errors**: Use `get_errors` tool
4. **Manual smoke test**: All scenarios from checklist
5. **Update documentation**: Add examples to readme if needed
6. **Git commit**: Follow conventional commits format

---

## Questions & Support

**Architecture Questions**: See `.specify/memory/constitution.md`  
**Coding Standards**: See `.github/copilot-instructions.md`  
**Testing Patterns**: See `tests/unit/data/test_import_export.py` (existing)  
**UI Patterns**: See `ui/settings.py` (existing modals)  

---

## Summary

**Implementation Order**:
1. Data layer functions (1 hour)
2. UI components (30 min)
3. Callbacks (1 hour)
4. Tests (30 min)

**Key Files**:
- `data/import_export.py` - Core logic
- `callbacks/import_export.py` - Event handlers
- `ui/settings.py` - UI components
- `tests/unit/data/test_import_export.py` - Unit tests

**Remember**:
- Business logic in data layer
- Callbacks delegate to data layer
- Deep copy before mutating
- Validate early, fail with helpful messages
- Default to secure options (token excluded)

Estimated total time: **2-3 hours** for experienced developer familiar with codebase.
