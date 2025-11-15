# Feature 011: Improved Workspace & Query Management Concept

**Version**: 5.0.0  
**Status**: Enhanced Concept - Dependency-First Architecture  
**Created**: 2025-11-14  
**Updated**: 2025-11-14  
**Author**: AI Agent (GitHub Copilot)

---

## Executive Summary

**Problem**: Current UI doesn't express proper dependencies between Profile → JIRA → Query entities, leading to configuration confusion and broken workflows.

**Root Cause Analysis**:
- Configuration steps are shown in wrong order (JIRA first, Profile last)
- Users can attempt to configure queries without profiles or JIRA connection
- No automatic default profile creation for first-time users
- JQL editor is separate from query management, breaking the "save query" workflow
- App doesn't enforce "always have a defined query" rule

**Enhanced Solution**: **Dependency-First Architecture** with proper entity relationships and progressive disclosure.

**Key Innovation - Progressive Dependency Unlocking**:
1. **Foundation**: Always ensure Default Profile exists
2. **Connection**: JIRA config unlocks only after profile exists
3. **Mapping**: Field mappings unlock only after JIRA connection works
4. **Queries**: Query management unlocks only after basic setup complete
5. **Integration**: JQL editor embedded within query management

**Benefits**:
- ✅ **Logical Flow**: Users can't skip prerequisite steps
- ✅ **No Dead Ends**: Every configuration screen leads to the next logical step
- ✅ **Auto-Recovery**: App creates missing defaults automatically
- ✅ **Integrated Workflow**: "Edit JQL → Save Query" in single component
- ✅ **Always Valid**: App always has a working profile + query combination

---

## Dependency Architecture

### Current (Broken) Dependencies

```
❌ CURRENT FLOW - Inverted and Optional:
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  JIRA Config    │    │  Field Mappings │    │ Profile (Maybe) │
│  (First Step)   │ ── │  (Second Step)  │ ── │ (Last Step)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ↓                       ↓                       ↓
┌─────────────────────────────────────────────────────────────────┐
│                   JQL Query Editor                              │
│                 (Separate Component)                            │
│              [Save Query] [Update Data]                        │
│                (Confusing Actions)                             │
└─────────────────────────────────────────────────────────────────┘

PROBLEMS:
- Can configure JIRA without profile (where does config get saved?)
- Can write JQL without profile (which query does it belong to?)
- Can map fields without JIRA connection (which instance are we mapping?)
- "Save Query" vs "Update Data" is confusing (two separate actions)
```

### Enhanced (Dependency-First) Architecture

```
✅ ENHANCED FLOW - Dependency Chain with Progressive Unlock:

1. FOUNDATION (Auto-Created)
┌─────────────────────────────────────────────────────────────────┐
│                    WORKSPACE PROFILE                            │
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────────┐ │
│ │ Profile: Default│ │ PERT: 1.5       │ │ Deadline: 2025-12  │ │
│ │ [Switch ▼] [+]  │ │ [Edit]          │ │ [Edit]             │ │
│ └─────────────────┘ └─────────────────┘ └─────────────────────┘ │
│ Status: ✅ Profile Ready → JIRA Connection Enabled              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
2. CONNECTION (Unlocked when profile exists)
┌─────────────────────────────────────────────────────────────────┐
│                    JIRA CONNECTION                              │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ URL:   https://jira.example.com          [Test Connection] │ │
│ │ Token: ****************************     [🔗 Connected ✅] │ │
│ │ Points Field: Story Points (customfield_10002) [Auto ✅]  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ Status: ✅ JIRA Connected → Field Mapping Enabled              │
└─────────────────────────────────────────────────────────────────┘
                                ↓
3. MAPPING (Unlocked when JIRA connection works)
┌─────────────────────────────────────────────────────────────────┐
│                    FIELD MAPPINGS                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ DORA Metrics:                                              │ │
│ │ ├ Deployment Date: [Auto-detect ▼] customfield_10020 ✅   │ │
│ │ ├ Work Started:    [Auto-detect ▼] customfield_10021 ✅   │ │
│ │ └ Work Type:       [Auto-detect ▼] customfield_10022 ✅   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│ Status: ✅ Fields Mapped → Query Management Enabled            │
└─────────────────────────────────────────────────────────────────┘
                                ↓
4. QUERY MANAGEMENT (Unlocked when mappings complete)
┌─────────────────────────────────────────────────────────────────┐
│                  QUERY MANAGEMENT                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Query: [Default Query ▼] [+ New] [📋 Duplicate] [🗑 Delete] │ │
│ │                                                             │ │
│ │ ┌─ INTEGRATED JQL EDITOR (Part of Query Management) ─────┐ │ │
│ │ │ Name: Default Query                                    │ │ │
│ │ │ JQL:  project = EXAMPLE AND created >= -12w           │ │ │
│ │ │       ORDER BY created DESC                           │ │ │
│ │ │                                                        │ │ │
│ │ │ [💾 Save Query] [🔄 Update Data] [❌ Cancel Changes]   │ │ │
│ │ └────────────────────────────────────────────────────────┘ │ │
│ │                                                             │ │
│ │ Last Updated: 2025-11-14 10:30 | Cache: 2.4MB | Issues: 156│ │
│ └─────────────────────────────────────────────────────────────┘ │
│ Status: ✅ Query Defined → Dashboard & Metrics Available       │
└─────────────────────────────────────────────────────────────────┘
```

