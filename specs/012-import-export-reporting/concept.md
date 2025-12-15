# Feature 012: Enhanced Import/Export & HTML Reporting

**Version**: 1.0.0  
**Status**: Concept  
**Created**: 2025-12-15  
**Author**: AI Agent (GitHub Copilot)

---

## Executive Summary

**Problem**: The current "Export Project Data" only exports basic statistics (`project_data.json`), making it impossible to:
- Share complete project state with teammates
- Work offline with full DORA/Flow metrics
- Create portable reports for stakeholders
- Backup and restore complete project configuration

**Proposed Solution**: Implement comprehensive import/export system with three capabilities:

1. **Full Profile Export/Import**: Complete offline capability with all cache files
2. **HTML Report Generation**: Self-contained single-page reports with embedded data/charts
3. **Enhanced Data Panel UI**: Unified access point for all data operations

**Key Benefits**:
- ✅ **Offline capability**: Import full profile and work without JIRA connection
- ✅ **Team collaboration**: Share complete project state including metrics history
- ✅ **Stakeholder reporting**: Generate portable HTML reports with interactive charts
- ✅ **Data portability**: Backup/restore complete project configuration
- ✅ **Historical analysis**: Preserve project state after JIRA archives

**Implementation Complexity**: Medium (3-4 days)
- Leverage existing `export_profile_enhanced()` function
- Create HTML report generator with embedded Plotly charts
- Extend Data panel UI with tabbed interface

---

## Problem Analysis

### Current State

**Existing Export** (`callbacks/visualization.py::export_project_data`):
```python
def export_project_data(n_clicks):
    """Export only project_data.json (statistics + scope)"""
    project_data = load_unified_project_data()
    return dict(content=json.dumps(project_data, indent=2), ...)
```

**What's Exported**:
- ✅ `project_data.json`: Statistics, scope, velocity

**What's Missing**:
- ❌ `metrics_snapshots.json`: DORA/Flow metrics (critical)
- ❌ `profile.json`: JIRA config, field mappings
- ❌ `jira_cache.json`: Issue details
- ❌ `jira_changelog_cache.json`: Status histories
- ❌ `query.json`: Query metadata

**Impact**:
- Imported data only shows burndown charts
- DORA/Flow dashboards display "No Data"
- Cannot work offline (metrics not preserved)

### Backend Capability Already Exists

**Full Export** (`data/import_export.py::export_profile_enhanced`):
```python
def export_profile_enhanced(
    profile_id: str,
    export_path: str,
    include_cache: bool = False,
    include_queries: bool = True,
    export_type: str = "backup"
) -> Tuple[bool, str]:
    """Export complete profile as ZIP with all configuration and optional cache"""
```

**Export Structure**:
```
profile_backup.zip
├── manifest.json              # Export metadata
├── profile.json               # JIRA config, field mappings, settings
├── queries/
│   ├── q_5680de66ba78.json   # Query definitions
│   └── q_641c9d97614a.json
└── cache/                     # Optional (include_cache=True)
    ├── project_data.json      # Statistics, scope
    ├── metrics_snapshots.json # DORA/Flow pre-calculated
    ├── jira_cache.json        # Issue details (~5MB)
    └── jira_changelog_cache.json # Status histories (~10MB)
```

**Status**: ✅ Fully implemented, ❌ NOT exposed in UI

### Reporting Gap

**Current Limitations**:
- No way to generate portable reports for stakeholders
- Screenshots required for sharing metrics with non-technical users
- Cannot embed interactive charts in documentation
- No single-page summary view for executive reviews

**Desired**: Self-contained HTML report with:
- Embedded Plotly charts (interactive)
- Metric summary cards
- CSS styling (no external dependencies)
- Works offline (open in any browser)

---

## User Stories

### US1: Full Profile Backup for Offline Work

**As a** developer traveling without internet  
**I want to** export my complete project including metrics  
**So that** I can analyze DORA/Flow data offline

