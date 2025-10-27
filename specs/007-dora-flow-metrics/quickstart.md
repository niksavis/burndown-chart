# Quickstart Guide: DORA and Flow Metrics Dashboard

**Feature**: `007-dora-flow-metrics`  
**For**: Developers implementing the DORA and Flow Metrics feature  
**Updated**: 2025-10-27

## 🎯 What You're Building

A comprehensive metrics dashboard that displays:
- **4 DORA Metrics**: Deployment Frequency, Lead Time for Changes, Change Failure Rate, Mean Time to Recovery
- **5 Flow Metrics**: Velocity, Time, Efficiency, Load, Distribution
- **Field Mapping Configuration**: UI for mapping Jira custom fields to metric calculation fields
- **Performance Tier Indicators**: Elite/High/Medium/Low benchmarking for DORA metrics
- **Time Period Selection**: 7d, 30d, 90d, or custom date range

## 🏗️ Architecture Overview

```
User Interaction → Callback (event handling) → Data Layer (business logic) → Jira API / Cache
                        ↓                            ↓                              ↓
                  UI Components                Charts/Metrics              Persistence (JSON)
```

**Key Principle**: Callbacks ONLY handle events and delegate to data layer. NO business logic in callbacks.

## 📁 File Structure

```
callbacks/
├── dora_flow_metrics.py     # NEW: Tab navigation, metric display callbacks
└── field_mapping.py          # NEW: Field mapping modal callbacks

data/
├── dora_calculator.py        # NEW: DORA metric calculations
├── flow_calculator.py        # NEW: Flow metric calculations
├── field_mapper.py           # NEW: Field mapping validation and persistence
└── metrics_cache.py          # NEW: Metric caching with TTL

ui/
├── dora_metrics_dashboard.py    # NEW: DORA metrics UI components
├── flow_metrics_dashboard.py    # NEW: Flow metrics UI components
├── field_mapping_modal.py       # NEW: Field mapping configuration modal
└── metric_cards.py              # NEW: Reusable metric card component

visualization/
├── dora_charts.py            # NEW: DORA-specific charts
└── flow_charts.py            # NEW: Flow-specific charts

configuration/
├── dora_config.py            # NEW: DORA benchmarks and definitions
└── flow_config.py            # NEW: Flow metric definitions

tests/
├── unit/data/
│   ├── test_dora_calculator.py
│   ├── test_flow_calculator.py
│   ├── test_field_mapper.py
│   └── test_metrics_cache.py
└── integration/
    ├── test_dora_flow_workflow.py
    └── test_field_mapping_workflow.py
```

## 🚀 Implementation Steps

### Phase 1: Configuration & Data Layer (Days 1-3)

#### 1.1 DORA Configuration (`configuration/dora_config.py`)

```python
"""DORA metric definitions and performance benchmarks"""

DORA_BENCHMARKS = {
    "deployment_frequency": {
        "elite": {"threshold": 1, "unit": "deployments/day", "color": "green"},
        "high": {"threshold": 1, "unit": "deployments/week", "color": "yellow"},
        "medium": {"threshold": 1, "unit": "deployments/month", "color": "orange"},
        "low": {"threshold": 0.17, "unit": "deployments/month", "color": "red"},  # ~1 per 6 months
    },
    "lead_time_for_changes": {
        "elite": {"threshold": 0.04, "unit": "days", "color": "green"},  # < 1 hour
        "high": {"threshold": 7, "unit": "days", "color": "yellow"},
        "medium": {"threshold": 30, "unit": "days", "color": "orange"},
        "low": {"threshold": 180, "unit": "days", "color": "red"},
    },
    # ... add other metrics
}

def determine_performance_tier(metric_name: str, value: float) -> dict:
    """Determine performance tier for a DORA metric"""
    # Implementation here
```

#### 1.2 Field Mapper (`data/field_mapper.py`)

