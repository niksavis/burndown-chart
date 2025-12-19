# Implementation Plan: Enhanced Import/Export Options

**Branch**: `013-import-export-scenarios` | **Date**: December 19, 2025 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/013-import-export-scenarios/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Extend existing import/export system to support three distinct export modes: (1) Configuration-only for secure team sharing, (2) Full profile with data for offline analysis, and (3) Optional JIRA token inclusion with security warnings. Builds on T009 enhanced import/export foundation to enable collaboration without credential leakage and selective data portability.

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.13  
**Primary Dependencies**: Dash 3.1.1, dash-bootstrap-components 2.0.2, pytest, Playwright (browser testing)  
**Storage**: JSON files in profiles/{profile_id}/ structure (profile.json, queries/{query_id}/*.json)  
**Testing**: pytest with unit, integration, and Playwright-based browser tests  
**Target Platform**: Windows (PowerShell), cross-platform PWA (Dash web app)
**Project Type**: Web application (single codebase, layered architecture)  
**Performance Goals**: Export <3s regardless of cache size, UI interactions <100ms, configuration-only 90% smaller than full export  
**Constraints**: JSON file-based persistence, no database, profile-based multi-tenant structure, 24hr cache TTL  
**Scale/Scope**: Single-user desktop app, 10-50 profiles per installation, 100-10k JIRA issues per query

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: Layered Architecture ✅ PASS
- Export/import logic resides in `data/import_export.py` (existing)
- Callbacks in `callbacks/import_export.py` delegate to data layer
- No business logic in UI callbacks

### Principle II: Test Isolation ✅ PASS
- All tests use `tempfile.TemporaryDirectory()` for file operations
- No tests write to project root
- Existing tests in `tests/unit/data/test_import_export.py` follow pattern

### Principle III: Performance Budgets ✅ PASS
- Export target: <3 seconds (within 2s page load budget)
- UI interactions: <100ms (matches requirement)
- Configuration-only export optimized for minimal file size

### Principle IV: Simplicity & Reusability ✅ PASS
- Extends existing `data/import_export.py` ExportManifest pattern
- Reuses profile/query path resolution logic
- No complex abstractions needed

### Principle V: Data Privacy & Security ✅ PASS
- **CRITICAL**: JIRA token stripping mechanism required (FR-003)
- Default to token exclusion (FR-002)
- Security warning on token inclusion (FR-005)
- All test data uses placeholders (Acme Corp, example.com)

### Principle VI: Defensive Refactoring ✅ PASS
- No unused code removal in this feature
- Extends existing functions, no deprecation needed

**GATE RESULT**: ✅ PASS - All principles satisfied. Proceed to Phase 0.

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
data/
├── import_export.py     # Extend ExportManifest, add export modes
└── query_manager.py     # Profile/query path resolution (existing)

callbacks/
├── import_export.py     # Update export callback with mode selector
└── __init__.py          # Already imports import_export

ui/
├── settings.py          # Add export mode radio buttons + token checkbox
└── toast_notifications.py  # Reuse for success/error notifications

tests/
├── unit/
│   └── data/
│       └── test_import_export.py  # Extend with mode tests
└── integration/
    └── test_import_export_scenarios.py  # New: End-to-end tests

profiles/
├── {profile_id}/
│   ├── profile.json     # Contains JIRA token (strip when needed)
│   └── queries/
│       └── {query_id}/
│           ├── project_data.json     # Exclude in config-only mode
│           ├── jira_cache.json       # Exclude in config-only mode
│           └── metrics_snapshots.json # Include in full mode
```

**Structure Decision**: Web application with Dash layered architecture. All business logic in `data/` layer, UI components in `ui/`, callbacks delegate to data layer. Existing import/export foundation (T009) provides ExportManifest pattern to extend.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

**No violations detected.** All constitution principles satisfied.

---

## Phase 1 Complete: Post-Design Constitution Re-Check

### Principle I: Layered Architecture ✅ PASS (Confirmed)
- **Design**: All business logic in data layer functions (strip_credentials, export_profile_with_mode, validate_import_data, resolve_profile_conflict)
- **Callbacks**: Pure event handlers delegating to data layer
- **Verification**: See contracts/api-contracts.md for clear separation

### Principle II: Test Isolation ✅ PASS (Confirmed)
- **Design**: All tests use tempfile.TemporaryDirectory() for profile/query file operations
- **Pattern**: Existing test fixtures provide tempfile pattern to extend
- **Verification**: quickstart.md includes test isolation examples

### Principle III: Performance Budgets ✅ PASS (Confirmed)
- **Design**: Export <3s (bounded by single query, not all queries)
- **Optimization**: CONFIG_ONLY excludes large cache files (90% reduction)
- **Measurement**: Performance validation scripts in quickstart.md

### Principle IV: Simplicity & Reusability ✅ PASS (Confirmed)
- **Design**: Extends ExportManifest dataclass (existing pattern)
- **Reuse**: Uses existing query_manager path resolution
- **No abstraction creep**: Simple enum for export modes, direct function calls

### Principle V: Data Privacy & Security ✅ PASS (Confirmed)
- **Design**: strip_credentials() with validation assertions
- **Default secure**: Token excluded by default (FR-002)
- **User awareness**: Two-tier warning system (tooltip + modal)
- **Test data**: All examples use "Acme Corp", "example.com" placeholders

### Principle VI: Defensive Refactoring ✅ PASS (Confirmed)
- **Design**: No code removal in this feature
- **Extension only**: Adds new functions, extends existing data structures
- **Backward compatible**: Existing exports continue to work

**POST-PHASE 1 GATE RESULT**: ✅ PASS - Design adheres to all constitution principles. Ready for Phase 2 (task breakdown) via /speckit.tasks command.

---

## Artifacts Generated

### Phase 0: Research
- ✅ [research.md](research.md) - All unknowns resolved, technology decisions documented

### Phase 1: Design
- ✅ [data-model.md](data-model.md) - Entities, validation rules, state transitions
- ✅ [contracts/api-contracts.md](contracts/api-contracts.md) - Function signatures, callback contracts, UI components
- ✅ [quickstart.md](quickstart.md) - Developer onboarding guide with implementation checklist
- ✅ `.github/agents/copilot-instructions.md` - Updated agent context (via update-agent-context.ps1)

### Next: Phase 2 (NOT in this command)
- ⏭️ `tasks.md` - Generated by `/speckit.tasks` command (breaks design into atomic implementation tasks)
