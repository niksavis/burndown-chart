# Feature 012: Implementation Tasks

**Feature**: Enhanced Import/Export & HTML Reporting  
**Branch**: `012-import-export-reporting`  
**Estimated**: 30-38 hours (3-5 days)

---

## Task Breakdown

### Phase 1: Enhanced Export (6-8 hours)

#### T001: Create Import/Export Tab in Data Panel
**Priority**: HIGH  
**Estimate**: 1.5 hours  
**File**: `ui/import_export_panel.py`

**Implementation**:
```python
def create_import_export_panel():
    """Create tabbed Data panel with Import/Export and Reports tabs."""
    return dbc.Tabs([
        dbc.Tab(
            create_import_export_tab(),
            label="Import/Export",
            tab_id="import-export-tab"
        ),
        dbc.Tab(
            create_reports_tab(),
            label="Reports",
            tab_id="reports-tab"
        )
    ], id="data-panel-tabs", active_tab="import-export-tab")
```

**Checklist**:
- [ ] Extract current import/export UI to dedicated function
- [ ] Create dbc.Tabs wrapper
- [ ] Move existing upload component to first tab
- [ ] Update callbacks to use new component IDs
- [ ] Test tab switching

---

#### T002: Add Export Options UI
**Priority**: HIGH  
**Estimate**: 2 hours  
**File**: `ui/import_export_panel.py`

**Implementation**:
```python
def create_export_options_ui():
    """Create export options section with radio buttons and checkboxes."""
    return dbc.Card([
        dbc.CardHeader("Export Project Data"),
        dbc.CardBody([
            dbc.RadioItems(
                id="export-type-radio",
                options=[
                    {"label": "Quick Export (Statistics & Metrics Only)", "value": "quick"},
                    {"label": "Full Profile Backup (Complete Project State)", "value": "full"}
                ],
                value="full"
            ),
            dbc.Collapse(
                id="export-options-collapse",
                is_open=True,
                children=[
                    dbc.Checklist(
                        id="export-options-checklist",
                        options=[
                            {"label": "Include DORA/Flow Metrics Snapshots", "value": "metrics"},
                            {"label": "Include Query Definitions", "value": "queries"},
                            {"label": "Include JIRA Cache (~15MB)", "value": "cache"},
                            {"label": "Include JIRA Credentials (⚠️ Warning)", "value": "credentials"}
                        ],
                        value=["metrics", "queries"]
                    )
                ]
            ),
            html.Div(id="export-size-estimate", className="text-muted"),
            dbc.Button("Export Profile ZIP", id="export-profile-button", color="primary"),
            dcc.Download(id="export-profile-download")
        ])
    ])
```

**Checklist**:
- [ ] Create radio button group for export type
- [ ] Create checkboxes for export options
- [ ] Add collapse for full export options
- [ ] Add help tooltips with icons
- [ ] Add size estimate display
- [ ] Style with Bootstrap classes

---

#### T003: Create Export Callback
**Priority**: HIGH  
**Estimate**: 2 hours  
**File**: `callbacks/import_export.py` (new)

**Implementation**:
```python
@app.callback(
    [
        Output("export-profile-download", "data"),
        Output("export-status-toast", "is_open")
    ],
    [
        Input("export-profile-button", "n_clicks"),
    ],
    [
        State("export-type-radio", "value"),
        State("export-options-checklist", "value")
    ],
    prevent_initial_call=True
)
def export_profile_callback(n_clicks, export_type, options):
    """Export profile with selected options."""
    from data.import_export import export_profile_enhanced
    from data.profile_manager import get_active_profile_id
    
    if not n_clicks:
        raise PreventUpdate
    
    profile_id = get_active_profile_id()
    include_cache = "cache" in options
    include_queries = "queries" in options
    
    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M")
    filename = f"profile_backup_{timestamp}.zip"
    
    # Call backend export
    success, message = export_profile_enhanced(
        profile_id,
        filename,
        include_cache=include_cache,
        include_queries=include_queries,
        export_type="backup" if export_type == "full" else "quick"
    )
    
    if success:
        return dict(filename=filename), True
    else:
        return no_update, True
```

