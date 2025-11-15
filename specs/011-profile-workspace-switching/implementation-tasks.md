# Feature 011: Enhanced Task Breakdown & Implementation Plan

**Version**: 5.0.0  
**Priority**: High - Foundational Architecture Fix  
**Estimated Duration**: 8-10 days  
**Status**: Ready for Implementation

---

## 🎯 **Core Problem Summary**

**Current State**: UI doesn't express dependencies, users can configure in wrong order, no auto-defaults
**Target State**: Progressive unlock UI, auto-default creation, integrated JQL workflow

**Key Requirements Identified**:
1. **Auto-create Default Profile** if none exists
2. **Enforce dependency chain**: Profile → JIRA → Fields → Queries  
3. **Integrate JQL Editor** into Query Management (not separate)
4. **Always ensure valid query** exists for data operations
5. **Progressive UI unlock** based on completion status

---

## 📋 **Detailed Task Breakdown**

### **PHASE 1: Foundation & Auto-Setup** 
*Priority: Blocking - Must complete before other phases*

#### **T001: App Startup Auto-Setup** ⭐
**Goal**: Ensure app always has valid profile + query foundation on startup

**Implementation**:
```python
# app.py - Add before server start
def ensure_valid_workspace():
    """Ensure app has valid workspace configuration on startup."""
    from data.profile_manager import (
        profile_exists, create_default_profile, 
        get_active_profile, switch_to_profile
    )
    from data.query_manager import (
        list_queries_for_profile, create_default_query,
        get_active_query, switch_to_first_query
    )
    
    logger.info("🚀 Ensuring valid workspace configuration...")
    
    # Step 1: Ensure default profile exists
    if not profile_exists("default"):
        logger.info("First run: Creating default profile")
        create_default_profile({
            "name": "Default",
            "description": "Default workspace for JIRA analysis",
            "pert_factor": 1.5,
            "deadline": get_default_deadline(),  # +6 months
            "data_points_count": 12,
            "jira_config": {},
            "field_mappings": {}
        })
    
    # Step 2: Ensure active profile is valid  
    active_profile = get_active_profile()
    if not active_profile:
        logger.info("No active profile: Switching to default")
        switch_to_profile("default")
        active_profile = get_active_profile()
    
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
    
    logger.info("✅ Workspace configuration validated")

# Call during app initialization
ensure_valid_workspace()
```

**Files to Create/Modify**:
- Modify: `app.py` (add startup validation)
- Modify: `data/profile_manager.py` (add auto-creation functions)
- Modify: `data/query_manager.py` (add auto-creation functions)

**Test Cases**:
1. Delete `profiles.json` → restart app → verify default profile created
2. Delete all queries from profile → restart app → verify default query created
3. Corrupt configuration → restart app → verify auto-recovery

**Acceptance**: Fresh install or corrupted state creates valid defaults automatically

---

#### **T002: Configuration Status Validation** ⭐
**Goal**: Create dependency validation system

**Implementation**:
```python
# data/config_validation.py - NEW FILE
def get_configuration_status() -> Dict[str, Dict]:
    """Get status of all configuration dependencies."""
    
    status = {
        "profile": {
            "enabled": True,  # Always enabled
            "complete": profile_exists("default"),
            "message": "✅ Profile ready" if profile_exists("default") else "⏳ Creating default profile",
            "next_step": "Configure JIRA Connection"
        },
        
        "jira": {
            "enabled": profile_exists("default"),
            "complete": is_jira_connected(),
            "message": get_jira_status_message(),
            "next_step": "Map JIRA Fields"
        },
        
        "fields": {
            "enabled": is_jira_connected(),
            "complete": has_minimum_field_mappings(),
            "message": get_field_mapping_status_message(),
            "next_step": "Create Queries"
        },
        
        "queries": {
            "enabled": has_minimum_field_mappings(),
            "complete": has_valid_queries(),
            "message": get_query_status_message(),
            "next_step": "Launch Dashboard"
        }
    }
    
    return status

def is_setup_complete() -> bool:
    """Check if all setup steps are complete."""
    status = get_configuration_status()
    return all(step["complete"] for step in status.values())

def get_next_setup_step() -> Optional[str]:
    """Get the next incomplete setup step."""
    status = get_configuration_status()
    for step_name, step_status in status.items():
        if not step_status["complete"]:
            return step_name
    return None
```

