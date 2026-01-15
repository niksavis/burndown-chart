# Burndown Chart - AI Agent Guide

**What**: Dash PWA for PERT-based agile forecasting with JIRA integration  
**Stack**: Python 3.13, Dash Bootstrap Components, Plotly, Waitress

## CRITICAL RULES (Read First)

### 1. Zero Errors Policy (NON-NEGOTIABLE)

ALL errors MUST be fixed immediately: type errors, linting, runtime. Run `get_errors` after every change.

**Pre-Commit Check (MANDATORY)**: BEFORE any `git add` or `git commit`, you MUST:

1. Run `get_errors` on all modified files
2. Fix ALL errors found (zero tolerance)
3. Verify fixes with another `get_errors` call
4. Only proceed with commit after confirming zero errors

**If errors exist, commit is FORBIDDEN.** No exceptions.

### 2. Layered Architecture (NON-NEGOTIABLE)

`callbacks/` → event handling ONLY, delegate to `data/` layer. Never implement logic in callbacks.

```python
# CORRECT: Callback delegates to data layer
@callback(Output("out", "children"), Input("btn", "n_clicks"))
def handle(n): return my_data_function(n)  # data/ layer

# WRONG: Logic in callback
@callback(...)
def handle(n): return sum([x for x in range(n)])  # ❌ NO LOGIC HERE
```

### 3. KISS + DRY + Boy Scout (NON-NEGOTIABLE)

- **KISS**: Simplify, early returns, break functions >50 lines
- **DRY**: Extract duplicated code (3+ blocks) → helpers
- **Boy Scout**: Every change MUST improve codebase (remove dead code, add type hints, fix smells)

**Code smells to fix**: Magic numbers→constants, long parameter lists→config objects, deep nesting→flatten

**Clean Code**: Single Responsibility (one thing well), Low Coupling (interfaces not implementations), High Cohesion (related functionality grouped), Encapsulation (logic in data layer)

### 4. No Customer Data (NON-NEGOTIABLE)

NEVER commit: real company names, production domains, JIRA field IDs, credentials.  
Use: "Acme Corp", "example.com", "customfield_10001"

### 5. Test Isolation (NON-NEGOTIABLE)

Tests MUST use `tempfile.TemporaryDirectory()` - NEVER create files in project root.

```python
@pytest.fixture
def temp_file():
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name
    yield temp_file
    if os.path.exists(temp_file):
        os.unlink(temp_file)
```

### 6. No Emoji (NON-NEGOTIABLE)

NEVER use emoji in code, logs, commits, or comments - causes encoding issues and breaks grep/search.

### 7. Terminal Management (NON-NEGOTIABLE)

When app running (`python app.py`), MUST open NEW terminal for other commands. Never interrupt app process.

### 8. Self-Healing Documentation (NON-NEGOTIABLE)

When discovering errors or outdated information in `copilot-instructions.md`:

1. **INFORM** user immediately about the discrepancy
2. **PROPOSE** specific correction with evidence from codebase
3. **UPDATE** instructions after user approval

Keep documentation synchronized with evolving codebase. Examples: wrong file paths, obsolete workflows, incorrect technical details.

### 9. Conventional Commits (NON-NEGOTIABLE)

ALL commits MUST follow Conventional Commits format: `type(scope): description`

**Required format**: `type(scope): description` where scope is optional

**Valid types**:

- `feat`: New features for users
- `fix`: Bug fixes for users
- `docs`: Documentation changes
- `style`: Code style changes (formatting, whitespace, no logic change)
- `refactor`: Code restructuring (no feature change)
- `perf`: Performance improvements
- `test`: Adding or updating tests
- `build`: Build system changes (package.json, pip, etc.)
- `ci`: CI/CD pipeline changes (GitHub Actions, etc.)
- `chore`: Maintenance tasks (tooling, dependencies, cleanup)

**Examples**:

```
feat(dashboard): add velocity trend visualization
fix(jira): handle pagination timeout errors
docs(readme): update installation instructions
refactor(metrics): extract calculation logic to helper
chore(deps): update plotly to 5.18.0
```

**Enforcement**: Changelog generation relies on commit types. Non-conforming commits won't appear in user-facing changelogs.

---

## Architecture

```
callbacks/      Event handling ONLY → delegate to data/
data/           Business logic, JIRA API, persistence, calculations
ui/             Component rendering (Dash Bootstrap)
visualization/  Plotly chart generation
configuration/  Constants, settings, help text
```

