# Implementation Plan: Metrics Performance & Logging Optimization

**Branch**: `008-metrics-performance` | **Date**: November 9, 2025 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-metrics-performance/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

This feature optimizes the DORA and Flow metrics implementation (Feature 007) by adding comprehensive file-based logging with automatic sensitive data redaction, optimizing JIRA data fetching with intelligent cache invalidation and incremental updates, and improving metric calculation performance through pre-loading, caching, and efficient data structures. Target performance: 2s for ≤1000 issues, 5s for 1000-5000 issues, 40% faster data fetches, 60% cache hit rate, 50% reduction in API calls.

## Technical Context

**Language/Version**: Python 3.11 (confirmed from requirements.txt)  
**Primary Dependencies**: Dash 3.1.1, Flask 3.1.2, requests (JIRA API), pytest (testing), Python logging module (stdlib)  
**Storage**: JSON files (app_settings.json, project_data.json, jira_cache.json, jira_changelog_cache.json, metrics_snapshots.json) - file-based persistence  
**Testing**: pytest with pytest-cov for coverage, Playwright for integration tests  
**Target Platform**: Windows development (PowerShell), cross-platform Python web application (Waitress server)  
**Project Type**: Web application - Dash-based PWA with layered architecture  
**Performance Goals**: 2s metric calculation (≤1000 issues), 5s (1000-5000 issues), 40% faster data fetches, 60% cache hit rate, <500ms chart rendering  
**Constraints**: 100 requests/10s JIRA API rate limit, 10MB log file rotation, 30-day log retention, file-based caching (no external cache), single-user environment  
**Scale/Scope**: 100-5000 JIRA issues per dataset, structured logging for all operations, automatic sensitive data redaction

**Logging Architecture**: Currently basic console logging via `logging.basicConfig()` in `configuration/settings.py`. Need to add:
- File handlers with rotation (`logging.handlers.RotatingFileHandler`)
- Structured JSON formatting
- Sensitive data redaction filter
- Performance timing decorators
- Multi-handler setup (console + file)

**Caching Architecture**: Existing cache in `data/jira_simple.py` with JSON files. Need to add:
- Configuration change detection (JQL, field mappings, time period)
- Incremental fetch logic
- Cache metadata tracking
- In-memory caching layer (`functools.lru_cache`, `caching.py` module exists)

**Calculation Optimization**: Existing calculators in `data/dora_calculator.py`, `data/flow_calculator.py`. Need to add:
- Date parsing cache
- Pre-loaded field mapping index
- Shared calculation results
- Input validation before expensive operations

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Core Principle I: Layered Architecture ✅ PASS

**Status**: COMPLIANT - Logging utilities, cache managers, and calculation optimizations will be implemented in `data/` layer. Callbacks remain event handlers only.

**Application**: 
- New logging module: `configuration/logging_config.py` (central logging setup)
- Cache optimization: `data/cache_manager.py` (enhanced caching logic)
- Performance utilities: `data/performance_utils.py` (timing decorators, profiling)
- Calculation helpers: Updates to existing `data/dora_calculator.py`, `data/flow_calculator.py`

### Core Principle II: Test Isolation ✅ PASS

**Status**: COMPLIANT - All tests will use `tempfile` for log files and cache files. No project root pollution.

**Application**:
- Test fixtures: `tests/conftest.py` - add `temp_log_dir`, `temp_cache_dir` fixtures
- Mock logging configuration in tests to use temporary directories
- Validate log rotation with temporary files only

### Core Principle III: Performance Budgets ✅ PASS

**Status**: COMPLIANT - This feature directly addresses performance budgets with specific targets (2s/5s calculations, 40% faster fetches).

**Application**:
- Performance tests: `tests/unit/data/test_performance.py` - validate 2s/5s targets
- Benchmarking: Log execution times for all critical operations
- Regression detection: Compare before/after metrics

### Core Principle IV: Simplicity & Reusability ✅ PASS