**Files to Create**:
- Create: `data/config_validation.py` (new validation module)
- Modify: `data/profile_manager.py` (add validation functions)
- Modify: `data/query_manager.py` (add validation functions)

**Test Cases**:
1. Empty configuration → verify all except profile marked incomplete
2. JIRA configured → verify fields step unlocked
3. All steps complete → verify `is_setup_complete()` returns True

---

#### **T003: Profile Config Enhancement**
**Goal**: Add setup status tracking to profile structure

**Implementation**:
```python
# Enhanced profile.json structure
{
  "id": "default",
  "name": "Default",
  "version": "5.0",
  "created_at": "2025-11-14T10:00:00Z",
  
  "setup_status": {
    "profile_ready": true,
    "jira_connected": false,
    "fields_mapped": false, 
    "queries_created": false,
    "setup_complete": false,
    "current_step": "jira_connection",
    "last_validation": "2025-11-14T15:30:00Z"
  },
  
  "forecast_settings": {
    "pert_factor": 1.5,
    "deadline": "2025-12-31",
    "data_points_count": 12
  },
  
  "jira_config": {
    "base_url": "",
    "token": "",
    "connection_tested": false,
    "test_status": "not_tested"
  },
  
  "field_mappings": {
    "auto_detected": false,
    "story_points": "",
    "deployment_date": "",
    "work_type": ""
  }
}
```

**Files to Modify**:
- Modify: `data/profile_manager.py` (update profile schema)
- Modify: `data/persistence.py` (handle enhanced profile structure)

---

### **PHASE 2: Dependency-Based UI**
*Priority: High - Core UX improvement*

#### **T004: Progressive Section Unlocking** ⭐
**Goal**: UI sections unlock based on dependency completion

**Implementation**:
```python
# callbacks/settings.py - Enhanced settings panel
@callback(
    [Output("jira-config-section", "className"),
     Output("field-mapping-section", "className"),
     Output("query-management-section", "className"),
     Output("setup-progress-display", "children")],
    Input("configuration-status-store", "data")
)
def update_section_states(config_status):
    """Enable/disable configuration sections based on dependencies."""
    
    # Progressive class assignment
    jira_class = "config-section" if config_status["profile"]["complete"] else "config-section disabled"
    fields_class = "config-section" if config_status["jira"]["complete"] else "config-section disabled" 
    queries_class = "config-section" if config_status["fields"]["complete"] else "config-section disabled"
    
    # Progress display
    progress = create_setup_progress_display(config_status)
    
    return jira_class, fields_class, queries_class, progress

def create_setup_progress_display(config_status):
    """Create visual progress indicators."""
    steps = []
    for step_name, step_info in config_status.items():
        icon = "✅" if step_info["complete"] else "⏳" if step_info["enabled"] else "🔒"
        status_text = step_info["message"]
        
        steps.append(
            html.Div([
                html.Span(f"{icon} {step_name.title()}", className="fw-bold"),
                html.Span(status_text, className="text-muted ms-2")
            ], className="setup-step mb-1")
        )
    
    return html.Div(steps, className="setup-progress")
```

**CSS Enhancement**:
```css
/* assets/custom.css */
.config-section.disabled {
    opacity: 0.5;
    pointer-events: none;
    position: relative;
}

.config-section.disabled::before {
    content: "🔒 Complete previous steps to unlock";
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: rgba(0,0,0,0.8);
    color: white;
    padding: 10px 15px;
    border-radius: 5px;
    font-size: 14px;
    z-index: 10;
}

.setup-step {
    display: flex;
    align-items: center;
    padding: 5px 0;
}
```