**Checklist**:
- [ ] Create callback file with proper imports
- [ ] Handle export type selection
- [ ] Handle export options checkboxes
- [ ] Call `export_profile_enhanced()`
- [ ] Generate timestamped filename
- [ ] Return dcc.Download data
- [ ] Add error handling
- [ ] Show success/failure toast

---

#### T004: Update Current Export to Include Snapshots
**Priority**: MEDIUM  
**Estimate**: 1 hour  
**File**: `callbacks/visualization.py`

**Implementation**:
```python
def export_project_data(n_clicks):
    """Export project data including metrics snapshots."""
    from data.persistence import load_unified_project_data
    from data.metrics_snapshots import load_snapshots
    
    project_data = load_unified_project_data()
    metrics_snapshots = load_snapshots()
    
    # Combine for export
    export_data = {
        "version": "3.0",
        "exported_at": datetime.now().isoformat(),
        "export_type": "quick",
        "project_data": project_data,
        "metrics_snapshots": metrics_snapshots
    }
    
    filename = f"project_data_{datetime.now().strftime('%Y%m%d_%H%M')}.json"
    return dict(
        content=json.dumps(export_data, indent=2),
        filename=filename,
        type="application/json"
    )
```

**Checklist**:
- [ ] Import metrics_snapshots module
- [ ] Load snapshots data
- [ ] Combine with project_data
- [ ] Add version and export metadata
- [ ] Keep backward compatible format
- [ ] Test import of new format

---

#### T005: Add Cache Size Calculation
**Priority**: LOW  
**Estimate**: 1 hour  
**File**: `data/import_export.py`

**Implementation**:
```python
def get_export_size_estimate(
    profile_id: str,
    include_cache: bool = False,
    include_queries: bool = True
) -> Tuple[int, str]:
    """Calculate estimated export file size.
    
    Returns:
        Tuple of (bytes, human_readable_string)
    """
    from data.profile_manager import get_profile_file_path, PROFILES_DIR
    
    total_size = 0
    
    # Profile config (~50KB)
    profile_path = get_profile_file_path(profile_id)
    if profile_path.exists():
        total_size += profile_path.stat().st_size
    
    # Queries (~10KB each)
    if include_queries:
        queries_dir = PROFILES_DIR / profile_id / "queries"
        if queries_dir.exists():
            for query_file in queries_dir.rglob("query.json"):
                total_size += query_file.stat().st_size
    
    # Cache files (large)
    if include_cache:
        cache_files = [
            "project_data.json",
            "metrics_snapshots.json",
            "jira_cache.json",
            "jira_changelog_cache.json"
        ]
        for query_dir in (PROFILES_DIR / profile_id / "queries").glob("q_*"):
            for cache_file in cache_files:
                cache_path = query_dir / cache_file
                if cache_path.exists():
                    total_size += cache_path.stat().st_size
    
    # Format as human-readable
    if total_size < 1024:
        size_str = f"{total_size} bytes"
    elif total_size < 1024 * 1024:
        size_str = f"{total_size / 1024:.1f} KB"
    else:
        size_str = f"{total_size / (1024 * 1024):.1f} MB"
    
    return total_size, size_str
```

**Checklist**:
- [ ] Calculate profile.json size
- [ ] Calculate queries size
- [ ] Calculate cache files size
- [ ] Format as human-readable
- [ ] Add to export options callback
- [ ] Update on checkbox change

---

#### T006: Export Integration Tests
**Priority**: MEDIUM  
**Estimate**: 1.5 hours  
**File**: `tests/integration/test_import_export.py`

**Implementation**:
```python
def test_export_without_cache(temp_profile):
    """Test export creates minimal ZIP."""
    from data.import_export import export_profile_enhanced
    
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        temp_zip = f.name
    
    success, message = export_profile_enhanced(
        temp_profile,
        temp_zip,
        include_cache=False,
        include_queries=True
    )
    
    assert success
    assert Path(temp_zip).exists()
    
    # Verify ZIP contents
    with zipfile.ZipFile(temp_zip) as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "profile.json" in names
        assert "queries/" in [n.split("/")[0] for n in names]
        assert "cache/" not in [n.split("/")[0] for n in names]
```

**Checklist**:
- [ ] Test export without cache (< 1MB)
- [ ] Test export with cache (verify files)
- [ ] Test credentials redaction
- [ ] Test ZIP structure validation
- [ ] Test with multiple queries

