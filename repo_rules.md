# Repository Rules

**Purpose**: Define repository-specific rules that keep this codebase maintainable for human and AI contributors. These rules complement the language-agnostic architecture guidelines in docs/architecture/.

## Scope

- Applies to all changes in this repository.
- Repository rules override generic architecture guidelines when they conflict.
- Store repo-specific conventions here (naming, tooling, workflow, release steps).

## Platform and Tooling

- Windows and PowerShell only. Do not use bash commands.
- Use Select-String, Get-ChildItem, Get-Content, and other PowerShell cmdlets.
- Never assume shell state persists between commands.

## Python Virtual Environment

- Activate the venv before any Python command.
- PowerShell pattern:
  - .venv\Scripts\activate; python app.py
  - .venv\Scripts\activate; pytest tests/ -v

## SQLite Querying (Local DB)

Use these patterns for ad-hoc SQLite queries in this repo. They avoid quoting
issues in PowerShell and follow the venv rule.

### Preferred: short Python script file

```powershell
@'
import sqlite3

conn = sqlite3.connect(r"profiles\burndown.db")
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
print([r[0] for r in cur.fetchall()])
conn.close()
'@ | Set-Content -Path .\tmp_query.py

.venv\Scripts\activate; C:/Development/burndown-chart/.venv/Scripts/python.exe .\tmp_query.py
```

### One-liner (only when necessary)

```powershell
.venv\Scripts\activate; C:/Development/burndown-chart/.venv/Scripts/python.exe -c "import sqlite3; conn=sqlite3.connect(r'profiles\\burndown.db'); cur=conn.cursor(); cur.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;\"); print([r[0] for r in cur.fetchall()]); conn.close()"
```

### SQLite CLI (if installed)

```powershell
sqlite3 .\profiles\burndown.db "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;"
```

### Rules

- Always activate the venv in the same command when running Python.
- Prefer a short script file over `-c` to avoid PowerShell quoting errors.
- Keep queries read-only unless the task explicitly requires writes.
- Do not print or store customer data in logs or generated files.

## Architecture and Layering

- callbacks/ contains event handlers only.
- callbacks/ must delegate to data/ for all business logic.
- data/ contains calculations, API calls, and persistence orchestration.
- ui/ contains component builders and layout assembly.
- visualization/ contains chart and plotting logic.
- Persistence lives under data/persistence/.
- JIRA access goes through data/jira_query_manager.py.

## Data Architecture

- **Persistence**: SQLite database at `profiles/burndown.db`
- **Tables** (12): profiles, queries, jira_cache, jira_issues, jira_changelog_entries, project_statistics, project_scope, metrics_data_points, budget_revisions, budget_settings, app_state, task_progress
- **JSON usage**: Export/import/reports only (not primary storage)
- **User Data Protection**: All user data in `profiles/` (excluded via `.gitignore`)

## Code Standards

- No emoji in code, comments, or logs.
- All functions have type hints.
  - Exception: Dash callbacks and test fixtures.
- Functions should stay under 50 lines when possible.
- Avoid duplicate logic; extract helpers when patterns repeat.

## Logging and Data Safety

- Follow docs/LOGGING_STANDARDS.md.
- Never log credentials, tokens, or customer data.
- Use safe placeholders such as Acme Corp, example.com, customfield_10001.

## Testing

- Tests must use tempfile.TemporaryDirectory() for isolation.
- Do not write to profiles/, logs/, cache/, or the project root in tests.

## Security

- Use parameterized SQL queries only.
- Validate user input and external API responses.

## File Naming

- All file names use lowercase with underscores.
- Avoid vague names such as utils.py or misc.py.

## Version Control and Beads

- Commit format: type(scope): description (bd-XXX)
- Close the bead before pushing code.
- Beads metadata is stored in a separate worktree and must be pushed.

## Release Process

- Use release.py for version bumps and tagging.
- Changelog rules:
  - Flat bullet lists only
  - Focus on user benefits
  - Bold major features

## Reference Documents

- docs/architecture/ for repository-agnostic guidelines
- .github/copilot-instructions.md for agent workflow
- docs/LOGGING_STANDARDS.md for logging conventions
- docs/release_process.md for release and packaging steps
