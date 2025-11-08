````markdown
# Implementation Plan: DORA and Flow Metrics Dashboard

**Branch**: `007-dora-flow-metrics` | **Date**: 2025-10-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-dora-flow-metrics/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a comprehensive DORA and Flow Metrics dashboard that displays industry-standard DevOps performance indicators (Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Recovery) and workflow efficiency metrics (Velocity, Time, Efficiency, Load, Distribution). The feature includes a configurable Jira field mapping system that allows administrators to map their organization's custom Jira fields to the internal fields required for metric calculations. Metrics are calculated from Jira issue data using the existing JIRA API integration, cached for performance, and presented in a mobile-responsive dashboard with performance tier benchmarking and trend visualization.

## Technical Context

**Language/Version**: Python 3.13  
**Primary Dependencies**: Dash 3.1.1, Dash Bootstrap Components 2.0.2, Plotly 6.0.1, Requests 2.32.3, Pandas 2.2.3, Pytest 8.3.5  
**Storage**: JSON file persistence (app_settings.json, project_data.json, jira_cache.json)  
**Testing**: pytest with pytest-cov, Playwright for integration tests  
**Target Platform**: Web application (PWA) with mobile-first responsive design, Windows development environment  
**Project Type**: Web application (Dash framework) with layered architecture  
**Performance Goals**: 
- Initial page load < 2 seconds
- Chart rendering < 500ms
- User interactions < 100ms response time
- Metric calculation for 5,000 issues within 15 seconds
- Cache hit for repeated queries < 200ms

**Constraints**: 
- Must integrate with existing Jira REST API integration (data/jira_simple.py)
- Must use existing settings persistence (app_settings.json via data/persistence.py)
- Must maintain layered architecture (callbacks → data layer delegation)
- Must ensure test isolation (no files in project root during tests)
- Must work with existing JIRA cache mechanism (jira_cache.json with version tracking)
- Windows PowerShell development environment (no Unix commands)

**Scale/Scope**: 
- Support 100-5,000 Jira issues per calculation
- 4 DORA metrics + 5 Flow metrics = 9 total metrics
- ~15 configurable Jira field mappings
- Mobile-responsive UI (320px to 1440px+ viewports)
- Multiple time period selections (7d, 30d, 90d, custom)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Initial Check (Pre-Research)

| Principle                    | Status | Notes                                                                                                                                                                                        |
| ---------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **I. Layered Architecture**  | ✅ PASS | Feature follows existing pattern: callbacks delegate to `data/` layer for all metric calculations, Jira API calls, and field mapping logic. No business logic in callbacks.                  |
| **II. Test Isolation**       | ✅ PASS | All tests will use `tempfile.TemporaryDirectory()` and `tempfile.NamedTemporaryFile()` for settings files, cache files, and test data. No files created in project root.                     |
| **III. Performance Budgets** | ✅ PASS | Explicit performance requirements align with constitution: Page load < 2s, chart rendering < 500ms, interactions < 100ms. Metric calculation performance tested for 5,000 issues within 15s. |

**Initial Gate Status**: ✅ **APPROVED** - All constitutional principles satisfied. No violations requiring justification.

### Post-Design Re-Check (After Phase 1)

| Principle                    | Status | Verification                                                                                                                                                                                                                                                                                                                                                                                                             |
| ---------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **I. Layered Architecture**  | ✅ PASS | **Design Confirms Compliance**: All business logic implemented in `data/` layer modules (`dora_calculator.py`, `flow_calculator.py`, `field_mapper.py`, `metrics_cache.py`). Callbacks in `callbacks/dora_flow_metrics.py` and `callbacks/field_mapping.py` only handle events and delegate to data layer functions. UI components in `ui/` layer purely render data passed from callbacks. Clear separation maintained. |
| **II. Test Isolation**       | ✅ PASS | **Design Confirms Compliance**: Test files explicitly use `tempfile.NamedTemporaryFile()` fixtures (see `quickstart.md` integration test example). All file operations in tests patch file paths to use temporary locations. No test creates `metrics_cache.json` or modifies `app_settings.json` in project root.                                                                                                       |
| **III. Performance Budgets** | ✅ PASS | **Design Confirms Compliance**: Multi-layered optimization strategy documented in `research.md` Task 6: JQL date filters, pandas vectorization, lazy loading, caching with 1-hour TTL. Performance calculation validated: 5,000 issues × 2ms = 10s + 200ms API + 500ms rendering = 10.7s total, under 15s target. Cache hit < 200ms target achieved via simple JSON file read.                                           |

**Post-Design Gate Status**: ✅ **APPROVED** - All constitutional principles satisfied after detailed design. No violations detected. Implementation plan maintains architecture integrity.

**Additional Verification**:
- ✅ No new dependencies added (all technologies in existing `requirements.txt`)
- ✅ Existing patterns extended (Jira API integration, JSON persistence, Dash callbacks)
- ✅ Mobile-first design maintained (responsive grid layout, 44px touch targets)
- ✅ Error handling with user-friendly messages (explicit error states in data model)
- ✅ Caching aligns with existing pattern (similar to `jira_cache.json` with version tracking)

## Project Structure

### Documentation (this feature)

