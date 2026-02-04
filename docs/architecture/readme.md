# Architecture Guidelines Index

**Purpose**: Comprehensive architectural guidelines that establish maintainable, modular, scalable code patterns for both human and AI development. These guidelines ensure:
- **Cognitive clarity**: Code sized for human comprehension and AI context windows
- **Maintainability**: Clear patterns enable safe modifications without cascading effects
- **Modularity**: Independent, reusable components with single responsibilities
- **Quality**: Consistent standards across all languages (Python, JavaScript, HTML, CSS, SQL)
- **Collaboration**: Structures optimized for human-AI pair programming
- **Scalability**: Architectures that grow without becoming unmaintainable

## Quick Reference

| Language       | File Size Limit | Target Size | Key Principles                                          |
| -------------- | --------------- | ----------- | ------------------------------------------------------- |
| **Python**     | 500 lines       | 200-300     | Single Responsibility, Type Hints, Layered Architecture |
| **JavaScript** | 400 lines       | 150-250     | ES6 Modules, Early Returns, Async/Await                 |
| **HTML**       | 300 lines       | 100-200     | Semantic HTML5, Accessibility, Component Split          |
| **CSS**        | 500 lines       | 200-300     | BEM, Variables, Component-Based                         |
| **SQL**        | 50 lines/query  | 30 lines    | Indexes, Transactions, Parameterized Queries            |

## Scope and Applicability

These guidelines are repository-agnostic. Project-specific rules (naming, tooling, branching, CI, environment setup) must live in repository instructions such as copilot-instructions.md or a dedicated repo_rules.md.

## Guidelines by Language

### [Python Guidelines](python_guidelines.md)
- **Max file size**: 500 lines (hard limit)
- **Max function size**: 50 lines
- **Max class methods**: 15 methods
- **Key patterns**:
  - Layered architecture (callbacks → data → persistence)
  - Type hints mandatory
  - Google-style docstrings
  - Single Responsibility Principle
  - Split strategies: Feature-based, Layer-based, Responsibility-based

**When to check**: Before creating/editing any `.py` file

### [JavaScript Guidelines](javascript_guidelines.md)
- **Max file size**: 400 lines (hard limit)
- **Max function size**: 40 lines
- **Key patterns**: ES6 modules (import/export), Airbnb style guide, framework clientside callbacks (if applicable), early returns over nested conditionals, debounce/throttle user input

**When to check**: Before creating/editing any `.js` file

### [HTML Guidelines](html_guidelines.md)
- **Max file size**: 300 lines (hard limit for templates)
- **Max component size**: 200 lines
- **Key patterns**: Semantic HTML5 elements, ARIA attributes mandatory, framework component structure (if applicable), lowercase for all HTML, no inline styles or JavaScript

**When to check**: Before creating/editing HTML or template files

### [CSS Guidelines](css_guidelines.md)
- **Max file size**: 500 lines (hard limit)
- **Max component file**: 300 lines
- **Key patterns**:
  - BEM naming convention
  - CSS custom properties (variables)
  - Class selectors only (no IDs)
  - Component-based organization
  - Mobile-first responsive design

**When to check**: Before creating/editing any `.css` file

### [SQL Guidelines](sql_guidelines.md)
- **Max query length**: 50 lines (hard limit)
- **Max schema file**: 200 lines
- **Max query file**: 400 lines
- **Key patterns**:
  - Foreign keys mandatory
  - Index all foreign keys
  - WAL mode for concurrency
  - Parameterized queries (prevent SQL injection)
  - CTEs for complex queries

**When to check**: Before creating/editing schema or query files

## Common Refactoring Strategies

### 1. Feature-Based Split
Split by functional area when file > limit:

```
# Before: one large file
large_module.py (1200 lines)

# After: feature-based
feature/
├── __init__.py
├── client.py (< 300)
├── query_builder.py (< 250)
├── cache.py (< 200)
└── models.py (< 250)
```

### 2. Layer-Based Split
Split by architectural layer:

```
# Before
handlers/visualization.py (800 lines)

# After
handlers/visualization/
├── __init__.py
├── chart_events.py (< 250)
├── filters.py (< 200)
└── updates.py (< 250)
```

### 3. Component-Based Split
Split by UI component:

```
# Before
assets/custom.css (1000 lines)

# After
assets/components/
├── buttons.css (< 150)
├── modals.css (< 200)
├── forms.css (< 250)
└── charts.css (< 150)
```

## AI Agent Workflow

### Before Creating Code

1. **Check existing file size** (use your editor line count or repo tooling).

2. **If file > 80% of limit → create new file instead**:
   - Python: > 400 lines → new file
   - JavaScript: > 320 lines → new file
   - CSS: > 400 lines → new file