### Dependency Rules & Enforcement

**1. Foundation Rule: Profile Always Exists**
```python
def ensure_default_profile_exists():
    """Ensure default profile exists on app startup."""
    if not profile_exists("default"):
        create_default_profile()
    if get_active_profile() is None:
        switch_to_profile("default")
```

**2. Progressive Unlock Rules**
```python
def is_jira_config_enabled() -> bool:
    """JIRA config only enabled if profile exists."""
    return get_active_profile() is not None

def is_field_mapping_enabled() -> bool:
    """Field mapping only enabled if JIRA connection works."""
    return is_jira_config_enabled() and test_jira_connection()

def is_query_management_enabled() -> bool:
    """Query management only enabled if basic setup complete."""
    return (is_field_mapping_enabled() and 
            has_minimum_field_mappings() and
            has_default_query())
```

**3. Auto-Recovery Rules**
```python
def ensure_valid_configuration():
    """Auto-create missing components."""
    # Always ensure default profile
    ensure_default_profile_exists()
    
    # Auto-create default query if none exists
    if not has_any_queries():
        create_default_query()
    
    # Auto-switch to valid query if current is invalid
    if not is_current_query_valid():
        switch_to_first_valid_query()
```

---

## Enhanced UI Design

### Progressive Disclosure Interface

**State 1: Fresh Install (Auto-Setup)**
```
┌─────────────────────────────────────────┐
│ 🚀 WORKSPACE SETUP                     │
├─────────────────────────────────────────┤
│ ✅ Default Profile Created              │
│ ✅ Default Settings Applied             │
│    PERT Factor: 1.5                    │ 
│    Deadline: 2025-12-31                │
│                                         │
│ ▶️  Next: Configure JIRA Connection     │
│    [Continue Setup] [Skip for now]     │
└─────────────────────────────────────────┘

AUTO-ACTIONS:
- Create "Default" profile automatically
- Set reasonable PERT factor (1.5) and deadline
- Show "Setup Complete" status
- Guide user to next step (JIRA config)
```

**State 2: JIRA Connection (Guided Setup)**
```
┌─────────────────────────────────────────┐
│ 🔗 JIRA CONNECTION                     │
├─────────────────────────────────────────┤
│ Profile: Default ✅                     │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ JIRA URL:                           │ │
│ │ [https://jira.example.com         ] │ │
│ │                                     │ │
│ │ API Token:                          │ │
│ │ [****************************   ] │ │
│ │                                     │ │
│ │ [🧪 Test Connection]               │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Status: ⏳ Click "Test" to continue     │
└─────────────────────────────────────────┘

DEPENDENCY CHECK:
- Profile exists ✅ → JIRA config enabled
- Show clear next step after connection test
```

**State 3: Field Mapping (Auto-Detection)**
```
┌─────────────────────────────────────────┐
│ 🎯 FIELD MAPPING                       │
├─────────────────────────────────────────┤
│ Profile: Default ✅                     │
│ JIRA: jira.example.com ✅               │
│                                         │
│ ┌─────────────────────────────────────┐ │
│ │ 🤖 AUTO-DETECTING FIELDS...        │ │
│ │                                     │ │
│ │ ✅ Story Points: customfield_10002  │ │
│ │ ✅ Deployment Date: customfield_... │ │
│ │ ⏳ Work Type: Scanning...           │ │
│ │                                     │ │
│ │ [📝 Manual Override] [✓ Accept]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Status: ⏳ Auto-detection in progress   │
└─────────────────────────────────────────┘

AUTO-ACTIONS:
- Scan JIRA instance for common field patterns
- Auto-detect story points, epic links, work types
- Show progress and allow manual override
```

