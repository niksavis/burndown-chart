# HTML Architecture Guidelines

**Purpose**: Create semantic, accessible, maintainable HTML that serves all users and is easily understood by both humans and AI agents. These guidelines enforce:

- **Semantic structure**: Use proper HTML5 elements for meaning and clarity
- **Universal accessibility**: ARIA attributes and screen reader support for all users
- **Component modularity**: Reusable, focused layout components
- **Separation of concerns**: Structure separate from presentation and behavior
- **Discoverability**: Intuitive organization makes code easy to navigate
- **AI collaboration**: Component structures optimized for AI-assisted development

## Terminology and Enforcement

- **MUST**: Required rule for all new/updated markup in scope.
- **SHOULD**: Strong recommendation; deviations need a clear reason.
- **MAY**: Optional guidance for context-specific improvements.

Critical/hard limits in this document are **MUST** constraints.

## 2026 Standards Refresh (MDN-aligned)

Apply these as current defaults for new and updated markup:

- Keep `<!doctype html>` at the top of every document to ensure standards mode rendering.
- Prefer native semantic elements (`<main>`, `<nav>`, `<button>`, `<form>`, `<input>`) before adding ARIA roles.
- Use ARIA to augment semantics, not replace native semantics; avoid redundant `role` attributes on semantic elements.
- Ensure form controls have programmatic labels (`<label for>` or explicit accessible name) and clear error associations.
- Use heading hierarchy (`h1` to `h6`) in document order; do not skip levels for visual styling.
- Avoid presentational/deprecated attributes and keep behavior/presentation in JavaScript/CSS, not inline HTML attributes.

## File Size Limits

**CRITICAL RULES**:

- **Maximum file size**: 300 lines (hard limit for template files)
- **Target size**: 100-200 lines per layout component
- **Warning threshold**: 250 lines → split components

## HTML5 Semantic Structure (Google Style Guide)

### Document Structure

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Example App - Dashboard</title>
    <link rel="stylesheet" href="styles.css" />
  </head>
  <body>
    <!-- Navigation -->
    <nav class="primary-nav" aria-label="Main navigation">
      <ul class="nav-list">
        <li class="nav-item"><a href="/" class="nav-link">Home</a></li>
        <li class="nav-item"><a href="/dashboard" class="nav-link">Dashboard</a></li>
      </ul>
    </nav>

    <!-- Main content -->
    <main class="main-content">
      <h1>Dashboard</h1>
      <!-- Content here -->
    </main>

    <!-- Footer -->
    <footer class="site-footer">
      <p>&copy; 2026 Example App</p>
    </footer>

    <script src="app.js"></script>
  </body>
</html>
```

## Naming Conventions (Google Style Guide)

### Use Lowercase

```html
<!-- GOOD: Lowercase for all HTML -->
<div class="container">
  <img src="logo.png" alt="Company logo" />
  <button type="button" class="btn-primary">Submit</button>
</div>

<!-- BAD: Mixed case -->
<div class="Container">
  <img src="logo.png" alt="Company Logo" />
  <button type="button" class="Btn-Primary">Submit</button>
</div>
```

### Class Naming

```html
<!-- GOOD: Descriptive, hyphenated -->
<div class="modal-dialog">
  <div class="modal-header">
    <h2 class="modal-title">Settings</h2>
  </div>
  <div class="modal-body">
    <!-- Content -->
  </div>
  <div class="modal-footer">
    <button class="btn btn-primary">Save</button>
    <button class="btn btn-secondary">Cancel</button>
  </div>
</div>

<!-- BAD: Cryptic, inconsistent -->
<div class="md">
  <div class="mdHdr">
    <h2 class="mdT">Settings</h2>
  </div>
  <div class="modal_body">
    <!-- Content -->
  </div>
</div>
```

## Component Organization (Optional)

### Python-Generated HTML Pattern (Example)

```python
# ui/components/modal.py (< 200 lines)
from dash import html, dcc

