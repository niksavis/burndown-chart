# CSS Architecture Guidelines

**Purpose**: Create scalable, maintainable stylesheets with predictable behavior that are easily modified by both humans and AI agents. These guidelines enforce:

- **Scalability**: Systems that grow without becoming unmaintainable
- **Modularity**: Component-based architecture with BEM methodology
- **Consistency**: CSS variables for unified theming
- **Predictability**: Low specificity and clear naming prevent conflicts
- **Performance**: Optimized selectors and minimal repaints/reflows
- **Maintainability**: Clear patterns enable safe modifications
- **AI collaboration**: Structured organization optimized for AI-assisted development

## Terminology and Enforcement

- **MUST**: Required rule for all new/updated CSS in scope.
- **SHOULD**: Strong recommendation; deviations need a clear reason.
- **MAY**: Optional guidance for context-specific improvements.

Critical/hard limits in this document are **MUST** constraints.

## 2026 Standards Refresh (MDN-aligned)

Apply these as current defaults for new and updated styles:

- Use cascade layers (`@layer`) to define explicit order between reset, base, components, utilities, and overrides.
- Prefer logical properties (`margin-inline`, `padding-block`, `inset-inline-start`) over left/right/top/bottom where possible.
- Respect user motion preferences with `@media (prefers-reduced-motion: reduce)` and provide non-animated fallbacks.
- Keep theming in custom properties; avoid hard-coded colors/spacing in component rules.
- Keep accessibility-visible focus states with `:focus-visible`; do not remove focus outlines without accessible replacements.
- Avoid deprecated HTML styling attributes and inline style-driven layout decisions; keep presentation in CSS.

## File Size Limits

**CRITICAL RULES**:

- **Maximum file size**: 500 lines (hard limit)
- **Target size**: 200-300 lines per stylesheet
- **Warning threshold**: 400 lines → split immediately

## File Organization

### Structure Pattern

```
assets/
├── core/
│   ├── reset.css           # CSS reset (< 100 lines)
│   ├── variables.css       # CSS custom properties (< 150 lines)
│   └── base.css            # Base styles (< 200 lines)
├── components/
│   ├── buttons.css         # Button styles (< 150 lines)
│   ├── modal.css           # Modal styles (< 200 lines)
│   ├── forms.css           # Form styles (< 250 lines)
│   └── cards.css           # Card styles (< 150 lines)
├── layout/
│   ├── grid.css            # Grid system (< 200 lines)
│   ├── header.css          # Header styles (< 150 lines)
│   └── navigation.css      # Navigation styles (< 200 lines)
└── custom.css              # Main entry point (< 100 lines)
```

## Naming Conventions (Google Style Guide)

### Class Names

```css
/* GOOD: Lowercase with hyphens */
.modal-dialog {
}
.btn-primary {
}
.chart-container {
}
.settings-panel {
}

/* BAD: Mixed case or underscores */
.Modal-Dialog {
}
.btn_primary {
}
.chartContainer {
}
```

### File Names

```css
/* GOOD: Descriptive, hyphenated */
modal-component.css
button-styles.css
chart-visualization.css

/* BAD: Generic or cryptic */
styles.css
comp.css
s1.css
```

## CSS Custom Properties (Variables)

### Variable Organization

```css
/* variables.css (< 150 lines) */

/* === COLORS === */
:root {
  /* Primary colors */
  --color-primary: #007bff;
  --color-primary-dark: #0056b3;
  --color-primary-light: #3395ff;

  /* Semantic colors */
  --color-success: #28a745;
  --color-warning: #ffc107;
  --color-danger: #dc3545;
  --color-info: #17a2b8;

  /* Neutral colors */
  --color-text: #212529;
  --color-text-muted: #6c757d;
  --color-bg: #ffffff;
  --color-bg-alt: #f8f9fa;
  --color-border: #dee2e6;

  /* === SPACING === */
  --space-xs: 0.25rem;
  --space-sm: 0.5rem;
  --space-md: 1rem;
  --space-lg: 1.5rem;
  --space-xl: 2rem;
  --space-xxl: 3rem;

  /* === TYPOGRAPHY === */
  --font-family-base: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  --font-family-mono: 'Courier New', monospace;

  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-xxl: 2rem;

  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold: 700;

  --line-height-tight: 1.25;
  --line-height-base: 1.5;
  --line-height-relaxed: 1.75;

  /* === LAYOUT === */
  --container-max-width: 1200px;
  --sidebar-width: 250px;
  --header-height: 60px;

  /* === EFFECTS === */
  --border-radius-sm: 0.25rem;
  --border-radius-md: 0.375rem;
  --border-radius-lg: 0.5rem;

  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.15);

  --transition-fast: 150ms ease;
  --transition-base: 300ms ease;
  --transition-slow: 500ms ease;

  /* === Z-INDEX === */
  --z-dropdown: 1000;
  --z-sticky: 1020;
  --z-fixed: 1030;
  --z-modal-backdrop: 1040;
  --z-modal: 1050;
  --z-popover: 1060;
  --z-tooltip: 1070;
}
```