```python
"""Jira custom field mapping logic"""

from typing import Dict, Optional, Tuple
from data.persistence import load_app_settings, save_app_settings
from data.jira_simple import get_jira_config
import requests
import hashlib
import json

def fetch_available_jira_fields() -> list:
    """Fetch all fields from Jira instance"""
    config = get_jira_config()
    response = requests.get(
        f"{config['api_endpoint']}/field",
        headers={"Authorization": f"Bearer {config['token']}"}
    )
    return response.json()

def validate_field_mapping(internal_field: str, jira_field_id: str, field_metadata: dict) -> Tuple[bool, Optional[str]]:
    """Validate that Jira field type matches required internal field type"""
    # Implementation: Check type compatibility
    pass

def save_field_mappings(mappings: dict) -> bool:
    """Save field mappings to app_settings.json"""
    settings = load_app_settings()
    settings["dora_flow_config"] = mappings
    save_app_settings(settings)
    return True

def get_field_mappings_hash() -> str:
    """Calculate MD5 hash of current field mappings for cache invalidation"""
    settings = load_app_settings()
    mappings_str = json.dumps(settings.get("dora_flow_config", {}), sort_keys=True)
    return hashlib.md5(mappings_str.encode()).hexdigest()[:8]
```

**Test**: `tests/unit/data/test_field_mapper.py`

#### 1.3 Metrics Cache (`data/metrics_cache.py`)

```python
"""Metrics calculation caching with TTL"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional, Dict

CACHE_FILE = "metrics_cache.json"
CACHE_VERSION = "1.0"
MAX_ENTRIES = 100
DEFAULT_TTL_SECONDS = 3600

def generate_cache_key(metric_type: str, start_date: str, end_date: str, field_hash: str) -> str:
    """Generate unique cache key"""
    return f"{metric_type}_{start_date}_{end_date}_{field_hash}"

def load_cached_metrics(cache_key: str) -> Optional[Dict]:
    """Load metrics from cache if valid"""
    if not os.path.exists(CACHE_FILE):
        return None
    
    with open(CACHE_FILE, 'r') as f:
        cache = json.load(f)
    
    if cache_key not in cache.get("entries", {}):
        return None
    
    entry = cache["entries"][cache_key]
    expires_at = datetime.fromisoformat(entry["expires_at"])
    
    if datetime.utcnow() > expires_at:
        return None  # Expired
    
    return entry["metrics"]

def save_cached_metrics(cache_key: str, metrics: Dict, ttl_seconds: int = DEFAULT_TTL_SECONDS):
    """Save calculated metrics to cache"""
    # Implementation: Load existing cache, add entry, enforce max size, save
    pass

def invalidate_cache():
    """Clear all cache entries"""
    if os.path.exists(CACHE_FILE):
        os.remove(CACHE_FILE)
```

**Test**: `tests/unit/data/test_metrics_cache.py` (MUST use `tempfile.NamedTemporaryFile` for isolation)

#### 1.4 DORA Calculator (`data/dora_calculator.py`)

```python
"""DORA metrics calculation logic"""

from typing import List, Dict, Optional, Tuple
from datetime import datetime
from configuration.dora_config import determine_performance_tier
import pandas as pd

def calculate_deployment_frequency(
    issues: List[Dict],
    field_mappings: Dict,
    time_period: Tuple[datetime, datetime]
) -> Dict:
    """
    Calculate Deployment Frequency metric.
    
    Returns:
        {
            "metric_name": "deployment_frequency",
            "value": 45.2,
            "unit": "deployments/month",
            "performance_tier": "High",
            "error_state": "success",
            ...
        }
    """
    # Validate field mappings
    deployment_date_field = field_mappings.get("dora", {}).get("deployment_date")
    if not deployment_date_field:
        return {
            "metric_name": "deployment_frequency",
            "value": None,
            "error_state": "missing_mapping",
            "error_message": "Configure 'Deployment Date' field mapping"
        }
    
    # Filter valid issues
    valid_issues = [i for i in issues if deployment_date_field in i.get("fields", {})]
    
    if not valid_issues:
        return {
            "metric_name": "deployment_frequency",
            "value": None,
            "error_state": "no_data",
            "error_message": "No deployments found in time period"
        }
    
    # Calculate metric
    start, end = time_period
    period_days = (end - start).days
    value = len(valid_issues) / (period_days / 30)  # Per month
    
    # Determine performance tier
    tier_info = determine_performance_tier("deployment_frequency", value)
    
    return {
        "metric_name": "deployment_frequency",
        "value": value,
        "unit": "deployments/month",
        "performance_tier": tier_info["tier"],
        "performance_tier_color": tier_info["color"],
        "error_state": "success",
        "error_message": None,
        "excluded_issue_count": len(issues) - len(valid_issues),
        "total_issue_count": len(issues),
        "details": tier_info["details"]
    }

# Similar functions for other DORA metrics:
# - calculate_lead_time_for_changes()
# - calculate_change_failure_rate()
# - calculate_mean_time_to_recovery()

def calculate_all_dora_metrics(issues: List[Dict], field_mappings: Dict, time_period: Tuple) -> Dict:
    """Calculate all four DORA metrics"""
    return {
        "deployment_frequency": calculate_deployment_frequency(issues, field_mappings, time_period),
        "lead_time_for_changes": calculate_lead_time_for_changes(issues, field_mappings, time_period),
        "change_failure_rate": calculate_change_failure_rate(issues, field_mappings, time_period),
        "mean_time_to_recovery": calculate_mean_time_to_recovery(issues, field_mappings, time_period),
    }
```

