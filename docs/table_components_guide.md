# Table Components Guide

This guide documents how to use the standardized table components from the `ui.table_components` module.

## Overview

The table components module provides a set of reusable, standardized table components with consistent styling, mobile responsiveness, and accessibility features. These components simplify the creation of tables throughout the application while ensuring consistency.

## Basic Table Component

The most fundamental component is `create_basic_table()`, which creates a Bootstrap-style table with standardized styling:

```python
from ui.table_components import create_basic_table

# Sample data
data = [
    {"name": "Project A", "status": "Active", "progress": "75%"},
    {"name": "Project B", "status": "Completed", "progress": "100%"},
    {"name": "Project C", "status": "On Hold", "progress": "30%"}
]

# Column definitions
columns = [
    {"id": "name", "name": "Project Name"},
    {"id": "status", "name": "Status"},
    {"id": "progress", "name": "Progress"}
]

# Create the table
table = create_basic_table(
    data=data,
    columns=columns,
    id="projects-table",
    striped=True,
    bordered=True,
    hover=True,
    responsive=True
)
```

## Advanced Data Table

For more complex tables with pagination, sorting, and filtering, use `create_data_table()`:

```python
from ui.table_components import create_data_table

# Create the data table with additional features
table = create_data_table(
    data=data,
    columns=columns,
    id="advanced-table",
    page_size=10,
    sortable=True,
    filterable=True,
    export_format=["csv", "excel"],
    mobile_responsive=True
)
```

## Mobile Optimization

All table components are optimized for mobile viewing by default:

1. Tables are wrapped in responsive containers with proper overflow handling
2. Tables on small screens have optimized styles for better readability
3. Column visibility can be adjusted based on screen size
4. Touch targets meet accessibility standards

## Accessibility Features

The standardized table components include several accessibility enhancements:

- Proper ARIA attributes for screen readers
- Sufficient color contrast
- Keyboard navigation support
- Descriptive table captions and headers

## Integration with Grid System

Tables can be easily integrated with the application's grid system:

```python
from ui.grid_utils import create_responsive_column
from ui.table_components import create_basic_table

layout = create_responsive_column(
    content=create_basic_table(data, columns),
    xs=12,
    md=10,
    lg=8,
    className="mx-auto"
)
```

## Best Practices

1. **Use the appropriate table type**:
   - Use `create_basic_table()` for simple, static data displays
   - Use `create_data_table()` for interactive tables with large datasets

2. **Mobile considerations**:
   - Consider hiding less important columns on mobile
   - Use the `responsive` parameter to enable horizontal scrolling

3. **Performance**:
   - For very large datasets, implement pagination
   - Consider lazy loading for better performance

## Migration Guide

When migrating existing table code to the standardized components:

1. Identify the table structure and data source
2. Determine the appropriate table component type
3. Convert the column definitions to the standardized format
4. Replace the existing implementation with the standardized component
5. Test across different screen sizes and with screen readers

## Example: Converting Existing Table

Before:

```python
html.Table(
    [
        html.Thead(
            html.Tr([html.Th("Name"), html.Th("Value")])
        ),
        html.Tbody(
            [html.Tr([html.Td("Item 1"), html.Td("Value 1")]), 
             html.Tr([html.Td("Item 2"), html.Td("Value 2")])]
        )
    ],
    className="table table-striped"
)
```

After:

```python
create_basic_table(
    data=[{"name": "Item 1", "value": "Value 1"}, 
          {"name": "Item 2", "value": "Value 2"}],
    columns=[
        {"id": "name", "name": "Name"},
        {"id": "value", "name": "Value"}
    ],
    striped=True
)
```
