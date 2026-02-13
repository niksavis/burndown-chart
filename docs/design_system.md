# Design System Documentation

**Purpose**: Comprehensive design system documentation for the Burndown Chart application. This system provides:
- **Consistency**: Unified visual language across all UI components
- **Maintainability**: Single source of truth for design decisions via CSS variables
- **Scalability**: Reusable tokens and patterns that grow with the application
- **Accessibility**: WCAG-compliant colors, contrast ratios, and interaction patterns
- **Developer Experience**: Clear guidelines for both human and AI developers

**Version**: 1.0.0  
**Last Updated**: 2026-02-13

---

## Quick Reference

| Category       | Location                    | Key Variable Prefix    | Usage                    |
| -------------- | --------------------------- | ---------------------- | ------------------------ |
| **Colors**     | `assets/core/variables.css` | `--color-*`            | Brand, semantic, neutral |
| **Typography** | `assets/core/variables.css` | `--text-*`, `--font-*` | Sizes, weights, families |
| **Spacing**    | `assets/core/variables.css` | `--space-*`            | 8px grid system          |
| **Shadows**    | `assets/core/variables.css` | `--shadow-*`           | Elevation levels         |
| **Radius**     | `assets/core/variables.css` | `--radius-*`           | Corner rounding          |
| **Icons**      | `ui/tooltip_utils.py`       | `create_help_icon()`   | Standardized help icons  |

---

## Table of Contents