**Test**: `tests/unit/data/test_dora_calculator.py` - Parametrized tests for edge cases

#### 1.5 Flow Calculator (`data/flow_calculator.py`)

Similar structure to DORA calculator, implementing:
- `calculate_flow_velocity()`
- `calculate_flow_time()`
- `calculate_flow_efficiency()`
- `calculate_flow_load()`
- `calculate_flow_distribution()`
- `calculate_all_flow_metrics()`

**Test**: `tests/unit/data/test_flow_calculator.py`

### Phase 2: UI Components (Days 4-6)

#### 2.1 Metric Card Component (`ui/metric_cards.py`)

```python
"""Reusable metric card component"""

import dash_bootstrap_components as dbc
from dash import html

def create_metric_card(metric_data: dict) -> dbc.Card:
    """
    Create a metric display card.
    
    Args:
        metric_data: Dictionary with metric_name, value, unit, performance_tier, error_state
    
    Returns:
        Dash Bootstrap Card component
    """
    if metric_data["error_state"] != "success":
        # Error state card
        return dbc.Card([
            dbc.CardHeader(metric_data["metric_name"].replace("_", " ").title()),
            dbc.CardBody([
                html.I(className="fas fa-exclamation-triangle fa-3x text-warning"),
                html.P(metric_data["error_message"], className="mt-3"),
                dbc.Button("Configure Mappings", id="open-field-mapping-modal", color="primary")
            ])
        ])
    
    # Success state card
    tier_color_map = {"green": "success", "yellow": "warning", "orange": "warning", "red": "danger"}
    color = tier_color_map.get(metric_data["performance_tier_color"], "secondary")
    
    return dbc.Card([
        dbc.CardHeader([
            html.Span(metric_data["metric_name"].replace("_", " ").title()),
            dbc.Badge(
                metric_data["performance_tier"],
                color=color,
                className="float-end"
            )
        ]),
        dbc.CardBody([
            html.H2(f"{metric_data['value']:.1f}", className="text-center"),
            html.P(metric_data["unit"], className="text-muted text-center"),
            html.Small(f"Based on {metric_data['total_issue_count']} issues", className="text-muted")
        ])
    ], className="metric-card mb-3")
```

**Test**: `tests/unit/ui/test_metric_cards.py` - Verify rendering for success and error states

#### 2.2 DORA Dashboard (`ui/dora_metrics_dashboard.py`)