**State 4: Query Management (Integrated)**
```
┌─────────────────────────────────────────┐
│ 📝 QUERY MANAGEMENT                    │
├─────────────────────────────────────────┤
│ Profile: Default ✅                     │
│ JIRA: jira.example.com ✅               │
│ Fields: 5 mapped ✅                     │
│                                         │
│ Query: [Default Query ▼] [+] [📋] [🗑] │
│                                         │
│ ┌─ JQL EDITOR (INTEGRATED) ───────────┐ │
│ │ Name: Default Query                 │ │
│ │ JQL:  project = EXAMPLE AND         │ │
│ │       created >= -12w               │ │
│ │                                     │ │
│ │ [💾 Save Query] [🔄 Update Data]    │ │
│ └─────────────────────────────────────┘ │
│                                         │
│ Status: ✅ Ready for analysis           │
│ [🚀 Launch Dashboard]                  │
└─────────────────────────────────────────┘

KEY FEATURES:
- JQL editor is PART of query management (not separate)
- Save Query creates/updates query in current profile  
- Update Data fetches fresh data for current query
- Clear path to dashboard once query is defined
```

### Mobile-First Progressive Layout

**Mobile Wireframe (Stacked Dependencies)**
```
┌─────────────────────┐
│ WORKSPACE SETUP     │
├─────────────────────┤
│ 1. Profile ✅       │
│    Default          │
│    PERT: 1.5        │
│                     │
│ 2. JIRA ⏳          │
│    [Configure]      │
│                     │
│ 3. Fields 🔒        │
│    (Locked)         │
│                     │
│ 4. Queries 🔒       │
│    (Locked)         │
└─────────────────────┘

MOBILE UX:
- Show dependency chain as numbered steps
- Lock future steps until prerequisites complete
- Clear progress indicators (✅ ⏳ 🔒)
- Each step expands when unlocked
```

---

## Enhanced Data Model & Lifecycle

### Auto-Creation & Recovery Patterns

**1. Default Profile Auto-Creation**
```python
# app.py startup sequence
def ensure_valid_workspace():
    """Ensure app has valid workspace configuration."""
    
    # Step 1: Ensure default profile exists
    if not profile_exists("default"):
        logger.info("First run: Creating default profile")
        create_default_profile({
            "name": "Default",
            "description": "Default workspace for JIRA analysis",
            "pert_factor": 1.5,
            "deadline": get_default_deadline(),  # +6 months from now
            "data_points_count": 12
        })
    
    # Step 2: Ensure active profile is valid
    active_profile = get_active_profile()
    if not active_profile:
        logger.info("No active profile: Switching to default")
        switch_to_profile("default")
    
    # Step 3: Ensure profile has at least one query
    queries = list_queries_for_profile(active_profile.id)
    if not queries:
        logger.info("No queries in profile: Creating default query")
        create_default_query(active_profile.id, {
            "name": "Default Query",
            "jql": "project = EXAMPLE AND created >= -12w ORDER BY created DESC",
            "description": "Default query for getting started"
        })
    
    # Step 4: Ensure active query is valid
    active_query = get_active_query()
    if not active_query:
        logger.info("No active query: Switching to first available")
        switch_to_first_query()

# Called during app initialization
ensure_valid_workspace()
```

