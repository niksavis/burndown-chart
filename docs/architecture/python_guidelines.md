# Python Architecture Guidelines

**Purpose**: Create maintainable, modular, and scalable Python code that is easily understood and modified by both humans and AI agents. These guidelines enforce:

- **Cognitive clarity**: Keep files and functions small enough to understand at a glance
- **Single responsibility**: Each module, class, and function has one clear purpose
- **Discoverability**: Intuitive structure and naming make code easy to navigate
- **Testability**: Focused components are easier to test in isolation
- **Refactorability**: Modular design enables safe changes without cascading effects
- **AI collaboration**: Files sized for AI context windows enable effective AI-assisted development

## Terminology and Enforcement

- **MUST**: Required rule for all new/updated Python code in scope.
- **SHOULD**: Strong recommendation; deviations need a clear reason.
- **MAY**: Optional guidance for context-specific improvements.

Critical/hard limits in this document are **MUST** constraints.

## 2026 Standards Refresh (Python 3.13-aligned)

Apply these as current defaults for new and updated Python code:

- Prefer modern typing syntax (`list[str]`, `dict[str, Any]`, `X | None`) over legacy `typing.List`/`Optional[X]` forms.
- Prefer `type` aliases (3.12+) over legacy `TypeAlias` for new aliases.
- Prefer `pathlib.Path` operations over `os.path` string manipulation for filesystem code.
- Use context managers (`with`) for files, locks, and resources; ensure deterministic cleanup on error paths.
- Catch specific exceptions first; avoid bare `except` and avoid swallowing exceptions without action.
- Use `asyncio` synchronization/context patterns (`async with` locks/semaphores/task groups) for concurrent async flows.

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

### Layered Architecture (Generic Pattern)

Use a layered architecture to separate responsibilities:

- **Presentation**: UI composition and rendering
- **Callbacks/Handlers**: Event routing only
- **Domain/Data**: Business logic and calculations
- **Persistence**: Storage and external API access

Each layer should depend on lower layers only. Avoid business logic inside UI or event handlers.

```python
# BEFORE: One class does everything
class DataManager:
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
    manager = ServiceManager()
    results = manager.fetch_items()
"""

# 1. Future imports
from __future__ import annotations

# 2. Standard library
import sys
from typing import Any, Optional

# 3. Third-party
import requests

# 4. Local application
from services import api_client
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
def process_records(data):
    # Parse data (20 lines)
    # Validate data (25 lines)
    # Transform data (20 lines)
    # Cache data (15 lines)
    pass

# GOOD: Split into focused functions
def process_records(data: dict) -> dict:
    """Process records through pipeline."""
    parsed = _parse_data(data)
    validated = _validate_data(parsed)
    transformed = _transform_data(validated)
    return _cache_data(transformed)

def _parse_data(data: dict) -> dict:
    """Parse raw records."""
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
class ServiceManager:
    def connect(self): ...
    def query(self): ...
    def cache(self): ...
    def transform(self): ...
    def visualize(self): ...

# GOOD: Focused classes
class ServiceClient:
    """Handle external API connections."""
    def connect(self): ...
    def query(self): ...

class CacheStore:
    """Manage data caching."""
    def save(self): ...
    def load(self): ...

class DataTransformer:
    """Transform data."""
    def transform(self): ...
```

### Maximum Methods Per Class

- **Data classes**: < 10 methods
- **Service classes**: < 15 methods
- **Warning threshold**: 20 methods → consider splitting

## Type Hints (Mandatory)

```python
# MANDATORY: All functions must have type hints
def fetch_items(
    project: str,
    max_results: int = 100,
    filters: dict[str, Any] | None = None
) -> list[dict[str, Any]]:
    """Fetch items from a service.

    Args:
        project: Project key or identifier
        max_results: Maximum issues to fetch
        filters: Optional filter dictionary

    Returns:
        List of item dictionaries
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
    param3: bool | None = None
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

## Framework-Specific Patterns (Optional)

### Layered Architecture (Example)

```
handlers/            # Event handlers only (< 150 lines each)
├── __init__.py
└── settings_handler.py  # Delegates to services

services/            # Business logic (< 300 lines each)
├── __init__.py
├── settings_service.py
└── persistence/
    └── database.py

ui/                  # Components (< 200 lines each)
└── components/
    └── settings_panel.py

utils/               # Helpers (< 100 lines each)
└── logging.py
```

### Handler Pattern (Framework Example)

```python
# handlers/settings_handler.py (< 150 lines)
from framework import callback, Input, Output
from services.settings_service import SettingsService

@callback(
    Output('output-id', 'children'),
    Input('input-id', 'value')
)
def update_settings(value: str) -> str:
    """Handle settings update and delegate to service layer."""
    service = SettingsService()
    return service.update_settings(value)
```

### Service Layer Pattern

```python
# services/settings_service.py (< 300 lines)
from services.api_client import ApiClient
from services.cache_store import CacheStore

class SettingsService:
    """Coordinate settings operations."""

    def __init__(self) -> None:
        self.client = ApiClient()
        self.cache = CacheStore()

    def update_settings(self, config: dict) -> dict:
        """Update settings configuration."""
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
services/
├── query_manager.py
└── tests/
    └── test_query_manager.py  # < 400 lines

# If test file > 400 lines, split by feature
services/
├── query_manager.py
└── tests/
    ├── test_query_manager_basic.py
    ├── test_query_manager_cache.py
    └── test_query_manager_errors.py
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
services/api_client.py      # Clear, specific
services/query_builder.py   # Clear, specific

# NOT generic
services/helper.py          # Too vague
services/utils.py           # Too vague
services/misc.py            # Never acceptable
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
    from services.api_client import ApiClient

def function(client: 'ApiClient') -> None:
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
