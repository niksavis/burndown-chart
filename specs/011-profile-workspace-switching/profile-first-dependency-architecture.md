# Plan: Redesign Configuration Settings with Profile-First Dependency Architecture

**TL;DR**: Restructure configuration UI and data model to enforce hierarchical dependencies: Profile (auto-created) → JIRA Config → Field Mappings → Queries (saved before execution) → Data Files (1:1 with queries). Settings like PERT factor, deadline, and field mappings stored at profile level. Cascade deletion: Profile → all queries → all data files.

## Ambiguity Resolutions

All ambiguities have been resolved with the following decisions:

### Critical Decisions (1-15)

**1. Query-Data Binding Enforcement Location**: Both UI (disable button) AND data layer (raise DependencyError). UI prevents user error, data layer prevents API misuse.

**2. "Save Query" Behavior**: Only saves query.json metadata (name, JQL, description). Does NOT trigger data fetch. "Update Data" is separate action.

**3. Default Query Auto-Creation Timing**: On app startup if profile has 0 queries (Step 3 of `ensure_valid_workspace()`). Profile can temporarily exist with 0 queries during creation, but app startup fixes this.

**4. Field Mappings - Optional or Required**: Optional for query creation (soft requirement). User gets warning but can proceed. DORA/Flow metrics unavailable without mappings, basic statistics still work.

**5. Migration File Handling**: 
- Root `app_settings.json` → migrated to `profiles/default/profile.json`, then archived to `_migrated_backup/`
- Profile-level `app_settings.json` (if exists) → deprecated, redirect reads to `profile.json`
- After migration: Only `profile.json` is active source of truth

**6. Cascade Deletion Safety**: Add optional `allow_cascade: bool = False` parameter to `delete_query()`. When True, skips "cannot delete active query" check. On partial failure, log errors but continue deleting remaining queries (best-effort cleanup).

**7. Configuration Status "Complete" Definition**: Use persistent `configured=true` flag in `jira_config`, NOT transient test result. Flag set when test succeeds, cleared when config changes. This prevents UI flapping on network issues.

**8. Profile Settings Save Scope**: "Save Profile Settings" button saves only `forecast_settings` section (PERT, deadline, data points, milestone). JIRA config and field mappings have separate save buttons in their respective sections.

**9. JQL Editor State Management**: Track "dirty" flag via callback comparing `jql-query-input.value` with `active_query.jql`. On every change, disable "Update Data" button and show "unsaved changes" warning. Prompt user before navigating away if dirty=true.

**10. Mobile Accordion Current Step**: Auto-expand first incomplete step based on `configuration-status-store`. If all complete, collapse all. User can manually expand any section.

**11. Smart Defaults Integration Timing**: On-demand via "Auto-detect Fields" button in Field Mappings section (after JIRA connection succeeds). Also pre-fill placeholders in JIRA config modal.

**12. Error Recovery from Failed Migration**: Show error alert with manual recovery instructions. Do NOT auto-retry (prevents infinite loops). User can retry by deleting `profiles.json` and restarting app.

**13. Multi-Profile Query Naming**: Query names unique per profile only (case-insensitive). Different profiles can have queries with same name. Query IDs are globally unique.

**14. Active Query Persistence**: Stored in `profile.json` as `active_query_id`. Each profile remembers its own active query. Switching profiles loads that profile's last active query.

**15. Data Operations Section Content**: Contains buttons for "Update Data" (JIRA fetch) and "Calculate Metrics" (DORA/Flow). Also shows last update timestamp and cache status. Future: Add "Clear Cache", "Export Data".

### Technical Implementation Details (16-24)

**16. Profile ID Generation**: Slugified name with uniqueness counter. Examples: `default`, `apache-kafka`, `team-alpha-2`. Function: `slugify(name) + optional_counter`.

**17. Query ID Generation**: Slugified name scoped to profile. Examples: `default-query`, `last-12-weeks`, `bugs-only-2`. Function: `slugify(name) + optional_counter`.

**18. Directory Structure After Migration**:
```
ROOT LEVEL:
├─ profiles.json (NEW - registry)
├─ profiles/ (NEW - all profile workspaces)
└─ _migrated_backup/ (NEW - archived old files)
   ├─ app_settings.json.backup
   ├─ jira_cache.json.backup
   ├─ project_data.json.backup
   └─ jira_query_profiles.json.backup

MOVED TO PROFILE:
profiles/default/
├─ profile.json (NEW - all settings from app_settings.json)
└─ queries/default-query/
   ├─ query.json (NEW)
   ├─ jira_cache.json (MOVED from root)
   ├─ jira_changelog_cache.json (MOVED from root)
   ├─ project_data.json (MOVED from root)
   ├─ metrics_snapshots.json (MOVED from root)
   └─ cache/ (MOVED from root/cache/)
      └─ *.json
```

