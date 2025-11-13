# Implementation Plan: Profile & Query Management System

**Branch**: `011-profile-workspace-switching` | **Date**: 2025-11-13 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-profile-workspace-switching/spec.md`

**Note**: This plan incorporates technical design from `concept.md` (v3.0 - Profile-Level Settings Model).

## Summary

**Primary Requirement**: Enable users to switch between different JIRA queries (time periods, filters, teams) without losing cached data and recalculating metrics, eliminating 3-6 minute context switch delays.

**Technical Approach**: Implement two-level hierarchy (Profile → Query) with strategic settings separation:
- **Profile** = Shared comparison settings (PERT factor, deadline, field mappings, JIRA config) stored at profile level
- **Query** = JQL variation with dedicated cache (jira_cache.json, project_data.json, metrics_snapshots.json)

**Key Innovation**: Profile-level settings ensure all queries within a profile use same PERT factor and deadline, enabling apples-to-apples comparison without reconfiguration.

**Performance Targets**: Query switch <50ms, profile switch <100ms, cache hit rate >90%

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: Dash (Plotly), Dash Bootstrap Components, Waitress (server)  
**Storage**: JSON files (profiles.json, profile configs, query configs, cache files)  
**Testing**: pytest (unit tests during implementation, integration tests post-implementation)  
**Target Platform**: Windows (PowerShell environment), PWA (Progressive Web App)  
**Project Type**: Web application (single-page Dash app with backend data layer)  
**Performance Goals**: 
- Query switch: <50ms (swap cache file pointers)
- Profile switch: <100ms (reload settings + most recent query)
- Cache hit rate: >90% (avoid JIRA API refetches)
- Migration: <5 seconds for 50MB cached data

**Constraints**: 
- Zero breaking changes to existing callbacks (backward compatibility via path abstraction)
- Must support 50 profiles × 100 queries without performance degradation
- Windows-only PowerShell commands (no Unix tools like grep, find, cat)
- Virtual environment activation required for all Python commands

**Scale/Scope**: 
- 50 profiles max per installation (prevent storage bloat)
- 100 queries max per profile
- Profile storage: ~5-50MB per profile (JIRA cache dependent)
- Total storage target: <500MB for typical multi-profile setup

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Layered Architecture ✅ PASS
- **Compliance**: Profile management logic in `data/profile_manager.py`, path abstraction in `data/persistence.py`
- **Callbacks**: `callbacks/profile_management.py` only handles UI events, delegates to `data/profile_manager.py`
- **Verification**: All profile operations (create, switch, delete) testable via unit tests in `tests/unit/data/`

### II. Test Isolation ✅ PASS
- **Compliance**: Migration tests will use `tempfile.TemporaryDirectory()` for profiles directory
- **Verification**: No tests create `profiles/` in project root - use `temp_profiles_dir` fixture
- **Example fixture**:
  ```python
  @pytest.fixture
  def temp_profiles_dir():
      with tempfile.TemporaryDirectory() as temp_dir:
          with patch("data.profile_manager.PROFILES_DIR", temp_dir):
              yield temp_dir
  ```

### III. Performance Budgets ✅ PASS
- **Query switch target**: <50ms (just swap active_query_id pointer)
- **Profile switch target**: <100ms (update active_profile_id, load most recent query)
- **Page load target**: <2s (existing target maintained)
- **Verification**: Performance tests in `tests/integration/test_profile_switching_workflow.py`

### IV. Simplicity & Reusability ✅ PASS
- **KISS**: Profile model simpler than v2.0 workspace model (settings at profile level, not query level)
- **DRY**: Path abstraction (`get_profile_file_path()`) reused across all persistence operations
- **Reusability**: `Profile` class reusable for import/export features (Phase 2)

### V. Data Privacy & Security ✅ PASS
- **Compliance**: Profile exports will strip JIRA credentials (token field removed)
- **Validation**: Profile creation UI uses placeholder examples ("Example Organization", "example.com")
- **Documentation**: concept.md already uses generic examples (Apache Kafka, Example Company)

### VI. Defensive Refactoring ⚠️ REVIEW NEEDED
- **Potential issue**: Migration may leave unused `jira_query_profiles.json` at root level
- **Action**: Add cleanup step to migration that archives obsolete files to `_migrated_backup/`
- **Verification**: After migration, root should only contain `profiles.json` and `profiles/` directory

**GATE STATUS**: ✅ All checks pass (with minor refactoring note for Phase 3)

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# New directory structure for profiles
profiles/                                     # NEW: Root profiles directory
├── profiles.json                            # NEW: Profiles registry (active IDs, metadata)
├── profile-{id}/                            # NEW: Individual profile workspace
│   ├── profile.json                         # NEW: Profile config (PERT, deadline, JIRA, field mappings)
│   └── queries/                             # NEW: Queries within profile
│       ├── query-{id}/                      # NEW: Individual query workspace
│       │   ├── query.json                   # NEW: Query config (JQL only)
│       │   ├── project_data.json            # MOVED: Query-specific statistics
│       │   ├── jira_cache.json              # MOVED: Query-specific JIRA cache
│       │   ├── jira_changelog_cache.json    # MOVED: Query-specific changelog cache
│       │   ├── metrics_snapshots.json       # MOVED: Query-specific DORA/Flow snapshots
│       │   └── cache/                       # MOVED: Query-specific metric calculation cache
│       │       └── *.json
│       └── query-{id2}/                     # Additional queries...
└── default/                                 # NEW: Default profile (migration target)
    └── [same structure as profile-{id}]

# Modified files for profile support
data/
├── profile_manager.py                       # NEW: Profile lifecycle (create, switch, delete, duplicate)
├── query_manager.py                         # NEW: Query lifecycle operations
├── persistence.py                           # MODIFIED: Add path abstraction (get_profile_file_path)
├── processing.py                            # EXISTING: No changes (uses persistence layer)
├── jira_simple.py                           # EXISTING: No changes (uses persistence layer)
└── [other data modules]                     # EXISTING: No changes

callbacks/
├── profile_management.py                    # NEW: Profile/query switching callbacks
├── dashboard.py                             # EXISTING: No changes (uses persistence layer)
└── [other callback modules]                 # EXISTING: No changes

ui/
├── profile_selector.py                      # NEW: Profile dropdown + management buttons
├── query_selector.py                        # NEW: Query dropdown + management buttons
├── profile_create_modal.py                  # NEW: Profile creation modal dialog
├── query_create_modal.py                    # NEW: Query creation modal dialog
└── [existing UI modules]                    # EXISTING: No changes

# Test structure
tests/
├── unit/
│   ├── data/
│   │   ├── test_profile_manager.py          # NEW: Profile operations unit tests
│   │   ├── test_query_manager.py            # NEW: Query operations unit tests
│   │   └── test_persistence.py              # MODIFIED: Add path abstraction tests
│   └── ui/
│       └── test_profile_selectors.py        # NEW: UI component tests
├── integration/
│   ├── test_profile_switching_workflow.py   # NEW: End-to-end profile switching
│   ├── test_migration.py                    # NEW: First-run migration tests
│   └── test_cache_isolation.py              # NEW: Cache isolation verification
└── fixtures/
    └── temp_profiles_dir.py                 # NEW: Temporary profile directory fixture

# Root level changes
app.py                                       # MODIFIED: Add migrate_to_profiles() call on startup
app_settings.json                            # DEPRECATED: Migrated to profiles/default/
project_data.json                            # DEPRECATED: Migrated to profiles/default/queries/default/
jira_cache.json                              # DEPRECATED: Migrated to profiles/default/queries/default/
jira_changelog_cache.json                    # DEPRECATED: Migrated to profiles/default/queries/default/
metrics_snapshots.json                       # DEPRECATED: Migrated to profiles/default/queries/default/
cache/                                       # DEPRECATED: Migrated to profiles/default/queries/default/cache/
```

