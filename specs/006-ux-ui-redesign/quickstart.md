# Developer Quickstart Guide

**Feature**: Unified UX/UI and Architecture Redesign  
**Branch**: `006-ux-ui-redesign`  
**Date**: 2025-10-23

## Quick Reference

**Goal**: Redesign the Burndown Chart Generator for UX/UI uniformity and architectural consistency

**Key Changes**:
- Dashboard becomes first tab and default view
- Parameter controls moved to collapsible sticky panel
- Standardized component builders with design tokens
- Improved mobile responsiveness

**Development Environment**: Windows with PowerShell, Python 3.11.12, virtual environment required

---

## Prerequisites

### Required Tools

- **Python**: 3.11.12 (verify: `.\.venv\Scripts\activate; python --version`)
- **Git**: For version control
- **VS Code**: Recommended IDE with Python extension
- **PowerShell**: Windows PowerShell 5.1+ (default shell)

### Project Setup

```powershell
# Clone repository (if not already done)
git clone https://github.com/niksavis/burndown-chart.git
cd burndown-chart

# Switch to feature branch
git checkout 006-ux-ui-redesign

# Activate virtual environment (REQUIRED for all Python commands)
.\.venv\Scripts\activate

# Install dependencies
.\.venv\Scripts\activate; pip install -r requirements.txt

# Verify installation
.\.venv\Scripts\activate; python -c "import dash; print(f'Dash {dash.__version__}')"
```

**CRITICAL**: Always prefix Python commands with `.\.venv\Scripts\activate;` - this is a Windows environment requirement.

---

## Architecture Overview

### Directory Structure

```
burndown-chart/
├── ui/                      # Presentation layer (YOU WILL MODIFY THIS)
│   ├── layout.py           # Main layout composition
│   ├── tabs.py             # Tab navigation system
│   ├── cards.py            # Card components
│   ├── components.py       # Input components
│   ├── dashboard.py        # NEW: Dashboard tab module
│   ├── style_constants.py  # Design tokens (ENHANCE)
│   └── button_utils.py     # Button builders (ENHANCE)
│
├── callbacks/               # Event handling layer (YOU WILL ADD NEW CALLBACKS)
│   ├── dashboard.py        # NEW: Dashboard callbacks
│   ├── visualization.py    # Existing chart callbacks
│   └── settings.py         # Parameter callbacks (MODIFY)
│
├── data/                    # Business logic layer (NO CHANGES)
│   ├── processing.py       # Core calculations (REUSE)
│   └── persistence.py      # JSON file operations (REUSE)
│
├── tests/                   # Test suites (YOU WILL ADD TESTS)
│   ├── unit/ui/            # Component tests
│   └── integration/        # Workflow tests
│
└── specs/006-ux-ui-redesign/  # Feature documentation (READ THIS)
    ├── spec.md             # User requirements
    ├── plan.md             # Implementation plan
    ├── research.md         # Technical decisions
    ├── data-model.md       # Entity definitions
    ├── quickstart.md       # This file
    └── contracts/          # API contracts
```

---

## Development Workflow

### Step 1: Understand Current State

```powershell
# Run application to see current UI
.\.venv\Scripts\activate; python app.py

# Open browser to http://localhost:8050
# Observe issues:
# - Parameter controls below charts (scroll required)
# - No Dashboard tab
# - Inconsistent styling
```

### Step 2: Read Documentation

**Required Reading** (in order):

1. `specs/006-ux-ui-redesign/spec.md` - User requirements and acceptance criteria
2. `specs/006-ux-ui-redesign/research.md` - Technical decisions made
3. `specs/006-ux-ui-redesign/data-model.md` - Data entities and structures
4. `specs/006-ux-ui-redesign/contracts/component-builders.md` - Component API contracts
5. `specs/006-ux-ui-redesign/contracts/callbacks.md` - Callback contracts

### Step 3: Set Up Development Environment

```powershell
# Create a feature branch off 006-ux-ui-redesign (if working on subtask)
git checkout -b 006-ux-ui-redesign-dashboard

# Install development dependencies (if needed)
.\.venv\Scripts\activate; pip install pytest pytest-cov playwright

# Install Playwright browsers (first time only)
.\.venv\Scripts\activate; playwright install chromium

# Verify tests run
.\.venv\Scripts\activate; pytest tests/unit/ -v
```