def create_modal(modal_id: str, title: str) -> html.Div:
    """Create modal component.

    Args:
        modal_id: Unique identifier for modal
        title: Modal title text

    Returns:
        Dash HTML Div component
    """
    return html.Div([
        html.Div([
            # Modal header
            html.Div([
                html.H2(title, className='modal-title'),
                html.Button(
                    '×',
                    id=f'{modal_id}-close',
                    className='modal-close',
                    **{'aria-label': 'Close'}
                ),
            ], className='modal-header'),

            # Modal body
            html.Div(
                id=f'{modal_id}-body',
                className='modal-body'
            ),

            # Modal footer
            html.Div([
                html.Button(
                    'Save',
                    id=f'{modal_id}-save',
                    className='btn btn-primary'
                ),
                html.Button(
                    'Cancel',
                    id=f'{modal_id}-cancel',
                    className='btn btn-secondary'
                ),
            ], className='modal-footer'),
        ], className='modal-dialog'),
    ], id=modal_id, className='modal', **{'aria-hidden': 'true'})
```

### Component File Structure (Example)

```
ui/
├── __init__.py
├── layout.py               # Main layout (< 250 lines)
└── components/
    ├── __init__.py
    ├── modal.py            # Modal component (< 150 lines)
    ├── chart.py            # Chart container (< 200 lines)
    ├── settings_panel.py   # Settings panel (< 250 lines)
    └── navigation.py       # Nav component (< 100 lines)
```

## Semantic HTML5 Elements

### Use Appropriate Elements

```html
<!-- GOOD: Semantic HTML5 -->
<article class="card">
  <header class="card-header">
    <h2>Project Overview</h2>
  </header>

  <section class="card-body">
    <p>Project details...</p>

    <figure class="chart-container">
      <figcaption>Progress Chart</figcaption>
      <!-- Chart here -->
    </figure>
  </section>

  <footer class="card-footer">
    <time datetime="2026-01-30">Last updated: Jan 30, 2026</time>
  </footer>
</article>

<!-- BAD: Div soup -->
<div class="card">
  <div class="card-header">
    <div class="title">Project Overview</div>
  </div>

  <div class="card-body">
    <div>Project details...</div>

    <div class="chart-container">
      <div>Progress Chart</div>
      <!-- Chart here -->
    </div>
  </div>

  <div class="card-footer">
    <div>Last updated: Jan 30, 2026</div>
  </div>
</div>
```

### Element Selection Guide

| Content Type | Element     | Example                             |
| ------------ | ----------- | ----------------------------------- |
| Navigation   | `<nav>`     | Main menu, breadcrumbs              |
| Main content | `<main>`    | Primary page content                |
| Article      | `<article>` | Blog post, card, standalone content |
| Section      | `<section>` | Thematic grouping                   |
| Aside        | `<aside>`   | Sidebar, related content            |
| Header       | `<header>`  | Page/section header                 |
| Footer       | `<footer>`  | Page/section footer                 |
| Figure       | `<figure>`  | Charts, diagrams, code blocks       |

## Accessibility (ARIA)

### ARIA Labels and Roles

```html
<!-- GOOD: Accessible navigation -->
<nav aria-label="Main navigation">
  <ul>
    <li><a href="/" aria-current="page">Home</a></li>
    <li><a href="/dashboard">Dashboard</a></li>
  </ul>
</nav>

<!-- GOOD: Accessible buttons -->
<button type="button" aria-label="Close modal" aria-expanded="false" aria-controls="modal-content">
  ×
</button>

<!-- GOOD: Accessible forms -->
<form aria-label="Service configuration">
  <div class="form-group">
    <label for="service-url">Service URL</label>
    <input
      type="url"
      id="service-url"
      name="service-url"
      required
      aria-describedby="service-url-help"
    />
    <span id="service-url-help" class="form-text"> Enter your service URL </span>
  </div>
</form>

<!-- GOOD: Accessible tabs -->
<div role="tablist" aria-label="Settings tabs">
  <button role="tab" aria-selected="true" aria-controls="general-panel" id="general-tab">
    General
  </button>
  <button role="tab" aria-selected="false" aria-controls="advanced-panel" id="advanced-tab">
    Advanced
  </button>
</div>

<div role="tabpanel" id="general-panel" aria-labelledby="general-tab">
  <!-- General settings -->
</div>
```

### Screen Reader Support

```html
<!-- GOOD: Hidden but accessible -->
<button type="button" class="icon-btn">
  <span class="sr-only">Delete item</span>
  <span aria-hidden="true">Delete</span>
</button>

<!-- CSS for sr-only -->
<style>
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    border: 0;
  }
