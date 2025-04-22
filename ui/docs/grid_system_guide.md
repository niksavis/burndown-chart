# Grid System Guide

## Overview

This guide explains the new unified grid system in the Burndown Chart application. The new system combines functionality from both `grid_templates.py` and `responsive_grid.py` into a single cohesive API in `grid_utils.py`.

## Why We Unified the Grid System

Previously, our application had two separate modules for creating grid layouts:

1. `grid_templates.py` - Focused on simpler Bootstrap layouts with mainly xs/md breakpoints, and integrated with the vertical rhythm system.
2. `responsive_grid.py` - Provided advanced responsive behaviors across all breakpoints with conditional visibility and reordering capabilities.

This dual approach led to inconsistencies and duplication. The new unified system:

- Provides a single source of truth for grid layouts
- Organizes functions into logical layers based on complexity
- Maintains backward compatibility with existing code patterns
- Better integrates with our vertical rhythm system

## Grid API Structure

The new grid system is organized into logical layers:

### Low-Level Functions (Core Building Blocks)

These provide maximum flexibility for custom layouts:

```python
create_responsive_row(
    children, 
    className="",
    style=None, 
    row_class_by_breakpoint=None,
    alignment_by_breakpoint=None, 
    gutters_by_breakpoint=None
)

create_responsive_column(
    content,
    xs=12, sm=None, md=None, lg=None, xl=None, xxl=None,
    className="", 
    style=None,
    order_by_breakpoint=None,
    visibility_by_breakpoint=None,
    padding_by_breakpoint=None
)

apply_grid_rhythm(component, rhythm_type="section", extra_classes=None)
```

### Mid-Level Functions (Common Grid Patterns)

These provide standard column layouts with sensible defaults:

```python
create_multi_column_layout(
    columns_content, 
    column_widths=None, 
    breakpoint="md", 
    spacing="standard", 
    className=""
)

create_two_column_layout(
    left_content, 
    right_content, 
    left_width=6, 
    right_width=6, 
    breakpoint="md", 
    className=""
)

create_three_column_layout(
    left, middle, right, 
    left_width=4, middle_width=4, right_width=4, 
    breakpoint="md", 
    className=""
)

create_stacked_to_horizontal(
    left_content, 
    right_content,
    stack_until="md", 
    left_width=6, 
    right_width=6, 
    equal_height=True,
    className=""
)
```

### High-Level Pattern Functions (Specific Layout Patterns)

These implement complex, reusable layout patterns:

```python
create_content_sidebar_layout(
    content,
    sidebar,
    sidebar_position="right",
    sidebar_width=4,
    content_width=8,
    stack_until="md",
    spacing="standard"
)

create_dashboard_layout(
    main_content,
    side_content,
    secondary_content=None,
    stack_until="lg",
    main_width=8,
    side_width=4,
    secondary_display_breakpoint="xl"
)
```

### Specialized Grid Functions (By Purpose)

These handle specific use cases like card grids and form layouts:

```python
create_card_grid(
    cards, 
    cols_by_breakpoint={"xs": 1, "md": 2, "lg": 3}, 
    equal_height=True
)

create_form_row(form_groups, columns=None)

create_responsive_table_wrapper(
    table_component, 
    max_height=None, 
    className=""
)

create_form_section(title, components, help_text=None)

create_breakpoint_visibility_examples()

create_mobile_container(content, expanded_height="auto", className="")
```

## Migration Guide

### Step 1: Update Imports

Replace imports from the old modules with imports from the new unified module:

```python
# Old imports
from ui.grid_templates import create_two_column_layout
from ui.responsive_grid import create_responsive_dashboard_layout

# New imports
from ui.grid_utils import create_two_column_layout, create_dashboard_layout
```

### Step 2: Update Function Names

Some functions have been renamed for clarity and consistency:

| Old Function                         | New Function              |
| ------------------------------------ | ------------------------- |
| `create_responsive_dashboard_layout` | `create_dashboard_layout` |
| `create_responsive_card_deck`        | `create_card_grid`        |

### Step 3: Update Parameter Names

Some parameters have been renamed or reorganized:

- Breakpoint parameters are now consistent (e.g., `stack_until` instead of varying names)
- Use `breakpoint` to specify when layouts change from stacked to side-by-side

### Step 4: Use the Test Suite

Run the test script (`ui/test_grid.py`) to see examples of the new grid system in action:

```
python ui/test_grid.py
```

This will launch a Dash application showing examples of all the grid layouts.

## Best Practices

1. **Choose the Right Abstraction Level**
   - Use higher-level functions for standard patterns
   - Use lower-level functions for custom layouts

2. **Mobile-First Approach**
   - All grid components default to full width on xs (mobile)
   - Specify larger breakpoints for side-by-side layouts

3. **Vertical Rhythm Integration**
   - Grid components automatically apply proper spacing
   - Use `apply_grid_rhythm()` for custom components

4. **Equal Height Columns**
   - Use `equal_height=True` (default) to maintain equal height columns
   - Set to `False` when you need columns to size to their content

5. **Breakpoint Consistency**
   - Use the standard Bootstrap breakpoints: xs, sm, md, lg, xl, xxl
   - Default stacking breakpoint is "md" (768px) for most layouts

## Examples

### Simple Two-Column Layout

```python
create_two_column_layout(
    left_content=html.Div("Sidebar content"),
    right_content=html.Div("Main content"),
    left_width=4,
    right_width=8
)
```

### Card Grid with Responsive Columns

```python
create_card_grid(
    cards=[card1, card2, card3, card4],
    cols_by_breakpoint={
        "xs": 1,  # 1 card per row on mobile
        "sm": 2,  # 2 cards per row on tablets
        "lg": 4   # 4 cards per row on desktop
    }
)
```

### Dashboard Layout with Conditional Content

```python
create_dashboard_layout(
    main_content=html.Div("Main dashboard charts"),
    side_content=html.Div("Filters and controls"),
    secondary_content=html.Div("Additional information"),
    stack_until="lg",
    secondary_display_breakpoint="xl"  # Only show on very large screens
)
```

### Advanced Custom Layout

```python
create_responsive_row(
    [
        create_responsive_column(
            html.Div("First on mobile, last on desktop"),
            xs=12, md=4,
            order_by_breakpoint={"xs": "1", "md": "3"}
        ),
        create_responsive_column(
            html.Div("Second on mobile and desktop"),
            xs=12, md=4,
            order_by_breakpoint={"xs": "2", "md": "2"}
        ),
        create_responsive_column(
            html.Div("Third on mobile, first on desktop"),
            xs=12, md=4,
            order_by_breakpoint={"xs": "3", "md": "1"},
            visibility_by_breakpoint={"xs": True, "sm": False, "lg": True}
        ),
    ]
)
```

## Testing Responsive Layouts

Use the `create_breakpoint_visibility_examples()` function to visualize which breakpoints are active as you resize your browser:

```python
import ui.grid_utils as grid

layout = html.Div([
    html.H2("Breakpoint Test"),
    grid.create_breakpoint_visibility_examples()
])
```

This tool is invaluable for debugging responsive behaviors.