**19. Backward Compatibility Period**: Permanent fallback for `load_app_settings()` - checks `profile.json` first, falls back to `app_settings.json` if profile.json missing. This allows rollback to pre-v5.0 if needed. `app_settings.json` never re-created after migration.

**20. Profile.json vs app_settings.json Coexistence**: After migration, only `profile.json` exists in profile directory. `app_settings.json` deleted from root (archived to `_migrated_backup/`). No coexistence - clean cutover.

**21. Atomic Query Switch with Missing Files**: Fail entire switch if ANY required file missing/corrupted. Show error: "Query data incomplete. Try 'Update Data' to rebuild cache." Do NOT partially load query.

**22. Profile/Query Name Validation**:
- Max length: 50 characters
- Allowed: Letters, numbers, spaces, hyphens, underscores
- Forbidden: `/ \ : * ? " < > |` (filesystem unsafe chars)
- Reserved: `default` (profile), `default-query` (query), `new`, `temp`
- Case-insensitive uniqueness check

**23. Concurrent Access Handling**: No special handling in v5.0 (single-user app assumption). Add file locking in future if multi-user/multi-tab support needed. If query deleted in another tab, show error on switch attempt.

**24. Cache Invalidation Across Queries**: Changing JIRA config (base_url, token) invalidates ALL query caches in profile. Changing field mappings does NOT invalidate cache (only affects metric calculations). Implemented via `invalidate_profile_caches(profile_id)` function.

### UI/UX Behavior (25-28)

**25. Accordion Section Interaction**: Disabled sections are clickable to expand, showing locked state message: "🔒 Complete [previous step] to unlock this section." User can see what's coming next but cannot interact with form fields.

**26. "Update Data" Button Placement**: Single button in Section 4 (Query Management) that is ALSO mirrored in Section 5 (Data Operations). Both buttons trigger same callback. Section 5 shows additional context (last update time, cache size).

**27. Query Selector Behavior on Query Delete**: Auto-switch to first remaining query in profile. If no queries left (should not happen - enforced by validation), create default query automatically.

**28. Profile Selector Behavior on Profile Delete**: Auto-switch to "Default" profile. If "Default" was deleted (should not happen - enforced by validation), create new "Default" profile automatically.

### Settings Inheritance & Overrides (29-30)

**29. Query-Level Settings Override**: NOT supported in v5.0. All settings at profile level only. Future enhancement could add query-level overrides with explicit UI (e.g., "Use profile PERT" checkbox with override field).

**30. Default Values Hierarchy**: Hardcoded constants in `configuration/settings.py`:
```python
DEFAULT_PERT_FACTOR = 1.2
DEFAULT_DATA_POINTS_COUNT = 12
DEFAULT_DEADLINE_MONTHS = 6  # +6 months from today
```
Used by `ensure_default_profile_exists()`. No template inheritance from existing profiles.

### Error States & Edge Cases (31-34)

**31. JIRA Connection Flapping**: Field mapping section stays unlocked once unlocked (use persistent `configured` flag). Show warning banner if connection currently down: "⚠️ JIRA unreachable. Saved mappings preserved, but cannot auto-detect new fields."

**32. Empty Query Results**: Valid state. Query returns 0 issues = empty dataset. Dashboard shows "No data available" message. "Calculate Metrics" button disabled (nothing to calculate). "Update Data" button enabled (user can refetch).

**33. Incomplete Field Mappings**: Query executable with partial mappings. Metrics affected:
- DORA: Requires `deployment_date` minimum. Missing = "DORA metrics unavailable" message.
- Flow: Requires `flow_item_type` + `work_completed_date` minimum. Missing = "Flow metrics unavailable".
- Statistics: Always available (uses JIRA standard fields only).

Show per-metric status indicators in dashboard.

**34. Query Validation Timing**: Async validation on blur (user leaves JQL field). Debounced (500ms) validation on keystroke (live syntax check). Full validation on save. Validation checks: JQL syntax valid, estimated result count <10,000 (warn if higher).

### Testing & Verification (35-36)

**35. Test Data Fixtures**: Use fixture JSON files for cache (no real JIRA server needed). Mock `jira_simple.fetch_all_issues()` to return fixture data. For connection tests, mock requests.get() to return success/failure. Integration tests use `tempfile.TemporaryDirectory()` for isolated profile workspaces.

**36. Performance Benchmarks**:
- **Settings panel load**: Measured from page navigation to DOMContentLoaded event. Target <500ms.
- **Query switch**: Measured from dropdown change to dashboard chart re-render complete. Target <50ms. Excludes network time (cache hit assumed).
- Measured via `performance.mark()` / `performance.measure()` in browser, logged to console.

