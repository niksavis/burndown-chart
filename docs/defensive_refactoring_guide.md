# Defensive Refactoring Guide

**Audience**: Human developers and AI coding agents performing code cleanup
**Purpose**: Systematic removal of unused code, obsolete comments, and dead dependencies
**Philosophy**: Safety first - verify before removing, test after each change

---

## 🎯 When to Use This Guide

**Triggers for refactoring**:
- Codebase has accumulated TODOs older than 6 months
- Code search returns false positives from dead code
- New developers confused by commented-out alternatives
- Import statements cluttered with unused dependencies
- Functions exist with no callers (confirmed via search)

**Before starting**:
- ✅ All tests passing on main branch
- ✅ No active feature branches with merge conflicts
- ✅ Team aware of refactoring work (avoid parallel changes)
- ✅ Time allocated for careful verification (not rushed)

---

## ⚡ Quick Win Process (Function Removal)

### 1. Create Backup Branch

```powershell
git checkout -b refactor/remove-unused-functions-$(Get-Date -Format "yyyyMMdd")
git push -u origin HEAD
```

### 2. Find Unused Functions

**Option A: Automated (recommended)**

```powershell
# Install Vulture
.\.venv\Scripts\activate; pip install vulture

# Run analysis
.\.venv\Scripts\activate; vulture . --min-confidence 80 --exclude .venv,__pycache__ > dead_code_report.txt

# Review candidates
Get-Content dead_code_report.txt | Select-String -Pattern "unused function"
```

**Option B: Manual Search**

```powershell
# For each function, check if it's used anywhere
function Test-FunctionUsage {
    param([string]$FunctionName, [string]$SourceFile)
    
    $directCalls = Select-String -Path "*.py" -Pattern "\\b$FunctionName\\(" -Recurse
    $imports = Select-String -Path "*.py" -Pattern "import.*\\b$FunctionName\\b" -Recurse
    $moduleRefs = Select-String -Path "*.py" -Pattern "\\.$FunctionName\\b" -Recurse
    
    $totalMatches = ($directCalls | Measure-Object).Count + 
                    ($imports | Measure-Object).Count + 
                    ($moduleRefs | Measure-Object).Count
    
    if ($totalMatches -eq 0 -or ($totalMatches -eq 1 -and $directCalls[0].Path -eq $SourceFile)) {
        Write-Host "UNUSED: $FunctionName in $SourceFile" -ForegroundColor Yellow
        return $false
    }
    return $true
}

# Example
Test-FunctionUsage -FunctionName "calculate_old_metric" -SourceFile "data/processing.py"
```

### 3. Verify Safe to Remove

**DO NOT REMOVE if function has any of these**:

```powershell
# Check for callback decorators
Select-String -Path "callbacks/*.py" -Pattern "@callback|@app.callback" -Recurse

# Check for __init__.py exports
Select-String -Path "*/__init__.py" -Pattern "from .* import|__all__" -Recurse

# Check for unit tests
Select-String -Path "tests/unit/**/*.py" -Pattern "def test_.*$FunctionName|class Test.*$FunctionName" -Recurse
```

### 4. Remove Function Safely

**Per-function checklist**:

```powershell
# 1. Run tests BEFORE removal
.\.venv\Scripts\activate; pytest tests/unit/ -v

# 2. Remove the function and related imports
# (manually edit the file)

# 3. Run tests AFTER removal
.\.venv\Scripts\activate; pytest tests/unit/ -v

# 4. Commit if tests pass
git add <file>
git commit -m "refactor: remove unused function $FunctionName"
```

### 5. Clean Up Comments

```powershell
# Find old TODOs (>6 months)
Select-String -Path "*.py" -Pattern "TODO.*\d{4}-\d{2}-\d{2}" -Recurse

# Find deprecated warnings
Select-String -Path "*.py" -Pattern "deprecated|legacy|old.*implementation" -Recurse
```

**Comment cleanup rules**:

- ✅ **Remove**: Commented-out code (use git history)
- ✅ **Remove**: Outdated TODOs (>6 months old)
- ✅ **Remove**: Redundant comments explaining obvious code
- ❌ **Keep**: Complex algorithm explanations
- ❌ **Keep**: Business logic rationale

### 6. Clean Up Imports

```powershell
# Install Ruff (fast linter)
.\.venv\Scripts\activate; pip install ruff

# Auto-fix unused imports
.\.venv\Scripts\activate; ruff check . --select F401 --fix
```

### 7. Final Validation

```powershell
# Full test suite
.\.venv\Scripts\activate; pytest tests/ -v

# Check syntax
.\.venv\Scripts\activate; python -m py_compile **/*.py

# Verify app starts
.\.venv\Scripts\activate; python -c "import app; print('App loads successfully')"

# Push if all tests pass
git push origin refactor/remove-unused-functions-$(Get-Date -Format "yyyyMMdd")
```

## 🚨 Safety Rules

**NEVER remove without verification**:

1. Functions with `@callback` or `@app.callback` decorators
2. Functions in `callbacks/__init__.py` registrations
3. Functions exported in `__init__.py` files
4. Functions with unit tests in `tests/unit/`
5. Entry points: functions in `app.py`, `server.py`

