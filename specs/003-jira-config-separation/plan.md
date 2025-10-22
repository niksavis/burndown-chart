# Implementation Plan: JIRA Configuration Separation

**Branch**: `003-jira-config-separation` | **Date**: October 21, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-jira-config-separation/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Separate JIRA API configuration (endpoint, token, cache settings, API version, custom fields) from the JQL query interface by creating a dedicated configuration page/modal. Users will configure JIRA connection once, with the system automatically handling API endpoint construction and connection validation. The Data Source interface will be simplified to focus solely on JQL query editing, with configuration accessible via a dedicated interface.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Dash 3.1.1, dash-bootstrap-components 2.0.2, Flask 3.1.0, requests 2.32.3  
**Storage**: JSON files (app_settings.json for configuration persistence)  
**Testing**: pytest 8.3.5, pytest-playwright for integration tests  
**Target Platform**: Web application (desktop and mobile browsers)  
**Project Type**: Single web application with Dash framework  
**Performance Goals**: Configuration save/load < 500ms, connection test < 10 seconds, UI interactions < 100ms  
**Constraints**: Must maintain backward compatibility with existing JQL query profiles, secure token storage, mobile-responsive UI  
**Scale/Scope**: Single-user local application, ~15 configuration fields to relocate, affects 3-4 existing UI components

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Based on constitutional amendments (v1.2.0 - Pragmatic Development Gates):

### Pre-Implementation Gates

| Gate                      | Status | Notes                                                                                                                                                                                 |
| ------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Mobile-First Design**   | ✅ PASS | Configuration modal/page will be responsive with mobile-first approach. Touch targets will meet 44px minimum.                                                                         |
| **Performance Standards** | ✅ PASS | Configuration operations (save/load) target < 500ms. Connection test targets < 10s (with progress feedback). No complex computations blocking UI.                                     |
| **Accessibility**         | ✅ PASS | Form inputs will have proper labels, keyboard navigation support. Screen reader friendly with ARIA labels. Aspirational WCAG 2.1 AA.                                                  |
| **Simplicity**            | ✅ PASS | Reasonable scope: 1 new configuration component, 1-2 new callback functions, updates to existing persistence module. Clear single purpose: separate JIRA config from query interface. |
| **Testing Approach**      | ✅ PASS | Unit tests for configuration validation/persistence logic during implementation. Integration tests (Playwright) as final validation before merge.                                     |

### Implementation Quality Gates

*To be verified after Phase 1 design:*

| Gate                         | Target                               | Strategy                                                                          |
| ---------------------------- | ------------------------------------ | --------------------------------------------------------------------------------- |
| **Code Quality**             | Reasonable maintainability           | Type hints where helpful, docstrings where needed, Pylint guidance (not blocking) |
| **Test Coverage**            | Acceptance criteria covered          | Unit tests during development, integration tests final validation                 |
| **Performance Validation**   | Manual testing shows responsiveness  | No formal profiling required unless performance issues detected                   |
| **Accessibility Validation** | Basic keyboard/screen reader testing | Manual verification with browser tools, NVDA testing optional                     |

**Gate Decision**: All pre-implementation gates PASS - proceed to Phase 0 research.

---

### Post-Phase 1 Constitution Check

**Re-evaluation Date**: October 21, 2025  
**Status**: ✅ ALL GATES STILL PASS

| Gate              | Design Review                                                                         | Status |
| ----------------- | ------------------------------------------------------------------------------------- | ------ |
| **Simplicity**    | 3 new files, 3 modified files - within reasonable scope                               | ✅ PASS |
| **Mobile-First**  | Bootstrap modal is mobile-responsive, 44px touch targets confirmed                    | ✅ PASS |
| **Performance**   | All operations use existing patterns (JSON file I/O), connection test has 10s timeout | ✅ PASS |
| **Accessibility** | Form labels, ARIA support via Bootstrap, keyboard navigation designed                 | ✅ PASS |
| **Test Strategy** | Unit tests planned for data/UI layers, Playwright tests as final validation           | ✅ PASS |

**No new concerns identified. Ready to proceed to Phase 2 (Tasks).**

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
# Existing Structure (Dash Web Application)
app.py                          # Main application entry point
callbacks/
├── __init__.py
├── settings.py                 # 🔄 TO MODIFY: Extract JIRA config callbacks
├── visualization.py
├── scope_metrics.py
├── statistics.py
├── jql_editor.py
└── mobile_navigation.py