### Minor Design Decisions (37-40)

**37. Status Icons Consistency**: Use emoji for status (✅ ⏳ 🔒 ❌ ⚠️) + Font Awesome for actions. Rationale: Emoji work without icon library loading, accessible across all devices.

**38. Button Icon Conventions**: Use Font Awesome for all buttons to match existing UI. Examples: `fa-save` (save), `fa-sync` (update), `fa-times` (cancel). Emoji in accordion titles only.

**39. Section Numbering Visibility**: Numbers visible in UI (part of accordion title). Reinforces dependency sequence. Mobile: Numbers larger and bold (primary color).

**40. Mobile Breakpoint Definition**: Use Bootstrap's md breakpoint (768px) to trigger mobile layout. Matches existing app responsive design. Below 768px: Single-column stack, larger touch targets, auto-expand first incomplete step.

---

## Requirements Summary

### Hierarchical Model (1-n-1-1)

```
Application
└─ 1 to n: PROFILES
   ├─ Profile Settings (shared by all queries)
   │  ├─ Forecast: PERT factor, deadline, data points, milestone, confidence window
   │  ├─ JIRA Config: base_url, token, API version, cache settings, points_field
   │  └─ Field Mappings: DORA fields, Flow fields, project classification, statuses
   │
   └─ 0 to n: QUERIES (per profile)
      ├─ Query Metadata: name, JQL string, timestamps
      │
      └─ 1:1 DATA FILES (per query)
         ├─ jira_cache.json (JIRA API responses)
         ├─ project_data.json (statistics, scope)
         ├─ metrics_snapshots.json (DORA/Flow metrics)
         └─ cache/*.json (metric calculation cache)
```

### Dependency Chain (Must Enforce)

```
Step 1: PROFILE EXISTS
   ↓ (auto-create "Default" on first run)
Step 2: JIRA CONFIGURED (requires profile to store config)
   ↓ (validate connection works)
Step 3: FIELD MAPPINGS (optional, but recommended)
   ↓
Step 4: QUERY CREATED & SAVED (requires profile + JIRA)
   ↓ (query MUST be saved before execution)
Step 5: EXECUTE "Update Data" (fetches JIRA, saves to query workspace)
   ↓
Step 6: EXECUTE "Calculate Metrics" (computes DORA/Flow, saves to query workspace)
```

### Critical Rules

1. **Profile-First**: Cannot configure JIRA without a profile (need somewhere to save config)
2. **Query-Data Binding**: Cannot execute "Update Data" without a saved query (need to know where to save cache)
3. **Query Selection**: When switching queries, load that query's data files into app
4. **Cascade Deletion**: Deleting profile → deletes all queries → deletes all data files
5. **Profile-Level Settings**: PERT, deadline, JIRA config, field mappings shared across all queries in profile

## Implementation Steps

### Step 1: Update Data Model - Move Settings to Profile Level

**Files**: `data/persistence.py`, `data/profile_manager.py`

**Changes**:
- Migrate `pert_factor`, `deadline`, `data_points_count`, `milestone`, `show_milestone`, `show_points` from `app_settings.json` to `profile.json`
- Migrate `jira_config` (entire object) from `app_settings.json` to `profile.json`
- Migrate `field_mappings` (entire object) from `app_settings.json` to `profile.json`
- Migrate all project classification arrays (`development_projects`, `devops_projects`, `devops_task_types`, `bug_types`, etc.) to `profile.json`
- Update `Profile.to_dict()` to serialize all settings sections
- Update `Profile.from_dict()` to deserialize all settings sections
- Implement `ensure_default_profile_exists()` for auto-creation on first run with defaults:
  - `pert_factor`: 1.2
  - `deadline`: +6 months from today
  - `data_points_count`: 12
  - `show_milestone`: false
  - `show_points`: true
  - `jira_config`: empty but structured (base_url="", token="", configured=false)
  - `field_mappings`: empty but structured

