# Burndown Chart Generator - Development Best Practices

## Project Vision

Modern, mobile-first web application for agile project forecasting that prioritizes usability, performance, and intuitive user interactions across all devices.

## Modern Web App Principles

### Mobile-First Design Strategy

**Priority Order**: Mobile → Tablet → Desktop

- Design all components for mobile screens first (320px+)
- Use progressive enhancement for larger screens
- Optimize touch interactions and gesture support
- Ensure all features work on mobile without degradation

### User Experience Excellence

**Core UX Principles**:

1. **Immediate Value**: Users should see meaningful data within 3 seconds
2. **Minimal Cognitive Load**: Reduce clicks, forms, and complex interactions
3. **Progressive Disclosure**: Show essential info first, details on demand
4. **Contextual Help**: Just-in-time guidance, not overwhelming documentation

### Performance-First Architecture

**Critical Performance Targets**:

- Initial page load: < 2 seconds
- Chart rendering: < 500ms
- User interactions: < 100ms response time
- Mobile data usage: Minimize API calls and payload size

```python
# Performance pattern: Lazy load heavy components
from dash import callback, Output, Input
from dash.exceptions import PreventUpdate
from visualization.charts import create_forecast_plot

@callback(Output("chart", "figure"), Input("tab", "active_tab"))
def load_chart_on_demand(active_tab):
    if active_tab != "chart-tab":
        raise PreventUpdate  # Don't render until needed
    # Example data and settings - replace with actual data loading logic
    data = {"x": [1, 2, 3], "y": [1, 4, 2]}
    settings = {"title": "Forecast Chart"}
    return create_forecast_plot(data, settings)  # Use actual function from visualization module
```

## Modern Component Architecture

### Atomic Design System

**Component Hierarchy**:

1. **Atoms**: Basic UI elements (buttons, inputs, icons)
2. **Molecules**: Simple component groups (input with label, card headers)
3. **Organisms**: Complex UI sections (charts, data tables, forms)
4. **Templates**: Page layouts and navigation patterns

```python
# Example: Atomic component with consistent props
from dash import html
import dash_bootstrap_components as dbc

def create_action_button(text, icon, action_type="primary", size="md", **kwargs):
    return dbc.Button(
        [html.I(className=f"fas fa-{icon} me-2"), text],
        color=action_type,  # Use Bootstrap color names directly
        size=size,
        className=f"action-btn action-btn-{action_type}",
        **kwargs
    )
```

### State Management Optimization

**Modern State Patterns**:

- Use `dcc.Store` for client-side caching and reduce server round-trips
- Implement optimistic updates for better perceived performance
- Batch related state updates to minimize re-renders

```python
# Optimized state management
import time
from dash import Dash, callback, Output, Input

app = Dash(__name__)

@callback(
    [Output("data-store", "data"), Output("ui-state", "data")],
    Input("user-action", "n_clicks"),
    prevent_initial_call=True
)
def handle_user_action(n_clicks):
    # Batch multiple state updates
    new_data = {"processed_items": n_clicks or 0}  # Example data structure
    return new_data, {"loading": False, "last_update": time.time()}
```

## Development Workflows

**Windows Development Environment**: PowerShell with virtual environment activation required.

### ⚠️ **CRITICAL: PowerShell-Only Commands**

**ALWAYS use PowerShell commands** - this is a Windows development environment. Unix/Linux commands like `find`, `grep`, `ls`, `cat`, etc. will NOT work.

**PowerShell Equivalents for Common Tasks:**

```powershell
# File operations (NOT find, ls, cat)
Get-ChildItem -Recurse -Filter "*.py" | Select-Object -First 20    # Instead of: find . -name "*.py" | head -20
Get-Content "file.txt" | Select-Object -First 10                   # Instead of: head -10 file.txt
Get-ChildItem -Path "src/" -Recurse                                # Instead of: ls -la src/
Get-Content "file.txt" | Where-Object { $_ -match "pattern" }      # Instead of: grep "pattern" file.txt

# Process and system info
Get-Process | Where-Object { $_.ProcessName -like "*python*" }     # Instead of: ps aux | grep python
Get-Location                                                        # Instead of: pwd
Set-Location "path"                                                # Instead of: cd path

# File content and manipulation
Get-Content "file.txt" | Measure-Object -Line                     # Instead of: wc -l file.txt
Select-String -Path "*.py" -Pattern "function"                     # Instead of: grep -r "function" *.py
```

