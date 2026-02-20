# Context Routing Map

**Purpose**: Help agents quickly identify which files to load into context for different task types.

**Last Updated**: 2026-02-20

## How to use this map

1. Identify the task type (bug fix, feature, refactor, etc.)
2. Find the relevant system area
3. Load the suggested core files first
4. Expand to related files only if needed
5. Use semantic_search for unknown areas

## Task Type → File Routing

### 1. Python Backend Changes

#### Data layer changes (business logic, API calls, calculations)

**Core files** (always load):

- `data/{specific_module}.py` - The module being changed
- `data/__init__.py` - Module exports
- `docs/architecture/python_guidelines.md` - Coding standards

**Related files** (load as needed):

- `callbacks/{related_callback}.py` - If callback delegates to this module
- `tests/unit/data/test_{module}.py` - Existing tests
- `data/persistence/` - If database operations involved
- `data/jira/` - If JIRA API calls involved

**Validation**:

- Run `get_errors` on changed files
- Run `pytest tests/unit/data/test_{module}.py -v`

#### Callback changes (event routing only)

**Core files**:

- `callbacks/{specific_callback}.py` - The callback being changed
- `data/{delegate_module}.py` - Business logic this delegates to
- `.github/instructions/python-dash-layering.instructions.md` - Layering rules

**Related files**:

- `ui/{component}.py` - UI component this callback serves
- `assets/{clientside}.js` - If clientside callback coordination needed

**Validation**:

- Verify callback only routes (no business logic)
- Run `get_errors`
- Test in browser

#### Visualization changes (charts, plotting)

**Core files**:

- `visualization/{chart_module}.py` - The chart being changed
- `visualization/chart_config.py` - Chart configuration
- `visualization/helpers.py` - Shared utilities

**Related files**:

- `data/{data_module}.py` - Data preparation for chart
- `callbacks/visualization.py` - Callback that triggers chart
- `tests/visual/test_{chart}.py` - Visual regression tests

**Validation**:

- Run `get_errors`
- Visual verification in browser
- Check chart performance (<500ms target)

### 2. Frontend/JavaScript Changes

#### Clientside callbacks

**Core files**:

- `assets/{callback}.js` - The clientside callback
- `.github/skills/frontend-javascript-quality/SKILL.md` - JS patterns
- `docs/architecture/javascript_guidelines.md` - Coding standards

**Related files**:

- `callbacks/{related_callback}.py` - Server callback coordination
- `ui/{component}.py` - UI component structure
- `assets/{related}.css` - Styling

**Validation**:

- Run `get_errors`
- Browser console check (no errors)
- Test keyboard navigation
- Test mobile viewport

#### CSS/Styling changes

**Core files**:

- `assets/{stylesheet}.css` - The CSS being changed
- `docs/design_system.md` - Design tokens
- `docs/architecture/css_guidelines.md` - CSS standards

**Related files**:

- `ui/{component}.py` - Component using these styles
- `assets/custom.css` - Global styles (check for conflicts)

**Validation**:

- Visual verification (desktop + mobile)
- No layout breakage
- Accessibility (contrast, focus states)

### 3. Database/Persistence Changes

#### Schema changes or migrations

**Core files**:

- `data/persistence/sqlite/backend.py` - SQLite backend
- `data/migration/schema.py` - Schema definitions
- `data/migration/migrator.py` - Migration logic
- `.github/skills/sqlite-persistence-safety/SKILL.md` - Safety patterns

**Related files**:

- `data/schema.py` - Data models
- `tests/unit/data/persistence/` - Persistence tests
- `docs/sqlite_persistence.md` - Architecture docs

**Validation**:

- Test migration on clean DB
- Test migration on existing data
- Verify backward compatibility
- Run `get_errors`
- Run `pytest tests/unit/data/persistence/ -v`

#### Cache changes

**Core files**:

- `data/cache_manager.py` - Cache orchestration
- `data/jira/cache_operations.py` - JIRA cache ops
- `data/jira/cache_validator.py` - Cache validation
- `.github/instructions/cache-management.instructions.md` - Cache patterns

**Related files**:

- `data/persistence/sqlite/issues_cache.py` - Issue caching
- `docs/caching_system.md` - Cache architecture
- `data/metrics_cache.py` - Metrics caching

**Validation**:

- Test cache hit/miss scenarios
- Verify invalidation logic
- Check performance improvement
- Run `get_errors`

### 4. JIRA Integration Changes

**Core files**:

- `data/jira/adapter.py` - JIRA API client
- `data/jira/cache_operations.py` - Caching layer
- `.github/skills/jira-integration-reliability/SKILL.md` - Reliability patterns
- `docs/jira_configuration.md` - JIRA config docs

**Related files**:

- `callbacks/jira_*.py` - JIRA callbacks
- `data/field_detector.py` - Field mapping
- `data/field_mapper.py` - Field transformation
- `tests/unit/data/jira/` - JIRA tests

**Validation**:

- Test with real JIRA instance (use test data)
- Verify error handling
- Check sanitized logging (no customer data)
- Run `get_errors`

### 5. UI Component Changes

**Core files**:

- `ui/{component}.py` - The UI component
- `ui/styles.py` or `ui/style_constants.py` - Styling utilities
- `docs/architecture/python_guidelines.md` - Python standards

**Related files**:

- `callbacks/{related}.py` - Callbacks serving this component
- `assets/{related}.js` - Clientside behavior
- `assets/{related}.css` - Component styles
- `ui/components.py` - Shared component utilities

**Validation**:

- Visual verification
- Test all interactive elements
- Check mobile responsiveness
- Run `get_errors`

### 6. Build/Release Changes

**Core files**:

- `release.py` - Release automation
- `build/build.ps1` - Build script
- `.github/skills/release-management/SKILL.md` - Release patterns
- `docs/release_process.md` - Release workflow

**Related files**:

- `regenerate_changelog.py` - Changelog generation
- `changelog.md` - Changelog file
- `build/generate_version_info.py` - Version info
- `pyproject.toml` - Project metadata
- `.github/instructions/release-workflow.instructions.md` - Workflow rules

**Validation**:

- Test in clean environment
- Verify version bumping
- Check changelog generation
- Run build locally

### 7. Updater System Changes

**Core files**:

- `updater/{module}.py` - Updater component
- `data/update_manager.py` - Update orchestration
- `.github/skills/updater-reliability/SKILL.md` - Updater patterns
- `docs/updater_architecture.md` - Updater design

**Related files**:

- `callbacks/app_update.py` - Update UI callbacks
- `ui/update_notification.py` - Update notification UI
- `build/updater.spec` - Updater build spec

**Validation**:

- Test two-phase update flow
- Verify file replacement
- Test rollback on failure
- Run `get_errors`

### 8. Configuration Changes

**Core files**:

- `configuration/{module}.py` - Configuration module
- `.github/instructions/configuration-changes.instructions.md` - Config patterns
- `data/config_validation.py` - Validation logic

**Related files**:

- `data/persistence/sqlite/app_state.py` - Persisted config
- `ui/{config_form}.py` - Configuration UI
- `callbacks/{config_callback}.py` - Config callbacks

**Validation**:

- Test default values
- Verify validation rules
- Check persistence
- Run `get_errors`

### 9. Testing Additions

**Core files**:

- `tests/{type}/{module}/test_{feature}.py` - Test file
- `tests/conftest.py` - Shared fixtures
- `.github/instructions/testing-quality.instructions.md` - Test standards
- `.github/prompts/add-targeted-tests.prompt.md` - Test patterns

**Related files**:

- Source file being tested
- `tests/fixtures/` - Test data
- `tests/utils/` - Test utilities

**Validation**:

- Run new tests: `pytest tests/{path} -v`
- Verify isolation (no side effects)
- Check coverage: `pytest --cov={module}`
- Run `get_errors`

### 10. Documentation Updates

**Core files**:

- `docs/{specific_doc}.md` - The doc being updated
- `.github/prompts/documentation-update.prompt.md` - Doc patterns
- `docs/readme.md` - Doc index

**Related files**:

- Related code files (for accuracy)
- Other docs in same area (cross-references)

**Validation**:

- Verify accuracy against code
- Check markdown formatting
- Update doc index if new file
- Run `get_errors`

## Context Strategy by Task Type

| Task Type            | Strategy          | Max Files | Focus Folders                     |
| -------------------- | ----------------- | --------- | --------------------------------- |
| Single bug fix       | Targeted          | 3-5       | Specific module + tests           |
| Feature addition     | Targeted-chunking | 10-15     | Feature area + layer coordination |
| Refactor             | Strict-chunking   | 5-10      | Module being refactored + callers |
| Architecture change  | Strict-chunking   | 15-25     | All affected layers               |
| Build/release change | Targeted          | 5-8       | build/ + release scripts          |
| Documentation        | Targeted          | 2-5       | Specific doc + related code       |

## Semantic Search Queries

When file locations are unknown, use these semantic search patterns:

- **JIRA integration**: "JIRA API fetch issues authentication error handling"
- **Cache logic**: "cache invalidation cache key generation timestamp"
- **UI components**: "modal form input validation feedback"
- **Charts**: "plotly chart render update data preparation"
- **Database**: "SQLite query transaction persistence repository"
- **Tests**: "test fixture isolation tempfile cleanup"

## File Size Awareness

Before loading files, check token limits:

- **Total codebase**: ~1.9M tokens (too large for full context)
- **Use strict-chunking strategy**: Load <500 lines per file
- **Prefer targeted searches**: semantic_search with specific queries
- **Module focus**: Load specific folders (data/, ui/, callbacks/, etc.)

## Related Documents

- [codebase_context_metrics.md](../docs/codebase_context_metrics.md) - Context sizing
- [copilot_capability_map.md](.github/copilot_capability_map.md) - Artifact usage
- [Architecture index](../docs/architecture/readme.md) - Coding standards