### Step 4: Choose a Task

**Recommended Task Order**:

1. **Task A**: Standardize design tokens (easiest, foundational)
2. **Task B**: Create component builders (uses Task A)
3. **Task C**: Create Dashboard tab (uses Task B)
4. **Task D**: Implement collapsible parameter panel (uses Task A, B)
5. **Task E**: Update navigation order (uses Task C)
6. **Task F**: Refactor existing components (uses all above)

---

## Task Implementation Guides

### Task A: Standardize Design Tokens

**Goal**: Centralize all styling values in `ui/style_constants.py`

**Files to Modify**:
- `ui/style_constants.py` (enhance existing constants)

**Steps**:

1. **Audit Current Styles**:
```powershell
# Find all inline styles in UI components
Get-ChildItem -Path "ui\" -Recurse -Filter "*.py" | Select-String -Pattern "style\s*=" | Select-Object -First 20
```

2. **Add Design Tokens**:
```python
# ui/style_constants.py

# Colors (Bootstrap FLATLY theme)
COLOR_PRIMARY = "#0d6efd"
COLOR_SECONDARY = "#6c757d"
COLOR_SUCCESS = "#198754"
COLOR_WARNING = "#ffc107"
COLOR_DANGER = "#dc3545"
COLOR_INFO = "#0dcaf0"
COLOR_LIGHT = "#f8f9fa"
COLOR_DARK = "#343a40"

# Spacing (Bootstrap scale)
SPACING_XS = "0.25rem"
SPACING_SM = "0.5rem"
SPACING_MD = "1rem"
SPACING_LG = "1.5rem"
SPACING_XL = "2rem"
SPACING_XXL = "3rem"

# Typography
FONT_SIZE_XS = "0.75rem"
FONT_SIZE_SM = "0.875rem"
FONT_SIZE_BASE = "1rem"
FONT_SIZE_LG = "1.125rem"
FONT_SIZE_XL = "1.25rem"

FONT_WEIGHT_NORMAL = 400
FONT_WEIGHT_MEDIUM = 500
FONT_WEIGHT_BOLD = 700

# Layout
BORDER_RADIUS_SM = "0.25rem"
BORDER_RADIUS_MD = "0.375rem"
BORDER_RADIUS_LG = "0.5rem"

SHADOW_SM = "0 .125rem .25rem rgba(0,0,0,.075)"
SHADOW_MD = "0 .5rem 1rem rgba(0,0,0,.15)"
SHADOW_LG = "0 1rem 3rem rgba(0,0,0,.175)"

Z_INDEX_STICKY = 1020
Z_INDEX_MODAL = 1050
Z_INDEX_TOOLTIP = 1070

# Animation
TRANSITION_FAST = "200ms"
TRANSITION_BASE = "300ms"
TRANSITION_SLOW = "500ms"
EASING_DEFAULT = "ease-in-out"

# Helper functions
def get_card_style(variant="default"):
    """Get standardized card styling."""
    return {
        "borderRadius": BORDER_RADIUS_MD,
        "boxShadow": SHADOW_SM,
        "padding": SPACING_MD,
        "backgroundColor": COLOR_WHITE if variant == "default" else COLOR_LIGHT
    }

def get_button_color(variant="primary"):
    """Get button color for variant."""
    colors = {
        "primary": COLOR_PRIMARY,
        "secondary": COLOR_SECONDARY,
        "success": COLOR_SUCCESS,
        "danger": COLOR_DANGER,
        "warning": COLOR_WARNING,
        "info": COLOR_INFO,
    }
    return colors.get(variant, COLOR_PRIMARY)
```

3. **Test**:
```python
# tests/unit/ui/test_style_constants.py
import pytest
from ui.style_constants import (
    COLOR_PRIMARY, SPACING_MD, get_card_style, get_button_color
)

def test_design_tokens_defined():
    """Verify all design tokens are defined."""
    assert COLOR_PRIMARY == "#0d6efd"
    assert SPACING_MD == "1rem"

def test_get_card_style_default():
    """Test card style helper."""
    style = get_card_style("default")
    assert "borderRadius" in style
    assert "boxShadow" in style

def test_get_button_color_variants():
    """Test button color helper."""
    assert get_button_color("primary") == COLOR_PRIMARY
    assert get_button_color("danger") == COLOR_DANGER
```