### Using Variables

```css
/* GOOD: Use variables for consistency */
.button {
  padding: var(--space-sm) var(--space-md);
  background-color: var(--color-primary);
  color: var(--color-bg);
  border-radius: var(--border-radius-md);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  transition: background-color var(--transition-fast);
}

.button:hover {
  background-color: var(--color-primary-dark);
}

/* BAD: Hard-coded values */
.button {
  padding: 8px 16px;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  font-size: 14px;
  font-weight: 500;
  transition: background-color 0.15s;
}
```

## Selector Best Practices

### Avoid ID Selectors

```css
/* GOOD: Class selectors */
.header {
}
.navigation {
}
.modal {
}

/* BAD: ID selectors (too specific) */
#header {
}
#navigation {
}
#modal {
}
```

### Avoid Type Qualifiers

```css
/* GOOD: Simple class selector */
.error {
}
.warning {
}
.success {
}

/* BAD: Qualified class selector (unnecessary specificity) */
div.error {
}
p.warning {
}
span.success {
}
```

### Keep Specificity Low

```css
/* GOOD: Low specificity (10) */
.card {
}
.card-header {
}
.card-title {
}

/* BAD: High specificity (30) */
.dashboard .content .card .header .title {
}
```

## BEM Methodology (Recommended)

### BEM Naming Convention

```css
/* Block */
.card {
}

/* Element: block__element */
.card__header {
}
.card__body {
}
.card__footer {
}

/* Modifier: block--modifier */
.card--large {
}
.card--featured {
}

/* Element modifier: block__element--modifier */
.card__header--dark {
}
.card__title--small {
}
```

### BEM Example

```css
/* Component: modal.css */

/* Block */
.modal {
  position: fixed;
  inset: 0;
  background-color: rgba(0, 0, 0, 0.5);
  z-index: var(--z-modal);
}

/* Elements */
.modal__dialog {
  position: relative;
  max-width: 600px;
  margin: 3rem auto;
  background-color: var(--color-bg);
  border-radius: var(--border-radius-lg);
  box-shadow: var(--shadow-lg);
}

.modal__header {
  padding: var(--space-lg);
  border-bottom: 1px solid var(--color-border);
}

.modal__title {
  margin: 0;
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-bold);
}

.modal__close {
  position: absolute;
  inset-block-start: var(--space-md);
  inset-inline-end: var(--space-md);
  background: none;
  border: none;
  font-size: var(--font-size-xl);
  cursor: pointer;
}

.modal__body {
  padding: var(--space-lg);
}

.modal__footer {
  padding: var(--space-lg);
  border-top: 1px solid var(--color-border);
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}

/* Modifiers */
.modal--large .modal__dialog {
  max-width: 900px;
}

.modal--fullscreen .modal__dialog {
  width: 100%;
  height: 100%;
  max-width: none;
  margin: 0;
  border-radius: 0;
}

.modal__header--dark {
  background-color: var(--color-primary);
  color: var(--color-bg);
}
```

## Breaking Down Large Files

### Strategy: Split by Component

**Before** (800 lines):

```css
/* styles.css */
/* Buttons (150 lines) */
/* Forms (200 lines) */
/* Cards (150 lines) */
/* Modals (200 lines) */
/* Charts (100 lines) */
```

**After**:

```
assets/components/
├── buttons.css     # 150 lines
├── forms.css       # 200 lines
├── cards.css       # 150 lines
├── modals.css      # 200 lines
└── charts.css      # 100 lines
```

### Main Entry Point

