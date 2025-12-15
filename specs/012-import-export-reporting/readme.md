# Feature 012: Enhanced Import/Export & HTML Reporting

**Branch**: `012-import-export-reporting`  
**Status**: In Progress  
**Created**: 2025-12-15

---

## Overview

Comprehensive import/export system with offline capability and HTML report generation.

### Goals
1. ✅ **Full Profile Export/Import** - Complete offline capability with all cache files
2. 📊 **HTML Report Generation** - Self-contained reports for stakeholders
3. 🎨 **Enhanced Data Panel** - Unified UI for all data operations

---

## Quick Links

- **Concept**: [concept.md](./concept.md) - Full specification and architecture
- **Tasks**: [tasks.md](./tasks.md) - Detailed implementation checklist
- **Constitution**: [../../.specify/memory/constitution.md](../../.specify/memory/constitution.md)
- **Guidelines**: [../../.github/copilot-instructions.md](../../.github/copilot-instructions.md)

---

## Implementation Plan

### Phase 1: Enhanced Export (6-8 hours)
- Expose `export_profile_enhanced()` in UI
- Add export options (with/without cache)
- Update current export to include metrics_snapshots.json
- **Status**: Not Started

### Phase 2: Enhanced Import (6-8 hours)
- Support ZIP profile imports
- Add import validation
- Show import success/failure feedback
- **Status**: Not Started

### Phase 3: HTML Report Generation (10-12 hours)
- Create report generator module
- Build HTML template with embedded charts
- Add Reports tab to Data panel
- **Status**: Not Started

### Phase 4: UI Polish (8-10 hours)
- Add progress indicators
- Add help tooltips
- E2E testing
- **Status**: Not Started

**Total Estimate**: 30-38 hours (3-5 days)

---

## Current Progress

### Completed
- [x] Feature specification
- [x] Task breakdown
- [x] Branch created

### In Progress
- [ ] Phase 1: Enhanced Export

### Blocked
- None

---

## Testing Strategy

### Unit Tests
- `tests/unit/data/test_import_export.py` - Export/import functions
- `tests/unit/data/test_report_generator.py` - Report generation

### Integration Tests
- `tests/integration/test_offline_capability.py` - Verify offline mode works
- `tests/integration/test_report_workflow.py` - Report generation workflow

### E2E Tests (Playwright)
- `tests/e2e/test_import_export_ui.py` - UI workflows
- `tests/e2e/test_report_generation.py` - Report generation and rendering

---

## Key Technical Decisions

### 1. Leverage Existing Backend
- Use `data/import_export.py::export_profile_enhanced()` (already implemented)
- Use `data/import_export.py::import_profile_enhanced()` (already implemented)
- Just expose in UI - no new backend code needed for export/import

### 2. Single-Page HTML Reports
- Embed Plotly.js from CDN
- Inline CSS (no external dependencies)
- Chart data embedded as JSON
- Works offline in any browser

### 3. Tabbed Data Panel
- Tab 1: Import/Export (existing + enhanced)
- Tab 2: Reports (new)
- Maintains existing import/upload functionality

---

## Success Criteria

### Must Have
- [ ] Full profile export creates ZIP with cache
- [ ] Import restores complete offline capability
- [ ] HTML reports generated with interactive charts
- [ ] All dashboards work after import without JIRA
- [ ] No breaking changes to existing functionality

### Should Have
- [ ] Export size estimates before download
- [ ] Import validation with helpful errors
- [ ] Progress indicators for large exports
- [ ] Recent exports/reports history

### Nice to Have
- [ ] Report preview before generation
- [ ] Export scheduling
- [ ] PDF export option

---

## Architecture Notes

### Offline Capability Requirements

**For Full Offline**:
```
profiles/{profile_id}/
├── profile.json              # JIRA config, field mappings
└── queries/{query_id}/
    ├── query.json            # Query definition
    ├── project_data.json     # Statistics, scope
    ├── metrics_snapshots.json # DORA/Flow metrics ← CRITICAL
    ├── jira_cache.json       # Issue details (optional)
    └── jira_changelog_cache.json # Histories (optional)
```

### What Works Offline
- ✅ Burndown charts (from project_data.json)
- ✅ DORA metrics (from metrics_snapshots.json)
- ✅ Flow metrics (from metrics_snapshots.json)
- ✅ Issue drill-down (from jira_cache.json)
- ❌ Metric recalculation (needs JIRA API)
- ❌ Fetch new data (needs JIRA API)

---

## Development Workflow

### Setup
```powershell
# Switch to feature branch
git checkout 012-import-export-reporting

# Activate venv
.\.venv\Scripts\activate

# Run app
python app.py
```

### Before Committing
```powershell
# Check errors
# Use get_errors tool in Copilot

# Run tests
pytest tests/unit/ -v

# Check coverage
pytest --cov=data --cov=callbacks --cov-report=html
```

### Commit Convention
```
feat(012): add full profile export UI
fix(012): handle ZIP import validation errors
test(012): add report generation tests
docs(012): update import/export help content
```

---

## Dependencies

### Existing (No Changes)
- Dash >= 2.14.0
- Plotly >= 5.18.0
- Jinja2 (already installed)

### New (None Required)
- No new Python packages needed
- Plotly.js loaded from CDN in reports

---

## Risks & Mitigations

### Risk: Large Export Files
**Mitigation**: Warn at >20MB, provide option to exclude cache

### Risk: Import Overwrites Data
**Mitigation**: Always generate unique profile ID, never overwrite

### Risk: Reports Don't Render
**Mitigation**: Use Plotly.js CDN (stable), test on multiple browsers

---

## Documentation Updates Needed

### Help Content
- [ ] Update `configuration/help_content.py`
- [ ] Add export options explanations
- [ ] Add report generation guide

### README
- [ ] Update main README.md with new features
- [ ] Add offline capability section

---

## Related Features

- **011: Profile & Query Management** - Multi-profile architecture
- **007: DORA/Flow Metrics** - Metrics being exported/reported
- **008: Metrics Performance** - Caching strategy

---

## Team Notes

### For Reviewers
- Check constitution compliance (layered architecture, test isolation)
- Verify no customer data in examples
- Test offline capability manually
- Review HTML report template for XSS risks

### For QA
- Test export/import round-trip
- Test offline mode (disconnect internet)
- Test report generation with all section combinations
- Test on different browsers (Chrome, Firefox, Edge)

---

**Last Updated**: 2025-12-15  
**Next Review**: After Phase 1 completion