**New Profile Structure** (`profiles/{profile_id}/profile.json`):
```json
{
  "id": "default",
  "name": "Default",
  "description": "Default workspace for JIRA analysis",
  "version": "5.0",
  "created_at": "2025-11-14T10:00:00Z",
  "last_used": "2025-11-14T15:30:00Z",
  
  "forecast_settings": {
    "pert_factor": 1.2,
    "deadline": "2026-05-14",
    "data_points_count": 12,
    "show_milestone": false,
    "milestone": null,
    "show_points": true
  },
  
  "jira_config": {
    "base_url": "",
    "api_version": "v3",
    "token": "",
    "cache_size_mb": 100,
    "max_results_per_call": 100,
    "points_field": "customfield_10016",
    "configured": false,
    "last_test_timestamp": null,
    "last_test_success": false
  },
  
  "field_mappings": {
    "deployment_date": "resolutiondate",
    "target_environment": "environment",
    "flow_item_type": "issuetype",
    "work_started_date": "created",
    "work_completed_date": "resolutiondate",
    "status": "status"
  },
  
  "project_classification": {
    "devops_projects": [],
    "development_projects": ["YOUR_PROJECT"],
    "devops_task_types": ["Task", "Sub-task"],
    "bug_types": ["Bug"],
    "production_environment_values": [],
    "completion_statuses": ["Resolved", "Closed"],
    "active_statuses": ["In Progress", "In Review"],
    "flow_start_statuses": ["In Progress"],
    "wip_statuses": ["In Progress", "In Review", "Testing"]
  },
  
  "flow_type_mappings": {
    "Feature": {
      "issue_types": ["Story", "Epic", "New Feature"],
      "effort_categories": []
    },
    "Defect": {
      "issue_types": ["Bug"],
      "effort_categories": []
    }
  },
  
  "queries": ["default-query"],
  "active_query_id": "default-query"
}
```

**Backward Compatibility**:
- Keep `load_app_settings()` but redirect to load from `profile.json` instead of `app_settings.json`
- Keep `save_app_settings()` but redirect to save to `profile.json` instead
- Deprecate `app_settings.json` after migration (archive to `_migrated_backup/`)

### Step 2: Enforce Dependency Chain in Query Management

**Files**: `data/query_manager.py`

**Changes**:
- Update `create_query()` to validate JIRA configured before allowing query creation:
  ```python
  def create_query(profile_id: str, name: str, jql: str, description: str = "") -> str:
      # Dependency check: JIRA must be configured
      profile = get_profile(profile_id)
      if not profile.jira_config.get("configured"):
          raise DependencyError("JIRA must be configured before creating queries. "
                              "Go to JIRA Configuration section and test connection first.")
      
      # Optionally warn if fields not mapped
      if not profile.field_mappings:
          logger.warning("Field mappings not configured - metrics may be limited")
      
      # Create query...
  ```

- Add query validation before data operations:
  ```python
  def validate_query_exists_for_data_operation(profile_id: str, query_id: str) -> None:
      """Ensure query is saved before allowing data fetch/calculation."""
      queries = list_queries_for_profile(profile_id)
      if query_id not in [q.id for q in queries]:
          raise DependencyError("Query must be saved before executing data operations. "
                              "Click 'Save Query' first, then 'Update Data'.")
  ```

- Update `delete_query()` to delete all data files:
  ```python
  def delete_query(profile_id: str, query_id: str) -> None:
      # Validate safety checks
      if query_id == get_active_query_id():
          raise ValueError("Cannot delete active query. Switch to another query first.")
      
      queries = list_queries_for_profile(profile_id)
      if len(queries) == 1:
          raise ValueError("Cannot delete the only query. Create another query first.")
      
      # Delete query directory (includes query.json and all data files)
      query_dir = PROFILES_DIR / profile_id / "queries" / query_id
      shutil.rmtree(query_dir)
      
      # Remove from profile.json queries list
      profile = get_profile(profile_id)
      profile.queries.remove(query_id)
      save_profile(profile)
  ```

### Step 3: Restructure Settings Panel UI with Progressive Disclosure

**Files**: `ui/settings_panel.py`, create new `ui/profile_settings_card.py`

**Changes**:
- Restructure `create_settings_panel()` to show 5-section accordion with dependency indicators:

```python
def create_settings_panel() -> html.Div:
    """Settings panel with progressive dependency disclosure."""
    
    return html.Div([
        # Configuration status store (updated by callback)
        dcc.Store(id="configuration-status-store", data={}),
        
        dbc.Accordion([
            # Section 1: Profile Management (ALWAYS ENABLED)
            dbc.AccordionItem([
                create_profile_settings_card(),
            ], title="1. Profile Settings", id="profile-section-accordion"),
            
            # Section 2: JIRA Configuration (ENABLED WHEN PROFILE EXISTS)
            dbc.AccordionItem([
                html.Div(id="jira-config-section-content", children=[
                    create_jira_config_card(),
                ]),
            ], title="2. JIRA Configuration", id="jira-section-accordion"),
            
            # Section 3: Field Mappings (ENABLED WHEN JIRA CONNECTED)
            dbc.AccordionItem([
                html.Div(id="field-mapping-section-content", children=[
                    create_field_mapping_card(),
                ]),
            ], title="3. Field Mappings", id="field-mapping-section-accordion"),
            
            # Section 4: Query Management (ENABLED WHEN JIRA CONFIGURED)
            dbc.AccordionItem([
                html.Div(id="query-management-section-content", children=[
                    create_query_management_card(),  # Integrated JQL editor
                ]),
            ], title="4. Query Management", id="query-section-accordion"),
            
            # Section 5: Data Actions (ENABLED WHEN QUERY SAVED)
            dbc.AccordionItem([
                html.Div(id="data-actions-section-content", children=[
                    create_data_actions_card(),
                ]),
            ], title="5. Data Operations", id="data-actions-section-accordion"),
        ], id="settings-accordion", always_open=False, start_collapsed=False),
        
        # Status indicators
        html.Div(id="dependency-status-display", className="mt-3"),
    ])
```