```python
"""DORA metrics dashboard UI"""

import dash_bootstrap_components as dbc
from dash import html, dcc
from ui.metric_cards import create_metric_card

def create_dora_dashboard() -> dbc.Container:
    """Create DORA metrics dashboard layout"""
    return dbc.Container([
        dbc.Row([
            dbc.Col([
                html.H3("DORA Metrics"),
                html.P("DevOps Research and Assessment performance indicators")
            ], width=8),
            dbc.Col([
                dbc.Button(
                    [html.I(className="fas fa-cog me-2"), "Configure Mappings"],
                    id="open-dora-field-mapping",
                    color="primary"
                )
            ], width=4, className="text-end")
        ], className="mb-4"),
        
        # Time period selector
        dbc.Row([
            dbc.Col([
                dbc.Select(
                    id="dora-time-period",
                    options=[
                        {"label": "Last 7 days", "value": "7d"},
                        {"label": "Last 30 days", "value": "30d"},
                        {"label": "Last 90 days", "value": "90d"},
                        {"label": "Custom range", "value": "custom"}
                    ],
                    value="30d"
                )
            ], width=6)
        ], className="mb-4"),
        
        # Metric cards grid
        html.Div(id="dora-metrics-container", children=[
            dbc.Row([
                dbc.Col([html.Div(id="deployment-frequency-card")], width=12, lg=6),
                dbc.Col([html.Div(id="lead-time-card")], width=12, lg=6),
            ]),
            dbc.Row([
                dbc.Col([html.Div(id="change-failure-rate-card")], width=12, lg=6),
                dbc.Col([html.Div(id="mttr-card")], width=12, lg=6),
            ])
        ])
    ], fluid=True)
```

#### 2.3 Field Mapping Modal (`ui/field_mapping_modal.py`)

```python
"""Field mapping configuration modal"""

import dash_bootstrap_components as dbc
from dash import html

def create_field_mapping_modal() -> dbc.Modal:
    """Create field mapping configuration modal"""
    return dbc.Modal([
        dbc.ModalHeader("Configure Jira Field Mappings"),
        dbc.ModalBody([
            html.H5("DORA Metrics Fields"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Deployment Date"),
                    dbc.Select(id="mapping-deployment-date", options=[])
                ], width=6),
                dbc.Col([
                    dbc.Label("Target Environment"),
                    dbc.Select(id="mapping-target-environment", options=[])
                ], width=6),
            ], className="mb-3"),
            # ... more field mappings
            
            html.H5("Flow Metrics Fields", className="mt-4"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Flow Item Type"),
                    dbc.Select(id="mapping-flow-item-type", options=[])
                ], width=6),
                # ... more field mappings
            ])
        ]),
        dbc.ModalFooter([
            dbc.Button("Cancel", id="cancel-field-mapping", color="secondary"),
            dbc.Button("Save Configuration", id="save-field-mapping", color="primary")
        ])
    ], id="field-mapping-modal", size="xl", is_open=False)
```

### Phase 3: Callbacks (Days 7-8)

#### 3.1 DORA Metrics Callbacks (`callbacks/dora_flow_metrics.py`)

```python
"""Callbacks for DORA and Flow metrics dashboard"""

from dash import callback, Output, Input, State
from data.dora_calculator import calculate_all_dora_metrics
from data.flow_calculator import calculate_all_flow_metrics
from data.field_mapper import load_field_mappings, get_field_mappings_hash
from data.metrics_cache import load_cached_metrics, save_cached_metrics, generate_cache_key
from data.jira_simple import fetch_all_issues
from ui.metric_cards import create_metric_card
from datetime import datetime, timedelta

@callback(
    [
        Output("deployment-frequency-card", "children"),
        Output("lead-time-card", "children"),
        Output("change-failure-rate-card", "children"),
        Output("mttr-card", "children")
    ],
    Input("dora-time-period", "value"),
    prevent_initial_call=True
)
def update_dora_metrics(time_period_value):
    """Update DORA metric cards when time period changes"""
    
    # Parse time period
    if time_period_value == "7d":
        start_date = datetime.utcnow() - timedelta(days=7)
        end_date = datetime.utcnow()
    elif time_period_value == "30d":
        start_date = datetime.utcnow() - timedelta(days=30)
        end_date = datetime.utcnow()
    # ... handle other periods
    
    # Load field mappings
    field_mappings = load_field_mappings()
    field_hash = get_field_mappings_hash()
    
    # Check cache
    cache_key = generate_cache_key("dora", start_date.isoformat(), end_date.isoformat(), field_hash)
    cached_metrics = load_cached_metrics(cache_key)
    
    if cached_metrics:
        metrics = cached_metrics
    else:
        # Fetch Jira data (uses existing jira_cache.json)
        issues = fetch_all_issues(start_date=start_date, end_date=end_date)
        
        # Calculate metrics (DELEGATE TO DATA LAYER)
        metrics = calculate_all_dora_metrics(issues, field_mappings, (start_date, end_date))
        
        # Cache results
        save_cached_metrics(cache_key, metrics)
    
    # Render cards (UI layer)
    return (
        create_metric_card(metrics["deployment_frequency"]),
        create_metric_card(metrics["lead_time_for_changes"]),
        create_metric_card(metrics["change_failure_rate"]),
        create_metric_card(metrics["mean_time_to_recovery"])
    )

# Similar callback for Flow metrics
```