4. **Run Tests**:
```powershell
.\.venv\Scripts\activate; pytest tests/unit/ui/test_style_constants.py -v
```

---

### Task B: Create Component Builders

**Goal**: Implement standardized component builder functions

**Files to Create/Modify**:
- `ui/button_utils.py` (enhance existing)
- `ui/components.py` (enhance existing)
- `ui/cards.py` (enhance existing)

**Example: Button Builder**:

```python
# ui/button_utils.py
from dash import html
import dash_bootstrap_components as dbc
from .style_constants import get_button_color, SPACING_SM

def create_action_button(
    text: str,
    icon: str = None,
    variant: str = "primary",
    size: str = "md",
    id_suffix: str = "",
    **kwargs
) -> dbc.Button:
    """
    Create standardized action button.
    
    See contracts/component-builders.md for full contract.
    """
    if not text:
        raise ValueError("Button text is required")
    
    # Generate ID
    text_slug = text.lower().replace(" ", "-")
    button_id = f"btn-{text_slug}"
    if id_suffix:
        button_id += f"-{id_suffix}"
    
    # Build button content
    children = []
    if icon:
        children.append(html.I(className=f"fas fa-{icon} me-2"))
    children.append(text)
    
    # Return button with consistent props
    return dbc.Button(
        children,
        id=button_id,
        color=variant,
        size=size,
        **{
            "aria-label": kwargs.pop("aria_label", text),
            **kwargs
        }
    )
```

**Test Component Builder**:

```python
# tests/unit/ui/test_button_utils.py
import pytest
from ui.button_utils import create_action_button

def test_create_action_button_default():
    """Test button with default parameters."""
    btn = create_action_button("Save")
    assert btn.id == "btn-save"
    assert btn.color == "primary"
    assert btn.size == "md"

def test_create_action_button_with_icon():
    """Test button with icon."""
    btn = create_action_button("Delete", icon="trash", variant="danger")
    assert "fa-trash" in str(btn.children[0])

def test_create_action_button_validation():
    """Test validation errors."""
    with pytest.raises(ValueError):
        create_action_button("")  # Empty text
```

**Run Tests**:
```powershell
.\.venv\Scripts\activate; pytest tests/unit/ui/test_button_utils.py -v
```

---

### Task C: Create Dashboard Tab

**Goal**: Implement new Dashboard tab as first tab

**Files to Create**:
- `ui/dashboard.py` (new module)
- `callbacks/dashboard.py` (new module)

**Step-by-Step**:

1. **Create Dashboard Module**:

```python
# ui/dashboard.py
from dash import html, dcc
import dash_bootstrap_components as dbc
from .cards import create_info_card
from .style_constants import COLOR_PRIMARY, SPACING_MD

def create_dashboard_tab() -> dbc.Tab:
    """
    Create Dashboard tab with project metrics.
    
    See contracts/component-builders.md for full contract.
    """
    return dbc.Tab(
        label="Dashboard",
        tab_id="tab-dashboard",
        children=dbc.Container([
            # Row 1: Key metrics
            dbc.Row([
                dbc.Col([
                    create_completion_forecast_card()
                ], xs=12, md=4, className="mb-3"),
                dbc.Col([
                    create_velocity_metrics_card()
                ], xs=12, md=4, className="mb-3"),
                dbc.Col([
                    create_remaining_work_card()
                ], xs=12, md=4, className="mb-3"),
            ]),
            
            # Row 2: PERT timeline
            dbc.Row([
                dbc.Col([
                    create_pert_timeline_card()
                ], xs=12, md=6, className="mb-3"),
                dbc.Col([
                    create_scope_health_card()
                ], xs=12, md=6, className="mb-3"),
            ]),
        ], fluid=True, id="dashboard-container")
    )

def create_completion_forecast_card() -> dbc.Card:
    """Create completion forecast metrics card."""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-calendar-check me-2", style={"color": COLOR_PRIMARY}),
            "Completion Forecast"
        ]),
        dbc.CardBody([
            html.H3("--", id="forecast-date", className="text-primary mb-2"),
            html.P("--", id="forecast-confidence", className="text-muted mb-3"),
            dbc.Progress(id="completion-progress", value=0, className="mb-2"),
            html.Small("-- days to completion", id="days-to-completion", className="text-muted"),
        ]),
        dbc.CardFooter([
            dbc.Button("View Burndown", id="goto-burndown", size="sm", color="link")
        ])
    ], id="card-dashboard-forecast")

def create_velocity_metrics_card() -> dbc.Card:
    """Create velocity metrics card."""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-tachometer-alt me-2", style={"color": COLOR_PRIMARY}),
            "Current Velocity"
        ]),
        dbc.CardBody([
            html.Div([
                html.Strong("Items: "),
                html.Span("--", id="velocity-items"),
            ], className="mb-2"),
            html.Div([
                html.Strong("Points: "),
                html.Span("--", id="velocity-points"),
            ], className="mb-2"),
            html.Div([
                html.I(id="velocity-trend-icon", className="fas fa-minus me-2"),
                html.Span("--", id="velocity-trend-text"),
            ], className="text-muted"),
        ]),
    ], id="card-dashboard-velocity")

def create_remaining_work_card() -> dbc.Card:
    """Create remaining work metrics card."""
    return dbc.Card([
        dbc.CardHeader([
            html.I(className="fas fa-tasks me-2", style={"color": COLOR_PRIMARY}),
            "Remaining Work"
        ]),
        dbc.CardBody([
            html.Div([
                html.Strong("Items: "),
                html.Span("--", id="remaining-items"),
            ], className="mb-2"),
            html.Div([
                html.Strong("Points: "),
                html.Span("--", id="remaining-points"),
            ]),
        ]),
    ], id="card-dashboard-remaining")

def create_pert_timeline_card() -> dbc.Card:
    """Create PERT timeline visualization card."""
    return dbc.Card([
        dbc.CardHeader("PERT Forecast Timeline"),
        dbc.CardBody([
            dcc.Graph(id="pert-timeline-figure", config={"displayModeBar": False})
        ]),
    ], id="card-dashboard-pert")

def create_scope_health_card() -> dbc.Card:
    """Create scope health card."""
    return dbc.Card([
        dbc.CardHeader("Scope Health"),
        dbc.CardBody([
            html.P("Scope metrics visualization", className="text-muted")
        ]),
    ], id="card-dashboard-scope")
```

2. **Create Dashboard Callbacks**:

```python
# callbacks/dashboard.py
from dash import Input, Output, callback
from typing import List, Dict, Any, Tuple

@callback(
    [
        Output("forecast-date", "children"),
        Output("forecast-confidence", "children"),
        Output("completion-progress", "value"),
        Output("days-to-completion", "children"),
        Output("velocity-items", "children"),
        Output("velocity-points", "children"),
        Output("velocity-trend-icon", "className"),
        Output("velocity-trend-text", "children"),
        Output("remaining-items", "children"),
        Output("remaining-points", "children"),
    ],
    [
        Input("statistics-store", "data"),
        Input("settings-store", "data")
    ]
)
def update_dashboard_metrics(
    statistics: List[Dict[str, Any]],
    settings: Dict[str, Any]
) -> Tuple[str, ...]:
    """
    Update dashboard metrics display.
    
    See contracts/callbacks.md for full contract.
    """
    # Implement according to callback contract
    # For now, return placeholder values
    return (
        "2025-12-15",
        "75% confidence",
        68.5,
        "53 days to completion",
        "8.2 items/week",
        "24.7 points/week",
        "fas fa-arrow-up text-success",
        "Increasing",
        "42 items",
        "125.5 points"
    )
```

3. **Register Dashboard Module**:

```python
# ui/__init__.py
from .dashboard import create_dashboard_tab

# callbacks/__init__.py
from . import dashboard  # Import to register callbacks
```

4. **Update Tabs Order**:

```python
# ui/tabs.py (modify existing)
from .dashboard import create_dashboard_tab

def create_tab_navigation():
    """Create main tab navigation with Dashboard first."""
    tabs = [
        create_dashboard_tab(),  # NEW - First position
        create_burndown_tab(),
        create_items_per_week_tab(),
        create_points_per_week_tab(),
        create_scope_tracking_tab(),
        create_bug_analysis_tab(),
    ]
    return dbc.Tabs(tabs, id="chart-tabs", active_tab="tab-dashboard")  # Dashboard default
```

5. **Test Dashboard**:

```python
# tests/unit/ui/test_dashboard.py
from ui.dashboard import (
    create_dashboard_tab,
    create_completion_forecast_card,
    create_velocity_metrics_card
)

def test_create_dashboard_tab():
    """Test dashboard tab creation."""
    tab = create_dashboard_tab()
    assert tab.tab_id == "tab-dashboard"
    assert tab.label == "Dashboard"

def test_dashboard_cards_have_ids():
    """Test all dashboard cards have proper IDs."""
    forecast_card = create_completion_forecast_card()
    assert forecast_card.id == "card-dashboard-forecast"
    
    velocity_card = create_velocity_metrics_card()
    assert velocity_card.id == "card-dashboard-velocity"
```

```powershell
.\.venv\Scripts\activate; pytest tests/unit/ui/test_dashboard.py -v
```

6. **Integration Test**:

```python
# tests/integration/dashboard/test_dashboard_workflow.py
import pytest
from playwright.sync_api import sync_playwright
import waitress
import threading
import time

@pytest.fixture(scope="module")
def live_server():
    """Start app server for testing."""
    import app as dash_app
    
    def run_server():
        waitress.serve(dash_app.app.server, host="127.0.0.1", port=8051, threads=1)
    
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    time.sleep(3)  # Allow server startup
    
    yield "http://127.0.0.1:8051"

def test_dashboard_is_default_tab(live_server):
    """Test Dashboard loads as default tab."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto(live_server)
        page.wait_for_selector("#chart-tabs", timeout=10000)
        
        # Verify Dashboard tab is active
        tabs = page.locator("#chart-tabs .nav-link")
        dashboard_tab = tabs.filter(has_text="Dashboard")
        
        tab_class = dashboard_tab.get_attribute("class") or ""
        assert "active" in tab_class
        
        # Verify Dashboard content visible
        forecast_card = page.locator("#card-dashboard-forecast")
        assert forecast_card.is_visible()
        
        browser.close()
```

```powershell
.\.venv\Scripts\activate; pytest tests/integration/dashboard/ -v -s
```

---

### Task D: Implement Collapsible Parameter Panel

**Goal**: Move parameter controls to sticky collapsible panel

**Files to Create/Modify**:
- `ui/components.py` (add `create_parameter_panel`)
- `callbacks/settings.py` (modify for new panel)
- `assets/custom.css` (add sticky panel styles)

**Implementation** (see research.md section 3 for detailed design)

---

## Common Commands

### Running the Application

```powershell
# Development mode (hot reload)
.\.venv\Scripts\activate; python app.py

# Production mode
.\.venv\Scripts\activate; python app.py --port 8050
```

### Testing

```powershell
# Run all tests
.\.venv\Scripts\activate; pytest tests/ -v

# Run specific test file
.\.venv\Scripts\activate; pytest tests/unit/ui/test_dashboard.py -v

# Run with coverage
.\.venv\Scripts\activate; pytest --cov=ui --cov=callbacks --cov-report=html

# Run integration tests only
.\.venv\Scripts\activate; pytest tests/integration/ -v -s

# Run performance tests
.\.venv\Scripts\activate; pytest -k "performance" -v
```

### Code Quality

```powershell
# Format code (if black installed)
.\.venv\Scripts\activate; black ui/ callbacks/

# Lint (if pylint installed)
.\.venv\Scripts\activate; pylint ui/ callbacks/

# Type check (if mypy installed)
.\.venv\Scripts\activate; mypy ui/ callbacks/
```

### Git Workflow

```powershell
# Check current changes
git status
git diff

# Commit changes
git add ui/dashboard.py callbacks/dashboard.py
git commit -m "feat: add Dashboard tab with metrics cards"

# Push to remote
git push origin 006-ux-ui-redesign

# Pull latest changes
git pull origin 006-ux-ui-redesign
```

---

## Troubleshooting

