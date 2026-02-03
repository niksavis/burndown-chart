# Python Architecture Guidelines

**Purpose**: Create maintainable, modular, and scalable Python code that is easily understood and modified by both humans and AI agents. These guidelines enforce:
- **Cognitive clarity**: Keep files and functions small enough to understand at a glance
- **Single responsibility**: Each module, class, and function has one clear purpose
- **Discoverability**: Intuitive structure and naming make code easy to navigate
- **Testability**: Focused components are easier to test in isolation
- **Refactorability**: Modular design enables safe changes without cascading effects
- **AI collaboration**: Files sized for AI context windows enable effective AI-assisted development

## File Size Limits

**CRITICAL RULES**:
- **Maximum file size**: 500 lines (hard limit)
- **Target size**: 200-300 lines per module
- **Warning threshold**: 400 lines → refactor immediately

## Module Organization

### Structure Pattern

```
module/
├── __init__.py          # Public API exports only (< 50 lines)
├── core.py              # Core logic (< 300 lines)
├── helpers.py           # Utility functions (< 200 lines)
├── models.py            # Data structures (< 300 lines)
└── tests/
    └── test_*.py        # One test file per module
```

### Naming Conventions

```python
# Files: lowercase_with_underscores.py
module_name.py
jira_query_manager.py

# Classes: PascalCase
class QueryManager:
    pass

# Functions/Variables: snake_case
def fetch_jira_data():
    pass

# Constants: UPPER_CASE
MAX_RETRIES = 3
```

## Breaking Down Large Files

### Strategy 1: Feature-Based Split

**Before** (1200 lines):
```
data/jira_manager.py
```

**After**:
```
data/jira/
├── __init__.py         # Export public API
├── client.py           # API client (< 300 lines)
├── query_builder.py    # JQL construction (< 250 lines)
├── cache.py            # Caching logic (< 200 lines)
└── models.py           # Data models (< 250 lines)
```

### Strategy 2: Layer-Based Split

**Before** (800 lines):
```
callbacks/visualization.py
```

**After**:
```
callbacks/visualization/
├── __init__.py         # Register callbacks
├── chart_events.py     # Chart interactions (< 250 lines)
├── filters.py          # Filter callbacks (< 200 lines)
└── updates.py          # Data update callbacks (< 250 lines)
```

### Strategy 3: Responsibility Split

```python
# BEFORE: One god class (600 lines)
class DataManager:
    def fetch_data(self): ...
    def transform_data(self): ...
    def cache_data(self): ...
    def validate_data(self): ...

# AFTER: Single Responsibility Principle
# fetcher.py (< 200 lines)
class DataFetcher:
    def fetch(self): ...

# transformer.py (< 200 lines)
class DataTransformer:
    def transform(self): ...

# cache.py (< 150 lines)
class CacheManager:
    def cache(self): ...

# validator.py (< 150 lines)
class DataValidator:
    def validate(self): ...
```

## Code Organization Within Files

### Import Grouping (Google Style Guide)

```python
"""Module docstring: one-line summary.

Extended description with usage examples if needed.

Typical usage:
    manager = JiraQueryManager()
    results = manager.fetch_issues()
"""

# 1. Future imports
from __future__ import annotations

# 2. Standard library
import sys
from typing import Any, Optional

# 3. Third-party
import dash
from dash import html

# 4. Local application
from data.jira import client
from utils.logging import get_logger
```

### File Structure Template

```python
"""Module docstring."""

# Imports (grouped as above)
from __future__ import annotations

import logging
from typing import Optional

# Constants
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Logger
logger = logging.getLogger(__name__)

# Type aliases (if needed)
JsonDict = dict[str, Any]

# Classes
class MyClass:
    """Class docstring."""
    
    def __init__(self) -> None:
        """Initialize."""
        pass
    
    def public_method(self) -> None:
        """Public method docstring."""
        pass
    
    def _private_method(self) -> None:
        """Private method docstring."""
        pass

# Module-level functions
def public_function(param: str) -> str:
    """Function docstring.
    
    Args:
        param: Description
    
    Returns:
        Description
    """
    return param

# Private functions
def _helper_function() -> None:
    """Helper function docstring."""
    pass

# Main execution (if applicable)
if __name__ == '__main__':
    main()
```