**Structure Decision**: Web application (existing Dash PWA) with new profile management layer. All existing code remains unchanged except `data/persistence.py` (path abstraction) and `app.py` (migration hook). Profile hierarchy isolates configuration and cache data for instant context switching.

## Complexity Tracking

> **No violations - all Constitution checks pass**

**Simplicity Justifications**:

| Design Decision               | Why This Approach                                                                                            | Alternative Considered                                                                                          |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------- |
| Profile-level settings (v3.0) | Settings at profile level (not query level) simplifies comparison and reduces per-query configuration burden | v2.0 workspace model with query-level settings rejected - harder to compare queries with different PERT factors |
| JSON file storage             | Simple, inspectable, no database overhead, matches existing architecture                                     | SQLite database rejected - overengineering for 50 profiles, increases complexity                                |
| Path abstraction layer        | Minimal code changes, transparent to existing callbacks, backward compatible                                 | Direct file path updates rejected - would break existing code, require callback changes                         |
| Default profile migration     | Preserves existing data, no user action required, idempotent                                                 | Manual migration rejected - poor user experience, risk of data loss                                             |

---

## Phase 0: Research & Architecture Decisions

**Goal**: Resolve any unknowns and document key architectural decisions from concept.md

### Research Tasks

#### R1: Profile ID Generation Strategy
**Question**: Should we use UUID, slugified names, or sequential IDs for profile/query IDs?