### ⚠️ **CRITICAL: Virtual Environment Activation**

**ALWAYS prefix Python commands with virtual environment activation** - this is a Windows development environment that requires the virtual environment to be activated for EVERY new terminal window.

**Required Pattern**: `.\.venv\Scripts\activate; [command]`

**Why this is critical**:

- Global Python instance lacks required packages
- Virtual environment contains all project dependencies
- Each new terminal window needs activation
- Forgetting this causes import errors and missing dependencies

### Essential Commands

```powershell
# Run application with hot reload (ALWAYS activate venv first)
.\.venv\Scripts\activate; python app.py

# Run tests by category (current test structure)
.\.venv\Scripts\activate; pytest tests/unit/ -v
.\.venv\Scripts\activate; pytest tests/integration/ -v
.\.venv\Scripts\activate; pytest tests/ -k "performance" -v

# Performance profiling
.\.venv\Scripts\activate; pytest --cov=ui --cov=visualization --durations=10

# Any Python command pattern:
.\.venv\Scripts\activate; python -c "import dash; print('Dependencies loaded')"
.\.venv\Scripts\activate; pip list
.\.venv\Scripts\activate; python -m pytest --version
```

### Modern Callback Patterns

**Best Practices**:

1. **Debounced Inputs**: Prevent excessive API calls on user typing
2. **Loading States**: Always show feedback during async operations
3. **Error Boundaries**: Graceful failure handling with user-friendly messages
4. **Accessibility**: Proper ARIA labels and keyboard navigation

```python
# Modern callback with UX optimizations
from dash import Dash, callback, Output, Input, State, html, no_update

app = Dash(__name__)

@callback(
    [Output("results", "children"), Output("loading", "is_open")],
    Input("search", "value"),
    State("debounce-timer", "data"),
    prevent_initial_call=True
)
def search_with_debounce(search_value, timer_data):
    # Implement debouncing for better UX
    if len(search_value) < 3:
        return html.Div("Type at least 3 characters..."), False

    # Show loading immediately
    return no_update, True
```

### 🔧 **Setting Up Unix-Like Tools (Optional)**

If you need Unix-like commands for advanced development workflows, you can install one of these options:

**Option 1: Windows Subsystem for Linux (WSL)**

```powershell
# Enable WSL (requires admin privileges)
wsl --install
# Then use: wsl find . -name "*.py" | head -20
```

**Option 2: Git Bash (comes with Git for Windows)**

```bash
# Use Git Bash terminal instead of PowerShell
find . -name "*.py" -type f | head -20
grep -r "function" --include="*.py" .
```

**Option 3: PowerShell with Unix-like aliases**

```powershell
# Add to your PowerShell profile
Set-Alias grep Select-String
Set-Alias ls Get-ChildItem
Set-Alias cat Get-Content
```

**Recommended**: Stick with native PowerShell commands for consistency and reliability.

### Modern Testing Strategy

**User-Centric Test Pyramid**:

- **Unit Tests**: Component behavior and data transformations
- **Integration Tests**: User workflows and API interactions
- **Visual Tests**: Mobile responsiveness and accessibility
- **Performance Tests**: Load times and interaction latency

#### ⚡ **Browser Automation: Playwright vs Selenium**

**CRITICAL DECISION**: Always prefer Playwright over Selenium for new integration tests.

**What Actually Works**:

✅ **Playwright IS better than Selenium**:

- **Faster execution**: ~3x faster test runs due to modern browser automation
- **Better API**: Async/await support, cleaner syntax, built-in waiting
- **More reliable**: Better element detection, reduced flakiness
- **Modern browsers**: Native support for Chromium, Firefox, WebKit

✅ **We CAN use Playwright with Dash apps**:

- **Avoid Dash testing utilities**: `dash.testing.application_runners` requires Selenium
- **Use direct app import**: Import app directly and serve with waitress/Flask
- **Text-based selectors**: Use `has_text()` instead of dynamic React IDs
- **Custom server management**: Start server in background thread for testing

**Implementation Pattern**:

```python
# ✅ RECOMMENDED: Modern Playwright approach
import pytest
from playwright.sync_api import sync_playwright
import waitress
import threading
import sys
import os

# Import app directly (avoid dash.testing utilities)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
import app as dash_app

class TestModernIntegration:
    @pytest.fixture(scope="class")
    def live_server(self):
        """Start Dash app server for testing"""
        app = dash_app.app

        def run_server():
            waitress.serve(app.server, host="127.0.0.1", port=8051, threads=1)

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        time.sleep(3)  # Allow server startup

        yield "http://127.0.0.1:8051"

    def test_with_playwright(self, live_server):
        """Modern browser automation test"""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(live_server)
            page.wait_for_selector("#chart-tabs", timeout=10000)

            # Use text-based selectors (more reliable than dynamic IDs)
            tab_links = page.locator("#chart-tabs .nav-link")
            items_tab = tab_links.filter(has_text="Items per Week")

            items_tab.click()
            page.wait_for_timeout(2000)

            # Verify state with null-safe attribute checking
            items_class = items_tab.get_attribute("class") or ""
            assert "active" in items_class

            browser.close()
```

**Why NOT to use Selenium**:

❌ **Selenium Dependencies**: Dash's `testing.application_runners` imports selenium even when not needed
❌ **Slower execution**: Legacy WebDriver protocol causes performance overhead  
❌ **Flakier tests**: More prone to timing issues and element detection failures
❌ **Complex setup**: Requires WebDriver management and browser configuration

**Migration Strategy**: For existing selenium tests, gradually migrate to Playwright using the pattern above.

```python
# Example: Mobile-first component test
def test_chart_mobile_responsiveness():
    # Test component at various viewport sizes
    test_data = [{"x": [1, 2, 3], "y": [1, 4, 2]}]
    for width in [320, 768, 1024, 1440]:
        chart = create_mobile_optimized_chart(test_data, viewport_size="mobile" if width < 768 else "desktop")
        assert chart.figure is not None
        assert chart.config["responsive"] is True
```

## Test Automation Guidelines

### Test Structure Organization

**Directory Structure** (Current):

```
tests/
├── unit/           # Fast, isolated component tests
│   ├── ui/         # UI component tests (currently exists)
│   ├── visualization/  # Chart and data visualization tests
│   └── data/       # Data processing and persistence tests
├── integration/    # End-to-end workflow tests (currently exists)
│   ├── jira/       # JIRA API integration tests
│   └── dashboard/  # Full dashboard workflow tests
└── utils/          # Test helpers and fixtures (currently exists)
```

**Note**: Performance and accessibility tests should be added to existing directories or marked with pytest markers.

### Unit Testing Standards

**Component Testing Approach**:

- Test components in isolation with mocked dependencies
- Verify both happy path and edge cases
- Include mobile viewport testing for UI components
- Test keyboard navigation and accessibility features

```python
import pytest
from dash.testing.application_runners import import_app

class TestUIComponents:
    """Test UI components with mobile-first approach"""

    @pytest.fixture
    def dash_app(self):
        app = import_app("app")
        return app

    def test_button_accessibility(self, dash_app):
        """Test button meets accessibility standards"""
        button = create_action_button("Save", "save", "primary")

        # Test ARIA attributes
        assert button.get("aria-label")
        assert button.get("role") == "button"

        # Test keyboard navigation
        assert button.get("tabIndex") is not None

    def test_mobile_touch_targets(self):
        """Ensure touch targets meet 44px minimum"""
        button = create_action_button("Delete", "trash")

        # Verify minimum touch target size
        assert button.size >= 44  # pixels
        assert button.has_adequate_spacing()

    @pytest.mark.parametrize("viewport_width", [320, 768, 1024, 1440])
    def test_responsive_layout(self, viewport_width):
        """Test component responsiveness across viewports"""
        component = create_responsive_component()
        component.set_viewport_width(viewport_width)

        assert component.is_readable()
        assert component.maintains_functionality()
```

### Integration Testing Standards

**Workflow Testing**:

- Test complete user journeys from start to finish
- Verify data flows between components
- Test JIRA integration with real API calls (mocked in CI)
- Validate chart rendering and interactions

**Browser Automation Guidelines**:

- ✅ **Use Playwright** for all new integration tests requiring browser automation
- ✅ **Text-based selectors** (`has_text()`) for reliable element targeting
- ✅ **Custom server management** to avoid Dash testing utility dependencies
- ✅ **Null-safe attribute checking** (`get_attribute("class") or ""`) for robust assertions
- ❌ **Avoid Selenium** unless specifically required for legacy compatibility