</style>
```

## Forms (Framework-Specific, Optional)

### Dash Form Components (Example)

```python
# ui/components/forms.py
from dash import html, dcc

def create_text_input(
    input_id: str,
    label: str,
    placeholder: str = '',
    required: bool = False,
    help_text: str = ''
) -> html.Div:
    """Create accessible text input."""
    return html.Div([
        html.Label(label, htmlFor=input_id),
        dcc.Input(
            id=input_id,
            type='text',
            placeholder=placeholder,
            required=required,
            className='form-control',
            **{'aria-describedby': f'{input_id}-help' if help_text else None}
        ),
        html.Span(
            help_text,
            id=f'{input_id}-help',
            className='form-text'
        ) if help_text else None,
    ], className='form-group')

def create_select(
    select_id: str,
    label: str,
    options: list[dict],
    required: bool = False
) -> html.Div:
    """Create accessible select dropdown."""
    return html.Div([
        html.Label(label, htmlFor=select_id),
        dcc.Dropdown(
            id=select_id,
            options=options,
            className='form-control',
          **{'aria-describedby': f'{select_id}-help' if required else None}
        ),
    ], className='form-group')
```

### Form Validation

```python
def create_validated_input(
    input_id: str,
    label: str,
    error_id: str
) -> html.Div:
    """Create input with validation feedback."""
    return html.Div([
        html.Label(label, htmlFor=input_id),
        dcc.Input(
            id=input_id,
            type='text',
            className='form-control',
            **{
                'aria-invalid': 'false',
                'aria-describedby': error_id
            }
        ),
        html.Span(
            id=error_id,
            className='error-message',
            role='alert',
            **{'aria-live': 'polite'}
        ),
    ], className='form-group')
```

## Separation of Concerns

### HTML Structure Only

```html
<!-- GOOD: Structure only, no styling -->
<div class="alert alert-warning">
  <p>Warning: Configuration incomplete</p>
  <button type="button" class="btn-close">Dismiss</button>
</div>

<!-- BAD: Inline styles -->
<div style="padding: 10px; background: yellow; border: 1px solid orange;">
  <p style="font-weight: bold;">Warning: Configuration incomplete</p>
  <button style="float: right;">Dismiss</button>
</div>
```

### No Inline JavaScript

```html
<!-- GOOD: Use event listeners in JS -->
<button type="button" id="submit-btn" class="btn-primary">Submit</button>

<!-- JavaScript in separate file -->
<script>
  document.getElementById('submit-btn').addEventListener('click', handleSubmit);
</script>

<!-- BAD: Inline JavaScript -->
<button onclick="handleSubmit()" class="btn-primary">Submit</button>
```

## Breaking Down Large Components

### Strategy: Split by Section

**Before** (500 lines):

```python
# ui/layout.py
def create_layout():
    return html.Div([
        # Navigation (50 lines)
        # Header (100 lines)
        # Main content (200 lines)
        # Sidebar (100 lines)
        # Footer (50 lines)
    ])
```

**After**:

```python
# ui/layout.py (< 100 lines)
from ui.components import navigation, header, sidebar, footer
from ui.sections import main_content

def create_layout():
    """Create main application layout."""
    return html.Div([
        navigation.create_navigation(),
        header.create_header(),
        main_content.create_main_content(),
        sidebar.create_sidebar(),
        footer.create_footer(),
    ], className='app-container')

# ui/components/navigation.py (< 80 lines)
def create_navigation():
    """Create navigation component."""
    return html.Nav([
        # Navigation content
    ], className='primary-nav')

# ui/sections/main_content.py (< 200 lines)
def create_main_content():
    """Create main content section."""
    return html.Main([
        # Main content
    ], className='main-content')
```

## Data Attributes

### Use for JavaScript Hooks

```html
<!-- GOOD: Data attributes for JS -->
<div
  class="chart-container"
  data-chart-type="progress"
  data-chart-id="project-123"
  data-update-interval="5000"
>
  <!-- Chart content -->
</div>

<button type="button" class="filter-btn" data-filter="status" data-value="in-progress">
  In Progress
</button>
```

### Framework-Specific: Pattern-Matching IDs (Example)

```python
# GOOD: Structured IDs for callbacks
html.Div([
    dcc.Input(
        id={'type': 'filter', 'field': 'status'},
        type='text'
    ),
    html.Button(
        'Apply',
        id={'type': 'filter-btn', 'field': 'status'}
    ),
])