#### 3.2 Field Mapping Callbacks (`callbacks/field_mapping.py`)

```python
"""Callbacks for field mapping configuration"""

from dash import callback, Output, Input, State
from data.field_mapper import fetch_available_jira_fields, save_field_mappings, validate_field_mapping
from data.metrics_cache import invalidate_cache

@callback(
    Output("mapping-deployment-date", "options"),
    # ... outputs for all field dropdowns
    Input("field-mapping-modal", "is_open"),
    prevent_initial_call=True
)
def populate_field_options(is_open):
    """Fetch and populate available Jira fields when modal opens"""
    if not is_open:
        return []
    
    # DELEGATE TO DATA LAYER
    jira_fields = fetch_available_jira_fields()
    
    # Filter custom fields
    custom_fields = [f for f in jira_fields if f["id"].startswith("customfield_")]
    
    # Format for dropdown
    options = [{"label": f"{f['name']} ({f['id']})", "value": f["id"]} for f in custom_fields]
    
    return options

@callback(
    Output("field-mapping-modal", "is_open", allow_duplicate=True),
    Output("field-mapping-save-status", "children"),
    Input("save-field-mapping", "n_clicks"),
    State("mapping-deployment-date", "value"),
    # ... states for all mapped fields
    prevent_initial_call=True
)
def save_mappings(n_clicks, deployment_date_value, ...):
    """Save field mappings and invalidate cache"""
    if not n_clicks:
        return False, None
    
    # Build mappings dictionary
    mappings = {
        "dora": {
            "deployment_date": deployment_date_value,
            # ... other fields
        },
        "flow": {
            # ... flow fields
        }
    }
    
    # DELEGATE TO DATA LAYER
    success = save_field_mappings(mappings)
    invalidate_cache()  # Clear metrics cache
    
    if success:
        return False, "Configuration saved successfully!"
    else:
        return True, "Error saving configuration. Please try again."
```

### Phase 4: Integration & Testing (Days 9-10)

#### 4.1 Integration Test Example

```python
# tests/integration/test_dora_flow_workflow.py

import pytest
import tempfile
import os
from data.field_mapper import save_field_mappings
from data.dora_calculator import calculate_all_dora_metrics
from unittest.mock import patch

@pytest.fixture
def temp_settings_file():
    """Temporary settings file for test isolation"""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".json") as f:
        temp_file = f.name
    yield temp_file
    if os.path.exists(temp_file):
        os.unlink(temp_file)

def test_complete_dora_workflow(temp_settings_file):
    """Test end-to-end: field mapping → calculation → caching"""
    
    with patch("data.persistence.SETTINGS_FILE", temp_settings_file):
        # Step 1: Configure field mappings
        mappings = {
            "field_mappings": {
                "dora": {
                    "deployment_date": "customfield_10100",
                    "code_commit_date": "customfield_10102",
                    # ...
                }
            }
        }
        save_field_mappings(mappings)
        
        # Step 2: Mock Jira data
        sample_issues = [
            {
                "key": "DEP-1",
                "fields": {
                    "customfield_10100": "2025-01-15T10:00:00.000Z",
                    "customfield_10102": "2025-01-10T10:00:00.000Z"
                }
            },
            # ... more issues
        ]
        
        # Step 3: Calculate metrics
        from datetime import datetime
        time_period = (datetime(2025, 1, 1), datetime(2025, 1, 31))
        metrics = calculate_all_dora_metrics(sample_issues, mappings, time_period)
        
        # Step 4: Verify results
        assert metrics["deployment_frequency"]["error_state"] == "success"
        assert metrics["deployment_frequency"]["value"] > 0
        assert metrics["deployment_frequency"]["performance_tier"] in ["Elite", "High", "Medium", "Low"]
```