**Status**: COMPLIANT - Extract common patterns (logging decorators, cache utilities) into reusable modules. Avoid over-engineering.

**Application**:
- Reusable logging decorator: `@log_performance` for timing
- Reusable cache decorator: `@cached_with_invalidation` for smart caching
- Simple date parsing cache: `functools.lru_cache` on helper function

### Core Principle V: Data Privacy & Security ✅ PASS

**Status**: COMPLIANT - Automatic sensitive data redaction is core requirement (FR-006, FR-008, FR-011).

**Application**:
- Sensitive data filter: `configuration/sensitive_data_filter.py` - regex-based redaction
- Redaction patterns: API tokens (Bearer/token patterns), passwords, customfield values with sensitive data
- Test coverage: Verify redaction works for various sensitive data patterns

**GATE RESULT**: ✅ ALL GATES PASS - Proceed to Phase 0

## Project Structure

### Documentation (this feature)

```text
specs/008-metrics-performance/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
# Web application structure (existing Dash app)

configuration/
├── __init__.py
├── settings.py                    # [MODIFY] Update logging configuration
├── logging_config.py              # [NEW] Centralized logging setup with file rotation
└── sensitive_data_filter.py       # [NEW] Logging filter for redacting sensitive data

data/
├── __init__.py
├── cache_manager.py               # [NEW] Enhanced caching with invalidation logic
├── performance_utils.py           # [NEW] Performance timing decorators and profiling
├── dora_calculator.py             # [MODIFY] Add caching, pre-loading optimizations
├── flow_calculator.py             # [MODIFY] Add caching, pre-loading optimizations
├── field_mapper.py                # [MODIFY] Add indexed field mapping lookup
├── jira_simple.py                 # [MODIFY] Add incremental fetch, cache invalidation
├── jira_query_manager.py          # [MODIFY] Add rate limiting, request queuing
└── persistence.py                 # [MODIFY] Add cache metadata tracking

callbacks/
├── __init__.py
├── dora_flow_metrics.py           # [MODIFY] Add performance logging for metric calculations
├── dashboard.py                   # [MODIFY] Add performance logging for data updates
└── jira_config.py                 # [MODIFY] Trigger cache invalidation on config changes

tests/
├── conftest.py                    # [MODIFY] Add temp_log_dir, temp_cache_dir fixtures
├── unit/
│   ├── configuration/
│   │   ├── test_logging_config.py      # [NEW] Test log rotation, formatting, redaction
│   │   └── test_sensitive_data_filter.py  # [NEW] Test sensitive data patterns
│   └── data/
│       ├── test_cache_manager.py       # [NEW] Test cache invalidation logic
│       ├── test_performance_utils.py   # [NEW] Test timing decorators
│       ├── test_dora_calculator.py     # [MODIFY] Add performance benchmarks
│       └── test_flow_calculator.py     # [MODIFY] Add performance benchmarks
└── integration/
    └── test_logging_workflow.py        # [NEW] End-to-end logging tests

logs/                              # [NEW] Directory for log files (gitignored)
├── app.log                        # Main application log
├── app.log.1                      # Rotated log file
├── performance.log                # Performance metrics log
└── errors.log                     # Error-only log
```

**Structure Decision**: Using existing web application structure. All new logging infrastructure goes in `configuration/` module. Cache and performance optimizations go in `data/` layer per layered architecture principle. Tests follow existing pattern with unit tests in `tests/unit/` organized by module.

## Complexity Tracking

> No violations detected - all constitutional principles are satisfied by the proposed design.

---

## Implementation Phases

### ✅ Phase 0: Research (Complete)

**Status**: Complete - See [research.md](./research.md)

**Key Decisions**:
1. **Logging**: RotatingFileHandler + JSON formatting + SensitiveDataFilter (stdlib)
2. **Cache Invalidation**: MD5 hash-based cache keys (JQL + field_mappings + time_period)
3. **Rate Limiting**: Token bucket algorithm (100 req/10s) + exponential backoff
4. **Performance**: functools.lru_cache for date parsing, pre-computed field indexes
5. **Log Cleanup**: Startup function using os.path.getmtime() for age-based deletion