**New Profile Settings Card** (`ui/profile_settings_card.py`):
```python
def create_profile_settings_card() -> dbc.Card:
    """Profile-level settings: PERT, deadline, data points, milestone."""
    return dbc.Card([
        dbc.CardHeader("Profile Settings"),
        dbc.CardBody([
            # Profile selector (existing component)
            create_profile_selector(),
            
            html.Hr(),
            
            # Forecast settings (moved from dashboard settings)
            dbc.Row([
                dbc.Col([
                    dbc.Label("PERT Factor"),
                    dbc.Input(
                        id="profile-pert-factor-input",
                        type="number",
                        min=1.0, max=3.0, step=0.1,
                        value=1.2,
                        placeholder="1.2"
                    ),
                    dbc.FormText("Multiplier for forecast calculations (1.0-3.0)")
                ], md=4),
                
                dbc.Col([
                    dbc.Label("Project Deadline"),
                    dbc.Input(
                        id="profile-deadline-input",
                        type="date",
                        placeholder="YYYY-MM-DD"
                    ),
                    dbc.FormText("Target completion date")
                ], md=4),
                
                dbc.Col([
                    dbc.Label("Data Points"),
                    dbc.Input(
                        id="profile-data-points-input",
                        type="number",
                        min=4, max=52,
                        value=12,
                        placeholder="12"
                    ),
                    dbc.FormText("Weeks to show in charts (4-52)")
                ], md=4),
            ]),
            
            html.Hr(),
            
            dbc.Row([
                dbc.Col([
                    dbc.Checkbox(
                        id="profile-show-milestone-checkbox",
                        label="Show Milestone",
                        value=False
                    ),
                ], md=4),
                dbc.Col([
                    dbc.Input(
                        id="profile-milestone-input",
                        type="date",
                        placeholder="Milestone date",
                        disabled=True
                    ),
                ], md=8),
            ]),
            
            html.Hr(),
            
            dbc.Button("Save Profile Settings", id="save-profile-settings-btn", color="primary"),
            html.Div(id="profile-settings-status"),
        ])
    ])
```

**Integrated Query Management Card** (merge JQL editor into query management):
```python
def create_query_management_card() -> dbc.Card:
    """Query management with integrated JQL editor."""
    return dbc.Card([
        dbc.CardHeader("Query Management"),
        dbc.CardBody([
            # Query selector
            create_query_selector(),
            
            html.Hr(),
            
            # Integrated JQL editor (no longer separate section)
            dbc.Label("Query Configuration"),
            dbc.Input(
                id="query-name-input",
                type="text",
                placeholder="Query name",
                className="mb-2"
            ),
            dbc.Textarea(
                id="query-description-input",
                placeholder="Optional description",
                rows=2,
                className="mb-2"
            ),
            
            # JQL Editor (CodeMirror)
            html.Div(id="jql-editor-container", children=[
                dcc.Textarea(
                    id="jql-query-input",
                    placeholder="project = EXAMPLE AND created >= -12w",
                    style={"width": "100%", "height": "120px"}
                ),
            ]),
            
            html.Div(id="jql-validation-feedback", className="mt-2"),
            
            # Action buttons
            dbc.ButtonGroup([
                dbc.Button("💾 Save Query", id="save-query-btn", color="success"),
                dbc.Button("🔄 Update Data", id="update-data-btn", color="primary", disabled=True),
                dbc.Button("❌ Cancel", id="cancel-query-edit-btn", color="secondary", outline=True),
            ], className="mt-3"),
            
            html.Hr(),
            
            # Query metadata display
            html.Div(id="query-metadata-display"),
        ])
    ])
```

### Step 4: Implement Cascade Deletion

**Files**: `data/profile_manager.py`

**Changes**:
- Update `delete_profile()` to cascade delete all queries and data:

```python
def delete_profile(profile_id: str) -> None:
    """Delete profile and all associated queries/data."""
    
    # Validation: Cannot delete active profile
    active_profile_id = get_active_profile_id()
    if profile_id == active_profile_id:
        raise ValueError("Cannot delete active profile. Switch to another profile first.")
    
    # Validation: Cannot delete last remaining profile
    all_profiles = list_profiles()
    if len(all_profiles) == 1:
        raise ValueError("Cannot delete the only profile. Create another profile first.")
    
    # Step 1: Delete all queries (cascade to data files)
    queries = list_queries_for_profile(profile_id)
    for query in queries:
        try:
            # Temporarily allow deleting active query during cascade
            delete_query(profile_id, query.id, allow_cascade=True)
        except Exception as e:
            logger.error(f"Error deleting query {query.id}: {e}")
            # Continue deleting other queries
    
    # Step 2: Delete profile directory
    # This removes profile.json and any remaining files
    profile_dir = PROFILES_DIR / profile_id
    if profile_dir.exists():
        shutil.rmtree(profile_dir)
        logger.info(f"Deleted profile directory: {profile_dir}")
    
    # Step 3: Remove from profiles registry
    metadata = load_profiles_metadata()
    if profile_id in metadata.get("profiles", {}):
        del metadata["profiles"][profile_id]
        save_profiles_metadata(metadata)
        logger.info(f"Removed profile {profile_id} from registry")
    
    logger.info(f"Profile {profile_id} and all associated data deleted successfully")
```

**What Gets Deleted**:
```
profiles/kafka/
├─ profile.json ← DELETE (all profile-level settings)
└─ queries/
   ├─ query-12w/ ← DELETE ALL
   │  ├─ query.json
   │  ├─ jira_cache.json
   │  ├─ project_data.json
   │  ├─ metrics_snapshots.json
   │  └─ cache/*.json
   ├─ query-52w/ ← DELETE ALL
   └─ query-bugs/ ← DELETE ALL
```

### Step 5: Add Startup Initialization

**Files**: `app.py`

**Changes**:
- Add `ensure_valid_workspace()` call before app initialization:

```python
# app.py (add near top, before create_app())

from data.profile_manager import ensure_default_profile_exists
from data.query_manager import create_default_query
from data.persistence import get_active_profile, get_active_query

def ensure_valid_workspace():
    """Ensure app has valid profile + query foundation."""
    
    # Step 1: Ensure default profile exists
    if not profile_exists("default"):
        logger.info("First run: Creating default profile")
        ensure_default_profile_exists()
    
    # Step 2: Ensure active profile is set
    active_profile = get_active_profile()
    if not active_profile:
        logger.info("No active profile: Switching to default")
        switch_to_profile("default")
        active_profile = get_active_profile()
    
    # Step 3: Ensure profile has at least one query
    queries = list_queries_for_profile(active_profile.id)
    if not queries:
        logger.info("No queries in profile: Creating default query")
        create_default_query(
            profile_id=active_profile.id,
            name="Default Query",
            jql="project = EXAMPLE AND created >= -12w ORDER BY created DESC",
            description="Default query for getting started"
        )
    
    # Step 4: Ensure active query is set
    active_query = get_active_query()
    if not active_query:
        logger.info("No active query: Switching to first query")
        first_query = queries[0] if queries else None
        if first_query:
            switch_to_query(active_profile.id, first_query.id)
    
    logger.info("Workspace validation complete")

# Call during app initialization
ensure_valid_workspace()
app = create_app()
```

**Default Values**:
- `pert_factor`: 1.2 (conservative baseline)
- `deadline`: 6 months from today (datetime.now() + timedelta(days=180))
- `data_points_count`: 12 (3 months of weekly data)
- `show_milestone`: False
- `show_points`: True

### Step 6: Update Callbacks for Dependency Enforcement

**Files**: `callbacks/settings_panel.py`, `callbacks/query_management.py`

**New Callback: Configuration Status Tracker**:
```python
@callback(
    Output("configuration-status-store", "data"),
    [Input("profile-selector", "value"),
     Input("jira-test-connection-result", "data"),
     Input("field-mappings-store", "data"),
     Input("active-query-store", "data")],
    prevent_initial_call=False
)
def update_configuration_status(profile_id, jira_test_result, field_mappings, active_query):
    """Track configuration completion status for dependency chain."""
    
    status = {
        "profile": {
            "enabled": True,
            "complete": profile_id is not None,
            "icon": "✅" if profile_id else "⏳"
        },
        
        "jira": {
            "enabled": profile_id is not None,
            "complete": jira_test_result and jira_test_result.get("success", False),
            "icon": "✅" if (jira_test_result and jira_test_result.get("success")) else 
                   ("⏳" if profile_id else "🔒")
        },
        
        "fields": {
            "enabled": jira_test_result and jira_test_result.get("success", False),
            "complete": field_mappings and len(field_mappings) > 0,
            "icon": "✅" if (field_mappings and len(field_mappings) > 0) else
                   ("⏳" if (jira_test_result and jira_test_result.get("success")) else "🔒")
        },
        
        "queries": {
            "enabled": jira_test_result and jira_test_result.get("success", False),
            "complete": active_query is not None,
            "icon": "✅" if active_query else
                   ("⏳" if (jira_test_result and jira_test_result.get("success")) else "🔒")
        },
        
        "data_operations": {
            "enabled": active_query is not None,
            "complete": False,  # Always requires manual trigger
            "icon": "⏳" if active_query else "🔒"
        }
    }
    
    return status
```