```css
/* custom.css (< 100 lines) */

@layer reset, tokens, base, layout, components, overrides;

/* Core */
@import url('core/reset.css') layer(reset);
@import url('core/variables.css') layer(tokens);
@import url('core/base.css') layer(base);

/* Layout */
@import url('layout/grid.css') layer(layout);
@import url('layout/header.css') layer(layout);
@import url('layout/navigation.css') layer(layout);

/* Components */
@import url('components/buttons.css') layer(components);
@import url('components/forms.css') layer(components);
@import url('components/cards.css') layer(components);
@import url('components/modals.css') layer(components);
@import url('components/charts.css') layer(components);

/* Project-specific overrides */
.app-container {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: var(--space-lg);
}
```

## Component Structure Template

```css
/* Component: buttons.css */

/* ====================
   BUTTON COMPONENT
   ==================== */

/* Base button */
.btn {
  display: inline-block;
  padding: var(--space-sm) var(--space-md);
  font-family: var(--font-family-base);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: var(--line-height-base);
  text-align: center;
  text-decoration: none;
  border: 1px solid transparent;
  border-radius: var(--border-radius-md);
  cursor: pointer;
  transition: all var(--transition-fast);
}

.btn:hover {
  opacity: 0.9;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Button variants */
.btn--primary {
  background-color: var(--color-primary);
  color: var(--color-bg);
}

.btn--secondary {
  background-color: var(--color-text-muted);
  color: var(--color-bg);
}

.btn--success {
  background-color: var(--color-success);
  color: var(--color-bg);
}

.btn--danger {
  background-color: var(--color-danger);
  color: var(--color-bg);
}

/* Button sizes */
.btn--sm {
  padding: var(--space-xs) var(--space-sm);
  font-size: var(--font-size-sm);
}

.btn--lg {
  padding: var(--space-md) var(--space-lg);
  font-size: var(--font-size-lg);
}

/* Button states */
.btn--loading {
  position: relative;
  color: transparent;
}

.btn--loading::after {
  content: '';
  position: absolute;
  inset-block-start: 50%;
  inset-inline-start: 50%;
  width: 1rem;
  height: 1rem;
  transform: translate(-50%, -50%);
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
```

## Layout Patterns

### Flexbox Grid

```css
/* layout/grid.css */

.container {
  max-width: var(--container-max-width);
  margin: 0 auto;
  padding: 0 var(--space-md);
}

.row {
  display: flex;
  flex-wrap: wrap;
  margin: 0 calc(var(--space-md) * -1);
}

.col {
  flex: 1 0 0%;
  padding: 0 var(--space-md);
}

/* Column sizes */
.col-1 {
  flex: 0 0 8.333333%;
  max-width: 8.333333%;
}
.col-2 {
  flex: 0 0 16.666667%;
  max-width: 16.666667%;
}
.col-3 {
  flex: 0 0 25%;
  max-width: 25%;
}
.col-4 {
  flex: 0 0 33.333333%;
  max-width: 33.333333%;
}
.col-6 {
  flex: 0 0 50%;
  max-width: 50%;
}
.col-8 {
  flex: 0 0 66.666667%;
  max-width: 66.666667%;
}
.col-12 {
  flex: 0 0 100%;
  max-width: 100%;
}

/* Responsive */
@media (max-width: 768px) {
  .col,
  .col-1,
  .col-2,
  .col-3,
  .col-4,
  .col-6,
  .col-8 {
    flex: 0 0 100%;
    max-width: 100%;
  }
}
```

### CSS Grid

```css
/* layout/dashboard.css */

.dashboard {
  display: grid;
  grid-template-columns: var(--sidebar-width) 1fr;
  grid-template-rows: var(--header-height) 1fr;
  min-height: 100vh;
  gap: 0;
}

.dashboard__header {
  grid-column: 1 / -1;
  grid-row: 1;
}

.dashboard__sidebar {
  grid-column: 1;
  grid-row: 2;
}

.dashboard__main {
  grid-column: 2;
  grid-row: 2;
  padding: var(--space-lg);
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard {
    grid-template-columns: 1fr;
  }

  .dashboard__sidebar {
    display: none;
  }

  .dashboard__main {
    grid-column: 1;
  }
}
```

## Responsive Design

### Mobile-First Approach