1. [Design Tokens](#design-tokens)
2. [Color System](#color-system)
3. [Typography](#typography)
4. [Spacing](#spacing)
5. [Shadows and Elevation](#shadows-and-elevation)
6. [Border Radius](#border-radius)
7. [Component Patterns](#component-patterns)
8. [Icon System](#icon-system)
9. [Form Controls](#form-controls)
10. [Usage Guidelines](#usage-guidelines)
11. [Maintenance](#maintenance)

---

## Design Tokens

### What are Design Tokens?

Design tokens are CSS custom properties that store design decisions (colors, spacing, typography) in a centralized location. This provides:
- **Single source of truth**: Change once, update everywhere
- **Consistency**: Impossible to use arbitrary values
- **Maintainability**: Easy global theme changes
- **DRY principle**: No duplicated color/spacing values

### Location

**Primary file**: `assets/core/variables.css` (214 lines)

All design tokens are defined in the `:root` pseudo-class, making them globally accessible.

```css
:root {
  --color-brand-500: #3b82f6; /* Main brand color */
  --space-2: 1rem;             /* 16px spacing */
  --text-base: 1rem;           /* 16px body text */
}
```

---

## Color System

### Color Palette Overview

The application uses a three-tier color system:

1. **Brand Colors** - Primary interactive elements (buttons, links, icons)
2. **Accent Colors** - Success states, positive indicators
3. **Neutral Colors** - Text, backgrounds, borders
4. **Semantic Colors** - Success, warning, danger, info states

### Brand Colors (Primary)

**Usage**: Interactive elements, primary actions, info icons, checked states

| Variable            | Value     | Usage                          |
| ------------------- | --------- | ------------------------------ |
| `--color-brand-50`  | `#eff6ff` | Lightest tint (backgrounds)    |
| `--color-brand-100` | `#dbeafe` | Light backgrounds              |
| `--color-brand-200` | `#bfdbfe` | Subtle accents                 |
| `--color-brand-300` | `#93c5fd` | Disabled states                |
| `--color-brand-400` | `#60a5fa` | Hover preparation              |
| `--color-brand-500` | `#3b82f6` | **Main brand color** (default) |
| `--color-brand-600` | `#2563eb` | **Hover state** (interactive)  |
| `--color-brand-700` | `#1d4ed8` | **Active state** (pressed)     |
| `--color-brand-800` | `#1e40af` | Dark emphasis                  |
| `--color-brand-900` | `#1e3a8a` | Darkest shade                  |

**Examples**:

```css
/* Button hover state */
.btn-primary:hover {
  background-color: var(--color-brand-600);
}

/* Info icon */
.text-info {
  color: var(--color-brand-500) !important;
}

/* Checkbox checked state */
.form-check-input:checked {
  background-color: var(--color-brand-600) !important;
  border-color: var(--color-brand-600) !important;
}
```

### Accent Colors (Teal/Success)

**Usage**: Success indicators, positive trends, chart accents

| Variable             | Value     | Usage                |
| -------------------- | --------- | -------------------- |
| `--color-accent-50`  | `#f0fdfa` | Success backgrounds  |
| `--color-accent-100` | `#ccfbf1` | Light success tints  |
| `--color-accent-500` | `#14b8a6` | **Success/positive** |
| `--color-accent-600` | `#0d9488` | **Success hover**    |
| `--color-accent-900` | `#134e4a` | Dark success text    |

### Neutral Colors (Warm Gray)

**Usage**: Text, backgrounds, borders, surfaces

| Variable              | Value     | Usage                        |
| --------------------- | --------- | ---------------------------- |
| `--color-neutral-50`  | `#fafaf9` | **Page background**          |
| `--color-neutral-100` | `#f5f5f4` | **Card header backgrounds**  |
| `--color-neutral-200` | `#e7e5e4` | **Borders** (standard)       |
| `--color-neutral-300` | `#d6d3d1` | Subtle borders               |
| `--color-neutral-400` | `#a8a29e` | Disabled text                |
| `--color-neutral-500` | `#78716c` | **Secondary text** (labels)  |
| `--color-neutral-600` | `#57534e` | **Labels and captions**      |
| `--color-neutral-700` | `#44403c` | **Body text** (main content) |
| `--color-neutral-800` | `#292524` | Strong emphasis              |
| `--color-neutral-900` | `#1c1917` | **Headings** (darkest text)  |

### Semantic Colors

**Usage**: Status indicators, alerts, notifications

| Variable                | Value     | Usage                         |
| ----------------------- | --------- | ----------------------------- |
| `--color-success`       | `#10b981` | Success messages, positive    |
| `--color-success-light` | `#d1fae5` | Success backgrounds           |
| `--color-success-dark`  | `#065f46` | Dark success text             |
| `--color-warning`       | `#f59e0b` | Warning messages, caution     |
| `--color-warning-light` | `#fef3c7` | Warning backgrounds           |
| `--color-warning-dark`  | `#92400e` | Dark warning text             |
| `--color-danger`        | `#ef4444` | Error messages, destructive   |
| `--color-danger-light`  | `#fee2e2` | Error backgrounds             |
| `--color-danger-dark`   | `#991b1b` | Dark error text               |
| `--color-info`          | `#3b82f6` | Informational (matches brand) |
| `--color-info-light`    | `#dbeafe` | Info backgrounds              |
| `--color-info-dark`     | `#1e40af` | Dark info text                |

### Flow Metrics Colors

**Usage**: Work item type visualization (DORA/Flow metrics)

| Variable                 | Value                  | Usage              |
| ------------------------ | ---------------------- | ------------------ |
| `--flow-feature-color`   | `var(--color-success)` | Features (green)   |
| `--flow-defect-color`    | `var(--color-danger)`  | Bugs (red)         |
| `--flow-risk-color`      | `var(--color-warning)` | Risks (amber)      |
| `--flow-tech-debt-color` | `#fd7e14`              | Tech debt (orange) |

### Performance Tier Colors

**Usage**: Performance level indicators (DORA metrics)

| Variable            | Value                  | Tier           |
| ------------------- | ---------------------- | -------------- |
| `--tier-elite`      | `var(--color-success)` | Elite (green)  |
| `--tier-high`       | `var(--color-info)`    | High (blue)    |
| `--tier-medium`     | `var(--color-warning)` | Medium (amber) |
| `--tier-low-orange` | `#fd7e14`              | Low (orange)   |
| `--tier-critical`   | `var(--color-danger)`  | Critical (red) |

### Color Usage Guidelines

**DO**:
- ✓ Use `var(--color-brand-500)` for all info icons
- ✓ Use `var(--color-brand-600)` for checked/hover states
- ✓ Use neutral colors for text hierarchy (900 → 700 → 500)
- ✓ Use semantic colors for status indicators

**DON'T**:
- ✗ Never use hard-coded hex values (e.g., `#3b82f6`)
- ✗ Never mix `text-info` and `text-muted` for the same icon type
- ✗ Never use brand colors for body text (use neutrals)
- ✗ Never create new color variables without documentation

---

## Typography

### Font Families

```css
--font-sans: "Manrope", "Segoe UI Variable Text", "Segoe UI", 
             "Helvetica Neue", Arial, sans-serif;

--font-mono: ui-monospace, "SF Mono", "Cascadia Code", "Consolas", 
             "Courier New", monospace;
```

**Usage**:
- `--font-sans`: All UI text (default)
- `--font-mono`: Code snippets, JQL queries, logs

### Type Scale (8-Point Baseline)

| Variable      | Size       | Pixels | Usage                   |
| ------------- | ---------- | ------ | ----------------------- |
| `--text-xs`   | `0.75rem`  | 12px   | Fine print, captions    |
| `--text-sm`   | `0.875rem` | 14px   | Secondary text, labels  |
| `--text-base` | `1rem`     | 16px   | **Body text** (default) |
| `--text-lg`   | `1.125rem` | 18px   | Emphasized text         |
| `--text-xl`   | `1.25rem`  | 20px   | Small headings          |
| `--text-2xl`  | `1.5rem`   | 24px   | **Card titles**         |
| `--text-3xl`  | `1.875rem` | 30px   | **Section headings**    |
| `--text-4xl`  | `2.25rem`  | 36px   | **Page titles**         |

### Font Weights

| Variable          | Weight | Usage                 |
| ----------------- | ------ | --------------------- |
| `--font-normal`   | 400    | Body text             |
| `--font-medium`   | 500    | Emphasized text       |
| `--font-semibold` | 600    | Subheadings, labels   |
| `--font-bold`     | 700    | Headings, strong text |

### Line Heights

| Variable            | Value | Usage                        |
| ------------------- | ----- | ---------------------------- |
| `--leading-tight`   | 1.2   | **Headings** (compact)       |
| `--leading-normal`  | 1.5   | **Body text** (readable)     |
| `--leading-relaxed` | 1.75  | Long-form content (spacious) |

### Typography Examples

```css
/* Page title */
h1 {
  font-size: var(--text-4xl);
  font-weight: var(--font-bold);
  line-height: var(--leading-tight);
  color: var(--color-neutral-900);
}

/* Card title */
.card-title {
  font-size: var(--text-2xl);
  font-weight: var(--font-semibold);
  line-height: var(--leading-tight);
}

/* Body text */
body {
  font-family: var(--font-sans);
  font-size: var(--text-base);
  line-height: var(--leading-normal);
  color: var(--color-neutral-700);
}

/* Small caption */
.caption {
  font-size: var(--text-xs);
  color: var(--color-neutral-500);
}
```

### Python Typography Usage

```python
from ui.style_constants import TYPOGRAPHY

# Page heading
html.H1(
    "Dashboard",
    style={
        "fontSize": TYPOGRAPHY["scale"]["h1"],
        "fontWeight": TYPOGRAPHY["weights"]["bold"],
    }
)

# Card title
html.H3(
    "Burndown Chart",
    className="card-title",
    style={"fontSize": TYPOGRAPHY["scale"]["h3"]}
)
```

---

## Spacing

### 8px Grid System

All spacing follows an 8px baseline grid for visual rhythm and consistency.

| Variable     | Size     | Pixels | Usage                         |
| ------------ | -------- | ------ | ----------------------------- |
| `--space-0`  | `0`      | 0px    | No spacing                    |
| `--space-1`  | `0.5rem` | 8px    | Tight spacing (icon margins)  |
| `--space-2`  | `1rem`   | 16px   | **Default spacing** (padding) |
| `--space-3`  | `1.5rem` | 24px   | Medium spacing (sections)     |
| `--space-4`  | `2rem`   | 32px   | Large spacing (cards)         |
| `--space-5`  | `2.5rem` | 40px   | Extra large spacing           |
| `--space-6`  | `3rem`   | 48px   | Section breaks                |
| `--space-8`  | `4rem`   | 64px   | Major section dividers        |
| `--space-10` | `5rem`   | 80px   | Page-level spacing            |
| `--space-12` | `6rem`   | 96px   | Maximum spacing               |

### Legacy Mapping

For Bootstrap compatibility:

```css
--spacing-xs: var(--space-1);   /* 8px */
--spacing-sm: var(--space-1);   /* 8px */
--spacing-md: var(--space-2);   /* 16px */
--spacing-lg: var(--space-3);   /* 24px */
--spacing-xl: var(--space-4);   /* 32px */
--spacing-xxl: var(--space-6);  /* 48px */
```

### Spacing Examples

```css
/* Card padding */
.card-body {
  padding: var(--space-3); /* 24px */
}

/* Button padding */
.btn {
  padding: var(--space-1) var(--space-2); /* 8px 16px */
}

/* Section margin */
.section {
  margin-bottom: var(--space-6); /* 48px */
}

/* Icon margin */
.icon {
  margin-left: var(--space-1); /* 8px */
}
```

### Python Spacing Usage

```python
# Card with consistent padding
dbc.Card([
    dbc.CardBody([
        # Content
    ], style={"padding": "var(--space-3)"})
])

# Icon with standard margin
html.I(
    className="fas fa-info-circle",
    style={"marginLeft": "var(--space-1)"}
)
```

---

## Shadows and Elevation

### Shadow Scale

Shadows create visual hierarchy and depth. Higher elevations = stronger shadows.

| Variable        | Shadow Definition                                                | Usage               |
| --------------- | ---------------------------------------------------------------- | ------------------- |
| `--shadow-xs`   | `0 1px 2px rgba(0,0,0,0.05)`                                     | Subtle borders      |
| `--shadow-sm`   | `0 1px 3px rgba(0,0,0,0.1), 0 1px 2px rgba(0,0,0,0.06)`          | Buttons, inputs     |
| `--shadow-md`   | `0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)`         | **Cards** (default) |
| `--shadow-lg`   | `0 10px 15px rgba(0,0,0,0.1), 0 4px 6px rgba(0,0,0,0.05)`        | Dropdowns, popovers |
| `--shadow-xl`   | `0 20px 25px rgba(0,0,0,0.15), 0 10px 10px rgba(0,0,0,0.04)`     | Modals              |
| `--shadow-card` | `0 12px 30px rgba(15,23,42,0.08), 0 2px 8px rgba(15,23,42,0.05)` | **Metric cards**    |

### Shadow Examples

```css
/* Standard card */
.card {
  box-shadow: var(--shadow-md);
}

/* Elevated dropdown */
.dropdown-menu {
  box-shadow: var(--shadow-lg);
}

/* Modal */
.modal-dialog {
  box-shadow: var(--shadow-xl);
}

/* Hover effect */
.card:hover {
  box-shadow: var(--shadow-lg);
  transition: box-shadow var(--transition-base);
}
```

---

## Border Radius

### Radius Scale

| Variable        | Size       | Pixels | Usage                   |
| --------------- | ---------- | ------ | ----------------------- |
| `--radius-sm`   | `0.25rem`  | 4px    | Small elements, tags    |
| `--radius-md`   | `0.375rem` | 6px    | **Buttons, inputs**     |
| `--radius-lg`   | `0.5rem`   | 8px    | **Cards** (default)     |
| `--radius-xl`   | `0.75rem`  | 12px   | Large cards, modals     |
| `--radius-2xl`  | `1rem`     | 16px   | Hero sections           |
| `--radius-full` | `9999px`   | ∞      | Pills, circular buttons |

### Radius Examples

```css
/* Button */
.btn {
  border-radius: var(--radius-md); /* 6px */
}

/* Card */
.card {
  border-radius: var(--radius-lg); /* 8px */
}

/* Badge/tag */
.badge {
  border-radius: var(--radius-sm); /* 4px */
}

/* Pill button */
.btn-pill {
  border-radius: var(--radius-full); /* Fully rounded */
}
```

---

## Component Patterns

### Standard Card

```python
dbc.Card([
    dbc.CardHeader(
        html.H4("Card Title", className="mb-0"),
        style={
            "backgroundColor": "var(--color-neutral-100)",
            "borderBottom": "1px solid var(--color-neutral-200)"
        }
    ),
    dbc.CardBody([
        html.P("Card content goes here."),
    ], style={
        "padding": "var(--space-3)"
    })
], style={
    "borderRadius": "var(--radius-lg)",
    "boxShadow": "var(--shadow-md)",
    "marginBottom": "var(--space-4)"
})
```

### Button Variants

```python
# Primary button
dbc.Button(
    "Primary Action",
    color="primary",  # Uses --color-brand-500
    className="me-2"
)

# Secondary button
dbc.Button(
    "Secondary Action",
    color="secondary",  # Uses --color-neutral-600
    outline=True
)
```

### Form Group

```python
dbc.FormGroup([
    dbc.Label(
        [
            "Label Text",
            create_help_icon("help-id", position="inline")
        ],
        html_for="input-id",
        style={
            "fontSize": "var(--text-sm)",
            "color": "var(--color-neutral-600)",
            "fontWeight": "var(--font-medium)"
        }
    ),
    dbc.Input(
        id="input-id",
        type="text",
        placeholder="Enter value..."
    )
], style={"marginBottom": "var(--space-3)"})
```

---

## Icon System

### Help Icon Standardization

**Primary Function**: `create_help_icon()` from `ui/tooltip_utils.py`

This function ensures all help icons use consistent styling, positioning, and color.

#### Function Signature

```python
def create_help_icon(
    tooltip_id: str,
    position: str = "inline",
    icon_class: str = "fas fa-info-circle",
    color: str = "#3b82f6",  # Brand blue
) -> html.I:
```

#### Parameters

| Parameter    | Type  | Default                | Description                                   |
| ------------ | ----- | ---------------------- | --------------------------------------------- |
| `tooltip_id` | `str` | *Required*             | Unique ID for the tooltip target              |
| `position`   | `str` | `"inline"`             | Icon position: `inline`, `header`, `trailing` |
| `icon_class` | `str` | `"fas fa-info-circle"` | FontAwesome icon class                        |
| `color`      | `str` | `"#3b82f6"`            | Icon color (brand blue)                       |

#### Position Types

| Position   | Class     | Use Case                          |
| ---------- | --------- | --------------------------------- |
| `inline`   | `ms-1`    | **Default** - Next to text/labels |
| `header`   | `ms-2`    | Card/section headers              |
| `trailing` | `ms-auto` | End of container (right-aligned)  |

#### Usage Examples

```python
from ui.tooltip_utils import create_help_icon

# Inline help icon (most common)
dbc.Label([
    "Items in Sprint Scope",
    create_help_icon("items-scope-help", position="inline")
])

# Header help icon
html.H4([
    "Forecast Analysis",
    create_help_icon("forecast-help", position="header")
])

# Trailing help icon
html.Div([
    html.Span("Configuration"),
    create_help_icon("config-help", position="trailing")
], style={"display": "flex", "alignItems": "center"})
```

### Icon Color Constants

**File**: `ui/style_constants.py`

```python
HELP_ICON = {
    "class": "fas fa-info-circle",
    "color": "#3b82f6",          # Brand blue (matches --color-brand-500)
    "size": "0.875rem",          # 14px
    "margin_left": "0.5rem",     # 8px
    "cursor": "pointer",
    "position": "inline",
}
```

### Bootstrap Icon Classes

Use Bootstrap utility classes for consistent icon sizing:

```html
<!-- Small icon -->
<i class="fas fa-check text-success" style="fontSize: var(--text-sm);"></i>

<!-- Medium icon (default) -->
<i class="fas fa-info-circle text-info"></i>

<!-- Large icon -->
<i class="fas fa-chart-line" style="fontSize: var(--text-2xl);"></i>
```

### Icon Color Guidelines

**DO**:
- ✓ Use `create_help_icon()` for all info/help icons
- ✓ Use `text-info` class for brand blue icons
- ✓ Use semantic classes: `text-success`, `text-warning`, `text-danger`
- ✓ Use `var(--color-brand-500)` in inline styles

**DON'T**:
- ✗ Never use `text-muted` for info icons (gray is hard to see)
- ✗ Never hard-code icon colors like `#17a2b8` (use variables)
- ✗ Never mix icon color classes on the same icon type

---

## Form Controls

### Unified Form Control Styling

**File**: `assets/core/color-consistency.css`

All form controls (checkboxes, radio buttons, switches, range sliders) use unified brand blue colors.

### Checkboxes

```python
dbc.Checkbox(
    id="checkbox-id",
    label="Enable feature",
    value=False
)
```

**CSS (automatic)**:

```css
.form-check-input:checked {
  background-color: var(--color-brand-600) !important;  /* #2563eb */
  border-color: var(--color-brand-600) !important;
}
```

### Radio Buttons

```python
dbc.RadioItems(
    id="radio-id",
    options=[
        {"label": "Option 1", "value": 1},
        {"label": "Option 2", "value": 2},
    ],
    value=1
)
```

### Switches

```python
dbc.Switch(
    id="switch-id",
    label="Enable notifications",
    value=True
)
```

### Range Sliders

```python
dbc.Input(
    id="slider-id",
    type="range",
    min=0,
    max=100,
    step=1,
    value=50,
    className="form-range"
)
```

**CSS (automatic)**:

```css
.form-range::-webkit-slider-thumb {
  background-color: var(--color-brand-600) !important;
}

.form-range::-moz-range-thumb {
  background-color: var(--color-brand-600) !important;
}
```

### Form Control Color Consistency

**History**: Previously, form controls had inconsistent colors due to multiple Bootstrap CSS sources:
- Standard Bootstrap: `#0d6efd` (bright blue)
- Flatly theme: `#2c3e50` (navy blue)
- Custom CSS: `#2563eb` (brand blue)

**Solution**: `color-consistency.css` overrides all sources with `!important` to enforce brand blue.

**Result**: All checkboxes, radios, switches, and sliders now use `var(--color-brand-600)` (#2563eb).

---

## Z-Index Scale

Manages stacking order for overlays, modals, and tooltips.

| Variable             | Value | Usage                 |
| -------------------- | ----- | --------------------- |
| `--z-base`           | 0     | Default (no stacking) |
| `--z-dropdown`       | 1000  | Dropdown menus        |
| `--z-sticky`         | 1020  | Sticky headers        |
| `--z-fixed`          | 1030  | Fixed positioning     |
| `--z-modal-backdrop` | 1040  | Modal backdrop        |
| `--z-modal`          | 1050  | **Modal dialogs**     |
| `--z-popover`        | 1060  | Popovers              |
| `--z-tooltip`        | 1070  | **Tooltips** (top)    |

```css
/* Modal */
.modal {
  z-index: var(--z-modal); /* 1050 */
}

/* Tooltip */
.tooltip {
  z-index: var(--z-tooltip); /* 1070 */
}
```

---

## Transitions and Animations

### Transition Timing

| Variable            | Duration | Easing                      | Usage                   |
| ------------------- | -------- | --------------------------- | ----------------------- |
| `--transition-fast` | `150ms`  | `cubic-bezier(0.4,0,0.2,1)` | Hover, active states    |
| `--transition-base` | `200ms`  | `cubic-bezier(0.4,0,0.2,1)` | **Default** transitions |
| `--transition-slow` | `300ms`  | `cubic-bezier(0.4,0,0.2,1)` | Page transitions        |

### Focus Ring

```css
--focus-ring: 0 0 0 3px rgba(59, 130, 246, 0.2);
```

**Usage**:

```css
.btn:focus,
input:focus {
  outline: none;
  box-shadow: var(--focus-ring);
}
```

### Transition Examples

```css
/* Button hover */
.btn {
  background-color: var(--color-brand-500);
  transition: background-color var(--transition-fast);
}

.btn:hover {
  background-color: var(--color-brand-600);
}

/* Card elevation on hover */
.card {
  box-shadow: var(--shadow-md);
  transition: box-shadow var(--transition-base);
}

.card:hover {
  box-shadow: var(--shadow-lg);
}
```

---

## Usage Guidelines

### Using Design Tokens in CSS

**DO**:

```css
/* Good: Use CSS variables */
.button {
  padding: var(--space-2) var(--space-4);
  background-color: var(--color-brand-500);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-sm);
  font-size: var(--text-base);
}
```

**DON'T**:

```css
/* Bad: Hard-coded values */
.button {
  padding: 16px 32px;
  background-color: #3b82f6;
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.1);
  font-size: 16px;
}
```

### Using Design Tokens in Python

```python
# Good: Use CSS variables in inline styles
html.Div(
    "Content",
    style={
        "padding": "var(--space-3)",
        "color": "var(--color-neutral-700)",
        "fontSize": "var(--text-base)"
    }
)

# Good: Import constants for complex styling
from ui.style_constants import HELP_ICON, TYPOGRAPHY

html.I(
    className=HELP_ICON["class"],
    style={
        "color": HELP_ICON["color"],
        "fontSize": HELP_ICON["size"]
    }
)
```

### Color Contrast Requirements

For WCAG AA compliance:

- **Normal text** (< 18px): Minimum contrast ratio 4.5:1
- **Large text** (≥ 18px): Minimum contrast ratio 3:1
- **Interactive elements**: Minimum contrast ratio 3:1

**Tested Combinations**:

| Foreground            | Background           | Ratio | Pass |
| --------------------- | -------------------- | ----- | ---- |
| `--color-neutral-700` | `--color-neutral-50` | 8.3:1 | ✓✓   |
| `--color-brand-500`   | `--color-white`      | 4.1:1 | ✓    |
| `--color-neutral-500` | `--color-neutral-50` | 4.8:1 | ✓    |

---

## Maintenance

### Adding New Design Tokens

**Process**:

1. **Define in variables.css**:

```css
:root {
  /* New token */
  --color-tertiary-500: #8b5cf6; /* Purple */
}
```

2. **Document in this file**: Add to the relevant section (Colors, Typography, etc.)

3. **Add to style_constants.py** (if needed for Python):

```python
TERTIARY_COLOR = {
    "default": "#8b5cf6",
    "hover": "#7c3aed",
}
```

4. **Update color-consistency.css** (if affects form controls/icons)

5. **Test across all tabs**: Ensure consistent application

### Updating Existing Colors

**Example: Changing brand color**

1. Update in `variables.css`:

```css
--color-brand-500: #2563eb; /* Changed from #3b82f6 */
```

2. **No other changes needed** - All components automatically update via CSS variables

3. Update documentation hex values in this file

### Decision Log Template

When making design system changes:

```markdown
**Date**: 2026-02-13
**Change**: Unified form control colors to brand blue
**Rationale**: 
- Resolved inconsistent colors across checkboxes, radios, sliders
- Enforces DRY principle (single source of truth)
- Improved visual consistency across application
**Files Modified**:
- assets/core/color-consistency.css (created)
- ui/budget_settings_card.py (4 icon classes)
- ui/tooltip_utils.py (default color parameter)
- ui/style_constants.py (HELP_ICON constant)
**Breaking Changes**: None (visual only)
```

### Testing Checklist

When modifying design tokens:

- [ ] Visual regression test on all major tabs
- [ ] Check form controls (checkboxes, radios, switches, sliders)
- [ ] Check info icons across all tabs
- [ ] Verify color contrast ratios (use browser DevTools)
- [ ] Test in light/dark mode (if applicable)
- [ ] Validate with screen reader (if accessibility-related)
- [ ] Check mobile responsive breakpoints

---

## Best Practices

### Consistency Rules

1. **Always use CSS variables** - Never hard-code colors, spacing, or typography
2. **Use helper functions** - `create_help_icon()` for info icons, not manual HTML
3. **Follow the 8px grid** - All spacing should be multiples of 8px
4. **Use semantic colors** - `success`, `warning`, `danger`, `info` for status
5. **Maintain the scale** - Don't create arbitrary in-between values

### KISS and DRY Principles

**KISS (Keep It Simple, Stupid)**:
- Use existing design tokens instead of creating new ones
- Follow established patterns (e.g., `create_help_icon()`)
- Don't over-engineer simple components

**DRY (Don't Repeat Yourself)**:
- Never duplicate color values - use CSS variables
- Reuse helper functions across modules
- Centralize constants in `style_constants.py`

### Common Mistakes

❌ **Mistake**: Using `text-muted` for info icons

```python
# Bad
html.I(className="fas fa-info-circle text-muted")
```

✓ **Solution**: Use `text-info` or `create_help_icon()`

```python
# Good
create_help_icon("tooltip-id")
```

---

❌ **Mistake**: Hard-coding colors

```css
/* Bad */
.button {
  background-color: #3b82f6;
}
```

✓ **Solution**: Use CSS variable

```css
/* Good */
.button {
  background-color: var(--color-brand-500);
}
```

---

❌ **Mistake**: Arbitrary spacing

```css
/* Bad */
.card {
  padding: 17px; /* Not on 8px grid */
}
```

✓ **Solution**: Use spacing tokens

```css
/* Good */
.card {
  padding: var(--space-2); /* 16px - on grid */
}
```

---

## References

### External Resources

- [Bootstrap 5 Documentation](https://getbootstrap.com/docs/5.0/)
- [CSS Custom Properties (MDN)](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [WCAG 2.1 Contrast Guidelines](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [8-Point Grid System](https://spec.fm/specifics/8-pt-grid)

### Internal Documentation

- [CSS Guidelines](architecture/css_guidelines.md)
- [HTML Guidelines](architecture/html_guidelines.md)
- [JavaScript Guidelines](architecture/javascript_guidelines.md)
- [Repository Rules](../repo_rules.md)
- [Copilot Instructions](../.github/copilot-instructions.md)

### Related Files

- **Design tokens**: [assets/core/variables.css](../assets/core/variables.css)
- **Color overrides**: [assets/core/color-consistency.css](../assets/core/color-consistency.css)
- **Python constants**: [ui/style_constants.py](../ui/style_constants.py)
- **Helper functions**: [ui/tooltip_utils.py](../ui/tooltip_utils.py)

---

## Version History

| Version | Date       | Changes                                        |
| ------- | ---------- | ---------------------------------------------- |
| 1.0.0   | 2026-02-13 | Initial design system documentation created    |
|         |            | Includes color unification implementation      |
|         |            | Documents all design tokens from variables.css |

---

**Maintained by**: Development Team  
**Last Review**: 2026-02-13  
**Next Review**: Quarterly or when adding new design tokens