```python
class TestDashboardWorkflows:
    """Test complete user workflows"""

    def test_jira_data_import_workflow(self, dash_duo):
        """Test complete JIRA import process"""
        app = import_app("app")
        dash_duo.start_server(app)

        # Step 1: Configure JIRA settings
        dash_duo.find_element("#jira-url").send_keys("https://test.jira.com")
        dash_duo.find_element("#jira-token").send_keys("test-token")
        dash_duo.find_element("#jira-jql-query").send_keys("project = TEST")

        # Step 2: Import data
        dash_duo.find_element("#update-data-unified").click()

        # Step 3: Verify data loaded
        dash_duo.wait_for_text_to_equal("#jira-cache-status", "Data loaded", timeout=10)

        # Step 4: Verify charts render
        chart_element = dash_duo.find_element("#forecast-graph")
        assert chart_element.is_displayed()

    def test_mobile_navigation_workflow(self, dash_duo):
        """Test mobile navigation and interactions"""
        app = import_app("app")
        dash_duo.start_server(app)

        # Set mobile viewport
        dash_duo.driver.set_window_size(375, 667)  # iPhone size

        # Test tab navigation on mobile
        tabs = dash_duo.find_elements(".nav-tabs-modern .nav-link")
        for tab in tabs:
            tab.click()
            # Verify content loads and is readable
            assert dash_duo.find_element("#tab-content").is_displayed()
```

### Performance Testing Standards

**Load Time Validation**:

- Test initial page load < 2 seconds
- Chart rendering < 500ms
- User interactions < 100ms response time
- Memory usage monitoring

```python
import time
import pytest
from selenium.webdriver.common.action_chains import ActionChains

class TestPerformance:
    """Performance testing with specific targets"""

    def test_initial_page_load_time(self, dash_duo):
        """Test page loads within 2 seconds"""
        start_time = time.time()

        app = import_app("app")
        dash_duo.start_server(app)

        # Wait for critical elements to load
        dash_duo.wait_for_element("#chart-tabs", timeout=5)

        load_time = time.time() - start_time
        assert load_time < 2.0, f"Page load took {load_time:.2f}s, target: < 2.0s"

    def test_chart_rendering_speed(self, dash_duo):
        """Test chart renders within 500ms"""
        app = import_app("app")
        dash_duo.start_server(app)

        # Trigger chart render
        start_time = time.time()
        dash_duo.find_element("#tab-burndown").click()

        # Wait for chart to appear
        dash_duo.wait_for_element("#forecast-graph .plotly-graph-div svg", timeout=2)

        render_time = time.time() - start_time
        assert render_time < 0.5, f"Chart render took {render_time:.2f}s, target: < 0.5s"

    def test_interaction_responsiveness(self, dash_duo):
        """Test UI interactions respond within 100ms"""
        app = import_app("app")
        dash_duo.start_server(app)

        button = dash_duo.find_element("#add-row-button")

        start_time = time.time()
        button.click()

        # Wait for UI feedback
        dash_duo.wait_for_element(".loading-spinner", timeout=1)

        response_time = time.time() - start_time
        assert response_time < 0.1, f"Interaction took {response_time:.2f}s, target: < 0.1s"
```

### Accessibility Testing Standards

**WCAG 2.1 AA Compliance**:

- Color contrast validation
- Keyboard navigation testing
- Screen reader compatibility
- Focus management

```python
class TestAccessibility:
    """Accessibility compliance testing"""

    def test_wcag_compliance(self, dash_duo):
        """Test WCAG 2.1 AA compliance"""
        app = import_app("app")
        dash_duo.start_server(app)

        # Test basic accessibility requirements
        # Check for proper heading structure
        headings = dash_duo.find_elements("h1, h2, h3, h4, h5, h6")
        assert len(headings) > 0, "Page should have proper heading structure"

        # Check for alt text on images
        images = dash_duo.find_elements("img")
        for img in images:
            assert img.get_attribute("alt") is not None, "Images should have alt text"

    def test_keyboard_navigation(self, dash_duo):
        """Test complete keyboard navigation"""
        app = import_app("app")
        dash_duo.start_server(app)

        # Test tab order through interactive elements
        interactive_elements = dash_duo.find_elements("[tabindex]")

        for element in interactive_elements:
            element.send_keys("\t")  # Tab to element
            assert element == dash_duo.driver.switch_to.active_element

    def test_screen_reader_labels(self, dash_duo):
        """Test screen reader compatibility"""
        app = import_app("app")
        dash_duo.start_server(app)

        # Verify ARIA labels exist
        buttons = dash_duo.find_elements("button")
        for button in buttons:
            assert button.get_attribute("aria-label") or button.text

        # Verify form labels
        inputs = dash_duo.find_elements("input")
        for input_elem in inputs:
            input_id = input_elem.get_attribute("id")
            if input_id:
                label = dash_duo.find_element(f"label[for='{input_id}']")
                assert label.is_displayed()
```