3. **Name new file descriptively**:
   - `service_client.py` ✓
   - `utils.py` ✗

### During Implementation

1. **Track complexity**:
   - Functions > 50 lines (Python) → split
   - Functions > 40 lines (JavaScript) → split
   - Queries > 30 lines (SQL) → refactor

2. **Follow patterns**:
   - Python: Read [python_guidelines.md](python_guidelines.md)
   - JavaScript: Read [javascript_guidelines.md](javascript_guidelines.md)
   - HTML: Read [html_guidelines.md](html_guidelines.md)
   - CSS: Read [css_guidelines.md](css_guidelines.md)
   - SQL: Read [sql_guidelines.md](sql_guidelines.md)

3. **Verify before committing**:
   - Run tests
   - Check `get_errors`
   - Verify file sizes

### When File Exceeds Limit

**Immediate actions**:

1. Identify logical sections
2. Extract to new files
3. Update imports/references
4. Run tests
5. Commit with descriptive message

## Integration with Development Workflow

### Pre-commit Checks

Examples (adjust to your environment and tooling):

- Count lines in large files
- Enforce file size thresholds in CI
- Run static analysis and tests before merge

### Code Review Checklist

- [ ] All files < size limits
- [ ] Functions < line limits
- [ ] Naming conventions followed
- [ ] Architecture patterns applied
- [ ] Type hints present (Python)
- [ ] ARIA attributes present (HTML)
- [ ] BEM naming used (CSS)
- [ ] Queries parameterized (SQL)

## Key Principles Summary

### Universal Rules

1. **KISS** (Keep It Simple, Stupid)
   - Simple solutions over clever ones
   - Early returns over nested conditions
   - Clear names over comments

2. **DRY** (Don't Repeat Yourself)
   - Extract common patterns
   - Create reusable components
   - Use inheritance/composition wisely

3. **Single Responsibility**
   - One purpose per file/function/class
   - Split when doing too much
   - Clear, focused interfaces

4. **Boy Scout Rule**
   - Leave code better than you found it
   - Refactor during feature work
   - Remove dead code

### Language-Specific

**Python**:
- Type hints mandatory
- Docstrings (Google style)
- Layered architecture
- Early returns

**JavaScript**:
- ES6 modules
- Async/await for promises
- Debounce user input
- Cache DOM queries

**HTML**:
- Semantic elements
- ARIA mandatory
- No inline styles/JS
- Component-based

**CSS**:
- BEM naming
- Variables for theming
- Class selectors only
- Mobile-first

**SQL**:
- Foreign keys mandatory
- Index foreign keys
- Parameterized queries
- WAL mode enabled

## Tools and Automation

### Linting

```bash
# Python
flake8 --max-line-length=120 --max-complexity=10

# JavaScript
eslint --config .eslintrc.json

# CSS
stylelint "**/*.css"

# SQL
sqlfluff lint
```

### Complexity Analysis

```bash
# Python complexity
radon cc data/ -a -nb

# Python maintainability
radon mi data/
```

### File Size Monitoring

```python
# scripts/check_file_sizes.py
import os
import sys

LIMITS = {
    '.py': 500,
    '.js': 400,
    '.css': 500,
    '.html': 300,
}

def check_file_sizes(directory):
    violations = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in LIMITS:
                path = os.path.join(root, file)
                lines = sum(1 for _ in open(path))
                if lines > LIMITS[ext]:
                    violations.append((path, lines, LIMITS[ext]))
    return violations

if __name__ == '__main__':
    violations = check_file_sizes('.')
    if violations:
        print("File size violations:")
        for path, lines, limit in violations:
            print(f"  {path}: {lines} lines (limit: {limit})")
        sys.exit(1)
```

## Resources

### External Style Guides

- **Python**: [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- **JavaScript**: [Airbnb JavaScript Style Guide](https://github.com/airbnb/javascript)
- **HTML/CSS**: [Google HTML/CSS Style Guide](https://google.github.io/styleguide/htmlcssguide.html)
- **SQL**: [SQLite Best Practices](https://www.sqlite.org/bestpractice.html)

### Internal Documentation

- [Repository instructions](../../.github/copilot-instructions.md)
- [Repository rules](../../repo_rules.md)
- [Agent Instructions](../../agents.md)
- [Defensive Refactoring Guide](../defensive_refactoring_guide.md)
- [Logging Standards](../LOGGING_STANDARDS.md)

## Version History

- **v1.0** (2026-01-30): Initial guidelines based on Google, Airbnb, and Node.js best practices
  - Python: 500 line limit, type hints mandatory
  - JavaScript: 400 line limit, ES6 modules
  - HTML: 300 line limit, semantic + ARIA
  - CSS: 500 line limit, BEM naming
  - SQL: 50 line queries, foreign keys mandatory
