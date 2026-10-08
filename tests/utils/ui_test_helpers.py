import re
from typing import Any


def extract_numeric_value_from_component(
    component: Any, property_path: list[str] | None = None
) -> float | None:

    if property_path:
        try:
            value = component
            for prop in property_path:
                if hasattr(value, prop):
                    value = getattr(value, prop)
                else:
                    value = None
                    break

            if value is not None:
                try:
                    return float(value)
                except ValueError, TypeError:
                    pass
        except Exception:
            pass

    try:
        value_str = str(component)
        matches = re.findall(r"\d+\.\d+", value_str)
        if matches:
            return float(matches[0])

        matches = re.findall(r"\d+", value_str)
        if matches:
            return float(matches[0])
    except Exception:
        pass

    return None


def extract_formatted_value_from_component(
    component: Any, property_path: list[str] | None = None
) -> str | None:

    if property_path:
        try:
            value = component
            for prop in property_path:
                if hasattr(value, prop):
                    value = getattr(value, prop)
                else:
                    value = None
                    break

            if value is not None:
                return str(value)
        except Exception:
            pass

    try:
        value_str = str(component)
        matches = re.findall(r"\d+\.\d+", value_str)
        if matches:
            return matches[0]

        matches = re.findall(r"\d+", value_str)
        if matches:
            return matches[0]
    except Exception:
        pass

    return None


def validate_component_structure(
    component: Any, expected_attrs: list[str], min_children: int | None = None
) -> bool:

    if component is None:
        return False

    for attr in expected_attrs:
        if not hasattr(component, attr):
            return False

    if min_children is not None and hasattr(component, "children"):
        children = component.children
        if children is None:
            return False
        if not hasattr(children, "__len__"):
            return False
        if len(children) < min_children:
            return False

    return True