## Function Complexity

### Maximum Lines Per Function

- **Simple functions**: < 20 lines
- **Complex functions**: < 50 lines
- **Hard limit**: 75 lines → must refactor

### Refactoring Triggers

```python
# BAD: Function doing too much (80 lines)
def process_jira_data(data):
    # Parse data (20 lines)
    # Validate data (25 lines)
    # Transform data (20 lines)
    # Cache data (15 lines)
    pass

# GOOD: Split into focused functions
def process_jira_data(data: dict) -> dict:
    """Process JIRA data through pipeline."""
    parsed = _parse_data(data)
    validated = _validate_data(parsed)
    transformed = _transform_data(validated)
    return _cache_data(transformed)

def _parse_data(data: dict) -> dict:
    """Parse raw JIRA data."""
    # 15 lines
    pass

def _validate_data(data: dict) -> dict:
    """Validate parsed data."""
    # 20 lines
    pass
```

## Class Design

### Single Responsibility Principle

```python
# BAD: God class (400 lines)
class JiraManager:
    def connect(self): ...
    def query(self): ...
    def cache(self): ...
    def transform(self): ...
    def visualize(self): ...

# GOOD: Focused classes
class JiraClient:
    """Handle JIRA API connections."""
    def connect(self): ...
    def query(self): ...

class JiraCache:
    """Manage JIRA data caching."""
    def save(self): ...
    def load(self): ...

class JiraTransformer:
    """Transform JIRA data."""
    def transform(self): ...
```

### Maximum Methods Per Class

- **Data classes**: < 10 methods
- **Service classes**: < 15 methods
- **Warning threshold**: 20 methods → consider splitting

## Type Hints (Mandatory)

```python
# MANDATORY: All functions must have type hints
def fetch_issues(
    project: str,
    max_results: int = 100,
    filters: Optional[dict[str, Any]] = None
) -> list[dict[str, Any]]:
    """Fetch issues from JIRA.
    
    Args:
        project: JIRA project key
        max_results: Maximum issues to fetch
        filters: Optional filter dictionary
    
    Returns:
        List of issue dictionaries
    """
    pass

# Use typing for complex types
from typing import TypedDict

class IssueDict(TypedDict):
    key: str
    summary: str
    status: str

def process_issue(issue: IssueDict) -> None:
    pass
```

## Docstrings (Google Style)

```python
def complex_function(
    param1: str,
    param2: int,
    param3: Optional[bool] = None
) -> tuple[bool, str]:
    """One-line summary.
    
    Extended description providing more context about what
    this function does and why it exists.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        param3: Optional description of param3
    
    Returns:
        Tuple of (success, message)
    
    Raises:
        ValueError: If param2 is negative
        ConnectionError: If API unreachable
    
    Example:
        >>> success, msg = complex_function("test", 5)
        >>> print(success)
        True
    """
    if param2 < 0:
        raise ValueError("param2 must be non-negative")
    return True, "success"
```

## Project-Specific Rules

### Layered Architecture (Burndown Chart)

```
callbacks/          # Event handlers ONLY (< 150 lines each)
├── __init__.py
└── jira_config.py  # Delegates to data/ layer

data/               # Business logic (< 300 lines each)
├── __init__.py
├── jira_query_manager.py
└── persistence/
    └── database.py

ui/                 # Components (< 200 lines each)
└── components/
    └── settings_panel.py

utils/              # Helpers (< 100 lines each)
└── logging.py
```

### Callback Pattern

```python
# callbacks/jira_config.py (< 150 lines)
from dash import callback, Input, Output
from data.jira_query_manager import JiraQueryManager

@callback(
    Output('output-id', 'children'),
    Input('input-id', 'value')
)
def update_config(value: str) -> str:
    """Handle config update - delegate to data layer."""
    manager = JiraQueryManager()
    return manager.update_config(value)
```

### Data Layer Pattern