**Files to Modify**:
- Modify: `callbacks/settings.py` (add progressive unlock logic)
- Modify: `ui/settings_modal.py` (update section layout)
- Modify: `assets/custom.css` (add disabled section styles)

---

#### **T005: Next Step Guidance**
**Goal**: Clear guidance on what to do next

**Implementation**:
```python
# ui/setup_guidance.py - NEW FILE
def create_next_step_guidance(config_status):
    """Create next step guidance component."""
    next_step = get_next_setup_step(config_status)
    
    if not next_step:
        return dbc.Alert([
            html.I(className="fas fa-check-circle me-2"),
            "Setup Complete! ",
            dbc.Button("🚀 Launch Dashboard", color="primary", size="sm", href="/")
        ], color="success")
    
    step_guidance = {
        "jira": {
            "title": "Configure JIRA Connection",
            "description": "Connect to your JIRA instance to fetch project data",
            "action": "Enter your JIRA URL and API token above"
        },
        "fields": {
            "title": "Map JIRA Fields", 
            "description": "Map JIRA custom fields for DORA and Flow metrics",
            "action": "Use auto-detection or configure fields manually"
        },
        "queries": {
            "title": "Create Your First Query",
            "description": "Define what data to analyze with JQL queries",
            "action": "Create a query to fetch issues for analysis"
        }
    }
    
    guidance = step_guidance.get(next_step, {})
    
    return dbc.Alert([
        html.H6(f"▶️ Next: {guidance.get('title', 'Continue Setup')}", className="mb-1"),
        html.P(guidance.get('description', ''), className="mb-1 text-muted"),
        html.Small(guidance.get('action', ''), className="text-muted")
    ], color="info", className="next-step-guidance")
```

**Files to Create**:
- Create: `ui/setup_guidance.py` (guidance components)
- Modify: `ui/settings_modal.py` (integrate guidance display)

---

### **PHASE 3: Integrated Query Management**
*Priority: Medium - Workflow improvement*

#### **T006: JQL Editor Integration** ⭐
**Goal**: Move JQL editor into query management section

**Current Problem**:
```
❌ CURRENT: Separate sections
├── Query Management
│   └── [Query Dropdown] [Actions]
└── JQL Query Editor  
    └── [JQL Textarea] [Save Query] [Update Data]
```

**Target Solution**:
```
✅ TARGET: Integrated section
└── Query Management
    ├── [Query Dropdown] [Actions]
    └── Integrated JQL Editor
        ├── Name: [Input]
        ├── JQL: [Textarea] 
        └── [💾 Save Query] [🔄 Update Data]
```

**Implementation**:
```python
# ui/query_selector.py - ENHANCED
def create_integrated_query_management():
    """Create integrated query management with embedded JQL editor."""
    return dbc.Card([
        dbc.CardHeader([
            html.H6("📝 Query Management", className="mb-0")
        ]),
        dbc.CardBody([
            # Query selector and actions
            dbc.Row([
                dbc.Col([
                    dbc.Label("Active Query:"),
                    dbc.Select(
                        id="query-selector",
                        placeholder="Select query..."
                    )
                ], width=8),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("+", id="btn-create-query", size="sm", color="success"),
                        dbc.Button("📋", id="btn-duplicate-query", size="sm", color="info"),
                        dbc.Button("🗑", id="btn-delete-query", size="sm", color="danger")
                    ])
                ], width=4)
            ], className="mb-3"),
            
            # INTEGRATED JQL EDITOR (Previously separate)
            html.Div([
                dbc.Label("Query Name:"),
                dbc.Input(
                    id="query-name-input",
                    placeholder="e.g., Last 12 Weeks",
                    className="mb-2"
                ),
                
                dbc.Label("JQL Query:"),
                dbc.Textarea(
                    id="jira-jql-query",  # Same ID as existing for compatibility
                    placeholder="project = EXAMPLE AND created >= -12w",
                    rows=4,
                    className="mb-2"
                ),
                
                dbc.Label("Description (Optional):"),
                dbc.Input(
                    id="query-description-input",
                    placeholder="Analysis focus or notes",
                    className="mb-3"
                ),
                
                # Integrated action buttons
                dbc.ButtonGroup([
                    dbc.Button(
                        ["💾", " Save Query"],
                        id="save-query-btn",
                        color="primary",
                        size="sm"
                    ),
                    dbc.Button(
                        ["🔄", " Update Data"],
                        id="update-data-btn", 
                        color="secondary",
                        size="sm"
                    )
                ], className="mb-2"),
                
                # Status display
                html.Div(id="query-status-display", className="mt-2")
            ], id="jql-editor-section")
        ])
    ], className="mb-3")
```