---

### Phase 2: Enhanced Import (6-8 hours)

#### T007: Extend Import Callback for ZIP Files
**Priority**: HIGH  
**Estimate**: 2 hours  
**File**: `callbacks/statistics.py`

**Implementation**:
```python
def update_table(n_clicks, contents, data_timestamp, rows, filename, is_sample_data):
    """Handle file upload - CSV, JSON, or ZIP."""
    
    # ... existing CSV/JSON logic ...
    
    if filename.lower().endswith('.zip'):
        # Profile ZIP import
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        
        # Write to temp file
        with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
            f.write(decoded)
            temp_zip = f.name
        
        try:
            from data.import_export import import_profile_enhanced
            
            success, message, profile_id = import_profile_enhanced(
                temp_zip,
                preserve_setup_status=True,
                validate_dependencies=False
            )
            
            if success:
                # Show success notification
                return (
                    no_update,  # Keep table
                    False,  # Not sample data
                    None,  # Clear upload
                    f"Profile '{profile_id}' imported successfully"
                )
            else:
                return no_update, is_sample_data, None, f"Import failed: {message}"
        finally:
            os.unlink(temp_zip)
```

**Checklist**:
- [ ] Detect .zip extension
- [ ] Decode and write to temp file
- [ ] Call import_profile_enhanced()
- [ ] Handle success/failure
- [ ] Clean up temp file
- [ ] Show import notification
- [ ] Keep existing CSV/JSON logic

---

#### T008: Update Upload Component
**Priority**: MEDIUM  
**Estimate**: 1 hour  
**File**: `ui/import_export_panel.py`

**Implementation**:
```python
dcc.Upload(
    id="upload-data",
    children=html.Div([
        html.I(className="fas fa-cloud-upload-alt fa-3x mb-2"),
        html.P("Drag & Drop or Click to Browse"),
        html.Small([
            "Supported formats: ",
            html.Span(".zip ", className="badge bg-primary"),
            html.Span(".json ", className="badge bg-info"),
            html.Span(".csv", className="badge bg-success")
        ])
    ]),
    accept=".zip,.json,.csv",
    multiple=False
)
```

**Checklist**:
- [ ] Update accept attribute
- [ ] Add file type badges
- [ ] Update help text
- [ ] Show preview after selection
- [ ] Display file size

---

#### T009: Add Import Validation
**Priority**: HIGH  
**Estimate**: 2 hours  
**File**: `data/import_export.py`

**Implementation**:
```python
def validate_import_package(import_path: str) -> Tuple[bool, str, Dict]:
    """Validate imported ZIP structure and contents.
    
    Returns:
        Tuple of (is_valid, error_message, metadata)
    """
    try:
        with zipfile.ZipFile(import_path) as zf:
            names = zf.namelist()
            
            # Check required files
            if "manifest.json" not in names:
                return False, "Missing manifest.json", {}
            
            if "profile.json" not in names:
                return False, "Missing profile.json", {}
            
            # Load and validate manifest
            with zf.open("manifest.json") as f:
                manifest = json.load(f)
            
            # Check version compatibility
            version = manifest.get("version", "0.0")
            if version != "1.0":
                return False, f"Unsupported version: {version}", {}
            
            # Load profile metadata
            with zf.open("profile.json") as f:
                profile = json.load(f)
            
            metadata = {
                "profile_name": profile.get("name", "Unknown"),
                "exported_at": manifest.get("created_at"),
                "includes_cache": manifest.get("includes_cache", False),
                "query_count": len([n for n in names if n.startswith("queries/")])
            }
            
            return True, "", metadata
            
    except zipfile.BadZipFile:
        return False, "Invalid ZIP file", {}
    except json.JSONDecodeError as e:
        return False, f"Corrupted manifest: {e}", {}
    except Exception as e:
        return False, f"Validation failed: {e}", {}
```

**Checklist**:
- [ ] Validate ZIP structure
- [ ] Check manifest version
- [ ] Validate profile.json schema
- [ ] Check cache file integrity
- [ ] Return validation metadata
- [ ] Add detailed error messages

---

#### T010: Import Success/Failure Feedback
**Priority**: MEDIUM  
**Estimate**: 1.5 hours  
**File**: `callbacks/import_export.py`