**Acceptance Criteria**:
- [ ] Export creates ZIP with all cache files
- [ ] Export preserves JIRA configuration (redacted token)
- [ ] Export includes all queries and metrics snapshots
- [ ] Import restores complete project state
- [ ] All dashboards (Burndown, DORA, Flow) work after import
- [ ] No JIRA connection required after import

**Test Scenario**:
1. User exports profile with "Include cached data" checked
2. User disconnects from internet
3. User imports profile on another machine
4. User opens DORA Metrics dashboard
5. **Expected**: All metrics display instantly from cache

---

### US2: Team Sharing Without JIRA Access

**As a** team lead  
**I want to** share project metrics with contractor  
**So that** contractor can review progress without JIRA credentials

**Acceptance Criteria**:
- [ ] Export option excludes sensitive credentials
- [ ] Export includes all calculated metrics
- [ ] Contractor can import and view all dashboards
- [ ] Contractor cannot fetch new data (no JIRA config)
- [ ] File size reasonable for email (<20MB)

**Test Scenario**:
1. Team lead exports profile (cache: YES, credentials: NO)
2. Contractor imports on their machine
3. Contractor opens app and views DORA/Flow metrics
4. **Expected**: All metrics visible, Fetch Data button shows error (no credentials)

---

### US3: HTML Report for Stakeholders

**As a** project manager  
**I want to** generate HTML report of current metrics  
**So that** I can share with executives via email

**Acceptance Criteria**:
- [ ] Report is single HTML file (no external dependencies)
- [ ] Report includes all metric cards (DORA, Flow, Burndown)
- [ ] Charts are interactive (embedded Plotly JS)
- [ ] Report includes export date and query info
- [ ] CSS styling matches app theme
- [ ] File size < 2MB

**Test Scenario**:
1. User clicks "Generate Report" in Data panel
2. User selects time period (last 12 weeks)
3. User downloads report HTML
4. User emails HTML to stakeholder
5. Stakeholder opens in browser (offline)
6. **Expected**: All charts render, hover interactions work

---

### US4: Historical Snapshot After Project Closure

**As a** portfolio manager  
**I want to** preserve project metrics before JIRA archival  
**So that** I can analyze historical data 6 months later

**Acceptance Criteria**:
- [ ] Export captures all metrics history
- [ ] Export preserves field mappings and classifications
- [ ] Import works after JIRA project deleted
- [ ] Metrics trends visible across full project timeline
- [ ] Cannot refresh data (JIRA archived)

**Test Scenario**:
1. Project closes, user exports full backup
2. 6 months later, JIRA project archived/deleted
3. User imports backup on new machine
4. User views Flow metrics timeline
5. **Expected**: Full 52-week history visible from snapshots

---

## Architecture Design

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Data Panel (Top Banner)                  │
├─────────────────────────────────────────────────────────────┤
│  Tab 1: Import/Export  │  Tab 2: Reports                    │
├────────────────────────┴────────────────────────────────────┤
│                                                               │
│  Export Options:                 Generate Reports:           │
│  ○ Quick Export (Statistics)     ☐ Burndown Summary          │
│  ● Full Backup (Complete)        ☐ DORA Metrics Dashboard    │
│                                   ☐ Flow Metrics Dashboard   │
│  ☑ Include DORA/Flow Metrics     ☐ Combined Executive Report │
│  ☑ Include Query Definitions                                 │
│  ☐ Include JIRA Cache (~15MB)    Time Period: [12 weeks ▾]  │
│  ☐ Include Credentials (⚠️)                                   │
│                                   [Generate HTML Report]     │
│  [Export Profile ZIP]                                        │
│                                                               │
│  Import:                                                      │
│  [Drag & Drop or Browse]                                     │
│  Supports: .zip (profile), .json (legacy)                    │
└───────────────────────────────────────────────────────────────┘
```

### Data Flow: Export

```
User clicks "Export Profile ZIP"
  ↓
callbacks/import_export.py::export_profile_callback()
  ↓