**Callback Integration**:
```python
# callbacks/query_management.py - ENHANCED
@callback(
    [Output("query-status-display", "children"),
     Output("query-selector", "options", allow_duplicate=True)],
    Input("save-query-btn", "n_clicks"),
    [State("query-name-input", "value"),
     State("jira-jql-query", "value"),
     State("query-description-input", "value"),
     State("query-selector", "value")],
    prevent_initial_call=True
)
def save_query_integrated(n_clicks, name, jql, description, current_query_id):
    """Save query with integrated editor (no data refresh)."""
    if not n_clicks:
        return "", no_update
    
    try:
        profile_id = get_active_profile_id()
        
        # Update or create query
        if current_query_id and current_query_id != "new":
            # Update existing query
            update_query(profile_id, current_query_id, {
                "name": name,
                "jql": jql,
                "description": description,
                "last_edited": datetime.now().isoformat()
            })
            message = f"✅ Query '{name}' updated"
        else:
            # Create new query
            query_id = create_query(profile_id, {
                "name": name,
                "jql": jql, 
                "description": description
            })
            switch_query(profile_id, query_id)
            message = f"✅ Query '{name}' created"
        
        # Refresh query selector options
        updated_queries = list_queries_for_profile(profile_id)
        options = [{"label": q["name"], "value": q["id"]} for q in updated_queries]
        
        status_alert = dbc.Alert(message, color="success", dismissable=True, duration=3000)
        
        return status_alert, options
        
    except Exception as e:
        error_alert = dbc.Alert(f"❌ Error saving query: {e}", color="danger", dismissable=True, duration=5000)
        return error_alert, no_update

@callback(
    Output("query-status-display", "children", allow_duplicate=True),
    Input("update-data-btn", "n_clicks"),
    prevent_initial_call=True
)
def update_data_for_query(n_clicks):
    """Trigger data refresh for current query (separate from save)."""
    if not n_clicks:
        return ""
    
    try:
        # Trigger data refresh workflow
        from callbacks.settings import handle_unified_data_update
        # ... implementation
        
        return dbc.Alert("🔄 Data update started...", color="info", dismissable=True, duration=3000)
    except Exception as e:
        return dbc.Alert(f"❌ Data update failed: {e}", color="danger", dismissable=True, duration=5000)
```

**Files to Modify**:
- Modify: `ui/query_selector.py` (integrate JQL editor)
- Modify: `callbacks/query_management.py` (add integrated save logic)
- Remove: JQL editor from `ui/settings_modal.py`

---

#### **T007: Cascade Query Loading**
**Goal**: Query selection automatically loads JQL into editor

**Implementation**:
```python
# callbacks/query_management.py - ENHANCED
@callback(
    [Output("query-name-input", "value"),
     Output("jira-jql-query", "value", allow_duplicate=True),
     Output("query-description-input", "value")],
    Input("query-selector", "value"),
    prevent_initial_call=True
)
def load_query_into_editor(query_id):
    """Load selected query details into integrated editor."""
    if not query_id or query_id == "new":
        return "", "", ""
    
    try:
        profile_id = get_active_profile_id()
        query_config = get_query(profile_id, query_id)
        
        return (
            query_config.get("name", ""),
            query_config.get("jql", ""),
            query_config.get("description", "")
        )
    except Exception as e:
        logger.error(f"Failed to load query {query_id}: {e}")
        return "", "", ""
```