```python
# data/jira_query_manager.py (< 300 lines)
from data.jira.client import JiraClient
from data.jira.cache import JiraCache

class JiraQueryManager:
    """Coordinate JIRA operations."""
    
    def __init__(self):
        self.client = JiraClient()
        self.cache = JiraCache()
    
    def update_config(self, config: dict) -> dict:
        """Update JIRA configuration."""
        validated = self._validate_config(config)
        self.cache.save_config(validated)
        return validated
```

## Complexity Metrics

### Cyclomatic Complexity

- **Target**: < 10 per function
- **Maximum**: 15 per function
- **Action**: Use `radon cc` to measure

```bash
# Check complexity
pip install radon
radon cc data/ -a -nb
```

### Cognitive Complexity

- **Target**: < 15 per function
- **Indicators of high complexity**:
  - Nested loops (> 2 levels)
  - Nested conditionals (> 3 levels)
  - Multiple return statements (> 3)

```python
# BAD: High cognitive complexity
def process(data):
    if data:
        for item in data:
            if item.valid:
                for child in item.children:
                    if child.active:
                        return child
    return None

# GOOD: Extract to helper functions
def process(data):
    """Process data with early returns."""
    if not data:
        return None
    
    valid_items = _filter_valid(data)
    active_children = _find_active_children(valid_items)
    return active_children[0] if active_children else None
```

## Testing Guidelines

### One Test File Per Module

```
data/
├── jira_query_manager.py
└── tests/
    └── test_jira_query_manager.py  # < 400 lines

# If test file > 400 lines, split by feature
data/
├── jira_query_manager.py
└── tests/
    ├── test_jira_query_manager_basic.py
    ├── test_jira_query_manager_cache.py
    └── test_jira_query_manager_errors.py
```

### Test Organization

```python
# tests/test_module.py
"""Tests for module."""

import pytest
from module import function

class TestBasicFunctionality:
    """Basic functionality tests."""
    
    def test_simple_case(self):
        assert function("input") == "expected"
    
    def test_edge_case(self):
        assert function("") == ""

class TestErrorHandling:
    """Error handling tests."""
    
    def test_invalid_input(self):
        with pytest.raises(ValueError):
            function(None)
```

## Refactoring Checklist

When file exceeds 400 lines:

- [ ] Identify logical sections (classes, functions, helpers)
- [ ] Group related functionality
- [ ] Create submodule if > 3 sections
- [ ] Extract helpers to separate file
- [ ] Update imports in parent module
- [ ] Update `__init__.py` to export public API
- [ ] Run tests to verify behavior unchanged
- [ ] Update documentation

## AI Agent Guidelines

### Before Creating New Code

1. Check existing file sizes: `wc -l *.py`
2. If target file > 300 lines → create new file
3. If module has 5+ files → create subpackage

### When Editing Existing Code

1. Check current line count
2. If approaching 500 lines → split first, then add
3. Use semantic_search to find related code
4. Prefer creating focused files over appending

### Naming New Modules

```python
# Feature-based
data/jira_client.py         # Clear, specific
data/jira_query.py          # Clear, specific

# NOT generic
data/helper.py              # Too vague
data/utils.py               # Too vague
data/misc.py                # Never acceptable
```

## Performance Considerations

### Module Loading

```python
# GOOD: Import at top level
import expensive_module

def function():
    return expensive_module.call()

# BAD: Repeated imports (unless lazy loading needed)
def function():
    import expensive_module  # Avoid
    return expensive_module.call()
```

### Circular Imports

```python
# Prevent circular imports with TYPE_CHECKING
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from data.jira import JiraClient

def function(client: 'JiraClient') -> None:
    """Use string annotation to avoid import."""
    pass
```

## Summary

**Key Principles**:
1. Files < 500 lines (hard limit)
2. Functions < 50 lines (target)
3. Classes < 15 methods
4. Single Responsibility Principle
5. Type hints mandatory
6. Google-style docstrings
7. Layered architecture
8. Test files follow same size limits

**When in doubt**: Create a new file. Small, focused modules are easier to understand, test, and maintain for both humans and AI agents.