**Decision**: Use slugified names with uniqueness suffix if needed (e.g., `profile-kafka`, `profile-kafka-2`)
- **Rationale**: Human-readable IDs aid debugging, simpler directory names, easier URL sharing
- **Alternative**: UUIDs rejected - harder to debug, ugly directory names (`profiles/9b4c2712-e06f...`)
- **Implementation**: `profile-{slugify(name)}`, `query-{slugify(name)}`

#### R2: Atomic File Write Strategy
**Question**: How to prevent profiles.json corruption on concurrent writes or power loss?

**Decision**: Atomic rename pattern (write to `.tmp`, then rename)
```python
temp_file = f"{PROFILES_FILE}.tmp"
with open(temp_file, "w") as f:
    json.dump(profiles_meta, f, indent=2)
if os.path.exists(PROFILES_FILE):
    os.remove(PROFILES_FILE)
os.rename(temp_file, PROFILES_FILE)
```
- **Rationale**: OS-level atomic rename prevents partial writes, standard POSIX practice
- **Alternative**: File locking rejected - cross-platform issues, deadlock risk

#### R3: Profile Settings Schema Evolution
**Question**: How to handle future additions to profile.json schema (e.g., new field mappings)?

**Decision**: Version field + schema migration functions
```python
{
  "schema_version": "3.0",
  "id": "profile-kafka",
  ...
}
```
- **Rationale**: Explicit versioning enables backward compatibility checks, clear upgrade path
- **Alternative**: Implicit schema detection rejected - fragile, hard to validate
- **Implementation**: `migrate_profile_schema(profile_config, from_version, to_version)`

#### R4: Cache Invalidation Strategy
**Question**: When should query cache be invalidated (e.g., JQL change, field mapping change)?

**Decision**: Never auto-invalidate - manual "Refresh Data" button only
- **Rationale**: Preserves fast switching UX, users control when to refetch
- **Alternative**: Auto-invalidate on JQL change rejected - defeats purpose of profile switching
- **UI**: Add "Last Updated" timestamp to query selector, "Refresh" button per query

#### R5: Profile Deletion Confirmation
**Question**: What confirmation level needed to prevent accidental profile deletion?

**Decision**: Type-to-confirm pattern (user types profile name exactly)
```python
modal = dbc.Modal([
    dbc.Input(id="delete-confirm-input", placeholder="Type profile name to confirm"),
    dbc.Button("Delete", disabled=True)  # Enabled when input matches profile name
])
```
- **Rationale**: Stronger than simple "Are you sure?" dialog, prevents mis-clicks
- **Alternative**: Simple confirmation rejected - too easy to accidentally confirm

### Architecture Decisions Summary

**AD-1: Profile Hierarchy Model (v3.0)**
- Settings at profile level (PERT, deadline, field mappings)
- JQL only at query level
- Rationale: Enables apples-to-apples comparison across queries

**AD-2: Path Abstraction Layer**
- Transparently inject profile/query paths into existing persistence layer
- Zero breaking changes to existing callbacks
- Example: `get_profile_file_path("jira_cache.json")` → `profiles/active-profile-id/queries/active-query-id/jira_cache.json`

**AD-3: Migration Strategy**
- Automatic on first run (detect missing profiles.json)
- Move root files to `profiles/default/queries/default/`
- Idempotent (safe to run multiple times)
- Backup before migration (`.backup` suffix)

**AD-4: UI Integration Approach**
- Profile selector above query selector in settings panel
- Modals for creation (avoid inline form complexity)
- Confirmation dialogs for destructive actions

---

## Phase 1: Data Model & Contracts

### Data Model

#### Entity: Profile

**Purpose**: Represents a collection of queries with shared configuration settings