**Implementation**:
```python
# Add modal for import result
dbc.Modal([
    dbc.ModalHeader("Profile Import Result"),
    dbc.ModalBody(id="import-result-body"),
    dbc.ModalFooter([
        dbc.Button("Switch to Profile", id="switch-to-imported-profile"),
        dbc.Button("Close", id="close-import-modal")
    ])
], id="import-result-modal", is_open=False)

@app.callback(
    Output("import-result-modal", "is_open"),
    Output("import-result-body", "children"),
    Input("upload-data-success", "data")
)
def show_import_result(import_data):
    """Display import success/failure modal."""
    if not import_data:
        raise PreventUpdate
    
    if import_data["success"]:
        body = html.Div([
            html.I(className="fas fa-check-circle text-success fa-3x mb-3"),
            html.H5("Profile Imported Successfully"),
            html.P(f"Profile: {import_data['profile_name']}"),
            html.P(f"Queries: {import_data['query_count']} imported"),
            html.P(f"Cache: {import_data['cache_size']} loaded"),
            html.Hr(),
            html.P("All metrics available offline - no JIRA connection needed.", 
                   className="text-muted")
        ])
    else:
        body = html.Div([
            html.I(className="fas fa-exclamation-circle text-danger fa-3x mb-3"),
            html.H5("Import Failed"),
            html.P(import_data["error"], className="text-danger"),
            html.P("Please check the file and try again.", className="text-muted")
        ])
    
    return True, body
```

**Checklist**:
- [ ] Create import result modal
- [ ] Show success details
- [ ] Show error details
- [ ] Add "Switch to Profile" button
- [ ] Auto-close after 10 seconds

---

#### T011: Profile ID Conflict Resolution
**Priority**: MEDIUM  
**Estimate**: 1 hour  
**File**: `data/import_export.py`

Already implemented in `_generate_unique_profile_id()`. Just verify:

**Checklist**:
- [ ] Test import with existing profile ID
- [ ] Verify unique ID generation
- [ ] Verify original name preserved
- [ ] Test with multiple conflicts

---

#### T012: Import Integration Tests
**Priority**: MEDIUM  
**Estimate**: 1.5 hours  
**File**: `tests/integration/test_import_export.py`

**Implementation**:
```python
def test_import_profile_with_cache(temp_export_zip):
    """Test import restores complete offline capability."""
    from data.import_export import import_profile_enhanced
    from data.persistence import load_unified_project_data
    from data.metrics_snapshots import load_snapshots
    
    # Import
    success, message, profile_id = import_profile_enhanced(
        temp_export_zip,
        validate_dependencies=False
    )
    
    assert success
    assert profile_id is not None
    
    # Switch to imported profile
    from data.profile_manager import switch_profile
    switch_profile(profile_id)
    
    # Verify data loads without JIRA
    project_data = load_unified_project_data()
    assert len(project_data["statistics"]) > 0
    
    metrics = load_snapshots()
    assert len(metrics) > 0
```

**Checklist**:
- [ ] Test import without cache
- [ ] Test import with cache (verify offline)
- [ ] Test import with duplicate ID
- [ ] Test import corrupted ZIP
- [ ] Test import legacy JSON

---

### Phase 3: HTML Report Generation (10-12 hours)

#### T013: Create Report Generator Module ✅
**Priority**: HIGH  
**Estimate**: 3 hours  
**File**: `data/report_generator.py` (new)

**Implementation**:
```python
def generate_html_report(
    profile_id: str,
    query_id: str,
    weeks: int = 12,
    sections: List[str] = None
) -> str:
    """Generate self-contained HTML report.
    
    Args:
        profile_id: Profile to report on
        query_id: Query to report on
        weeks: Number of weeks to include
        sections: List of sections ["burndown", "dora", "flow", "all"]
    
    Returns:
        HTML string with embedded charts and CSS
    """
    from data.persistence import load_unified_project_data
    from data.metrics_snapshots import load_snapshots
    from data.profile_manager import get_profile
    from jinja2 import Template
    
    # Load data
    project_data = load_unified_project_data()
    metrics = load_snapshots()
    profile = get_profile(profile_id)
    
    # Generate charts
    charts = {}
    if "burndown" in sections or "all" in sections:
        charts["burndown"] = generate_burndown_chart(project_data, weeks)
    
    if "dora" in sections or "all" in sections:
        charts["dora"] = generate_dora_charts(metrics, weeks)
    
    if "flow" in sections or "all" in sections:
        charts["flow"] = generate_flow_charts(metrics, weeks)
    
    # Load template
    template_path = Path(__file__).parent / "report_template.html"
    with open(template_path) as f:
        template = Template(f.read())
    
    # Render
    html = template.render(
        profile=profile,
        project_data=project_data,
        charts=charts,
        generated_at=datetime.now(),
        weeks=weeks
    )
    
    return html
```