configuration/
├── __init__.py
├── settings.py                 # Application constants
├── help_content.py
└── server.py

data/
├── __init__.py
├── persistence.py              # 🔄 TO MODIFY: Add JIRA config persistence functions
├── jira_simple.py              # Existing JIRA API integration
├── jira_query_manager.py
├── jira_scope_calculator.py
├── processing.py
├── schema.py
└── scope_metrics.py

ui/
├── __init__.py
├── layout.py                   # Main layout
├── cards.py                    # 🔄 TO MODIFY: Remove JIRA config fields, add config button
├── components.py
├── tabs.py
├── styles.py
├── help_system.py
├── mobile_navigation.py
└── [various utility modules]

tests/
├── unit/
│   ├── ui/
│   ├── data/                   # ➕ TO ADD: Configuration validation tests
│   └── visualization/
├── integration/                # ➕ TO ADD: Configuration workflow tests (Playwright)
└── utils/

# New Files for This Feature
ui/
└── jira_config_modal.py        # ➕ NEW: JIRA configuration modal component

callbacks/
└── jira_config.py              # ➕ NEW: Configuration modal callbacks

tests/
└── unit/
    └── ui/
        └── test_jira_config_modal.py  # ➕ NEW: Unit tests for config component
```

**Structure Decision**: Single web application (Dash framework). Feature adds 1 new UI component module, 1 new callback module, and modifies 3 existing modules (ui/cards.py, callbacks/settings.py, data/persistence.py). Follows existing architectural patterns.

## Complexity Tracking

*No violations - all constitution gates passed. This section intentionally left empty.*

---

## Phase 0 & 1 Completion Summary

### ✅ Phase 0: Research & Design Decisions (Complete)

**Output**: [research.md](./research.md)

**Key Decisions Made**:
1. **UI Pattern**: Bootstrap Modal (consistent with existing help system)
2. **Data Storage**: Extend app_settings.json (backward compatible)
3. **Endpoint Construction**: Server-side in data.jira_simple.py
4. **Connection Test**: Synchronous serverInfo API call (< 10s)
5. **Migration Strategy**: Automatic with zero data loss
6. **Validation**: HTML5 + server-side (security + UX)
7. **Error Handling**: Contextual messages with actionable guidance

**All unknowns resolved** - no NEEDS CLARIFICATION items remain.

---

### ✅ Phase 1: Data Model & Contracts (Complete)

**Outputs**:
- [data-model.md](./data-model.md) - Entity definitions, validation rules, state transitions
- [contracts/dash-callbacks.md](./contracts/dash-callbacks.md) - 6 callback contracts defined
- [quickstart.md](./quickstart.md) - Developer implementation guide

**Artifacts Created**:
1. **Data Model**: 2 entities (JIRA Configuration, Connection Test Result) with complete validation rules
2. **API Contracts**: 6 Dash callbacks covering full workflow (open → load → test → save → cancel → status check)
3. **Quickstart Guide**: 4-phase implementation plan with code examples, testing checklist, common pitfalls

**Agent Context Updated**: GitHub Copilot instructions updated with Python 3.11+, Dash 3.1.1, JSON persistence patterns

---

### 🎯 Ready for Phase 2: Task Breakdown

**Next Command**: `/speckit.tasks`

This will generate a detailed task list (tasks.md) breaking down the implementation into actionable units prioritized by user story (P1 → P2 → P3).

**Estimated Implementation Time**: 4-6 hours (per quickstart.md)

**File Changes Required**:
- 3 new files: `ui/jira_config_modal.py`, `callbacks/jira_config.py`, tests
- 3 modified files: `ui/cards.py`, `data/persistence.py`, `data/jira_simple.py`

---

## Planning Complete

**Branch**: `003-jira-config-separation`  
**Status**: ✅ Design Phase Complete - Ready for Implementation  
**Constitution Gates**: All passed (pre-implementation and post-design)

**Generated Artifacts**:
- ✅ plan.md (this file)
- ✅ research.md (design decisions)
- ✅ data-model.md (entities & validation)
- ✅ contracts/dash-callbacks.md (6 callbacks)
- ✅ quickstart.md (developer guide)
- ⏳ tasks.md (pending `/speckit.tasks` command)