data/import_export.py::export_profile_enhanced()
  ├─→ Load profile.json (JIRA config, field mappings)
  ├─→ Load queries/*.json (all query definitions)
  ├─→ [Optional] Copy cache files to temp dir
  │   ├─ project_data.json (statistics)
  │   ├─ metrics_snapshots.json (DORA/Flow)
  │   ├─ jira_cache.json (issue details)
  │   └─ jira_changelog_cache.json (histories)
  ├─→ Create manifest.json (export metadata)
  └─→ ZIP all files
  ↓
dcc.Download → User receives profile_backup_20251215.zip
```

### Data Flow: Import

```
User drags profile_backup.zip to Data panel
  ↓
callbacks/import_export.py::import_profile_callback()
  ↓
data/import_export.py::import_profile_enhanced()
  ├─→ Extract ZIP to temp directory
  ├─→ Validate manifest.json
  ├─→ Parse profile.json
  ├─→ Generate unique profile ID
  ├─→ Create profiles/{new_id}/ directory
  ├─→ Write profile.json with settings
  ├─→ Import queries/ → create query workspaces
  ├─→ [If cache exists] Copy cache files
  └─→ Register profile in profiles.json
  ↓
UI shows success: "Profile imported as 'Project X - Imported 2025-12-15'"
  ↓
User switches to imported profile
  ↓
All dashboards load from cache (no JIRA needed)
```

### Data Flow: HTML Report

```
User clicks "Generate HTML Report"
  ↓
callbacks/reporting.py::generate_report_callback()
  ↓
data/report_generator.py::generate_html_report()
  ├─→ Load current metrics from cache
  │   ├─ project_data.json (burndown data)
  │   ├─ metrics_snapshots.json (DORA/Flow)
  │   └─ profile.json (metadata)
  ├─→ Generate Plotly charts (as JSON)
  │   ├─ Burndown chart
  │   ├─ DORA metrics sparklines
  │   └─ Flow metrics cards
  ├─→ Render HTML template
  │   ├─ Embed Plotly.js (from CDN or inline)
  │   ├─ Embed chart data as JSON
  │   ├─ Embed CSS (app theme)
  │   └─ Add metadata (date, query, profile)
  └─→ Return single HTML file
  ↓
dcc.Download → User receives metrics_report_20251215.html
  ↓
User opens in browser → Charts render offline
```

---

## Implementation Plan

### Phase 1: Enhanced Export (Priority: HIGH)

**Goal**: Expose existing `export_profile_enhanced()` in UI

**Tasks**:

**T001** [UI] Create Import/Export tab in Data panel
- File: `ui/import_export_panel.py`
- Add dbc.Tabs with "Import/Export" and "Reports" tabs
- Extract existing import/export UI to first tab
- Follow existing tabbed_settings_panel.py pattern

**T002** [UI] Add export options UI
- File: `ui/import_export_panel.py`
- Radio buttons: "Quick Export" vs "Full Backup"
- Checkboxes: Include metrics, queries, cache, credentials
- Warning badge for credentials inclusion
- Help tooltips explaining each option

**T003** [Callback] Create export callback
- File: `callbacks/import_export.py` (new)
- Input: Export button click, radio selection, checkboxes
- Call `data/import_export.py::export_profile_enhanced()`
- Generate timestamped filename
- Return dcc.Download with ZIP

**T004** [Callback] Update current export to include snapshots
- File: `callbacks/visualization.py::export_project_data`
- Load metrics_snapshots.json in addition to project_data
- Combine into single JSON export
- Keep backward compatible for legacy imports

**T005** [Data] Add cache size calculation
- File: `data/import_export.py`
- Function: `get_export_size_estimate(profile_id, include_cache)`
- Display estimated file size before export
- Warn if > 50MB

**T006** [Testing] Export integration tests
- File: `tests/integration/test_import_export.py`
- Test: Export without cache
- Test: Export with cache
- Test: Export with credentials (verify redaction)
- Test: ZIP structure validation

**Estimates**: 6-8 hours

---

### Phase 2: Enhanced Import (Priority: HIGH)

**Goal**: Support profile ZIP import via Data panel

**Tasks**:

**T007** [Callback] Extend import callback for ZIP files
- File: `callbacks/statistics.py::update_table` (refactor)
- Detect .zip extension
- Call `import_profile_enhanced()` for ZIP
- Keep existing JSON/CSV handling
- Show import progress notification

**T008** [UI] Update upload component
- File: `ui/import_export_panel.py`
- Accept: `.zip, .json, .csv`
- Show file type badge after selection
- Display import preview (manifest info for ZIP)

**T009** [Data] Add import validation
- File: `data/import_export.py`
- Validate manifest version compatibility
- Check for conflicting profile IDs
- Verify cache file integrity
- Return validation report

**T010** [UI] Import success/failure feedback
- File: `callbacks/import_export.py`
- Success: Show modal with imported profile info
- Failure: Show error details with fix suggestions
- Auto-switch to imported profile on success

**T011** [Data] Profile ID conflict resolution
- File: `data/import_export.py::_generate_unique_profile_id`
- If profile ID exists, append timestamp
- Preserve original name in profile metadata
- Update manifest with new ID

**T012** [Testing] Import integration tests
- File: `tests/integration/test_import_export.py`
- Test: Import profile without cache
- Test: Import profile with cache (verify offline works)
- Test: Import with conflicting ID
- Test: Import corrupted ZIP (error handling)

**Estimates**: 6-8 hours

---

### Phase 3: HTML Report Generation (Priority: MEDIUM)

**Goal**: Generate self-contained HTML reports with interactive charts

**Tasks**:

**T013** [Data] Create report generator module
- File: `data/report_generator.py` (new)
- Function: `generate_html_report(profile_id, query_id, weeks, sections)`
- Load metrics from cache files
- Generate Plotly chart JSON
- Render HTML from template

**T014** [Data] Create HTML report template
- File: `data/report_template.html` (new)
- Single-page layout with embedded CSS
- Jinja2 template with placeholders
- Include Plotly.js inline or CDN
- Responsive design (mobile-friendly)

**T015** [Data] Chart embedding functions
- File: `data/report_generator.py`
- Function: `embed_burndown_chart(data) -> str`
- Function: `embed_dora_metrics(data) -> str`
- Function: `embed_flow_metrics(data) -> str`
- Convert Plotly figures to HTML divs with inline JS

**T016** [UI] Add report generation UI (Tab 2)
- File: `ui/import_export_panel.py`
- Checkboxes: Select sections (Burndown, DORA, Flow, All)
- Dropdown: Time period (4w, 12w, 26w, 52w, All)
- Button: "Generate HTML Report"
- Preview: Estimated report size

**T017** [Callback] Create report callback
- File: `callbacks/reporting.py` (new)
- Input: Generate button, sections, time period
- Call `generate_html_report()`
- Show progress (generating charts, rendering HTML)
- Return dcc.Download with HTML

**T018** [Data] Report metadata and branding
- File: `data/report_generator.py`
- Add export timestamp, query name, profile name
- Add "Generated by Burndown Chart Generator" footer
- Include data freshness indicators (cache age)

**T019** [Testing] Report generation tests
- File: `tests/unit/data/test_report_generator.py`
- Test: Generate report with all sections
- Test: Generate report with subset of sections
- Test: Verify HTML structure and embedded data
- Test: Check file size < 2MB

**T020** [Testing] Report rendering validation
- File: `tests/integration/test_report_rendering.py` (Playwright)
- Test: Open generated HTML in browser
- Test: Verify charts render correctly
- Test: Test hover interactions on charts
- Test: Verify responsive layout on mobile viewport

**Estimates**: 10-12 hours

---

### Phase 4: UI Integration & Polish (Priority: LOW)

**Goal**: Integrate into Data panel with professional UX

**Tasks**:

**T021** [UI] Refactor Data panel to tabbed interface
- File: `ui/import_export_panel.py`
- Convert to dbc.Tabs: Import/Export, Reports
- Move current import/export UI to Tab 1
- Add new reporting UI to Tab 2
- Ensure keyboard navigation works

**T022** [UI] Add help tooltips and documentation
- File: `configuration/help_content.py`
- Add help text for export options
- Add help text for report generation
- Add examples of use cases
- Link to offline capability documentation

**T023** [Callback] Add export/import progress indicators
- File: `callbacks/import_export.py`
- Use dcc.Interval for progress polling
- Show spinner during export (large cache)
- Show progress bar during import (ZIP extraction)
- Disable buttons during operation

**T024** [UI] Add export history
- File: `ui/import_export_panel.py`
- Show last 5 exports with timestamps
- Quick re-export button (same settings)
- Storage: Save export settings to profile.json

**T025** [UI] Add report preview
- File: `ui/import_export_panel.py`
- Show thumbnail preview of report sections
- Display metric values in preview
- Estimate file size before generation

**T026** [Data] Add export/import logging
- File: `data/import_export.py`
- Log export operations with metadata
- Log import operations with validation results
- Store in export_log.json for audit trail

**T027** [Testing] End-to-end workflow tests
- File: `tests/e2e/test_import_export_workflow.py` (Playwright)
- Test: Complete export → import → verify offline
- Test: Generate report → open in new tab
- Test: Export with different options combinations
- Test: Error recovery scenarios

**Estimates**: 8-10 hours

---

## Technical Specifications

### Export File Structure

**Quick Export** (project_data_20251215.json):
```json
{
  "version": "3.0",
  "exported_at": "2025-12-15T16:30:00Z",
  "export_type": "quick",
  "project_data": {
    "project_scope": { ... },
    "statistics": [ ... ],
    "metadata": { ... }
  },
  "metrics_snapshots": {
    "2025-50": { ... },
    "2025-49": { ... }
  }
}
```

**Full Backup** (profile_backup_20251215.zip):
```
profile_backup_20251215.zip
├── manifest.json
│   {
│     "version": "1.0",
│     "created_at": "2025-12-15T16:30:00Z",
│     "created_by": "burndown-chart-backup",
│     "export_type": "backup",
│     "profiles": ["p_2561542e95d0"],
│     "includes_cache": true,
│     "includes_queries": true,
│     "includes_setup_status": true
│   }
│
├── profile.json
│   {
│     "id": "p_2561542e95d0",
│     "name": "Team Alpha - Q4 2025",
│     "jira_config": { "token": "<REDACTED>" },
│     "field_mappings": { ... },
│     "forecast_settings": { ... },
│     "project_classification": { ... }
│   }
│
├── queries/
│   ├── q_5680de66ba78.json
│   │   {
│   │     "id": "q_5680de66ba78",
│   │     "name": "Sprint 23",
│   │     "jql": "project = KAFKA AND sprint = 23",
│   │     "created_at": "2025-12-01T10:00:00Z"
│   │   }
│   └── q_641c9d97614a.json
│
└── cache/
    ├── q_5680de66ba78/
    │   ├── project_data.json
    │   ├── metrics_snapshots.json
    │   ├── jira_cache.json
    │   └── jira_changelog_cache.json
    └── q_641c9d97614a/
        └── ...
```

### HTML Report Structure

**File**: `metrics_report_20251215.html` (~1.5MB)

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Metrics Report - Project X - 2025-12-15</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        /* Embedded CSS - App theme colors */
        body { font-family: 'Segoe UI', sans-serif; margin: 0; }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .metric-card { border: 1px solid #dee2e6; border-radius: 8px; }
        /* ... more styles ... */
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Metrics Report: Team Alpha Q4 2025</h1>
            <p>Generated: 2025-12-15 16:30:00 | Query: Sprint 23 | Period: 12 weeks</p>
        </header>

        <section id="burndown">
            <h2>Burndown & Velocity</h2>
            <div id="burndown-chart"></div>
            <script>
                var burndownData = {
                    /* Embedded Plotly chart JSON */
                };
                Plotly.newPlot('burndown-chart', burndownData.data, burndownData.layout);
            </script>
        </section>

        <section id="dora-metrics">
            <h2>DORA Metrics</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Deployment Frequency</h3>
                    <div class="metric-value">12 per week</div>
                    <div id="dora-deploy-freq-chart"></div>
                </div>
                <!-- More metric cards -->
            </div>
        </section>

        <section id="flow-metrics">
            <!-- Flow metrics section -->
        </section>

        <footer>
            <p>Generated by Burndown Chart Generator v3.0</p>
        </footer>
    </div>
</body>
</html>
```

### Cache File Offline Requirements

**For Full Offline Capability**:
```python
# Required files in query workspace
REQUIRED_FOR_OFFLINE = [
    "project_data.json",        # Statistics, scope
    "metrics_snapshots.json",   # DORA/Flow pre-calculated
]

# Optional files for extended functionality
OPTIONAL_FOR_OFFLINE = [
    "jira_cache.json",          # Issue details (drill-down)
    "jira_changelog_cache.json", # Status histories (recalculation)
]

# Profile-level requirements
REQUIRED_PROFILE_DATA = [
    "profile.json",             # Field mappings, settings
    "queries/*.json",           # Query definitions
]
```

**Offline Capability Matrix**:
| Feature | Requires | Works Without JIRA? |
|---------|----------|---------------------|
| Burndown charts | project_data.json | ✅ YES |
| DORA metrics | metrics_snapshots.json | ✅ YES |
| Flow metrics | metrics_snapshots.json | ✅ YES |
| Issue drill-down | jira_cache.json | ✅ YES |
| Metric recalculation | jira_changelog_cache.json + JIRA API | ❌ NO |
| Fetch new data | JIRA API | ❌ NO |

---

## UI/UX Design

### Data Panel - Import/Export Tab

**Location**: Top banner sticky header, "Data" button dropdown

**Layout**:
```
┌─────────────────────────────────────────────────────────────┐
│  [Import/Export] [Reports]                                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Export Project Data                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                               │
│  Export Type:                                                 │
│  ○ Quick Export (Statistics & Metrics Only)                   │
│     ℹ️ Best for: Data analysis, smaller file size (~50KB)    │
│                                                               │
│  ● Full Profile Backup (Complete Project State)              │
│     ℹ️ Best for: Offline work, team sharing, backup          │
│                                                               │
│     Options:                                                  │
│     ☑ Include DORA/Flow Metrics Snapshots                    │
│     ☑ Include Query Definitions                              │
│     ☐ Include JIRA Cache (~15MB) ⓘ                           │
│     ☐ Include JIRA Credentials (⚠️ Security Warning) ⓘ       │
│                                                               │
│     Estimated size: 2.3 MB                                   │
│                                                               │
│  [Export Profile ZIP] [Export Statistics JSON]               │
│                                                               │
│  ─────────────────────────────────────────────────────────   │
│                                                               │
│  Import Project Data                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │  📁 Drag & Drop or Click to Browse                   │    │
│  │                                                       │    │
│  │  Supported formats:                                   │    │
│  │  • .zip - Full profile backup                         │    │
│  │  • .json - Legacy statistics export                   │    │
│  │  • .csv - Statistics import                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  Recent Exports:                                              │
│  • profile_backup_20251215_1630.zip (2.3 MB) - 5 min ago    │
│  • profile_backup_20251214_0920.zip (2.1 MB) - 1 day ago    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Data Panel - Reports Tab

```
┌─────────────────────────────────────────────────────────────┐
│  [Import/Export] [Reports]                                   │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Generate HTML Report                                         │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│                                                               │
│  Report Sections:                                             │
│  ☑ Burndown Chart & Velocity                                 │
│  ☑ DORA Metrics Dashboard                                    │
│  ☑ Flow Metrics Dashboard                                    │
│  ☐ Issue Details & Drill-Down                                │
│  ☐ Project Configuration Summary                             │
│                                                               │
│  Time Period:                                                 │
│  ○ Last 4 weeks    ● Last 12 weeks                           │
│  ○ Last 26 weeks   ○ Last 52 weeks                           │
│  ○ All time (custom range)                                    │
│                                                               │
│  Report Format:                                               │
│  ● Single Page HTML (interactive charts)                     │
│  ○ PDF Export (static, for printing) [Coming Soon]           │
│                                                               │
│  Preview:                                                     │
│  ┌─────────────────────────────────────────────────┐         │
│  │ 📊 Metrics Report                               │         │
│  │ Team Alpha Q4 2025 | 12 weeks | 2025-12-15     │         │
│  │                                                 │         │
│  │ [Burndown Chart Preview]                        │         │
│  │ Deployment Frequency: 12/wk | Lead Time: 2.1d  │         │
│  │ Flow Velocity: 8.3 items/wk | WIP: 12 items    │         │
│  └─────────────────────────────────────────────────┘         │
│                                                               │
│  Estimated size: ~1.8 MB                                     │
│                                                               │
│  [Generate Report] [Preview in New Tab]                      │
│                                                               │
│  Recent Reports:                                              │
│  • metrics_report_20251215.html - 10 min ago                 │
│  • metrics_report_20251208.html - 1 week ago                 │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Progress & Feedback

**Export Progress**:
```
┌─────────────────────────────────────────────────────────────┐
│  Exporting Profile...                                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░ 60%                          │
│                                                               │
│  ✓ Collected profile configuration                           │
│  ✓ Exported 3 queries                                        │
│  ⟳ Copying cache files (12.5 MB / 15 MB)...                 │
│    Creating ZIP archive...                                   │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

**Import Success**:
```
┌─────────────────────────────────────────────────────────────┐
│  ✓ Profile Imported Successfully                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Profile: Team Alpha Q4 2025 (Imported 2025-12-15)          │
│  Queries: 3 imported                                          │
│  Cache: 15.2 MB loaded                                       │
│                                                               │
│  All metrics available offline - no JIRA connection needed.  │
│                                                               │
│  [Switch to Profile] [View Details] [Close]                 │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/unit/data/test_import_export.py`
- Test export without cache (< 1MB)
- Test export with cache (verify all files included)
- Test credentials redaction
- Test import validation (manifest, profile structure)
- Test profile ID conflict resolution
- Test cache restoration

**File**: `tests/unit/data/test_report_generator.py`
- Test HTML template rendering
- Test chart embedding (Plotly JSON)
- Test CSS inlining
- Test metadata inclusion
- Test file size < 2MB

### Integration Tests

**File**: `tests/integration/test_offline_capability.py`
- Export full profile with cache
- Import on fresh profile directory
- Load dashboards without JIRA connection
- Verify DORA metrics display
- Verify Flow metrics display
- Verify burndown charts display

**File**: `tests/integration/test_report_workflow.py`
- Generate HTML report with all sections
- Write to temp file
- Parse HTML and verify structure
- Extract embedded chart data
- Validate Plotly chart config

### End-to-End Tests (Playwright)

**File**: `tests/e2e/test_import_export_ui.py`
- Navigate to Data panel
- Select export options
- Click export button
- Verify download initiated
- Upload exported file
- Verify import success message
- Verify profile appears in selector

**File**: `tests/e2e/test_report_generation.py`
- Navigate to Reports tab
- Select report sections
- Click generate button
- Verify download initiated
- Open report in new browser tab
- Verify charts render
- Test chart interactivity (hover, zoom)

### Performance Tests

**File**: `tests/performance/test_export_import.py`
- Export with 1000 issues cache < 5 seconds
- Import with 15MB cache < 10 seconds
- Report generation < 3 seconds
- HTML report size < 2MB

---

## Implementation Estimates

| Phase | Tasks | Estimated Hours | Complexity |
|-------|-------|-----------------|------------|
| Phase 1: Enhanced Export | T001-T006 | 6-8 hours | Medium |
| Phase 2: Enhanced Import | T007-T012 | 6-8 hours | Medium |
| Phase 3: HTML Reports | T013-T020 | 10-12 hours | High |
| Phase 4: UI Polish | T021-T027 | 8-10 hours | Low |
| **Total** | **27 tasks** | **30-38 hours** | **3-5 days** |

---

## Success Criteria

### Phase 1: Enhanced Export
- [ ] Full profile export creates ZIP with all cache files
- [ ] Export without cache creates ZIP < 1MB
- [ ] Export with cache includes metrics_snapshots.json
- [ ] Credentials redacted in export (token = "<REDACTED>")
- [ ] Export estimates file size before creating ZIP

### Phase 2: Enhanced Import
- [ ] Import profile ZIP restores complete project state
- [ ] Import handles duplicate profile IDs automatically
- [ ] Import validates manifest and shows errors
- [ ] Import success shows notification with new profile name
- [ ] All dashboards work after import without JIRA connection

### Phase 3: HTML Reports
- [ ] Report generation creates single HTML file
- [ ] Report includes all selected metric sections
- [ ] Charts are interactive (hover, zoom work)
- [ ] Report opens offline in any browser
- [ ] Report file size < 2MB

### Phase 4: UI Polish
- [ ] Data panel has tabbed interface
- [ ] Export/import progress indicators work
- [ ] Help tooltips explain all options
- [ ] Recent exports list shows last 5
- [ ] All E2E tests pass

---

## Dependencies

### Existing Components (Leverage)
- ✅ `data/import_export.py::export_profile_enhanced()` - Backend export
- ✅ `data/import_export.py::import_profile_enhanced()` - Backend import
- ✅ `ui/import_export_panel.py` - Current import UI
- ✅ `callbacks/statistics.py` - Current CSV import logic

### New Dependencies (Minimal)
- Jinja2 (already installed) - HTML template rendering
- Plotly.js CDN - Chart embedding in HTML reports
- No new Python packages required

---

## Risks & Mitigations

### Risk 1: Large Export File Sizes
**Risk**: Exports with full JIRA cache exceed email size limits (25MB)  
**Likelihood**: Medium  
**Impact**: High  
**Mitigation**:
- Warn user when estimated size > 20MB
- Provide option to exclude jira_cache.json (only affects drill-down)
- Compress using ZIP_DEFLATED (reduces size 30-50%)
- Document cloud storage options for large exports

### Risk 2: HTML Report Browser Compatibility
**Risk**: Generated reports don't render in older browsers  
**Likelihood**: Low  
**Impact**: Medium  
**Mitigation**:
- Use Plotly.js (supports IE11+, all modern browsers)
- Test on Chrome, Firefox, Edge, Safari
- Include browser compatibility note in report
- Provide PDF export option (future)

### Risk 3: Import Overwrites Existing Profile
**Risk**: User imports profile with same ID, loses local changes  
**Likelihood**: Medium  
**Impact**: High  
**Mitigation**:
- Always generate unique profile ID on import
- Never overwrite existing profiles
- Show confirmation dialog with new profile name
- Preserve original profile ID in metadata for reference

### Risk 4: Offline Metrics Become Stale
**Risk**: Users forget imported cache is snapshot, not live  
**Likelihood**: High  
**Impact**: Low  
**Mitigation**:
- Show cache age in profile selector
- Display "Offline Mode" badge when using imported cache
- Add "Last Updated" timestamp to all dashboards
- Warn when cache age > 7 days

---

## Follow-Up Features (Future)

### PDF Export
- Convert HTML reports to PDF using browser print API
- Preserve charts as static images
- Optimized for printing (page breaks, margins)

### Scheduled Exports
- Auto-export profile weekly (backup automation)
- Email reports to stakeholders on schedule
- Store exports in cloud storage (OneDrive, SharePoint)

### Export Diff/Compare
- Compare two exported snapshots
- Show metric deltas (deployment frequency: 10 → 12)
- Visualize trend changes (improving/degrading)

### Team Collaboration
- Share profiles via URL (cloud storage link)
- Import from URL (one-click setup)
- Version tracking for shared profiles

---

## Conclusion

This feature enables:
1. ✅ **Complete offline capability** - work without JIRA connection
2. ✅ **Team collaboration** - share complete project state
3. ✅ **Stakeholder reporting** - portable HTML reports
4. ✅ **Data portability** - backup/restore complete configuration

**Implementation**: 3-5 days, leveraging existing backend, minimal new code

**Impact**: Transforms app from online-only tool to portable, shareable platform
