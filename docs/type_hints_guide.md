# Type Hints Guide

This guide provides conventions and best practices for adding type hints to the Burndown Chart application codebase.

## Overview

Type hints improve code quality by:

1. Making code more self-documenting
2. Enabling better IDE support with autocomplete and error detection
3. Catching type-related bugs earlier
4. Improving maintainability and readability

## Basic Type Hint Usage

### Function Annotations

```python
def get_total_points(items: int, value_per_item: float) -> float:
    return items * value_per_item
```

### Variable Annotations

```python
user_count: int = 5
names: list[str] = ["Alice", "Bob", "Charlie"]
```

## Common Types

| Type                    | Example                                       | Description                                        |
| ----------------------- | --------------------------------------------- | -------------------------------------------------- |
| `int`                   | `count: int = 5`                              | Integer values                                     |
| `float`                 | `rate: float = 0.5`                           | Floating point values                              |
| `str`                   | `name: str = "Alice"`                         | String values                                      |
| `bool`                  | `is_active: bool = True`                      | Boolean values                                     |
| `list[T]`               | `scores: list[int] = [95, 87, 91]`            | Lists of type T                                    |
| `dict[K, V]`            | `user_scores: dict[str, int] = {"Alice": 95}` | Dictionaries with keys of type K, values of type V |
| `tuple[T1, T2, ...]`    | `point: tuple[float, float] = (1.0, 2.0)`     | Tuple with specific types                          |
| `set[T]`                | `unique_ids: set[int] = {1, 2, 3}`            | Sets of type T                                     |
| `Optional[T]`           | `middle_name: Optional[str] = None`           | Either type T or None                              |
| `Union[T1, T2, ...]`    | `id_value: Union[int, str] = "ABC123"`        | Can be any of the listed types                     |
| `Any`                   | `data: Any = get_data()`                      | Any type (use sparingly)                           |
| `Callable[[P1, P2], R]` | `handler: Callable[[Event], None]`            | Function type with param types and return type     |

## Project-Specific Types

For our application, we define these common type aliases:

```python
from typing import Dict, List, Union, Optional

# Type aliases
DataRow = Dict[str, Any]
DataTable = List[DataRow]
DateStr = str  # ISO format date string (YYYY-MM-DD)
JsonDict = Dict[str, Any]
NumericValue = Union[int, float]
```

## Type Hints for Dash Components

For Dash components, we use the Component type:

```python
from dash import html
from typing import List, Dict, Any

def create_summary_card(title: str, value: Any) -> html.Div:
    return html.Div([
        html.H4(title),
        html.P(str(value))
    ])

def create_chart_layout(charts: List[html.Div]) -> html.Div:
    return html.Div(charts, className="chart-container")
```

## Type Checking

We use [mypy](http://mypy-lang.org/) for static type checking:

```bash
mypy d:\Development\burndown-chart
```

## Implementation Strategy

1. **Start with Core Utils**: Begin by adding type hints to utility functions that are widely used
2. **Focus on APIs**: Prioritize functions that are called by other modules
3. **Add Gradually**: Add type hints as you touch files in regular development
4. **Type Docstrings**: Make sure docstrings and type hints are consistent

## Best Practices

1. **Be Specific**: Use the most specific type that accurately describes the data
2. **Use Type Aliases**: Create type aliases for complex or recurring types
3. **Don't Over-Type**: Internal function implementations may not need every variable typed
4. **Generics for Collections**: Use generics for collections (`List[str]` rather than just `List`)
5. **Avoid `Any`**: Use `Any` only when necessary, prefer Union types when possible
6. **Document Type Variables**: Add comments for complex type constructs

## Handling Complex Cases

### Dynamic Types

For dynamically determined types, use Union:

```python
def process_value(value: Union[str, int, float]) -> str:
    return str(value)
```

### Keyword Arguments

For functions with many keyword arguments:

```python
def create_component(
    title: str,
    *,
    description: Optional[str] = None,
    is_active: bool = False
) -> html.Div:
    # Implementation
```

### Type Variables and Generics

For functions that preserve types:

```python
from typing import TypeVar, List

T = TypeVar('T')

def first_item(items: List[T]) -> T:
    return items[0]
```

## Adding Types to Existing Functions

Example before:

```python
def calculate_points(items, value_per_item=1.0):
    """Calculate total points based on items count and value per item."""
    return items * value_per_item
```

Example after:

```python
def calculate_points(items: int, value_per_item: float = 1.0) -> float:
    """
    Calculate total points based on items count and value per item.
    
    Args:
        items: Number of items
        value_per_item: Points per item
        
    Returns:
        Total points value
    """
    return items * value_per_item
```
