# Responsive Design Guide

## Overview

This guide explains how to implement responsive layouts in the Burndown Chart application using our Bootstrap-based responsive system. The implementation leverages all Bootstrap breakpoints (xs, sm, md, lg, xl, xxl) for creating adaptive interfaces.

## Bootstrap Breakpoint System

Our application uses the standard Bootstrap breakpoint system:

| Breakpoint        | Class infix | Dimensions |
| ----------------- | ----------- | ---------- |
| Extra small       | xs          | <576px     |
| Small             | sm          | ≥576px     |
| Medium            | md          | ≥768px     |
| Large             | lg          | ≥992px     |
| Extra large       | xl          | ≥1200px    |
| Extra extra large | xxl         | ≥1400px    |

## Using Responsive Components

### Responsive Grid System

The `ui.grid_utils` module provides a unified grid system with components for creating responsive layouts:

```python
from ui.grid_utils import (
    create_responsive_column, 
    create_responsive_row,
    create_responsive_grid,
    create_stacked_to_horizontal,
    create_card_grid,
    create_dashboard_layout
)
```

### Creating Responsive Columns

Use the `create_responsive_column` function to create columns with different widths at different breakpoints:

```python
create_responsive_column(
    content,              # The content to put in the column
    xs=12,                # Width on extra small screens (default: full width)
    sm=6,                 # Width on small screens
    md=4,                 # Width on medium screens
    lg=3,                 # Width on large screens
    xl=3,                 # Width on extra large screens
    xxl=2,                # Width on extra extra large screens
    className="",         # Additional CSS classes
    visibility_by_breakpoint={'xs': True, 'md': False}  # Control visibility at different breakpoints
)
```

### Creating Responsive Rows

Use the `create_responsive_row` function to create rows with different properties at different breakpoints:

```python
create_responsive_row(
    children,            # Row content
    row_class_by_breakpoint={'xs': 'flex-column', 'md': 'flex-row'},  # Different classes by breakpoint
    alignment_by_breakpoint={'xs': 'justify-content-center', 'lg': 'justify-content-start'},
    gutters_by_breakpoint={'xs': '1', 'md': '3', 'lg': '5'}  # Different gutter sizes by breakpoint
)
```

### Creating Stacked-to-Horizontal Layouts

Use the `create_stacked_to_horizontal` function to create layouts that stack vertically on small screens and display horizontally on larger screens:

```python
create_stacked_to_horizontal(
    left_content,         # Content for the left column
    right_content,        # Content for the right column
    stack_until="md",     # Stack vertically until this breakpoint
    left_width=6,         # Width of left column when side-by-side
    right_width=6,        # Width of right column when side-by-side
    equal_height=True     # Whether to make columns equal height
)
```

### Creating Card Grids

Use the `create_card_grid` function to create card grids with different numbers of columns at different breakpoints:

```python
create_card_grid(
    cards,                # List of card components
    cols_by_breakpoint={  # Number of columns at each breakpoint
        'xs': 1, 
        'sm': 1, 
        'md': 2, 
        'lg': 3, 
        'xl': 4
    },
    equal_height=True     # Whether to make all cards the same height
)
```

### Creating Dashboard Layouts

Use the `create_dashboard_layout` function to create dashboard layouts with main content and sidebars:

```python
create_dashboard_layout(
    main_content,         # Primary content area
    side_content,         # Side panel content
    secondary_content,    # Optional secondary content (visible at larger breakpoints)
    stack_until="lg",     # Stack layout vertically until this breakpoint
    main_width=8,         # Width of main content when side-by-side
    side_width=4          # Width of side panel when side-by-side
)
```

## Bootstrap Utility Classes

### Responsive Visibility Classes

You can show or hide elements at different breakpoints:

- `d-none`: Hidden at all breakpoints
- `d-{breakpoint}-none`: Hidden from the specified breakpoint up
- `d-{breakpoint}-block`: Visible from the specified breakpoint up

Examples:

- `d-none d-md-block`: Hidden on xs and sm screens, visible from md up
- `d-block d-lg-none`: Visible on xs, sm, and md screens, hidden from lg up

### Responsive Flexbox Utilities

Apply different flex behaviors at different breakpoints:

- `flex-{breakpoint}-row`: Row direction from the breakpoint up
- `flex-{breakpoint}-column`: Column direction from the breakpoint up
- `justify-content-{breakpoint}-{value}`: Different justification at breakpoints

Example:

```html
<div class="d-flex flex-column flex-md-row">
    <!-- Stacks vertically on xs-sm, horizontally from md up -->
</div>
```

### Responsive Spacing

Apply different spacing at different breakpoints:

- `m{side}-{breakpoint}-{size}`: Margin at specific breakpoints
- `p{side}-{breakpoint}-{size}`: Padding at specific breakpoints

Where:

- `{side}` is t (top), b (bottom), s (start), e (end), x (horizontal), y (vertical), or blank (all sides)
- `{breakpoint}` is sm, md, lg, xl, or xxl
- `{size}` is 0-5 or auto

Example:

```html
<div class="mt-3 mt-md-5">
    <!-- Margin top of 1rem (mt-3) on xs-sm, 3rem (mt-5) from md up -->
</div>
```

## Best Practices

1. **Mobile-First Approach**
   - Start by designing for mobile screens and then enhance for larger screens
   - Use the smallest breakpoint (xs) as your base and add responsive adjustments

2. **Use Relative Units**
   - Prefer rem/em over px for better scaling across devices
   - Our spacing system uses rem units for consistent scaling

3. **Test Across Breakpoints**
   - Resize your browser to verify correct behavior across all breakpoints
   - Use browser developer tools to simulate different devices

4. **Avoid Fixed Width Elements**
   - Use percentages or Bootstrap grid columns instead of fixed widths
   - Always set appropriate max-width constraints

5. **Touch Targets**
   - Make interactive elements at least 44x44px on mobile
   - Add sufficient spacing between clickable elements

6. **Content Adjustments**
   - Use `d-none` and `d-{breakpoint}-block` to show/hide different content
   - Consider simplified interfaces for smaller screens

## Implementation Examples

### Complex Dashboard Layout

```python
layout = create_dashboard_layout(
    main_content=html.Div([
        html.H2("Main Dashboard"),
        # Charts, tables, etc.
    ], className="p-3 border rounded"),
    
    side_content=html.Div([
        html.H3("Filters"),
        # Filter controls
    ], className="p-3 border rounded"),
    
    secondary_content=html.Div([
        html.H3("Additional Info"),
        # Extra information that's only needed on large screens
    ], className="p-3 border rounded"),
    
    stack_until="lg",
    secondary_display_breakpoint="xl"
)
```

### Card Grid with Different Column Counts

```python
cards = [create_card(...) for _ in range(8)]  # 8 cards

card_grid = create_card_grid(
    cards=cards,
    cols_by_breakpoint={
        'xs': 1,  # 1 card per row on mobile
        'sm': 2,  # 2 cards per row on small screens
        'md': 2,  # 2 cards per row on medium screens
        'lg': 3,  # 3 cards per row on large screens
        'xl': 4   # 4 cards per row on extra large screens
    }
)
```

## Testing Your Responsive Layout

You can use `create_breakpoint_visibility_examples()` to display test elements showing when different breakpoints are active:

```python
import ui.grid_utils as grid

layout = html.Div([
    html.H2("Breakpoint Test"),
    grid.create_breakpoint_visibility_examples()
])
```

This will display colored bars indicating which breakpoints are currently active, helping you verify your responsive design.