### Test Execution Patterns

**Continuous Integration**:

```powershell
# Run full test suite with coverage
.\.venv\Scripts\activate; pytest --cov=ui --cov=visualization --cov=data --cov-report=html --durations=10

# Run specific test categories
.\.venv\Scripts\activate; pytest tests/unit/ -v                    # Fast unit tests
.\.venv\Scripts\activate; pytest tests/integration/ -v -s         # Integration tests

# Run tests by functionality
.\.venv\Scripts\activate; pytest -k "performance" -v              # Performance-related tests
.\.venv\Scripts\activate; pytest -k "mobile or responsive" -v     # Mobile/responsive tests

# Run with specific markers
.\.venv\Scripts\activate; pytest -m "slow" -v                     # Long-running tests
.\.venv\Scripts\activate; pytest -m "not slow" -v                 # Quick tests only
```

**Test Data Management**:

- Use fixtures for reusable test data
- Mock external API calls in unit tests
- Use real data samples for integration tests
- Clean up test data after each test

```python
@pytest.fixture
def sample_statistics_data():
    """Provide consistent test data"""
    return [
        {"date": "2025-01-01", "completed_items": 5, "completed_points": 25},
        {"date": "2025-01-08", "completed_items": 7, "completed_points": 35},
        {"date": "2025-01-15", "completed_items": 4, "completed_points": 20},
    ]

@pytest.fixture
def mock_jira_response():
    """Mock JIRA API responses for consistent testing"""
    return {
        "issues": [
            {
                "key": "TEST-1",
                "fields": {
                    "created": "2025-01-01T10:00:00.000Z",
                    "status": {"name": "Done"},
                    "customfield_10002": 5  # Story points
                }
            }
        ]
    }
```

## User Experience Patterns

### Progressive Web App Features

**Essential PWA Elements**:

- Responsive design with fluid typography
- Touch-optimized interactions (44px minimum touch targets)
- Offline capability for cached data
- Fast loading with skeleton screens

### Information Architecture

**Content Strategy**:

- **Primary Actions**: Most important user tasks prominently displayed
- **Secondary Info**: Available via progressive disclosure
- **Context-Sensitive Help**: Tooltips that appear when needed
- **Error Prevention**: Validation before user commits to actions

```python
# Example: Mobile-optimized form validation
from dash import html
import dash_bootstrap_components as dbc

def create_smart_form_field(field_name, validation_rules):
    return dbc.InputGroup([
        dbc.Input(
            id=f"{field_name}-input",
            placeholder=f"Enter {field_name.replace('_', ' ')}",
            valid=True,  # Start with positive feedback
        ),
        dbc.InputGroupText(
            html.I(className="fas fa-check-circle text-success"),
            id=f"{field_name}-feedback"
        )
    ])
```

### Responsive Data Visualization

**Chart Optimization Principles**:

- **Mobile-First Charts**: Readable on small screens without zooming
- **Touch Interactions**: Pinch-to-zoom, swipe navigation
- **Performance**: Lazy loading for complex visualizations
- **Accessibility**: Screen reader compatible, keyboard navigable

```python
# Modern chart with mobile optimization
from dash import dcc

def create_mobile_optimized_chart(data, viewport_size="mobile"):
    config = {
        "displayModeBar": viewport_size != "mobile",
        "responsive": True,
        "scrollZoom": True,  # Enable mobile-friendly zooming
        "doubleClick": "reset+autosize"
    }

    layout = {
        "font": {"size": 12 if viewport_size == "mobile" else 14},
        "margin": {"t": 20, "r": 10, "b": 40, "l": 40},  # Tight margins for mobile
        "showlegend": viewport_size != "mobile"  # Hide legend on mobile
    }

    return dcc.Graph(figure={"data": data, "layout": layout}, config=config)
```

## Technical Implementation Guidelines

### Data Architecture Best Practices

**Client-Side State Management**:

- Minimize server round-trips with smart caching
- Use `dcc.Store` for temporary UI state only
- Implement proper loading states for all async operations