---

### **PHASE 4: Enhanced UX & Polish**
*Priority: Low - Nice to have*

#### **T008: JIRA Field Auto-Detection**
**Goal**: Auto-detect common JIRA fields after connection test

#### **T009: Setup Completion Wizard**
**Goal**: Guided first-run experience

#### **T010: Query Validation**
**Goal**: Validate JQL and show estimated result counts

---

## 🧪 **Testing Strategy**

### **Auto-Setup Tests** (Critical)
```python
# tests/integration/test_auto_setup.py
def test_first_run_auto_setup():
    """Test fresh installation auto-creates defaults."""
    # Delete all configuration
    if os.path.exists("profiles.json"):
        os.remove("profiles.json")
    if os.path.exists("profiles/"):
        shutil.rmtree("profiles/")
    
    # Import app (triggers auto-setup)
    import app
    
    # Verify defaults created
    assert profile_exists("default")
    assert get_active_profile().id == "default"
    assert len(list_queries_for_profile("default")) >= 1
    assert get_active_query() is not None

def test_corrupted_config_recovery():
    """Test auto-recovery from corrupted configuration."""
    # Create corrupted profile
    create_corrupted_profile_json()
    
    # Import app (triggers auto-recovery)
    import app
    
    # Verify recovery
    assert profile_exists("default")
    assert get_configuration_status()["profile"]["complete"]
```

### **Dependency Tests** (Critical)
```python
def test_progressive_unlock():
    """Test UI sections unlock based on dependencies."""
    # Start with clean profile
    create_clean_default_profile()
    
    status = get_configuration_status()
    
    # Profile ready, others not
    assert status["profile"]["complete"] == True
    assert status["jira"]["enabled"] == True
    assert status["jira"]["complete"] == False
    assert status["fields"]["enabled"] == False
    assert status["queries"]["enabled"] == False
```

### **Integration Tests** (High)
```python
def test_integrated_query_workflow():
    """Test complete integrated query management workflow."""
    # Setup profile with JIRA
    setup_profile_with_jira()
    
    # Create query via integrated editor
    result = save_query_integrated(
        n_clicks=1,
        name="Test Query",
        jql="project = TEST",
        description="Test",
        current_query_id="new"
    )
    
    # Verify query created
    queries = list_queries_for_profile("default")
    assert any(q["name"] == "Test Query" for q in queries)
    
    # Verify JQL saved
    query = get_query("default", "test-query")
    assert query["jql"] == "project = TEST"
```

---

## 📊 **Success Metrics**

### **Functionality Metrics**
- ✅ **Auto-Setup**: Fresh install creates valid defaults in <5 seconds
- ✅ **Dependency Enforcement**: Cannot access locked sections 
- ✅ **Recovery**: Corrupted config auto-recovers without user intervention
- ✅ **Integration**: Single "Save Query" action creates query with JQL

### **UX Metrics** 
- ✅ **Progressive Clarity**: Each step shows clear next action
- ✅ **No Dead Ends**: Every configuration screen leads somewhere
- ✅ **Time to Dashboard**: New user reaches working dashboard in <5 minutes
- ✅ **Workflow Efficiency**: Create query + edit JQL in single component

### **Technical Metrics**
- ✅ **Startup Time**: Auto-setup adds <1 second to app startup
- ✅ **Error Recovery**: 100% recovery rate from common configuration errors
- ✅ **Code Quality**: Dependency validation centralizes all logic
- ✅ **Maintainability**: Adding new setup steps requires minimal code changes

---

This implementation plan addresses all the identified dependency and UX issues while maintaining compatibility with existing functionality.