## 🧪 Testing Checklist

### Unit Tests (MUST write during implementation)
- [ ] `test_dora_calculator.py` - All DORA metric calculations
- [ ] `test_flow_calculator.py` - All Flow metric calculations
- [ ] `test_field_mapper.py` - Field validation and persistence
- [ ] `test_metrics_cache.py` - Caching with TTL (use tempfile!)
- [ ] `test_metric_cards.py` - UI component rendering

### Integration Tests (After implementation)
- [ ] `test_dora_flow_workflow.py` - End-to-end metric calculation
- [ ] `test_field_mapping_workflow.py` - Configuration flow
- [ ] Performance test: 5,000 issues in < 15 seconds

## 🎨 UI/UX Considerations

### Mobile-First Design
- Metric cards: 1 column on mobile, 2 on tablet, 4 on desktop
- Touch targets: Minimum 44px for all buttons
- Progressive disclosure: Show basic metrics, expand for details

### Error States
Every metric card must handle:
- `missing_mapping`: Show "Configure Mappings" button
- `no_data`: Show "No data in time period" message
- `calculation_error`: Show "Something went wrong" with retry option

### Loading States
- Show skeleton loading cards while fetching data
- Display "Calculating..." during metric computation
- Cache hit: Instant display (< 200ms)

## 📊 Performance Targets

| Operation                      | Target  | How to Measure               |
| ------------------------------ | ------- | ---------------------------- |
| Page load                      | < 2s    | Browser DevTools Network tab |
| Metric calculation (5k issues) | < 15s   | `time.time()` in calculator  |
| Cache hit                      | < 200ms | Log timestamps               |
| Chart rendering                | < 500ms | Plotly render time           |
| UI interaction                 | < 100ms | Click to state change        |

## 🔧 Debugging Tips

### Cache Issues
```powershell
# Clear all caches
Remove-Item jira_cache.json, metrics_cache.json, app_settings.json -ErrorAction SilentlyContinue
```

### Field Mapping Not Saving
- Check `app_settings.json` has `dora_flow_config` key
- Verify `data/persistence.py` functions are called correctly
- Breakpoint in `save_field_mappings()` to inspect data

### Metrics Show Error State
- Check field mappings exist in `app_settings.json`
- Verify Jira fields have data: Query Jira API directly
- Check excluded_issue_count: Are issues missing required fields?

## 📚 Key References

- **DORA Definitions**: `DORA_Flow_Jira_Mapping.md`
- **Data Model**: `specs/007-dora-flow-metrics/data-model.md`
- **API Contracts**: `specs/007-dora-flow-metrics/contracts/`
- **Research**: `specs/007-dora-flow-metrics/research.md`
- **Constitution**: `.specify/memory/constitution.md`

## ✅ Definition of Done

- [ ] All unit tests pass with > 80% coverage
- [ ] Integration tests pass end-to-end workflow
- [ ] Performance tests meet targets (< 15s for 5k issues)
- [ ] Mobile responsive (tested at 320px, 768px, 1024px)
- [ ] Error states display user-friendly messages
- [ ] Field mapping configuration works with real Jira instance
- [ ] Metrics cache correctly with TTL
- [ ] Code review approved (layered architecture, test isolation)

## 🚦 Next Steps After Implementation

1. Run full test suite: `.\.venv\Scripts\activate; pytest tests/unit/ tests/integration/ -v`
2. Manual testing with real Jira instance
3. Performance profiling with large datasets
4. Accessibility testing (keyboard navigation, screen reader)
5. Documentation: Update README.md with DORA/Flow metrics usage

---

**Questions?** Refer to:
- Architecture questions → `.github/copilot-instructions.md`
- Data model questions → `specs/007-dora-flow-metrics/data-model.md`
- Jira API questions → `DORA_Flow_Jira_Mapping.md`