### Issue: Import errors when running app

**Symptom**: `ModuleNotFoundError: No module named 'dash'`

**Solution**:
```powershell
# Verify virtual environment activated
.\.venv\Scripts\activate
python -c "import sys; print(sys.prefix)"

# Should show: C:\Development\burndown-chart\.venv

# If not, activate again and reinstall
.\.venv\Scripts\activate; pip install -r requirements.txt
```

### Issue: Tests fail with "No such file or directory"

**Symptom**: `FileNotFoundError` in tests

**Solution**:
```powershell
# Run tests from project root
cd c:\Development\burndown-chart
.\.venv\Scripts\activate; pytest tests/unit/ -v

# Verify pytest working directory
.\.venv\Scripts\activate; python -c "import os; print(os.getcwd())"
```

### Issue: Playwright browser not found

**Symptom**: `Executable doesn't exist` when running integration tests

**Solution**:
```powershell
# Install Playwright browsers
.\.venv\Scripts\activate; playwright install chromium

# If still fails, try system-wide install
playwright install chromium
```

### Issue: Port 8050 already in use

**Symptom**: `OSError: [WinError 10048] Only one usage of each socket address`

**Solution**:
```powershell
# Find process using port 8050
netstat -ano | findstr :8050

# Kill process (replace PID with actual process ID)
taskkill /PID <PID> /F

# Or use different port
.\.venv\Scripts\activate; python app.py --port 8051
```

---

## Best Practices

### Code Style

- Follow existing code conventions (PEP 8)
- Use type hints for function parameters and returns
- Write docstrings for all public functions
- Use design tokens, never hardcode colors/spacing
- Component IDs follow pattern: `{type}-{purpose}[-{suffix}]`

### Testing

- Write tests BEFORE implementing (TDD)
- Test happy path AND edge cases
- Mock external dependencies (file I/O, network calls)
- Use fixtures for reusable test data
- Integration tests verify complete user workflows

### Git Commits

- Use conventional commit format: `type: description`
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `style`
- Examples:
  - `feat: add Dashboard tab with metrics cards`
  - `fix: correct parameter panel collapse animation`
  - `test: add unit tests for dashboard callbacks`
  - `docs: update quickstart with dashboard implementation`

### Performance

- Keep callback execution under target times (see contracts/callbacks.md)
- Use client-side callbacks for UI-only state
- Cache expensive calculations
- Debounce user inputs (500ms default)

---

## Next Steps

After completing tasks:

1. **Code Review**: Create pull request against `006-ux-ui-redesign` branch
2. **Documentation**: Update relevant docs if behavior changed
3. **Manual Testing**: Run app and verify all workflows work
4. **Performance Check**: Run performance tests, verify no regression

---

## Resources

### Documentation

- **Feature Spec**: `specs/006-ux-ui-redesign/spec.md`
- **Technical Plan**: `specs/006-ux-ui-redesign/plan.md`
- **Research Decisions**: `specs/006-ux-ui-redesign/research.md`
- **Data Model**: `specs/006-ux-ui-redesign/data-model.md`
- **Component Contracts**: `specs/006-ux-ui-redesign/contracts/component-builders.md`
- **Callback Contracts**: `specs/006-ux-ui-redesign/contracts/callbacks.md`

### External Resources

- **Dash Documentation**: https://dash.plotly.com/
- **Dash Bootstrap Components**: https://dash-bootstrap-components.opensource.faculty.ai/
- **Plotly**: https://plotly.com/python/
- **Playwright Python**: https://playwright.dev/python/
- **pytest**: https://docs.pytest.org/

### Project Guidelines

- **Copilot Instructions**: `.github/copilot-instructions.md`
- **Mobile-First Design**: See copilot-instructions.md
- **Testing Strategy**: See copilot-instructions.md "Modern Testing Strategy"
- **Component Architecture**: See copilot-instructions.md "Atomic Design System"

---

## Contact & Support

- **Repository**: https://github.com/niksavis/burndown-chart
- **Issues**: Create GitHub issue with `006-ux-ui-redesign` label
- **Questions**: Tag team members in pull request comments

---

**Last Updated**: 2025-10-23  
**Feature Branch**: `006-ux-ui-redesign`