# Pattern matching callbacks
@app.callback(
    Output('results', 'children'),
    Input({'type': 'filter', 'field': ALL}, 'value')
)
def update_results(values):
    pass
```

## Performance Considerations

### Minimize DOM Depth

```html
<!-- GOOD: Shallow DOM (3 levels) -->
<nav class="nav">
  <ul class="nav-list">
    <li class="nav-item"><a href="/">Home</a></li>
  </ul>
</nav>

<!-- BAD: Deep DOM (7 levels) -->
<nav>
  <div class="nav-wrapper">
    <div class="nav-container">
      <ul>
        <li>
          <div class="item-wrapper">
            <a href="/">Home</a>
          </div>
        </li>
      </ul>
    </div>
  </div>
</nav>
```

### Lazy Loading Images

```html
<!-- GOOD: Native lazy loading -->
<img src="chart-large.png" alt="Progress chart" loading="lazy" width="800" height="600" />
```

## Validation and Testing

### HTML5 Validation

```html
<!-- GOOD: Proper structure -->
<form>
  <label for="email">Email</label>
  <input type="email" id="email" name="email" required pattern="[^@]+@[^@]+\.[^@]+" />

  <label for="age">Age</label>
  <input type="number" id="age" name="age" min="0" max="120" />

  <button type="submit">Submit</button>
</form>
```

## Framework-Specific Patterns (Optional)

### Modal Structure

```python
# ui/components/modal.py
def create_settings_modal() -> html.Div:
    """Create settings modal component."""
    return html.Div([
        html.Div([
            # Header
            html.Div([
                html.H2('Settings', className='modal-title'),
                html.Button(
                    '×',
                    id='settings-modal-close',
                    className='modal-close',
                    **{'aria-label': 'Close settings'}
                ),
            ], className='modal-header'),

            # Body with tabs
            html.Div([
                # Tab list
                html.Div([
                    html.Button(
                        'General',
                        id='tab-general',
                        className='tab-btn active',
                        role='tab',
                        **{'aria-selected': 'true'}
                    ),
                    html.Button(
                        'Advanced',
                        id='tab-advanced',
                        className='tab-btn',
                        role='tab',
                        **{'aria-selected': 'false'}
                    ),
                ], role='tablist', className='tab-list'),

                # Tab panels
                html.Div([
                    html.Div(
                        id='panel-general',
                        role='tabpanel',
                        className='tab-panel active'
                    ),
                    html.Div(
                        id='panel-advanced',
                        role='tabpanel',
                        className='tab-panel'
                    ),
                ], className='tab-content'),
            ], className='modal-body'),

            # Footer
            html.Div([
                html.Button(
                    'Save Changes',
                    id='settings-save',
                    className='btn btn-primary'
                ),
                html.Button(
                    'Cancel',
                    id='settings-cancel',
                    className='btn btn-secondary'
                ),
            ], className='modal-footer'),
        ], className='modal-dialog'),
    ], id='settings-modal', className='modal', **{'aria-hidden': 'true'})
```

## Refactoring Checklist

When component exceeds 200 lines:

- [ ] Identify logical sections (header, body, footer)
- [ ] Extract repeated patterns to functions
- [ ] Create component helpers
- [ ] Split by responsibility
- [ ] Maintain accessibility attributes
- [ ] Test with screen reader
- [ ] Validate HTML5 structure

## AI Agent Guidelines

### Component Creation

1. Start with semantic HTML5
2. Add ARIA attributes for accessibility
3. Use descriptive class names
4. Keep structure < 200 lines
5. Extract to separate file if complex

### Naming Pattern

```python
# GOOD: Descriptive function names
def create_navigation_menu()
def create_chart_container()
def create_settings_panel()

# BAD: Generic names
def create_div()
def build_component()
```

## Summary

**Key Principles**:

1. Semantic HTML5 elements
2. Lowercase for all HTML
3. Accessibility (ARIA) mandatory
4. Descriptive class names (hyphenated)
5. No inline styles or JavaScript
6. Components < 200 lines
7. Shallow DOM structure
8. Valid HTML5 markup

**Optional: Framework-Specific**:

- Component functions in a dedicated UI module
- Structured IDs for pattern matching (if supported)
- Accessibility attributes on all interactive elements
- Extract large layouts to multiple functions