### ✅ Phase 1: Design & Contracts (Complete)

**Status**: Complete

**Deliverables**:
- ✅ [data-model.md](./data-model.md) - 6 entities (Log Entry, Log File, Cache Metadata, Fetch Operation, Calculation Performance, Performance Threshold)
- ✅ [contracts/logging_api.md](./contracts/logging_api.md) - Logging module API
- ✅ [contracts/cache_api.md](./contracts/cache_api.md) - Cache management module API
- ✅ [contracts/performance_api.md](./contracts/performance_api.md) - Performance utilities module API
- ✅ [quickstart.md](./quickstart.md) - Developer onboarding guide
- ✅ Agent context updated (.github/copilot-instructions.md)

**Constitution Re-check**: ✅ PASS - All 5 principles remain satisfied

### ⏳ Phase 2: Task Breakdown (Pending)

**Status**: Not started - requires separate `/speckit.tasks` command

**Expected Output**: [tasks.md](./tasks.md) - Numbered checklist of implementation tasks derived from API contracts

**Next Command**: User should run `/speckit.tasks` to generate task breakdown

---

## Performance Targets

**Metric Calculations**:
- ≤1000 issues: ≤2 seconds
- 1000-5000 issues: ≤5 seconds

**Data Fetching**:
- 40% faster via incremental updates
- 60% cache hit rate for repeated queries
- 50% reduction in JIRA API calls

**Logging**:
- Log rotation: 10MB max file size, 5 backups
- Retention: 30 days (auto-cleanup on startup)
- Redaction: 100% sensitive data coverage (tokens, passwords, emails)

**System Resources**:
- Log storage: <100MB with rotation
- Memory: <50MB additional for caches
- Startup overhead: <500ms for logging setup + log cleanup

---

## Risk Mitigation

**Risk 1: Log file rotation failures**
- Mitigation: Test rotation logic with various file sizes/permissions
- Fallback: Console-only logging if file handlers fail to initialize

**Risk 2: Cache invalidation false positives**
- Mitigation: Use MD5 hash with normalized config (sorted keys, consistent formatting)
- Validation: Integration tests verify cache invalidation on actual config changes only

**Risk 3: Performance optimization overhead**
- Mitigation: Benchmark each optimization (LRU cache, field indexes) separately
- Rollback: Keep original implementations for performance regression detection

**Risk 4: Sensitive data redaction gaps**
- Mitigation: Comprehensive test suite with known sensitive patterns
- Defense-in-depth: Multiple regex patterns for different token formats

---

## Dependencies

**Upstream Dependencies** (must complete first):
- Feature 007 (DORA & Flow Metrics) - provides calculators to optimize

**Downstream Impacts** (will affect):
- Future metrics features - will benefit from logging infrastructure
- Future API integrations - can reuse rate limiting utilities
- Future performance work - establishes benchmarking patterns

**External Dependencies** (third-party):
- Python stdlib: logging, logging.handlers, functools, hashlib, json, re, time, os
- No new external packages required (uses stdlib only)

---

## Notes

**Implementation Strategy**: Incremental rollout
1. Logging first (provides visibility for subsequent work)
2. Cache optimization second (easier to debug with logging)
3. Calculation optimization last (validate with logging + caching in place)

**Testing Strategy**: Comprehensive unit + integration + performance tests
- Unit: Each module tested in isolation with tempfile fixtures
- Integration: End-to-end workflows with real log files (temporary directories)
- Performance: Benchmarks for all optimized operations with pass/fail criteria

**Documentation**: Inline code comments + API contracts + quickstart guide
- API contracts define public interfaces (parameter types, return values, error handling)
- Quickstart provides step-by-step setup and usage examples
- Code comments explain implementation decisions (especially regex patterns, cache logic)