```css
/* Base (mobile) styles */
.card {
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}

.card__title {
  font-size: var(--font-size-lg);
}

/* Tablet and up */
@media (min-width: 768px) {
  .card {
    padding: var(--space-lg);
  }

  .card__title {
    font-size: var(--font-size-xl);
  }
}

/* Desktop and up */
@media (min-width: 1024px) {
  .card {
    padding: var(--space-xl);
  }

  .card__title {
    font-size: var(--font-size-xxl);
  }
}
```

### Breakpoint Variables

```css
/* variables.css */
:root {
  --breakpoint-xs: 0;
  --breakpoint-sm: 576px;
  --breakpoint-md: 768px;
  --breakpoint-lg: 1024px;
  --breakpoint-xl: 1200px;
}
```

## Performance Optimization

### Minimize Repaints/Reflows

```css
/* GOOD: Use transform for animations */
.modal {
  transform: translateY(-100%);
  transition: transform var(--transition-base);
}

.modal--active {
  transform: translateY(0);
}

/* BAD: Use top for animations (causes reflow) */
.modal {
  top: -100%;
  transition: top var(--transition-base);
}

.modal--active {
  top: 0;
}
```

### Use will-change Sparingly

```css
/* GOOD: Only on elements that will animate */
.modal {
  will-change: transform;
}

/* Remove after animation */
.modal--animated {
  will-change: auto;
}

/* BAD: Too broad */
* {
  will-change: transform, opacity;
}
```

## Dark Mode Support

```css
/* variables.css */
:root {
  --color-bg: #ffffff;
  --color-text: #212529;
  --color-border: #dee2e6;
}

@media (prefers-color-scheme: dark) {
  :root {
    --color-bg: #212529;
    --color-text: #f8f9fa;
    --color-border: #495057;
  }
}

/* Or class-based */
:root {
  --color-bg: #ffffff;
  --color-text: #212529;
}

[data-theme='dark'] {
  --color-bg: #212529;
  --color-text: #f8f9fa;
}
```

## Accessibility

### Focus Styles

```css
/* GOOD: Visible focus indicator */
:focus {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

/* For mouse users only */
:focus:not(:focus-visible) {
  outline: none;
}

/* For keyboard users */
:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}
```

### Screen Reader Only

```css
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  padding: 0;
  margin: -1px;
  overflow: hidden;
  clip: rect(0, 0, 0, 0);
  white-space: nowrap;
  border: 0;
}
```

## Comments and Documentation

### Section Comments (Google Style Guide)

```css
/* ====================
   MODAL COMPONENT
   ==================== */

.modal {
  /* Styles */
}

/* Header */
.modal__header {
  /* Styles */
}

/* Body */
.modal__body {
  /* Styles */
}

/* Footer */
.modal__footer {
  /* Styles */
}
```

## Project-Specific Patterns (Optional)

### Component Organization

```css
/* assets/components/chart.css */

/* Chart container */
.chart-container {
  position: relative;
  width: 100%;
  height: 400px;
  background-color: var(--color-bg);
  border: 1px solid var(--color-border);
  border-radius: var(--border-radius-md);
  padding: var(--space-md);
}

/* Loading state */
.chart-container--loading {
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart-container--loading::after {
  content: 'Loading...';
  color: var(--color-text-muted);
}

/* Error state */
.chart-container--error {
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--color-danger);
}
```

## Refactoring Checklist

When file exceeds 400 lines:

- [ ] Identify component boundaries
- [ ] Extract variables to separate file
- [ ] Group related selectors
- [ ] Split by component/feature
- [ ] Use `@import` to combine
- [ ] Remove duplicate rules
- [ ] Verify no regressions

## AI Agent Guidelines

### Before Creating Styles

1. Check if component file exists
2. Check current file size
3. If > 300 lines → create new file
4. Use BEM naming convention

### File Naming

```
components/
├── button.css          # Single component
├── form-input.css      # Descriptive
├── modal-dialog.css    # Clear purpose

# NOT
├── styles.css          # Too generic
├── comp.css            # Cryptic
```

## Summary

**Key Principles**:

1. Files < 500 lines (hard limit)
2. Use CSS custom properties
3. BEM naming convention
4. Class selectors only (no IDs)
5. Low specificity (< 30)
6. Mobile-first responsive
7. Section comments for organization
8. Split by component/feature

**Performance**:

- Use `transform` over `top`/`left`
- Minimize repaints/reflows
- Use `will-change` sparingly
- Optimize selectors

**Accessibility**:

- Visible focus indicators
- Screen reader utilities
- Sufficient color contrast
- Dark mode support