**2. Dependency Validation**
```python
def get_configuration_status() -> Dict[str, Dict]:
    """Get status of all configuration dependencies."""
    
    status = {
        "profile": {
            "enabled": True,  # Always enabled
            "complete": profile_exists("default"),
            "message": "✅ Profile ready" if profile_exists("default") else "⏳ Creating default profile"
        },
        
        "jira": {
            "enabled": profile_exists("default"),
            "complete": is_jira_connected(),
            "message": "✅ JIRA connected" if is_jira_connected() else 
                      "⏳ Configure JIRA connection" if profile_exists("default") else
                      "🔒 Requires profile setup"
        },
        
        "fields": {
            "enabled": is_jira_connected(),
            "complete": has_minimum_field_mappings(),
            "message": "✅ Fields mapped" if has_minimum_field_mappings() else
                      "⏳ Map JIRA fields" if is_jira_connected() else
                      "🔒 Requires JIRA connection"
        },
        
        "queries": {
            "enabled": has_minimum_field_mappings(),
            "complete": has_valid_queries(),
            "message": "✅ Queries ready" if has_valid_queries() else
                      "⏳ Create first query" if has_minimum_field_mappings() else
                      "🔒 Requires field mapping"
        }
    }
    
    return status
```

**3. Progressive UI State Management**
```python
@callback(
    [Output("jira-config-section", "className"),
     Output("field-mapping-section", "className"), 
     Output("query-management-section", "className")],
    Input("configuration-status-store", "data")
)
def update_section_states(config_status):
    """Enable/disable configuration sections based on dependencies."""
    
    # JIRA section: enabled if profile exists
    jira_class = "config-section" if config_status["profile"]["complete"] else "config-section disabled"
    
    # Fields section: enabled if JIRA connected
    fields_class = "config-section" if config_status["jira"]["complete"] else "config-section disabled"
    
    # Queries section: enabled if fields mapped
    queries_class = "config-section" if config_status["fields"]["complete"] else "config-section disabled"
    
    return jira_class, fields_class, queries_class
```

### Enhanced Profile Structure

**Profile Config (`profiles/default/profile.json`)**
```json
{
  "id": "default",
  "name": "Default",
  "description": "Default workspace for JIRA analysis",
  "version": "5.0",
  "created_at": "2025-11-14T10:00:00Z",
  "last_used": "2025-11-14T15:30:00Z",
  
  "setup_status": {
    "profile_ready": true,
    "jira_connected": false,
    "fields_mapped": false,
    "queries_created": false,
    "setup_complete": false,
    "setup_step": "jira_connection"
  },
  
  "forecast_settings": {
    "pert_factor": 1.5,
    "deadline": "2025-12-31",
    "data_points_count": 12
  },
  
  "jira_config": {
    "base_url": "",
    "token": "",
    "api_version": "2",
    "connection_tested": false,
    "last_test_at": null,
    "test_status": "not_tested"
  },
  
  "field_mappings": {
    "auto_detected": false,
    "detection_date": null,
    "story_points": "customfield_10002",
    "deployment_date": "customfield_10020",
    "work_started": "customfield_10021",
    "work_type": "customfield_10022"
  },
  
  "queries": [
    {
      "id": "default-query",
      "name": "Default Query", 
      "is_default": true,
      "created_at": "2025-11-14T10:00:00Z",
      "last_used": "2025-11-14T15:30:00Z"
    }
  ],
  
  "active_query_id": "default-query"
}
```

### Query Integration Model

**Enhanced Query Config (`profiles/default/queries/default-query/query.json`)**
```json
{
  "id": "default-query",
  "name": "Default Query",
  "description": "Default query for getting started with JIRA analysis",
  "version": "5.0",
  "created_at": "2025-11-14T10:00:00Z",
  "last_used": "2025-11-14T15:30:00Z",
  
  "jql_config": {
    "jql_query": "project = EXAMPLE AND created >= -12w ORDER BY created DESC",
    "last_edited": "2025-11-14T15:30:00Z",
    "is_valid": true,
    "validation_message": "",
    "estimated_results": 150
  },
  
  "data_status": {
    "last_data_fetch": "2025-11-14T14:45:00Z", 
    "cache_size_mb": 2.4,
    "issues_count": 156,
    "fetch_duration_ms": 3500,
    "next_refresh_suggested": "2025-11-15T08:00:00Z"
  },
  
  "metrics_status": {
    "last_calculation": "2025-11-14T14:50:00Z",
    "dora_metrics_available": true,
    "flow_metrics_available": true,
    "forecast_generated": true
  }
}
```

---

## Implementation Tasks

### Phase 1: Foundation & Auto-Setup (Priority 1)

**Goal**: Ensure app always has valid profile + query foundation