**Persistence**: SQLite at `profiles/burndown.db` (12 tables: profiles, queries, jira_cache, jira_issues, jira_changelog_entries, project_statistics, project_scope, metrics_data_points, budget_revisions, budget_settings, app_state, task_progress)

---

## Quick Reference

**Run**: `.\.venv\Scripts\activate; python app.py` → http://127.0.0.1:8050  
**Test**: `.\.venv\Scripts\activate; pytest tests/unit/ -v`

**Key Entry Points**:

- `app.py` - Application entry, initialization, migration
- `ui/layout.py` - Main layout, serve_layout()
- `callbacks/__init__.py` - Callback registration hub
- `data/persistence/` - Persistence layer (SQLite backend)
- `data/jira_query_manager.py` - JIRA API (use this, not jira_simple.py)

**Features → Files**:
| Feature | UI | Callback | Data |
|---------|----|---------| -----|
| Dashboard | `ui/dashboard_comprehensive.py` | `callbacks/visualization.py` | `data/metrics_calculator.py` |
| Burndown | - | `callbacks/visualization.py` | `visualization/charts.py` |
| DORA | `ui/dora_metrics_dashboard.py` | `callbacks/dora_flow_metrics.py` | `data/dora_metrics.py` |
| Flow | `ui/flow_metrics_dashboard.py` | `callbacks/dora_flow_metrics.py` | `data/flow_metrics.py` |
| Bugs | `ui/bug_analysis.py` | `callbacks/bug_analysis.py` | `data/bug_processing.py` |
| Settings | `ui/tabbed_settings_panel.py` | `callbacks/tabbed_settings.py` | `data/profile_manager.py` |
| Reports | - | `callbacks/report_generation.py` | `data/report_generator.py` |
| Import/Export | - | `callbacks/import_export.py` | `data/import_export.py` |

---

## Essential Workflows

### Add Callback

```python
# 1. Create callbacks/my_feature.py
from dash import callback, Output, Input
from data.processing import my_function

@callback(Output("out", "children"), Input("btn", "n_clicks"))
def handle(n): return my_function(n)  # Delegate to data/

# 2. Import in callbacks/__init__.py
from callbacks import my_feature  # noqa: F401
```

### Add Dependency

```powershell
# 1. Add to requirements.in with version + comment
# 2. Compile: .\.venv\Scripts\activate; pip-compile requirements.in
# 3. Install: pip install -r requirements.txt
```

### JIRA Integration

Use `data/jira_query_manager.py` (handles pagination, rate limiting, auth). Never call `jira_simple.py` directly.

### Field Mapping (DORA/Flow)

Namespace syntax: `[ProjectFilter.]FieldName[.Property][:ChangelogValue][.Extractor]`

```python
"*.created"                      # Any project, created field
"PROJECT.customfield_10100"      # Specific project, custom field
"*.status.name"                  # Object property access
"*.Status:Done.DateTime"         # Changelog timestamp
"DevOps|Platform.resolutiondate" # Multiple projects
```

See `docs/namespace_syntax.md` for details.

---

## Code Standards

**Naming**: Files `snake_case.py`, Classes `PascalCase`, functions/vars `snake_case`, constants `UPPER_CASE`

**Type Hints**: All functions MUST have type annotations

```python
def calc_velocity(issues: list[dict], days: int) -> float: ...
```

**Logging**: Follow `docs/LOGGING_STANDARDS.md`

```python
logger.info("Velocity calculated", extra={"operation": "calc_velocity", "result": velocity})
# Never log: customer data, credentials, PII
```

**Performance**: Page load <2s, charts <500ms, interactions <100ms

**Windows**: PowerShell only - no Unix commands (`grep`, `find`, `cat`)
| Task | PowerShell |
|------|-----------|
| Find files | `Get-ChildItem -Recurse -Filter "*.py"` |
| Search | `Select-String -Path "*.py" -Pattern "pattern"` |

---

## Version Control

**Branch Strategy**: Before implementing features/bugfixes, ask user: "Create feature branch or work on main?" Wait for decision.

- **Main branch**: Direct commits trigger version update notifications
- **Feature branches**: Enable isolated development and testing

**Version Management** (CRITICAL - every main merge):

1. **FIRST**: `git checkout main && git merge <feature-branch>` (merge to main)
2. **THEN**: `python bump_version.py [major|minor|patch]` (**on main only**)
3. **FINALLY**: `git push origin main --tags` (push with tag)

**MUST verify current branch is main before running bump script.** Bump script auto-updates files, commits, and creates annotated git tag. This sequence ensures tag is on main, not feature branch.

**Commits**: See CRITICAL RULE #9 - Conventional Commits format is MANDATORY

**Self-Review Checklist**:

- [ ] Code follows project conventions
- [ ] No debug code (print statements, commented blocks)
- [ ] Tests pass: `pytest tests/ -v`
- [ ] Zero type errors: `get_errors` tool
- [ ] No sensitive data in code/comments

---

## Development Workflow (Spec-Kit + Beads)

**For new features/specs, follow this structured workflow:**

### 1. Specification (Spec-Kit)

**In VS Code Chat** (`Ctrl+Alt+I`):

```
@speckit.specify <feature description>
```

Creates `specs/<feature>/spec.md` with user stories and acceptance criteria.

### 2. Planning (Spec-Kit)

**In VS Code Chat**:

```
@speckit.plan
```

Generates planning documents: research.md, plan.md, data-model.md, contracts/, quickstart.md

### 3. Task Generation (Spec-Kit)

**In VS Code Chat**:

```
@speckit.tasks
```

Generates `specs/<feature>/tasks.md` with 100+ actionable tasks organized by user stories.

### 4. Import to Beads

```powershell
.\.venv\Scripts\activate; python workflow/tasks_to_beads.py specs/<feature>/tasks.md tasks.jsonl
bd import -i tasks.jsonl --rename-on-import
bd sync
Remove-Item tasks.jsonl
```

### 5. Task Tracking (Beads)

**Daily commands**:

- `bd ready` - Show available tasks
- `bd show <id>` - View task details
- `bd update <id> --status in_progress` - Claim task
- `bd close <id>` - Complete task
- `bd sync` - Sync with git

**Commit format**:

```
feat(scope): description

Closes beads-<issue-id>
```

### 6. Feature Completion

**When all beads tasks are closed**, finalize the Spec-Kit workflow:

1. **Verify all tasks complete**:

   ```powershell
   bd list --status open  # Should show 0 open tasks
   ```

2. **Update tasks.md** - Check off completed tasks in `specs/<feature>/tasks.md`

3. **Update spec.md** - Add completion date and final notes to `specs/<feature>/spec.md`

4. **Run final quality gates**:

   ```powershell
   pytest tests/ -v          # All tests pass
   get_errors                # Zero errors
   ```

5. **Commit documentation updates**:

   ```powershell
   git add specs/<feature>/
   git commit -m "docs(spec-kit): mark <feature> as complete"
   ```

6. **Final sync and push**:

   ```powershell
   bd sync
   git push
   ```

7. **Ready for merge** - Feature branch ready for PR or merge to main

**Complete workflow**: See `workflow/README.md`  
**Tool setup**: See `workflow/SETUP.md`  
**Session completion**: See `AGENTS.md` for mandatory checklist

---

## Component Guidelines

**When to Extract Component**: Code duplicated 2+ places, function >50 lines, clear single responsibility, reusable across views

**Code Reuse**: Check existing code before implementing, extract common logic to utilities, composition over inheritance, document with examples

---

## Testing

**Unit tests**: MUST be written during implementation  
**Integration tests**: After feature completion  
**Browser**: Playwright (not Selenium)

```powershell
pytest tests/unit/ -v                      # Unit tests
pytest tests/integration/ -v               # Integration
pytest --cov=data --cov=ui --cov-report=html  # Coverage
```

### Add Data Source

1. Create `data/my_api.py`
2. Add caching: `@memoize(max_age_seconds=300)`
3. Wire to callback

---

## Key Technical Decisions

- **CodeMirror 5** (not v6): CM6 needs ES modules incompatible with Dash
- **Playwright** (not Selenium): Faster, more reliable browser automation
- **JIRA**: Paginated (100/page), cached with version tracking

---

## Troubleshooting

| Issue                 | Fix                                                 |
| --------------------- | --------------------------------------------------- |
| `ModuleNotFoundError` | Activate venv: `.\.venv\Scripts\activate`           |
| Charts not rendering  | Check browser console, clear cache                  |
| JIRA 401              | Update token in Settings                            |
| Stale data            | `python data/clear_metrics_cache.py` or Update Data |

---

## Documentation Reference

**Metrics**: `docs/dashboard_metrics.md`, `docs/dora_metrics.md`, `docs/flow_metrics.md`, `docs/budget_metrics.md`  
**Architecture**: `docs/caching_system.md`, `docs/namespace_syntax.md`  
**Guides**: `docs/defensive_refactoring_guide.md`, `docs/LOGGING_STANDARDS.md`  
**Index**: `docs/readme.md`, `docs/metrics_index.md`

---

**Version**: 2.2.0 | **Optimized**: 2026-01-14 | Target: <2000 tokens standalone