```text
specs/007-dora-flow-metrics/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── jira-field-mappings.json      # Field mapping configuration schema
│   ├── dora-metrics-response.json    # DORA metrics response format
│   └── flow-metrics-response.json    # Flow metrics response format
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Web application structure (existing Dash architecture)
callbacks/
├── __init__.py
├── dora_flow_metrics.py    # NEW: Callback handlers for DORA/Flow metrics tab
├── field_mapping.py         # NEW: Callback handlers for field mapping configuration
├── dashboard.py             # Existing
├── jira_config.py           # Existing
└── visualization.py         # Existing

data/
├── __init__.py
├── dora_calculator.py       # NEW: DORA metrics calculation logic
├── flow_calculator.py       # NEW: Flow metrics calculation logic
├── field_mapper.py          # NEW: Jira field mapping logic
├── metrics_cache.py         # NEW: Metrics caching with TTL
├── jira_simple.py           # Existing - will extend for custom field queries
├── persistence.py           # Existing - will extend for field mappings
└── processing.py            # Existing

ui/
├── __init__.py
├── dora_metrics_dashboard.py   # NEW: DORA metrics UI components
├── flow_metrics_dashboard.py   # NEW: Flow metrics UI components
├── field_mapping_modal.py      # NEW: Field mapping configuration UI
├── metric_cards.py             # NEW: Reusable metric card components
├── layout.py                   # Existing - will add new tab
└── dashboard.py                # Existing

visualization/
├── __init__.py
├── dora_charts.py           # NEW: DORA-specific chart generation
├── flow_charts.py           # NEW: Flow-specific chart generation
└── charts.py                # Existing

configuration/
├── __init__.py
├── dora_config.py           # NEW: DORA metric definitions and benchmarks
├── flow_config.py           # NEW: Flow metric definitions
└── settings.py              # Existing

tests/
├── unit/
│   ├── data/
│   │   ├── test_dora_calculator.py   # NEW
│   │   ├── test_flow_calculator.py   # NEW
│   │   ├── test_field_mapper.py      # NEW
│   │   └── test_metrics_cache.py     # NEW
│   └── ui/
│       ├── test_dora_dashboard.py    # NEW
│       └── test_flow_dashboard.py    # NEW
├── integration/
│   ├── test_dora_flow_workflow.py    # NEW: End-to-end metric calculation
│   └── test_field_mapping_workflow.py # NEW: Field mapping configuration flow
└── conftest.py              # Existing
```

**Structure Decision**: Using existing web application structure. All new DORA/Flow functionality follows the established layered architecture pattern with clear separation between callbacks (event handling), data (business logic), ui (component rendering), and visualization (chart generation). This ensures consistency with the constitution's layered architecture principle and enables proper unit testing of all business logic.

## Complexity Tracking

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected** - All constitutional principles are satisfied by this feature design. No complexity justification required.

---

## Phase 2 Planning Complete

### Deliverables Generated

✅ **Phase 0: Research** (`research.md`)
- 10 research tasks completed
- All unknowns resolved
- Technology decisions finalized
- No new dependencies required

✅ **Phase 1: Design & Contracts**
- Data model defined (`data-model.md`) with 6 core entities
- API contracts created (`contracts/*.json`) with JSON schemas
- Quickstart guide generated (`quickstart.md`) with implementation steps
- Agent context updated (`.github/copilot-instructions.md`)

✅ **Phase 1: Constitution Re-Check**
- All three constitutional principles verified post-design
- No violations detected
- Architecture integrity maintained

### Next Steps

**Command to proceed**: Run `/speckit.tasks` to generate Phase 3 implementation tasks.

**Implementation sequence**:
1. Configuration layer (Days 1-3): `dora_config.py`, `flow_config.py`, `field_mapper.py`, `metrics_cache.py`
2. Calculation layer (Days 4-6): `dora_calculator.py`, `flow_calculator.py` with unit tests
3. UI layer (Days 7-8): Dashboard components, metric cards, field mapping modal
4. Callbacks (Days 9-10): Event handlers with delegation to data layer
5. Integration testing (Days 11-12): End-to-end workflows, performance validation

**Estimated effort**: 12 development days (2.5 weeks with testing)

### Key Artifacts Summary

| Artifact            | Location                                       | Purpose                                |
| ------------------- | ---------------------------------------------- | -------------------------------------- |
| Implementation Plan | `specs/007-dora-flow-metrics/plan.md`          | This file - overall plan and structure |
| Research Findings   | `specs/007-dora-flow-metrics/research.md`      | All design decisions and rationale     |
| Data Model          | `specs/007-dora-flow-metrics/data-model.md`    | Entity definitions and relationships   |
| API Contracts       | `specs/007-dora-flow-metrics/contracts/*.json` | JSON schemas for data structures       |
| Developer Guide     | `specs/007-dora-flow-metrics/quickstart.md`    | Step-by-step implementation guide      |

### Branch Information

**Feature Branch**: `007-dora-flow-metrics`  
**Base Branch**: `main`  
**Spec File**: `specs/007-dora-flow-metrics/spec.md`

---

## Planning Session Complete

**Status**: ✅ Phase 0 Research and Phase 1 Design completed successfully.

**Ready for**: Phase 2 task breakdown via `/speckit.tasks` command.

**Date**: 2025-10-27

````