**Attributes**:
```python
{
  "id": str,                        # Slugified name (e.g., "profile-kafka")
  "name": str,                      # Display name (e.g., "Apache Kafka Analysis")
  "description": str,               # Optional user description
  "created_at": str,                # ISO 8601 timestamp
  "last_used": str,                 # ISO 8601 timestamp
  
  "forecast_settings": {
    "pert_factor": float,           # 1.0-3.0 (pessimism multiplier)
    "deadline": str,                # ISO 8601 date (nullable)
    "data_points_count": int        # Weeks to analyze (post-fetch filter)
  },
  
  "jira_config": {
    "base_url": str,                # JIRA instance URL
    "token": str,                   # API token (encrypted in future)
    "api_version": str,             # "v2" or "v3"
    "points_field": str,            # Story points customfield
    "cache_size_mb": int,           # Max cache size
    "max_results_per_call": int     # JIRA API pagination limit
  },
  
  "field_mappings": {
    "deployment_date": str,         # DORA: Deployment date field
    "deployment_successful": str,   # DORA: Success indicator field
    "work_started_date": str,       # Flow: Start date field
    "work_completed_date": str,     # Flow: Completion date field
    "work_type": str,               # Flow: Issue type field
    "work_item_size": str           # Flow: Story points field
  },
  
  "project_config": {
    "devops_projects": [str],       # DevOps project keys
    "development_projects": [str],  # Development project keys
    "bug_types": [str],             # Bug issue types
    "story_types": [str],           # Story issue types
    "task_types": [str]             # Task issue types
  },
  
  "queries": [                      # Metadata only (full configs in queries/)
    {
      "id": str,                    # Query ID
      "name": str,                  # Display name
      "jql_query": str,             # JQL string
      "created_at": str,            # ISO 8601 timestamp
      "last_used": str              # ISO 8601 timestamp
    }
  ]
}
```

**Validation Rules**:
- `name`: 1-100 characters, unique (case-insensitive)
- `pert_factor`: 1.0-3.0 (reasonable forecast range)
- `data_points_count`: 1-52 (weeks)
- Max 50 profiles per installation

**State Transitions**:
- Created → Active (when switched to)
- Active → Inactive (when switched away)
- Inactive → Deleted (when explicitly deleted)

#### Entity: Query

**Purpose**: Represents a JQL query variation with dedicated cache

**Attributes**:
```python
{
  "id": str,                        # Slugified name (e.g., "query-12w")
  "name": str,                      # Display name (e.g., "Last 12 Weeks")
  "description": str,               # Optional user description
  "jql_query": str,                 # Full JQL string
  "created_at": str,                # ISO 8601 timestamp
  "last_used": str                  # ISO 8601 timestamp
}
```

**Inherited from Profile** (not stored in query.json):
- PERT factor
- Deadline
- Data points count
- JIRA config
- Field mappings

**Validation Rules**:
- `name`: 1-100 characters, unique within profile (case-insensitive)
- `jql_query`: Non-empty, valid JQL syntax
- Max 100 queries per profile

**State Transitions**:
- Created → Active (when switched to)
- Active → Inactive (when switched away)
- Inactive → Deleted (when explicitly deleted)

#### Entity: ProfilesRegistry

**Purpose**: Global registry of all profiles and active selections

**Attributes**:
```python
{
  "version": str,                   # Schema version (e.g., "3.0")
  "active_profile_id": str,         # Currently active profile ID
  "active_query_id": str,           # Currently active query ID
  "profiles": [                     # Summary metadata for all profiles
    {
      "id": str,
      "name": str,
      "description": str,
      "created_at": str,
      "last_used": str,
      "jira_base_url": str,         # For display in selector
      "pert_factor": float,         # For display in selector
      "deadline": str,              # For display in selector
      "query_count": int            # For display in selector
    }
  ]
}
```

**Storage**: `profiles.json` at repository root

**Validation Rules**:
- `active_profile_id` must reference existing profile
- `active_query_id` must reference existing query in active profile
- Profile IDs in array must be unique

### API Contracts

#### Module: data/profile_manager.py

##### Function: create_profile
```python
def create_profile(
    name: str,
    description: str = "",
    clone_from_active: bool = True
) -> Tuple[bool, str, Optional[Profile]]:
    """
    Create new profile workspace.
    
    Args:
        name: Profile name (must be unique)
        description: Optional description
        clone_from_active: If True, clone current profile's data
        
    Returns:
        Tuple of (success: bool, message: str, profile: Optional[Profile])
        
    Raises:
        ValueError: If name invalid or duplicate
        OSError: If directory creation fails
    """
```

