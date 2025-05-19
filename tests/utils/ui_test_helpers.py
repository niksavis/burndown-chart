"""
Helper utilities for testing UI components.

This module provides reusable functions for extracting and validating
formatted values from UI components.

## Usage Examples

### Extracting numeric values from UI components

```python
from tests.utils.ui_test_helpers import extract_numeric_value_from_component

# Create a velocity metric card
card = _create_velocity_metric_card(
    title="Avg Items",
    value=8.72,
    trend=5,
    trend_icon="fas fa-arrow-up",
    trend_color="green",
    color="blue",
    is_mini=False,
)

# Extract the value
numeric_value = extract_numeric_value_from_component(card.children[1])
assert round(numeric_value, 1) == 8.7
```

### Validating component structure

```python
from tests.utils.ui_test_helpers import validate_component_structure

# Ensure component has the required structure
assert validate_component_structure(card, ['children'], min_children=2)
```

### Extracting formatted strings from UI components

```python
from tests.utils.ui_test_helpers import extract_formatted_value_from_component

# Get the formatted string value
formatted_value = extract_formatted_value_from_component(
    component=card.children[1],
    property_path=['children', 'children']
)
assert formatted_value == "8.7"
```
"""

import re
from typing import Any, Optional, List


def extract_numeric_value_from_component(
    component: Any, property_path: Optional[List[str]] = None
) -> Optional[float]:
    """
    Extract a numeric value from a UI component.

    This function tries to extract a numeric value from a component in two ways:
    1. First by trying to follow a property path (e.g., ['children', 'children'])
    2. If that fails, by converting the component to a string and extracting numbers using regex

    Args:
        component: The UI component to extract value from
        property_path: Optional list of attribute names to follow (e.g., ['children', 'children'])

    Returns:
        Extracted numeric value as float, or None if no value could be extracted
    """
    # Method 1: Try to follow the property path
    if property_path:
        try:
            value = component
            for prop in property_path:
                if hasattr(value, prop):
                    value = getattr(value, prop)
                else:
                    # Path doesn't exist
                    value = None
                    break

            # If we got a value and it can be converted to float, return it
            if value is not None:
                try:
                    return float(value)
                except (ValueError, TypeError):
                    # Not a numeric value
                    pass
        except Exception:
            # Any exception means this method failed
            pass

    # Method 2: Extract from string representation
    try:
        value_str = str(component)
        # Look for a number with a decimal point (pattern: digits.digit)
        matches = re.findall(r"\d+\.\d+", value_str)
        if matches:
            return float(matches[0])

        # Try to find just a number without decimal
        matches = re.findall(r"\d+", value_str)
        if matches:
            return float(matches[0])
    except Exception:
        # Any exception means this method failed too
        pass

    # Could not extract a value
    return None


def extract_formatted_value_from_component(
    component: Any, property_path: Optional[List[str]] = None
) -> Optional[str]:
    """
    Extract a formatted string value from a UI component.

    Similar to extract_numeric_value_from_component, but returns the formatted
    string instead of converting to float.

    Args:
        component: The UI component to extract value from
        property_path: Optional list of attribute names to follow (e.g., ['children', 'children'])

    Returns:
        Extracted formatted string, or None if no value could be extracted
    """
    # Method 1: Try to follow the property path
    if property_path:
        try:
            value = component
            for prop in property_path:
                if hasattr(value, prop):
                    value = getattr(value, prop)
                else:
                    # Path doesn't exist
                    value = None
                    break

            # If we got a value and it's a string or can be converted to string, return it
            if value is not None:
                return str(value)
        except Exception:
            # Any exception means this method failed
            pass

    # Method 2: Extract from string representation
    try:
        value_str = str(component)
        # Look for a number with a decimal point (pattern: digits.digit)
        matches = re.findall(r"\d+\.\d+", value_str)
        if matches:
            return matches[0]

        # Try to find just a number without decimal
        matches = re.findall(r"\d+", value_str)
        if matches:
            return matches[0]
    except Exception:
        # Any exception means this method failed too
        pass

    # Could not extract a value
    return None


def validate_component_structure(
    component: Any, expected_attrs: List[str], min_children: Optional[int] = None
) -> bool:
    """
    Validate that a component has the expected attributes and minimum number of children.

    Args:
        component: The UI component to validate
        expected_attrs: List of attribute names that should exist on the component
        min_children: Minimum number of children the component should have (if 'children' attr exists)

    Returns:
        True if the component has the expected structure, False otherwise
    """
    if component is None:
        return False

    # Check that all expected attributes exist
    for attr in expected_attrs:
        if not hasattr(component, attr):
            return False

    # If min_children is specified and the component has a children attribute,
    # check that it has at least min_children
    if min_children is not None and hasattr(component, "children"):
        children = getattr(component, "children")
        if children is None:
            return False
        if not hasattr(children, "__len__"):
            return False
        if len(children) < min_children:
            return False

    return True