```python
# Efficient data loading pattern
from dash import callback, Output, Input
from data.processing import load_statistics

@callback(
    Output("chart-data", "data"),
    Input("data-refresh", "n_clicks"),
    background=True,  # Non-blocking for better UX
    prevent_initial_call=True
)
def load_chart_data_async(n_clicks):
    return load_statistics()  # Use actual function from data module
```

### Simple Caching Strategy

**JSON File Persistence with Caching**:

```python
# Simple file-based caching matching current architecture
import os
import json
import time
from data.jira_simple import fetch_all_issues

def get_cached_jira_data(force_refresh=False):
    """Get JIRA data with simple file caching."""
    cache_file = "jira_cache.json"

    if not force_refresh and os.path.exists(cache_file):
        # Check cache age
        cache_age = time.time() - os.path.getmtime(cache_file)
        if cache_age < 3600:  # 1 hour cache
            with open(cache_file, 'r') as f:
                return json.load(f)

    # Fetch fresh data and cache it
    fresh_data = fetch_all_issues()  # Use actual JIRA function
    with open(cache_file, 'w') as f:
        json.dump(fresh_data, f, indent=2)

    return fresh_data
```

### Data Validation

**Basic Schema Validation**:

```python
# Simple data validation matching current schema
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def validate_project_data(data: Dict[str, Any]) -> bool:
    """Validate basic project data structure."""
    required_keys = ["project_scope", "statistics", "metadata"]

    for key in required_keys:
        if key not in data:
            logger.error(f"Missing required key: {key}")
            return False

    # Validate statistics structure
    if not isinstance(data["statistics"], list):
        logger.error("Statistics must be a list")
        return False

    return True
```

### Error Handling Patterns

**User-Friendly Error Management**:

```python
# Basic error handling with user feedback
import logging
from dash import callback, Output, Input, html
from data.schema import validate_project_data

logger = logging.getLogger(__name__)

@callback(Output("error-display", "children"), Input("data-input", "value"))
def handle_data_input_with_errors(data_input):
    try:
        validated_data = validate_project_data(data_input)  # Use actual validation function
        return html.Div("Data loaded successfully", className="alert alert-success")
    except ValueError as e:
        logger.warning(f"Data validation failed: {e}")
        return html.Div("Please check your data format and try again.", className="alert alert-danger")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return html.Div("Something went wrong. Please try again.", className="alert alert-danger")
```

### Health Checks

**Basic Application Health**:

```python
# Simple health check function
import json
import requests
from datetime import datetime
from configuration.settings import get_jira_settings

def check_application_health():
    """Basic health check for the application."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "checks": {}
    }

    # Check if data files are accessible
    try:
        with open("project_data.json", 'r') as f:
            json.load(f)
        health_status["checks"]["data_files"] = "OK"
    except Exception as e:
        health_status["checks"]["data_files"] = f"ERROR: {e}"
        health_status["status"] = "unhealthy"

    # Check JIRA connectivity (if configured)
    jira_settings = get_jira_settings()
    jira_endpoint = jira_settings.get("jira_url") if jira_settings else None
    if jira_endpoint:
        try:
            response = requests.get(f"{jira_endpoint}/rest/api/2/serverInfo", timeout=10)
            health_status["checks"]["jira_api"] = "OK" if response.status_code == 200 else "ERROR"
        except Exception as e:
            health_status["checks"]["jira_api"] = f"ERROR: {e}"

    return health_status
```

## Accessibility Considerations

### Basic WCAG Compliance

**Essential Accessibility Patterns**:

```python
# Basic accessibility utilities
from dash import html, dcc
import dash_bootstrap_components as dbc
from typing import Dict

def create_accessible_button(text: str, icon: str, **kwargs):
    """Create button with basic accessibility support."""
    return dbc.Button(
        [html.I(className=f"fas fa-{icon} me-2"), text],
        **{
            "aria-label": kwargs.get("aria_label", text),
            "role": "button",
            **kwargs
        }
    )

def create_accessible_chart(figure_data: Dict, title: str):
    """Create chart with accessibility attributes."""
    return dcc.Graph(
        figure=figure_data,
        **{
            "aria-label": title,
            "role": "img"
        }
    )
```

## Documentation Guidelines

**Markdown**: Use standard markdown syntax. The `.markdownlint.json` config disables problematic rules for Copilot-generated content.