**Updated Callback: Enable/Disable Sections**:
```python
@callback(
    [Output("jira-section-accordion", "className"),
     Output("field-mapping-section-accordion", "className"),
     Output("query-section-accordion", "className"),
     Output("data-actions-section-accordion", "className")],
    Input("configuration-status-store", "data"),
    prevent_initial_call=False
)
def update_section_states(config_status):
    """Enable/disable accordion sections based on dependencies."""
    
    if not config_status:
        return "disabled", "disabled", "disabled", "disabled"
    
    jira_class = "" if config_status["jira"]["enabled"] else "disabled"
    fields_class = "" if config_status["fields"]["enabled"] else "disabled"
    queries_class = "" if config_status["queries"]["enabled"] else "disabled"
    data_class = "" if config_status["data_operations"]["enabled"] else "disabled"
    
    return jira_class, fields_class, queries_class, data_class
```

**Updated Callback: Save Query Before Data Operations**:
```python
@callback(
    [Output("update-data-btn", "disabled"),
     Output("query-must-be-saved-alert", "children")],
    [Input("save-query-btn", "n_clicks"),
     Input("jql-query-input", "value")],
    State("active-query-store", "data"),
    prevent_initial_call=False
)
def enforce_query_save_before_data_ops(save_clicks, jql_value, active_query):
    """Disable 'Update Data' until query is saved."""
    
    # If query exists and hasn't been modified, enable data ops
    if active_query and active_query.get("jql") == jql_value:
        return False, None  # Enabled, no alert
    
    # If JQL has been modified or no query exists, disable data ops
    alert = dbc.Alert(
        "Query must be saved before fetching data. Click 'Save Query' first.",
        color="warning",
        className="mt-2"
    )
    return True, alert  # Disabled, show alert
```

## Further Considerations

### 1. Migration Strategy for Existing Users

**Problem**: Existing users have settings in `app_settings.json` at root level and profile level.

**Solution**: Create migration function that runs on first launch after upgrade:

```python
def migrate_existing_installation():
    """Migrate pre-v5.0 installation to profile-based architecture."""
    
    # Check if migration needed (profiles.json doesn't exist)
    if PROFILES_FILE.exists():
        logger.info("Profiles already exist, skipping migration")
        return
    
    logger.info("Starting migration to profile-based architecture...")
    
    # Step 1: Create default profile
    ensure_default_profile_exists()
    
    # Step 2: Migrate settings from app_settings.json to profile.json
    root_settings_file = Path("app_settings.json")
    if root_settings_file.exists():
        with open(root_settings_file, "r") as f:
            old_settings = json.load(f)
        
        # Extract profile-level settings
        profile = get_profile("default")
        profile.forecast_settings = {
            "pert_factor": old_settings.get("pert_factor", 1.2),
            "deadline": old_settings.get("deadline"),
            "data_points_count": old_settings.get("data_points_count", 12),
            "show_milestone": old_settings.get("show_milestone", False),
            "milestone": old_settings.get("milestone"),
            "show_points": old_settings.get("show_points", True)
        }
        profile.jira_config = old_settings.get("jira_config", {})
        profile.field_mappings = old_settings.get("field_mappings", {})
        # ... migrate all other settings
        
        save_profile(profile)
        logger.info("Migrated settings to default profile")
        
        # Archive old settings file
        backup_dir = Path("_migrated_backup")
        backup_dir.mkdir(exist_ok=True)
        shutil.copy(root_settings_file, backup_dir / "app_settings.json.backup")
        root_settings_file.unlink()
        logger.info("Archived old app_settings.json")
    
    # Step 3: Migrate existing queries (if any)
    # ... similar pattern for jira_query_profiles.json
    
    logger.info("Migration complete!")
```

**Call in `app.py`**:
```python
# Before ensure_valid_workspace()
migrate_existing_installation()
ensure_valid_workspace()
```

### 2. Reuse Enhanced Concept Components

**Integration Points**:

1. **Smart Defaults** (`data/smart_defaults.py`) - Use in JIRA config modal:
   ```python
   # When JIRA config modal opens
   @callback(Output("jira-base-url-input", "placeholder"), ...)
   def suggest_jira_url():
       defaults = get_smart_jira_defaults()
       return defaults["common_jira_urls"][0]  # "https://jira.example.com"
   ```