**ALWAYS**:

1. Create backup branch before starting
2. Run tests before AND after each removal
3. Commit incrementally with descriptive messages
4. Keep git history clean (no force pushes to main)

## 📋 Example Workflow

```powershell
# 1. Setup
git checkout -b refactor/remove-unused-20251112
.\.venv\Scripts\activate; pip install vulture ruff

# 2. Find candidates
.\.venv\Scripts\activate; vulture . --min-confidence 80 --exclude .venv > candidates.txt
Get-Content candidates.txt | Select-String "unused function"

# 3. Verify one function at a time
Test-FunctionUsage -FunctionName "calculate_legacy_score" -SourceFile "data/processing.py"

# 4. Remove if safe
# Edit data/processing.py to remove function

# 5. Test
.\.venv\Scripts\activate; pytest tests/unit/ -v

# 6. Commit if tests pass
git add data/processing.py
git commit -m "refactor: remove unused calculate_legacy_score"

# 7. Repeat for next function
# ...

# 8. Final push
.\.venv\Scripts\activate; pytest tests/ -v --cov=data --cov=callbacks
git push origin refactor/remove-unused-20251112
```

## 📚 Full Details

For comprehensive guidance, see:

- **Core axioms**: `.github/copilot-instructions.md` → Core Axioms (Zero Errors, Layering, Test Isolation, etc.)
- **Repository rules**: `repo_rules.md` → Architecture and Layering, Code Standards, Testing

## 🔄 Rollback Plan

```powershell
# If issues arise after merge
git revert <commit-sha>
git push origin main

# Or restore entire branch
git checkout main
git reset --hard origin/main~5  # Reset 5 commits back
git push --force-with-lease origin main
```

---

**Remember**: Defensive refactoring is about safety first. When in doubt, DON'T remove - investigate further.

---

## 🤖 AI Agent Guidelines

When performing refactoring tasks:

1. **ALWAYS verify against core axioms**: Check `.github/copilot-instructions.md` Core Axioms before removing code
2. **Context gathering**: Use semantic search and grep to find ALL references before declaring code unused
3. **Test-driven**: Run tests before AND after each removal - failures mean the code wasn't actually unused
4. **Incremental commits**: One function removal per commit with clear message format: `refactor: remove unused <function_name> from <module>`
5. **Documentation updates**: After code removal, check if any documentation references the removed code
6. **Ask for confirmation**: If uncertain about whether code is used (dynamic imports, reflection, etc.), ask the human before removing

**Common pitfalls for AI agents**:
- ❌ Removing code based on simple text search (misses dynamic imports, getattr, **import**)
- ❌ Batch removing multiple functions in one commit (hard to rollback specific changes)
- ❌ Forgetting to check test files for references
- ❌ Not running tests after removal (assuming they'll still pass)
- ❌ Removing code just because it has TODO comments (the TODO might be valid)

**Best practices for AI agents**:
- ✅ Use AST parsing to understand code structure, not just text search
- ✅ Check for indirect usage via decorators, metaclasses, dynamic registration
- ✅ Verify callback registration patterns in Dash apps (see layered architecture principle)
- ✅ Confirm with human if confidence < 90% that code is safe to remove
- ✅ Provide refactoring summary after completion: "Removed X functions, Y imports, Z lines of comments"

---

## 📊 Success Metrics

Track these metrics to measure refactoring impact:

```powershell
# Before refactoring
$beforeStats = @{
    TotalLines = (Get-Content **/*.py | Measure-Object -Line).Lines
    TotalFunctions = (Select-String -Path "*.py" -Pattern "^def " -Recurse | Measure-Object).Count
    UnusedImports = (ruff check . --select F401 | Measure-Object).Count
}

# After refactoring
$afterStats = @{
    TotalLines = (Get-Content **/*.py | Measure-Object -Line).Lines
    TotalFunctions = (Select-String -Path "*.py" -Pattern "^def " -Recurse | Measure-Object).Count
    UnusedImports = (ruff check . --select F401 | Measure-Object).Count
}

# Calculate impact
$linesRemoved = $beforeStats.TotalLines - $afterStats.TotalLines
$functionsRemoved = $beforeStats.TotalFunctions - $afterStats.TotalFunctions
Write-Host "Refactoring impact: $linesRemoved lines removed, $functionsRemoved functions removed"
```

**Target improvements**:
- Reduce codebase by 5-10% (lines of code)
- Zero unused imports (ruff check passes clean)
- Zero TODOs older than 6 months
- Test coverage maintained or improved (no tests removed without removing functionality)

---

## 🔗 Related Documentation

- **Core axioms**: `.github/copilot-instructions.md` → Core Axioms (Zero Errors, Layering, Test Isolation)
- **Repository rules**: `repo_rules.md` → Architecture and Layering, Code Standards, Testing
- **Architecture guidelines**: `docs/architecture/` → Language-specific guidelines and best practices

---

*Document Version: 1.0 | Last Updated: December 2025*
