# Mobile-First Implementation Guide

## Overview

This guide establishes standards for implementing a consistent mobile-first approach across all components in the Burndown Chart application.

## Core Principles

1. **Design for Mobile First**
   - Start with the mobile design and progressively enhance for larger screens
   - Default all components to full width (col-12) on mobile
   - Use min-width media queries to apply styles for larger screens

2. **Touch Target Requirements**
   - All interactive elements must be at least 44×44px on mobile
   - Maintain adequate spacing (min 8px) between touch targets
   - Use padding rather than height/width for touch targets when possible

3. **Text Handling**
   - Use the standard truncation pattern for long text on mobile
   - Implement "read more" patterns for essential but lengthy content
   - Use appropriate text sizing (min 16px for body text)

4. **Visibility & Breakpoint Consistency**
   - Follow Bootstrap breakpoint system: xs (<576px), sm, md, lg, xl, xxl
   - Use standard visibility classes: d-none, d-{breakpoint}-block, etc.
   - Default stacking breakpoint should be "md" (768px) unless specified

## Implementation Guidelines

### Components

All components should follow this structure:

```python
def create_component(content, mobile_optimized=True):
    # Mobile-first base styling
    base_style = {
        "width": "100%",
        "fontSize": "16px",
    }
    
    # Apply mobile optimizations
    if mobile_optimized:
        # Add touch target sizing, etc.
        base_style.update({
            "minHeight": "44px",
        })
    
    # Wrap in responsive container if needed
    return html.Div(content, style=base_style)
```

### Touch Targets

For buttons and interactive elements:

```python
# Correct
button = dbc.Button(
    "Action",
    className="d-flex align-items-center justify-content-center",
    style={"minHeight": "44px", "minWidth": "44px"}
)

# For icon buttons
icon_button = dbc.Button(
    html.I(className="fas fa-edit"),
    className="d-flex align-items-center justify-content-center", 
    style={"height": "44px", "width": "44px"}
)
```

### Text Truncation

Standard pattern for text truncation:

```python
truncated_text = html.Div(
    "This is a very long text that needs to be truncated on mobile screens",
    className="mobile-truncate",
    title="This is a very long text that needs to be truncated on mobile screens"
)
```

### CSS Classes

Use these standard utility classes:

```css
.mobile-truncate {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
}

.mobile-touch-target {
    min-height: 44px;
    min-width: 44px;
}

.mobile-stack {
    display: flex;
    flex-direction: column;
}

@media (min-width: 768px) {
    .mobile-stack {
        flex-direction: row;
    }
}
```

## Testing Checklist

- [ ] Verify all interactive elements are at least 44×44px on mobile
- [ ] Check text truncation displays correctly on small screens
- [ ] Test component stacking/layout at all breakpoints
- [ ] Ensure appropriate content is shown/hidden at different breakpoints
- [ ] Confirm touch targets have sufficient spacing
