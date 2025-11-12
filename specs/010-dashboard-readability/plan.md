# Implementation Plan: Dashboard Readability & Test Coverage

**Branch**: `010-dashboard-readability` | **Date**: 2025-11-12 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/010-dashboard-readability/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

**Primary Requirement**: Establish comprehensive test automation coverage for all Project Dashboard calculation functions while implementing minimal essential visual enhancements to improve readability and actionability.

**Technical Approach**: 
1. **Phase 1 (P1 - Test Coverage)**: Create unit tests for all dashboard calculation functions (`calculate_dashboard_metrics()`, `calculate_pert_timeline()`, `_calculate_health_score()`) with >90% code coverage target, including edge case validation
2. **Phase 2 (P2 - Visual Clarity)**: Enhance existing dashboard UI with improved visual hierarchy, prominent health score display, and consistent design language matching DORA/Flow metrics (no major redesign)
3. **Phase 3 (P3 - Actionable Insights)**: Verify and test existing key insights section functionality with edge case scenarios

This is primarily a **verification and enhancement** feature - the dashboard already exists and displays all required metrics. The work focuses on ensuring calculation accuracy through comprehensive testing and making minimal UX improvements for better readability.

## Technical Context

**Language/Version**: Python 3.13 (verified via project requirements)  
**Primary Dependencies**: Dash 2.x, Dash Bootstrap Components, Plotly, pandas, pytest  
**Storage**: JSON file persistence (`app_settings.json`, `project_data.json`, `jira_cache.json`, `metrics_snapshots.json`)  
**Testing**: pytest with coverage reporting, test isolation via tempfile (mandatory per Constitution)  
**Target Platform**: Windows development environment, web application (PWA with Dash)  
**Project Type**: Web application (Dash PWA) - single project structure  
**Performance Goals**: 
  - Dashboard calculation test suite execution < 5 seconds
  - Dashboard render time < 500ms (existing requirement)
  - Initial page load < 2 seconds (existing requirement)
  - Test coverage >90% for dashboard calculation functions
**Constraints**: 
  - Must maintain backward compatibility with existing dashboard data structures
  - No breaking changes to `DashboardMetrics` or `PERTTimelineData` schemas
  - Test isolation mandatory (no files created in project root)
  - Windows PowerShell environment (no Unix tools)
  - Virtual environment activation required for all Python commands
**Scale/Scope**: 
  - ~15 calculation functions to test (calculate_dashboard_metrics, calculate_pert_timeline, _calculate_health_score, card creation functions)
  - ~50+ edge case scenarios to validate
  - ~30 functional requirements to verify through tests
  - Existing dashboard with 4 metric cards + overview section + PERT timeline chart

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principle I: Layered Architecture ✅ PASS

**Gate**: Business logic MUST reside in `data/` layer. Callbacks MUST only handle events and delegate.

**Compliance**: 
- All dashboard calculation functions already exist in `data/processing.py` (calculate_dashboard_metrics, calculate_pert_timeline)
- Helper functions exist in `ui/dashboard_cards.py` (_calculate_health_score, _create_key_insights)
- Existing callbacks in `callbacks/dashboard.py` already delegate to data layer
- **No new business logic in callbacks** - only adding tests and minor UI enhancements

**Verification**: New unit tests will validate that calculation logic remains in data layer. No callback modifications planned except for potential UI state management.

### Core Principle II: Test Isolation ✅ PASS

**Gate**: Tests MUST NOT create files in project root. MUST use tempfile with proper cleanup.

**Compliance**:
- All new tests will use `tempfile.TemporaryDirectory()` or `tempfile.NamedTemporaryFile()`
- All tests will use pytest fixtures with `yield` for guaranteed cleanup
- **Explicitly required** in FR-010: "Test suite MUST include edge case tests" - all will follow isolation rules
- Existing test infrastructure already demonstrates proper isolation patterns

**Verification**: Code review will reject any test creating `app_settings.json`, `project_data.json`, or other persistence files in project root. Use `pytest --random-order` to verify isolation.

### Core Principle III: Performance Budgets ✅ PASS

**Gate**: Initial page load < 2s, Chart rendering < 500ms, User interactions < 100ms.

**Compliance**:
- SC-007 explicitly requires: "Dashboard renders within 500ms with typical project data"
- No changes to chart rendering logic - only testing existing calculations
- Minor UI enhancements (font sizes, icons, layout) have negligible performance impact
- Dashboard already meets performance budgets - this feature validates and maintains them

**Verification**: Performance tests will validate dashboard render time < 500ms. No architectural changes that would impact performance.

### Core Principle IV: Simplicity & Reusability ✅ PASS

**Gate**: Keep implementations simple (KISS). Avoid duplication (DRY).

**Compliance**:
- Test suite will use shared fixtures and helper functions to avoid duplication
- No complex abstractions - straightforward unit tests for calculation functions
- Visual enhancements reuse existing metric card components and design system
- No over-engineering - minimal essential changes per P2 priority

**Verification**: Code review will reject copy-pasted test setup code. Shared test utilities will be extracted to `tests/utils/` or test fixtures.

### Core Principle V: Data Privacy & Security ✅ PASS

**Gate**: MUST NEVER commit customer-identifying information. Use generic placeholders.