##### Function: switch_profile
```python
def switch_profile(profile_id: str) -> Tuple[bool, str]:
    """
    Switch to a different profile workspace.
    
    Fast operation (< 100ms) - only updates active pointer.
    
    Args:
        profile_id: Target profile ID (e.g., "profile-kafka")
        
    Returns:
        Tuple of (success: bool, message: str)
        
    Side Effects:
        - Updates profiles.json (active_profile_id, active_query_id)
        - Updates profile's last_used timestamp
        - Triggers UI reload via callback
    """
```

##### Function: delete_profile
```python
def delete_profile(profile_id: str) -> Tuple[bool, str]:
    """
    Delete profile and its workspace.
    
    Args:
        profile_id: Profile ID to delete
        
    Returns:
        Tuple of (success: bool, message: str)
        
    Raises:
        ValueError: If trying to delete active profile or last profile
        OSError: If directory deletion fails
    """
```

##### Function: duplicate_profile
```python
def duplicate_profile(
    source_profile_id: str,
    new_name: str
) -> Tuple[bool, str, Optional[Profile]]:
    """
    Duplicate existing profile.
    
    Args:
        source_profile_id: Source profile ID
        new_name: Name for duplicated profile
        
    Returns:
        Tuple of (success: bool, message: str, new_profile: Optional[Profile])
    """
```

#### Module: data/query_manager.py

##### Function: create_query
```python
def create_query(
    profile_id: str,
    name: str,
    jql_query: str,
    description: str = ""
) -> Tuple[bool, str, Optional[Query]]:
    """
    Create new query within profile.
    
    Args:
        profile_id: Parent profile ID
        name: Query name (must be unique within profile)
        jql_query: JQL query string
        description: Optional description
        
    Returns:
        Tuple of (success: bool, message: str, query: Optional[Query])
    """
```

##### Function: switch_query
```python
def switch_query(profile_id: str, query_id: str) -> Tuple[bool, str]:
    """
    Switch to a different query within the same profile.
    
    Fastest operation (< 50ms) - only updates active query pointer.
    
    Args:
        profile_id: Current profile ID
        query_id: Target query ID
        
    Returns:
        Tuple of (success: bool, message: str)
    """
```

#### Module: data/persistence.py (Modified)

##### Function: get_active_profile_workspace
```python
def get_active_profile_workspace() -> str:
    """
    Get file system path to active profile's workspace.
    
    Returns:
        str: Path like "profiles/profile-kafka/" or "" for root (legacy mode)
        
    Notes:
        - Returns "" if profiles.json doesn't exist (backward compatibility)
        - Returns "profiles/default/" for default profile
    """
```

##### Function: get_active_query_workspace
```python
def get_active_query_workspace() -> str:
    """
    Get file system path to active query's workspace.
    
    Returns:
        str: Path like "profiles/profile-kafka/queries/query-12w/"
        
    Notes:
        - Returns "" if profiles.json doesn't exist (backward compatibility)
        - Combines profile and query paths
    """
```

##### Function: get_profile_file_path
```python
def get_profile_file_path(filename: str) -> str:
    """
    Get full path to a file in active query workspace.
    
    Args:
        filename: Base filename (e.g., "jira_cache.json")
        
    Returns:
        str: Full path (e.g., "profiles/profile-kafka/queries/query-12w/jira_cache.json")
        
    Notes:
        - Transparently injects profile/query paths
        - Existing code using this function requires no changes
    """
```

#### Module: callbacks/profile_management.py

##### Callback: handle_profile_switch
```python
@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("profile-switch-alert", "children"),
    Output("profile-switch-alert", "is_open"),
    Input("profile-selector", "value"),
    State("active-profile-store", "data"),
    prevent_initial_call=True
)
def handle_profile_switch(new_profile_id, current_profile_id):
    """
    Handle profile selection from dropdown.
    
    Fast operation - only updates active pointer, triggers page reload.
    """
```

##### Callback: handle_query_switch
```python
@callback(
    Output("url", "pathname", allow_duplicate=True),
    Output("query-switch-alert", "children"),
    Output("query-switch-alert", "is_open"),
    Input("query-selector", "value"),
    State("active-query-store", "data"),
    prevent_initial_call=True
)
def handle_query_switch(new_query_id, current_query_id):
    """
    Handle query selection from dropdown.
    
    Fastest operation - only updates active query pointer, triggers reload.
    """
```

