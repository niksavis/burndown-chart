# Icon Usage Guidelines

> **Note:** This is the primary documentation for icon usage in the Burndown Chart application. The file in `docs/icon_usage_guide.md` now redirects here to avoid duplication.

## Overview

This document provides guidelines for consistent icon usage throughout the Burndown Chart Application. Following these standards ensures visual harmony and improved user experience.

## Icon System

The application uses Font Awesome 5 icons with a standardized approach for alignment, sizing, and semantic meaning.

### Key Functions

The following utility functions are available in `ui/styles.py`:

- `create_icon()`: Creates a standalone icon with consistent styling
- `create_icon_text()`: Creates an icon+text combination with proper alignment
- `create_icon_stack()`: Creates stacked icons for combined meanings
- `get_icon_class()`: Gets Font Awesome class from semantic key

## Semantic Icons

Use semantic icon names instead of direct Font Awesome classes whenever possible:

```python
# Recommended
create_icon("success")  # Uses "fas fa-check-circle"

# Avoid
create_icon("fas fa-check-circle")
```

### Common Semantic Icons

| Semantic Name | Font Awesome Class          | Usage                       |
| ------------- | --------------------------- | --------------------------- |
| items         | fas fa-tasks                | Represents work items/tasks |
| points        | fas fa-chart-line           | Represents story points     |
| success       | fas fa-check-circle         | Success state               |
| warning       | fas fa-exclamation-triangle | Warning state               |
| danger        | fas fa-exclamation-circle   | Error state                 |
| info          | fas fa-info-circle          | Information                 |
| chart         | fas fa-chart-bar            | Charts/visualization        |
| data          | fas fa-database             | Data-related actions        |
| deadline      | fas fa-calendar-times       | Project deadlines           |

## Standard Icon+Text Patterns

Always use the `create_icon_text()` function for consistent icon+text combinations:

```python
create_icon_text(
    icon="info",
    text="Important information",
    color="info",
    alignment="center"
)
```

### Best Practices

1. **Left alignment** is the default and preferred position for most icons
2. **Right alignment** should be used only for indicating actions or navigation
3. **Fixed-width icons** ensure alignment in lists or menus
4. **Consistent spacing** between icon and text (auto-handled by utility functions)

## Icon Sizing

Use the predefined size keys from `ICON_SIZES` for consistency:

- `"xs"`: 12px (0.75rem)
- `"sm"`: 14px (0.875rem)
- `"md"`: 16px (1rem) - default
- `"lg"`: 20px (1.25rem)
- `"xl"`: 24px (1.5rem)
- `"xxl"`: 32px (2rem)

```python
# Example
create_icon("info", size="lg")
```

## Proper Alignment

### Vertical Alignment

When combining icons with text, ensure proper vertical alignment:

```python
create_icon_text(
    icon="info",
    text="Important information",
    alignment="center"  # options: top, center, bottom
)
```

### Icon Buttons

Always use `create_icon_button()` for icon-only buttons with appropriate tooltip:

```python
create_icon_button(
    icon_class="delete",
    tooltip="Delete item",
    variant="danger",
    size="sm"
)
```

## Accessibility Considerations

1. Always provide tooltips for icon-only buttons
2. Use semantic colors to enhance meaning
3. Ensure sufficient contrast ratio
4. Icons should support, not replace, text where important

## Examples

### Standard Data Display

```python
create_icon_text(
    icon="items",
    text="73 items remaining",
    icon_color="primary"
)
```

### Status Indicator

```python
create_icon_text(
    icon="success",
    text="Project on schedule",
    color="success"
)
```

### Combined Meaning with Stack

```python
create_icon_stack(
    primary_icon="chart",
    secondary_icon="success",
    primary_color="primary",
    secondary_color="success"
)
```

## Troubleshooting

- If icons appear misaligned, use fixed-width option (`with_fixed_width=True`)
- For alignment issues in tables or grids, ensure all icons have the same size
- If icon colors don't match semantic colors, ensure you're using semantic names