2. **Error Handling** (`data/error_handling.py`) - Use in settings callbacks:
   ```python
   try:
       create_query(profile_id, name, jql)
   except DependencyError as e:
       setup_status = get_configuration_status()
       contextual_error = analyze_error_with_context(e, setup_status, "create_query")
       return dbc.Alert(contextual_error.remediation_steps, color="warning")
   ```

3. **Documentation** (`data/documentation.py`) - Use for tooltips:
   ```python
   # Add help icon next to PERT factor input
   dbc.Label([
       "PERT Factor ",
       html.I(
           className="fas fa-question-circle",
           id="pert-factor-help-icon",
           style={"cursor": "pointer"}
       )
   ]),
   dbc.Tooltip(
       get_progressive_help("pert_factor", user_level="beginner"),
       target="pert-factor-help-icon"
   )
   ```

### 3. Mobile-Responsive Dependency UI

**Design Approach**:
- Use Bootstrap accordion (already responsive)
- Stack sections vertically on mobile (<768px)
- Use numbered steps (1→5) as accordion titles
- Add visual indicators (✅ ⏳ 🔒) before titles
- Collapse all except current step on mobile

**Example Mobile Layout**:
```python
def create_mobile_friendly_accordion_title(step_num, title, status_icon):
    """Create accordion title with step number and status."""
    return html.Div([
        html.Span(f"{step_num}. ", className="step-number"),
        html.Span(status_icon, className="status-icon me-2"),
        html.Span(title, className="step-title")
    ], className="d-flex align-items-center")

# Use in accordion items
dbc.AccordionItem(
    [...],
    title=create_mobile_friendly_accordion_title(1, "Profile Settings", "✅"),
    id="profile-section"
)
```

**CSS for Mobile** (`assets/custom.css`):
```css
@media (max-width: 767px) {
    .accordion .step-number {
        font-size: 1.2rem;
        font-weight: bold;
        color: var(--bs-primary);
    }
    
    .accordion .status-icon {
        font-size: 1.1rem;
    }
    
    .accordion-item.disabled {
        opacity: 0.5;
        pointer-events: none;
    }
    
    .accordion-item.disabled .accordion-button {
        background-color: var(--bs-gray-200);
        cursor: not-allowed;
    }
}
```

## Testing Strategy

### Auto-Setup Tests
1. **Fresh Install**: Delete `profiles/` directory → restart app → verify default profile created with reasonable defaults
2. **Missing Queries**: Delete queries from default profile → restart app → verify default query created
3. **Invalid Configuration**: Corrupt `profile.json` → restart app → verify auto-recovery creates new default

### Dependency Chain Tests
1. **Profile → JIRA**: Fresh profile → verify JIRA section enabled, others disabled
2. **JIRA → Fields**: Connect JIRA → verify fields section enabled
3. **Fields → Queries**: Map fields → verify queries section enabled
4. **Queries → Data**: Save query → verify "Update Data" button enabled
5. **Locked Sections**: Try to access locked sections → verify proper error messages shown

### Integration Tests
1. **Create Query Flow**: Create profile → configure JIRA → map fields → create query → verify query.json created in correct location
2. **Edit Query Flow**: Edit JQL in integrated editor → save → verify query.json updated but no data fetch triggered
3. **Data Operations Flow**: Click "Update Data" → verify JIRA API called → verify cache saved to query workspace
4. **Query Switch Flow**: Switch between queries → verify integrated editor updates → verify data files loaded from correct query workspace

### Cascade Deletion Tests
1. **Delete Profile**: Create profile with 3 queries → delete profile → verify all queries and data files deleted
2. **Prevent Active Deletion**: Try to delete active profile → verify error shown
3. **Prevent Last Profile Deletion**: Try to delete only profile → verify error shown

### Migration Tests
1. **Existing User Migration**: Set up pre-v5.0 structure (root `app_settings.json`) → start app → verify settings migrated to `profiles/default/profile.json`
2. **Preserve Data**: Ensure existing cache files moved to correct query workspace
3. **Backup Creation**: Verify old files archived to `_migrated_backup/`

## Success Criteria

1. ✅ **Auto-Creation**: Fresh install creates "Default" profile automatically with reasonable defaults
2. ✅ **Dependency Enforcement**: Cannot skip prerequisite steps (UI disables locked sections)
3. ✅ **Query-Data Binding**: Cannot execute "Update Data" without saved query (button disabled with clear message)
4. ✅ **Profile-Level Settings**: PERT, deadline, JIRA config stored in `profile.json`, shared by all queries
5. ✅ **Cascade Deletion**: Deleting profile removes all queries and data files
6. ✅ **Migration Success**: Existing users upgrade seamlessly without data loss
7. ✅ **Mobile Responsive**: Dependency chain clear on mobile (stacked accordion with status indicators)
8. ✅ **Performance**: Settings panel loads in <500ms, query switch in <50ms