### Quickstart Guide Generation

**Action**: Generate `quickstart.md` for developers

**Command**:
```powershell
# Generate quickstart guide from plan.md data model and API contracts
# (This will be done in next step after completing plan.md)
```

---

## Phase 2: Implementation Tasks

**Note**: Detailed task breakdown will be generated separately via `/speckit.tasks` command.

### High-Level Task Phases

#### Phase 1: Profile-Aware Persistence Layer (Core)
**Goal**: Make `data/persistence.py` profile-aware without breaking existing code

**Key Modules**:
- `data/profile_manager.py` - Profile lifecycle operations
- `data/query_manager.py` - Query lifecycle operations
- `data/persistence.py` (modified) - Path abstraction functions

**Estimate**: 20 hours (2.5 days)

#### Phase 2: UI Integration
**Goal**: Add profile/query selectors and management UI

**Key Components**:
- `ui/profile_selector.py` - Profile dropdown and buttons
- `ui/query_selector.py` - Query dropdown and buttons
- `ui/profile_create_modal.py` - Profile creation dialog
- `ui/query_create_modal.py` - Query creation dialog
- `callbacks/profile_management.py` - All profile/query callbacks

**Estimate**: 22 hours (2.75 days)

#### Phase 3: Backward Compatibility & Migration
**Goal**: Seamless migration for existing users

**Key Functions**:
- `migrate_to_profiles()` - Move root files to profiles/default/
- Migration validation and rollback
- Startup hook in `app.py`

**Estimate**: 11 hours (1.5 days)

#### Phase 4: Testing & Validation
**Goal**: Comprehensive testing and performance validation

**Key Tests**:
- Integration tests for switching workflows
- Cache isolation tests
- Performance tests (< 50ms query, < 100ms profile)
- Migration tests with large datasets

**Estimate**: 17 hours (2 days)

### Overall Implementation Estimate

**Total**: 70 hours (8.75 days) + 20% buffer = **10.5 days** (2 weeks with other duties)

**Detailed task breakdown**: See `tasks.md` (generated via `/speckit.tasks`)

---

## Risk Analysis

### Risk 1: Migration Failure on Production Installations
**Probability**: Medium | **Impact**: High

**Scenario**: Users with large cache files (>100MB) or unusual file permissions experience migration failure and lose data.

**Mitigation**:
- Backup strategy: Create `.backup` copies before moving files
- Rollback function: Restore from backups if migration fails
- Validation: Checksum verification of migrated files
- Testing: Test migration with 100MB+ cache files, read-only files, symlinks

