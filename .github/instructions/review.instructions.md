---
applyTo: '**/*'
description: 'Comprehensive code review standards for burndown-chart'
---

# Code Review Rules - Burndown

**Stack**: Python 3.13, Dash, Plotly, SQLite | **Platform**: Windows

## CRITICAL Rules (Block Merge)

### Rule 0: Zero Errors

- `get_errors` → 0 errors (no exceptions)

### Rule 1: No Emoji

- ❌ ANY emoji in code/logging/comments
- Breaks grep, encoding issues

### Rule 2: Type Hints

- ALL functions → parameters + return types
- Exception: test fixtures, callbacks (Dash limitation)

### Rule 3: Bead ID

- Format: `type(scope): description (bd-XXX)`
- Types: feat|fix|docs|refactor|test|chore|perf|style|build|ci
- Enables `bd doctor` orphan detection

### Rule 4: No Customer Data

- ❌ Real: company names, domains, JIRA IDs, credentials
- ✓ Use: "Acme Corp", "example.com", "customfield_10001"

### Rule 5: Test Isolation

- MUST: `tempfile.TemporaryDirectory()`
- ❌ Write to: project root, profiles/, logs/, cache/

## Architecture (Layered Pattern)

**Separation of Concerns**:

```
callbacks/     → Event routing ONLY (delegate to data/)
data/          → Business logic, API calls, persistence
ui/            → Component builders (Dash Bootstrap)
visualization/ → Plotly chart generation
```

**FORBIDDEN in callbacks/**:

- Business logic, calculations, file I/O, API calls
- Direct JSON manipulation, complex conditionals

**Entry Points**:

- JIRA API → `data/jira_query_manager.py` (NOT jira_simple.py)
- Database → `data/persistence/` (Repository pattern)
- State → `callbacks/` → delegate → `data/`

## Python Standards (PEP 8+)

### Imports (Order Matters)

```python
# 1. Standard library
import os
from typing import Dict, List

# 2. Third-party
import dash
from dash import html

# 3. Local
from data.persistence import load_app_settings
```

### Error Handling

```python
# ✓ GOOD: Contextual exceptions
raise ValueError(f"Field '{field_name}' missing (expected: {expected})")
raise PersistenceError(f"Profile '{profile_id}' not found")

# ❌ BAD: Generic exceptions
raise Exception("Error occurred")
try: risky() except: pass  # Silent failures
```

### Logging Format

```python
# ✓ GOOD: `[Module] Operation: metrics`
logger.info(f"[JIRA] Fetched {count} issues in {duration:.1f}s")
logger.warning(f"[Cache] Miss: {key[:8]}... (fetching)")

# ❌ BAD: Emojis, redundant prefixes
logger.info("✓ Saved data")  # NO EMOJI
logger.info("Debug: Processing...")  # Use logger.debug()
```

### Function Size

- Max 50 lines → break into helpers if >50
- Early returns > nested conditionals
- Extract duplication (3+ blocks) → DRY

### Naming

```python
snake_case.py       # Files
PascalCase          # Classes
snake_case()        # Functions/variables
UPPER_CASE          # Constants
```

## JavaScript/CSS Standards

### Clientside Callbacks (Dash)

```javascript
// ✓ GOOD: Namespace + clear purpose
window.dash_clientside.namespace_autocomplete = {
  buildAutocompleteData: function(metadata) { ... }
};

// ❌ BAD: Global pollution
function myFunction() { ... }  // Use namespaces
```

### DOM Manipulation

- **React Controlled Inputs**: Use native setters + dispatch events
- **Event Handlers**: Always `removeEventListener` before `addEventListener`
- **Timeouts**: Clear with `clearTimeout` to prevent leaks

### CSS

```css
/* ✓ GOOD: BEM-like, scoped */
.namespace-autocomplete-dropdown {
}
.character-count-warning {
}

/* ❌ BAD: Generic, conflicts */
.dropdown {
}
.warning {
}
```

### Performance

- Debounce: resize/scroll handlers (150ms)
- Minimize: re-renders, DOM queries (cache selectors)
- Use: `requestAnimationFrame` for animations

## Performance Targets

| Layer        | Target | Measurement       |
| ------------ | ------ | ----------------- |
| Page Load    | <2s    | First paint       |
| Chart Render | <500ms | Plotly update     |
| Interaction  | <100ms | Button → feedback |

## Security

### SQL Injection

```python
# ✓ GOOD: Parameterized
cursor.execute("SELECT * FROM issues WHERE id = ?", (issue_id,))

# ❌ BAD: String concatenation
cursor.execute(f"SELECT * FROM issues WHERE id = {issue_id}")
```

### Input Validation

- Validate: user inputs, API responses, file uploads
- Sanitize: before storage, before display (XSS prevention)
- Never: trust external data

## Testing

### Patterns

```python
# ✓ GOOD: Isolation, cleanup
def test_function():
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = SQLiteBackend(Path(tmpdir) / "test.db")
        # Test logic
        # Cleanup automatic

# ❌ BAD: Project pollution
def test_function():
    backend = SQLiteBackend(Path("profiles/test.db"))
```

### Coverage

- New features → unit tests (>80% line coverage)
- Edge cases: empty lists, None, invalid types
- Integration: end-to-end user workflows

## Platform (Windows)

### PowerShell ONLY

```powershell
# ✓ GOOD
Select-String "pattern" file.txt    # NOT grep
Get-ChildItem *.py                  # NOT find
Get-Content file.txt                # NOT cat

# ❌ BAD: Bash commands fail on Windows
grep "pattern" file.txt
find . -name "*.py"
```

### Virtual Environment

- ALWAYS: `.venv\Scripts\activate` before Python commands
- Check: prompt shows `(.venv)`

## Pre-Merge Checklist

```
☐ get_errors → 0
☐ No emoji (code/logging/docs)
☐ Type hints (all functions)
☐ Commit format: type(scope): desc (bd-XXX)
☐ No customer data
☐ Architecture layers respected
☐ Functions <50 lines
☐ Tests → tempfile.TemporaryDirectory()
☐ PowerShell syntax (no bash)
☐ Performance targets met
```

## Review Priority

1. **CRITICAL** (Block): Rules 0-5, architecture violations, security
2. **HIGH**: Performance, missing tests, type hints
3. **MEDIUM**: Code quality (KISS, DRY), naming
4. **LOW**: Style, comments, documentation