**Compliance**:
- Test data will use generic placeholder values ("Acme Corp", "example.com")
- No production JIRA field IDs or customer-specific configurations
- Test fixtures will use synthetic data matching existing patterns in `tests/unit/data/test_processing.py`
- Documentation will reference generic examples only

**Verification**: Code review will scan for company names, production domains, or customer-specific field IDs in test files and documentation.

### Core Principle VI: Defensive Refactoring ✅ PASS

**Gate**: Unused code MUST be removed systematically with verification.

**Compliance**:
- This feature does NOT remove existing code - it adds tests and minor UI enhancements
- If any refactoring is needed during test development, will follow defensive practices:
  - Create backup branch before changes
  - Verify zero references before removal
  - Run tests before and after
  - Commit incrementally with descriptive messages
- No dead code removal planned in current scope

**Verification**: If refactoring becomes necessary, will follow `.github/copilot-instructions.md` defensive refactoring guide. All changes will be incremental with test validation.

## Project Structure

### Documentation (this feature)

```text
specs/010-dashboard-readability/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (minimal - most context already known)
├── data-model.md        # Phase 1 output (documents existing schemas + test data structures)
├── quickstart.md        # Phase 1 output (test execution and validation guide)
├── contracts/           # Phase 1 output (test contracts and coverage requirements)
│   └── test-coverage-contract.md  # Defines required tests for each function
├── checklists/
│   └── requirements.md  # Already created - spec validation checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Existing structure - this feature adds tests and minor enhancements
d:\Development\burndown-chart/
├── data/
│   └── processing.py           # ✅ Existing - contains calculate_dashboard_metrics(), calculate_pert_timeline()
├── ui/
│   ├── dashboard.py            # ✅ Existing - dashboard layout components
│   └── dashboard_cards.py      # ✅ Existing - contains _calculate_health_score(), card creation functions
├── callbacks/
│   └── dashboard.py            # ✅ Existing - dashboard event handlers (delegates to data layer)
├── visualization/
│   └── charts.py               # ✅ Existing - contains create_pert_timeline_chart()
├── tests/
│   ├── unit/
│   │   ├── data/
│   │   │   ├── test_processing.py           # ✅ Existing - has some coverage, need to expand
│   │   │   └── test_dashboard_metrics.py    # ⚠️ NEW - comprehensive dashboard metrics tests
│   │   └── ui/
│   │       ├── test_dashboard_cards.py      # ⚠️ NEW - health score and card creation tests
│   │       └── test_flow_dashboard.py       # ✅ Existing - pattern to follow for dashboard tests
│   ├── integration/
│   │   └── test_dashboard_integration.py    # ⚠️ NEW (optional) - end-to-end dashboard scenarios
│   └── utils/
│       └── dashboard_test_fixtures.py       # ⚠️ NEW - shared test data and fixtures
├── app_settings.json           # ✅ Existing - NEVER modify in tests (use tempfile)
├── project_data.json           # ✅ Existing - NEVER modify in tests (use tempfile)
└── metrics_snapshots.json      # ✅ Existing - NEVER modify in tests (use tempfile)

Legend:
✅ Existing - already in codebase
⚠️ NEW - to be created in this feature
```

**Structure Decision**: 

This is a **single project web application** (Dash PWA) with established structure. The feature focuses on:

1. **Test Coverage** (P1): Add comprehensive unit tests to `tests/unit/data/test_dashboard_metrics.py` and `tests/unit/ui/test_dashboard_cards.py`
2. **Test Utilities** (P1): Create `tests/utils/dashboard_test_fixtures.py` for shared test data and helper functions
3. **Visual Enhancements** (P2): Minor modifications to existing `ui/dashboard.py` and `ui/dashboard_cards.py` for improved readability
4. **Integration Tests** (P3): Optional end-to-end validation in `tests/integration/test_dashboard_integration.py`

**Key Files to Test**:
- `data/processing.py::calculate_dashboard_metrics()` - Core dashboard metrics calculation
- `data/processing.py::calculate_pert_timeline()` - PERT timeline data generation
- `ui/dashboard_cards.py::_calculate_health_score()` - Health score formula (4 components)
- `ui/dashboard_cards.py::_get_health_color_and_label()` - Color/label mapping
- `ui/dashboard_cards.py::_create_key_insights()` - Actionable insights generation
- `ui/dashboard_cards.py::create_dashboard_*_card()` - All 4 card creation functions

**Files NEVER Modified in Tests**:
- `app_settings.json`, `project_data.json`, `jira_cache.json`, `metrics_snapshots.json`
- All tests MUST use `tempfile` for any file operations (Constitution Principle II)

## Complexity Tracking

> **No violations to justify** - All Constitution principles pass without exceptions.

This feature maintains architectural simplicity:
- **Layered Architecture**: All calculation logic already in data layer, tests verify this separation
- **Test Isolation**: All new tests use tempfile patterns from existing test suite
- **Performance Budgets**: No architectural changes affecting performance
- **Simplicity**: Straightforward unit tests without complex abstractions
- **Data Privacy**: Test data uses generic placeholders only
- **Defensive Refactoring**: No code removal planned - adding tests and minor UI enhancements only

**No simpler alternatives needed** - the approach is already minimal and follows established patterns.