**Contingency**: If migration fails, app falls back to root workspace mode (profiles.json doesn't exist = legacy mode)

### Risk 2: Profile Switching Performance Degradation
**Probability**: Low | **Impact**: Medium

**Scenario**: Profile switch takes >100ms due to large profile.json files or slow disk I/O.

**Mitigation**:
- Lazy loading: Load profile config on demand, not all profiles upfront
- Caching: Cache active profile config in memory
- Optimization: Minimize JSON serialization/deserialization
- Testing: Performance tests with 50 profiles, 100 queries each

**Contingency**: Add loading spinner if switch takes >500ms, optimize profile.json structure

### Risk 3: Cache File Corruption
**Probability**: Medium | **Impact**: Medium

**Scenario**: Power loss or system crash during profiles.json atomic write causes corruption.

**Mitigation**:
- Atomic writes: Use temp file + rename pattern
- Validation: JSON schema validation on load
- Recovery: Fallback to default profile if profiles.json corrupted
- Testing: Simulate power loss during write (delete half-written file)

**Contingency**: Manual recovery: Delete profiles.json, re-run migration to recreate from root files

### Risk 4: Existing Callback Incompatibility
**Probability**: Low | **Impact**: High

**Scenario**: Some callbacks directly reference root file paths and break with path abstraction.

**Mitigation**:
- Code search: Find all hardcoded "app_settings.json", "jira_cache.json" references
- Testing: Run full test suite after Phase 1 path abstraction
- Regression tests: Integration tests verify all existing features work

**Contingency**: Add compatibility shim that redirects old paths to new paths

### Risk 5: User Confusion with Profile/Query Hierarchy
**Probability**: Medium | **Impact**: Low

**Scenario**: Users don't understand difference between profiles and queries, create redundant profiles.

**Mitigation**:
- UI guidance: Tooltips explaining "Profile = JIRA settings + PERT/deadline, Query = JQL variation"
- Examples: Pre-populate examples in dropdown ("Last 12 Weeks", "Last 52 Weeks")
- Documentation: Clear explanation in quickstart.md
- Onboarding: First-run tutorial showing how to create queries within profile

**Contingency**: Add "Profile vs Query" help dialog accessible from settings panel

---

## Success Criteria Verification

**How to verify each success criterion from spec.md**:

| Success Criterion                        | Verification Method                                              | Target                                               |
| ---------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------- |
| SC-001: Query switch <50ms               | Performance test: `test_query_switch_latency()`                  | Measure time from dropdown click to dashboard reload |
| SC-002: Profile switch <100ms            | Performance test: `test_profile_switch_latency()`                | Measure time from dropdown click to dashboard reload |
| SC-003: Cache hit rate >90%              | Integration test: Count JIRA API calls during 10 query switches  | <1 API call per 10 switches                          |
| SC-004: Compare queries <10s             | Manual test: Create 2 queries, switch between them twice         | Total time <10s                                      |
| SC-005: Migration data preservation 100% | Unit test: Compare file contents before/after migration          | Checksums match                                      |
| SC-006: Support 50 profiles, 100 queries | Load test: Create max profiles/queries, measure switch latency   | Still meets SC-001, SC-002                           |
| SC-007: Profile creation <500ms          | Performance test: `test_create_profile_latency()`                | Time from button click to dropdown update            |
| SC-008: Query creation <500ms            | Performance test: `test_create_query_latency()`                  | Time from button click to dropdown update            |
| SC-009: Create 5 queries <3min           | Manual test: Timed user workflow                                 | Includes typing JQL strings                          |
| SC-010: Cache isolation 100%             | Integration test: Verify cache file paths don't overlap          | Check file contents differ                           |
| SC-011: Prevent accidental deletion 100% | Unit test: Try deleting active profile/query, last profile/query | All attempts rejected                                |
| SC-012: Migration <5s for 50MB           | Performance test: `test_migration_performance()`                 | Measure migration time with 50MB cache               |

---

## Appendix: JSON Schema Examples

### profiles.json
```json
{
  "version": "3.0",
  "active_profile_id": "profile-kafka",
  "active_query_id": "query-12w",
  "profiles": [
    {
      "id": "profile-kafka",
      "name": "Apache Kafka Analysis",
      "description": "Apache Kafka project with 1.5x PERT factor",
      "created_at": "2025-11-13T10:00:00Z",
      "last_used": "2025-11-13T14:30:00Z",
      "jira_base_url": "https://issues.apache.org/jira",
      "pert_factor": 1.5,
      "deadline": "2025-12-31",
      "query_count": 4
    }
  ]
}
```

### profiles/profile-kafka/profile.json
```json
{
  "id": "profile-kafka",
  "name": "Apache Kafka Analysis",
  "description": "Apache Kafka project with 1.5x PERT factor",
  "created_at": "2025-11-13T10:00:00Z",
  "last_used": "2025-11-13T14:30:00Z",
  
  "forecast_settings": {
    "pert_factor": 1.5,
    "deadline": "2025-12-31",
    "data_points_count": 12
  },
  
  "jira_config": {
    "base_url": "https://issues.apache.org/jira",
    "token": "***",
    "api_version": "v3",
    "points_field": "customfield_10016"
  },
  
  "field_mappings": {
    "deployment_date": "customfield_10001",
    "work_started_date": "customfield_10003",
    "work_completed_date": "customfield_10004"
  },
  
  "project_config": {
    "development_projects": ["KAFKA"]
  },
  
  "queries": [
    {
      "id": "query-12w",
      "name": "Last 12 Weeks",
      "jql_query": "project = KAFKA AND created >= -12w",
      "created_at": "2025-11-13T10:00:00Z",
      "last_used": "2025-11-13T14:30:00Z"
    }
  ]
}
```

### profiles/profile-kafka/queries/query-12w/query.json
```json
{
  "id": "query-12w",
  "name": "Last 12 Weeks",
  "description": "Sprint retrospective analysis",
  "jql_query": "project = KAFKA AND created >= -12w ORDER BY created DESC",
  "created_at": "2025-11-13T10:00:00Z",
  "last_used": "2025-11-13T14:30:00Z"
}
```

````