- [ ] **T001**: Add `ensure_default_profile_exists()` to app startup
- [ ] **T002**: Add `ensure_valid_configuration()` validation function
- [ ] **T003**: Create default profile auto-creation with reasonable defaults
- [ ] **T004**: Create default query auto-creation when profile is empty
- [ ] **T005**: Add configuration status tracking in profile.json
- [ ] **T006**: Test auto-recovery: delete profiles.json → restart app → verify default created

**Acceptance**: Fresh install creates "Default" profile with reasonable settings automatically

### Phase 2: Dependency-Based UI (Priority 1)

**Goal**: UI sections unlock progressively based on dependencies

- [ ] **T007**: Create `get_configuration_status()` dependency checker
- [ ] **T008**: Add progressive section enabling/disabling CSS classes
- [ ] **T009**: Update settings panel to show dependency chain visually
- [ ] **T010**: Add status indicators (✅ ⏳ 🔒) for each configuration section
- [ ] **T011**: Add "Next Step" guidance messaging
- [ ] **T012**: Test dependency flow: Profile → JIRA → Fields → Queries

**Acceptance**: Users cannot skip prerequisite steps, clear guidance shown at each stage

### Phase 3: Integrated Query Management (Priority 2)

**Goal**: JQL editor becomes part of query management, not separate section

- [ ] **T013**: Move JQL editor into query management card
- [ ] **T014**: Add query name and description fields to integrated editor
- [ ] **T015**: Merge "Save Query" and "Update Data" into single flow
- [ ] **T016**: Remove standalone JQL editor section from settings
- [ ] **T017**: Add query metadata display (last updated, cache status)
- [ ] **T018**: Test integrated workflow: Create Query → Edit JQL → Save → Update Data

**Acceptance**: Single "Query Management" section handles query creation, JQL editing, and data refresh

### Phase 4: Enhanced UX & Polish (Priority 3)

**Goal**: Guided setup experience with auto-detection

- [ ] **T019**: Add JIRA field auto-detection after connection test
- [ ] **T020**: Add setup progress wizard for first-time users
- [ ] **T021**: Add "Launch Dashboard" button when setup complete
- [ ] **T022**: Add query validation with estimated result counts
- [ ] **T023**: Add setup completion checklist UI
- [ ] **T024**: Test complete first-run experience end-to-end

**Acceptance**: New users can go from zero to working dashboard in <5 minutes with minimal configuration

### Testing Strategy

**Auto-Setup Tests**:
1. Delete all profiles → restart app → verify default profile created
2. Delete queries from profile → restart app → verify default query created  
3. Invalid configuration → restart app → verify auto-recovery works

**Dependency Tests**:
1. Fresh profile → verify JIRA section enabled, others disabled
2. JIRA connected → verify fields section enabled
3. Fields mapped → verify queries section enabled
4. Try to access locked sections → verify proper error messages

**Integration Tests**:
1. Create new query in integrated editor → verify query.json created
2. Edit JQL in integrated editor → save → verify query updated but no data fetch
3. Click "Update Data" → verify JIRA API called and cache updated
4. Switch between queries → verify integrated editor updates

---

## Benefits of Enhanced Architecture

### For Users

✅ **Logical Flow**: Cannot skip prerequisites, guided through proper setup sequence  
✅ **No Confusion**: Each step clearly depends on the previous step  
✅ **Auto-Recovery**: App fixes common issues (missing profiles/queries) automatically  
✅ **Integrated Workflow**: JQL editing and query saving happens in one place  
✅ **Always Valid**: App guarantees working profile + query combination  

### For Developers

✅ **Clear Dependencies**: Code enforces profile → JIRA → fields → queries hierarchy  
✅ **Easier Testing**: Dependency validation functions make testing predictable  
✅ **Maintainable**: Progressive unlock logic contained in single configuration module  
✅ **Extensible**: Easy to add new configuration steps in dependency chain  
✅ **Defensive**: Auto-creation prevents broken states during development

### For System Reliability

✅ **No Broken States**: App always has valid configuration foundation  
✅ **Predictable Behavior**: Dependencies enforced at multiple levels (UI, API, data)  
✅ **Quick Recovery**: Automatic default creation handles corruption/deletion  
✅ **Clear Error Messages**: Users see exactly what's missing and how to fix it  
✅ **Version Migration**: Setup status tracking enables smooth upgrades

---

*This enhanced concept addresses the core dependency and UX issues while maintaining the original profile → query architecture benefits.*
