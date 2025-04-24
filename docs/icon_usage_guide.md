# Icon System Usage Guide

This guide explains how to use the standardized icon system in the Burndown Chart application.

## Overview

The icon system provides consistent usage patterns, semantic naming, and proper accessibility for all icons used in the application. It helps maintain visual consistency and simplifies icon management.

## Basic Usage

### Importing

```python
from ui.icon_utils import create_icon, create_icon_text
```

### Creating a Simple Icon

```python
# Basic icon
create_icon("chart")

# Icon with custom size and color
create_icon("success", size="lg", color="#28a745")
```

### Creating Icon with Text

```python
# Basic icon with text
create_icon_text("info", "Information")

# Icon with text and custom styling
create_icon_text(
    "warning", "Warning Message",
    size="md",
    color="#dc3545",
    spacing="0.75rem"
)
```

## Icon Sizes

The icon system uses standardized sizes:

- **xs**: Extra small (0.75em) - For inline text indicators
- **sm**: Small (0.875em) - For tight spacing or secondary information
- **md**: Medium (1em) - Default size, for most uses
- **lg**: Large (1.25em) - For primary interface elements
- **xl**: Extra large (1.5em) - For section headers

## Available Semantic Names

Instead of using Font Awesome class names directly, use semantic names:

| Semantic Name | Description           | Font Awesome Class      |
| ------------- | --------------------- | ----------------------- |
| add           | Add item              | fa-plus                 |
| delete        | Delete item           | fa-trash                |
| edit          | Edit item             | fa-edit                 |
| save          | Save changes          | fa-save                 |
| download      | Download data         | fa-download             |
| export        | Export to file        | fa-file-export          |
| success       | Success indicator     | fa-check-circle         |
| error         | Error indicator       | fa-exclamation-circle   |
| warning       | Warning indicator     | fa-exclamation-triangle |
| info          | Information indicator | fa-info-circle          |
| help          | Help information      | fa-question-circle      |
| chart         | Chart or graph        | fa-chart-bar            |
| points        | Story points          | fa-chart-bar            |
| items         | Work items            | fa-tasks                |
| forecast      | Forecast data         | fa-chart-line           |

## Accessibility Best Practices

1. **Never use icon-only buttons without tooltips** - Always add tooltips to icon-only buttons
2. **Use appropriate semantic icon names** - Choose names that convey meaning
3. **Include text labels with icons when possible** - Use create_icon_text() instead of bare icons

## Examples

### Button with Icon and Text

```python
dbc.Button(
    create_icon_text("export", "Export Data", size="sm"),
    color="primary"
)
```

### Icon-only Button with Tooltip

```python
button = dbc.Button(
    create_icon("help", size="sm"),
    id="help-button",
    color="link"
)

tooltip = dbc.Tooltip(
    "Show help information",
    target="help-button"
)

# Return both components together
[button, tooltip]
```

### Table Header with Icon

```python
html.Th(create_icon_text("chart", "Statistics", size="sm"))
```

## Component Extraction

For complex components, extract icon-related patterns into helper functions:

```python
def _create_header_with_icon(icon_name, title, color="#20c997"):
    """Create a header with an icon."""
    return html.H5(
        [
            create_icon(icon_name, color=color),
            html.Span(title, className="ms-2"),
        ],
        className="mb-3 border-bottom pb-2 d-flex align-items-center",
    )
```