**Checklist**:
- [x] Create module structure
- [x] Load data from cache files
- [x] Generate chart JSON
- [x] Render Jinja2 template
- [x] Return complete HTML string
- [x] Add error handling

---

#### T014: Create HTML Report Template ✅
**Priority**: HIGH  
**Estimate**: 2 hours  
**File**: `data/report_template.html` (new)

**Implementation**:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Metrics Report - {{ profile.name }} - {{ generated_at.strftime('%Y-%m-%d') }}</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        /* Embedded CSS - App theme */
        :root {
            --primary: #0d6efd;
            --secondary: #6c757d;
            --success: #198754;
            --danger: #dc3545;
            --warning: #ffc107;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            background: #f8f9fa;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: white;
        }
        header {
            border-bottom: 3px solid var(--primary);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 { color: var(--primary); margin: 0; }
        .metadata { color: #6c757d; margin-top: 10px; }
        .metric-card {
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .metric-value {
            font-size: 2rem;
            font-weight: bold;
            color: var(--primary);
        }
        footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
            text-align: center;
            color: #6c757d;
        }
        @media print {
            .no-print { display: none; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>📊 Metrics Report: {{ profile.name }}</h1>
            <div class="metadata">
                Generated: {{ generated_at.strftime('%Y-%m-%d %H:%M:%S') }} |
                Period: {{ weeks }} weeks |
                Query: {{ project_data.metadata.jira_query }}
            </div>
        </header>

        {% if 'burndown' in charts %}
        <section id="burndown">
            <h2>Burndown & Velocity</h2>
            <div id="burndown-chart"></div>
            <script>
                var burndownData = {{ charts.burndown | tojson }};
                Plotly.newPlot('burndown-chart', burndownData.data, burndownData.layout, {responsive: true});
            </script>
        </section>
        {% endif %}

        {% if 'dora' in charts %}
        <section id="dora-metrics">
            <h2>DORA Metrics</h2>
            <!-- DORA charts -->
        </section>
        {% endif %}

        {% if 'flow' in charts %}
        <section id="flow-metrics">
            <h2>Flow Metrics</h2>
            <!-- Flow charts -->
        </section>
        {% endif %}

        <footer>
            <p>Generated by Burndown Chart Generator v3.0</p>
            <p>Data as of {{ project_data.metadata.last_updated }}</p>
        </footer>
    </div>
</body>
</html>
```

**Checklist**:
- [x] Create template structure
- [x] Add responsive CSS
- [x] Add print styles
- [x] Create chart placeholders
- [x] Add Jinja2 variables
- [x] Test template rendering

---

#### T015: Chart Embedding Functions ✅
**Priority**: HIGH  
**Estimate**: 2.5 hours  
**File**: `data/report_generator.py`

**Implementation**:
```python
def generate_burndown_chart(project_data: Dict, weeks: int) -> Dict:
    """Generate Plotly chart JSON for burndown."""
    from visualization.burndown_chart import create_burndown_chart
    
    # Use existing visualization function
    fig = create_burndown_chart(
        project_data["statistics"],
        project_data["project_scope"]["total_items"],
        weeks
    )
    
    # Convert to JSON (Plotly format)
    return fig.to_dict()

def generate_dora_charts(metrics: Dict, weeks: int) -> Dict:
    """Generate DORA metric sparkline charts."""
    from data.time_period_calculator import get_iso_week, format_year_week
    
    # Get week labels
    week_labels = []
    current_date = datetime.now()
    for i in range(weeks):
        year, week = get_iso_week(current_date)
        week_labels.append(format_year_week(year, week))
        current_date = current_date - timedelta(days=7)
    week_labels.reverse()
    
    # Extract values
    deploy_freq = [
        metrics.get(week, {}).get("deployment_frequency", {}).get("count", 0)
        for week in week_labels
    ]
    
    lead_time = [
        metrics.get(week, {}).get("lead_time_for_changes", {}).get("median_hours", 0) / 24
        for week in week_labels
    ]
    
    # Create Plotly figures
    charts = {
        "deployment_frequency": {
            "data": [{
                "x": week_labels,
                "y": deploy_freq,
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Deployments"
            }],
            "layout": {
                "title": "Deployment Frequency",
                "xaxis": {"title": "Week"},
                "yaxis": {"title": "Deployments"}
            }
        },
        "lead_time": {
            "data": [{
                "x": week_labels,
                "y": lead_time,
                "type": "scatter",
                "mode": "lines+markers",
                "name": "Lead Time"
            }],
            "layout": {
                "title": "Lead Time for Changes",
                "xaxis": {"title": "Week"},
                "yaxis": {"title": "Days"}
            }
        }
    }
    
    return charts
```

**Checklist**:
- [x] Implement burndown chart generation
- [x] Implement DORA charts generation
- [x] Implement Flow charts generation
- [x] Convert Plotly figures to JSON
- [x] Test chart rendering in HTML

---

#### T016: Add Report Generation UI ✅
**Priority**: MEDIUM  
**Estimate**: 1.5 hours  
**File**: `ui/import_export_panel.py`

**Implementation**:
```python
def create_reports_tab():
    """Create Reports tab UI."""
    return dbc.Card([
        dbc.CardHeader("Generate HTML Report"),
        dbc.CardBody([
            html.H6("Report Sections:"),
            dbc.Checklist(
                id="report-sections-checklist",
                options=[
                    {"label": "Burndown Chart & Velocity", "value": "burndown"},
                    {"label": "DORA Metrics Dashboard", "value": "dora"},
                    {"label": "Flow Metrics Dashboard", "value": "flow"},
                    {"label": "All Sections", "value": "all"}
                ],
                value=["burndown", "dora", "flow"]
            ),
            html.Hr(),
            html.H6("Time Period:"),
            dbc.RadioItems(
                id="report-time-period-radio",
                options=[
                    {"label": "Last 4 weeks", "value": 4},
                    {"label": "Last 12 weeks", "value": 12},
                    {"label": "Last 26 weeks", "value": 26},
                    {"label": "Last 52 weeks", "value": 52}
                ],
                value=12
            ),
            html.Hr(),
            html.Div(id="report-size-estimate", className="text-muted mb-3"),
            dbc.Button("Generate HTML Report", id="generate-report-button", color="success"),
            dcc.Download(id="report-download")
        ])
    ])
```

**Checklist**:
- [x] Create report sections checkboxes
- [x] Create time period radio buttons
- [x] Add generate button
- [x] Add size estimate display
- [x] Add dcc.Download component

---

#### T017: Create Report Callback ✅
**Priority**: HIGH  
**Estimate**: 1.5 hours  
**File**: `callbacks/import_export.py`

**Implementation**:
```python
@app.callback(
    Output("report-download", "data"),
    Input("generate-report-button", "n_clicks"),
    [
        State("report-sections-checklist", "value"),
        State("report-time-period-radio", "value")
    ],
    prevent_initial_call=True
)
def generate_report_callback(n_clicks, sections, weeks):
    """Generate HTML report and trigger download."""
    if not n_clicks:
        raise PreventUpdate
    
    from data.report_generator import generate_html_report
    from data.profile_manager import get_active_profile_id
    from data.query_manager import get_active_query_id
    
    try:
        # Generate report
        profile_id = get_active_profile_id()
        query_id = get_active_query_id()
        
        html = generate_html_report(
            profile_id,
            query_id,
            weeks=weeks,
            sections=sections
        )
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"metrics_report_{timestamp}.html"
        
        return dict(
            content=html,
            filename=filename,
            type="text/html"
        )
        
    except Exception as e:
        logger.error(f"Report generation failed: {e}")
        return no_update
```

**Checklist**:
- [x] Create callback with inputs
- [x] Call report generator
- [x] Handle sections selection
- [x] Generate filename
- [x] Return dcc.Download
- [x] Add error handling
- [x] Add progress bar
- [x] Add background task execution

---

#### T018: Report Metadata and Branding ✅
**Priority**: LOW  
**Estimate**: 0.5 hours  
**File**: `data/report_template.html`

**Checklist**:
- [x] Add export timestamp
- [x] Add profile name
- [x] Add query info
- [x] Add footer with branding
- [x] Add cache age indicators

---

#### T019: Report Generation Tests
**Priority**: MEDIUM  
**Estimate**: 1.5 hours  
**File**: `tests/unit/data/test_report_generator.py` (new)

**Implementation**:
```python
def test_generate_report_all_sections(temp_profile_with_data):
    """Test report generation with all sections."""
    from data.report_generator import generate_html_report
    
    html = generate_html_report(
        temp_profile_with_data,
        "q_test",
        weeks=12,
        sections=["burndown", "dora", "flow"]
    )
    
    assert "<!DOCTYPE html>" in html
    assert "Burndown" in html
    assert "DORA" in html
    assert "Flow" in html
    assert "Plotly.newPlot" in html
    assert len(html) < 2 * 1024 * 1024  # < 2MB
```

**Checklist**:
- [ ] Test all sections
- [ ] Test subset of sections
- [ ] Test HTML structure
- [ ] Verify file size < 2MB
- [ ] Test chart data embedding

---

#### T020: Report Rendering Validation (Playwright)
**Priority**: LOW  
**Estimate**: 1 hour  
**File**: `tests/integration/test_report_rendering.py`

**Implementation**:
```python
def test_report_renders_in_browser(temp_report_file):
    """Test generated HTML renders correctly in browser."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"file://{temp_report_file}")
        
        # Verify charts render
        page.wait_for_selector("#burndown-chart .plotly", timeout=5000)
        
        # Test interactivity
        chart = page.locator("#burndown-chart .plotly")
        assert chart.is_visible()
        
        browser.close()
```

**Checklist**:
- [ ] Test HTML opens in browser
- [ ] Verify charts render
- [ ] Test hover interactions
- [ ] Test responsive layout

---

### Phase 4: UI Polish (8-10 hours)

Detailed tasks T021-T027 omitted for brevity. Key activities:
- Refactor Data panel to tabs
- Add help tooltips
- Add progress indicators
- Add export history
- Add report preview
- Add logging
- E2E workflow tests

---

## Implementation Order

### Sprint 1 (Day 1-2): Core Export/Import
1. T001 - Create tabbed panel
2. T002 - Export options UI
3. T003 - Export callback
4. T004 - Update current export
5. T007 - Extend import callback
6. T008 - Update upload component

**Milestone**: Full profile export/import working in UI

---

### Sprint 2 (Day 3): Report Generation
7. T013 - Report generator module
8. T014 - HTML template
9. T015 - Chart embedding
10. T016 - Report UI
11. T017 - Report callback

**Milestone**: HTML report generation working

---

### Sprint 3 (Day 4-5): Testing & Polish
12. T006 - Export tests
13. T012 - Import tests
14. T019 - Report tests
15. T020 - Report rendering tests
16. T021-T027 - UI polish tasks

**Milestone**: Feature complete with full test coverage

---

## Definition of Done

### Per Task
- [ ] Code implemented following constitution
- [ ] Type hints added
- [ ] Logger statements added
- [ ] Unit tests written (if applicable)
- [ ] Manual testing completed
- [ ] No errors in `get_errors` tool
- [ ] Code reviewed

### Per Phase
- [ ] All phase tasks completed
- [ ] Integration tests passing
- [ ] Performance targets met
- [ ] Documentation updated
- [ ] Demo prepared

### Feature Complete
- [ ] All 27 tasks completed
- [ ] All tests passing (unit + integration + e2e)
- [ ] Zero errors/warnings
- [ ] Documentation complete
- [ ] User acceptance testing passed
- [ ] Ready for merge to main

---

## Notes

- Follow constitution principles (layered architecture, test isolation)
- Use existing backend functions where possible
- Maintain backward compatibility
- Add comprehensive logging
- Test on Windows (PowerShell)
- No customer data in examples

---

**Created**: 2025-12-15  
**Branch**: `012-import-export-reporting`  
**Estimated Completion**: 3-5 days
