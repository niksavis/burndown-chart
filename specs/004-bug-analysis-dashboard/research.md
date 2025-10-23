# Research: Bug Analysis Dashboard

**Feature**: Bug Analysis Dashboard  
**Phase**: 0 - Research & Technology Selection  
**Date**: October 22, 2025

## Research Questions & Decisions

### R1: JIRA Issue Type Field Structure

**Question**: What is the structure of the JIRA `issuetype` field and how do we reliably extract bug issues?

**Research Findings**:
- JIRA REST API v2/v3 returns `issuetype` as nested object in `fields`
- Structure: `issue.fields.issuetype.name` contains the human-readable type name
- Standard types: Bug, Story, Task, Epic, Subtask
- Custom types: Organizations can define custom names (Defect, Incident, etc.)
- Field is always present in JIRA issues (required field)

**Decision**: 
- Fetch `issuetype` field in base_fields list: `"key,created,resolutiondate,status,issuetype"`
- Extract type name via: `issue["fields"]["issuetype"]["name"]`
- Support configurable mapping: any type name can map to "bug" category in our app

**Rationale**: 
- Standard JIRA field available in all instances
- Minimal API overhead (one additional field)
- Flexible mapping handles custom type names

**Alternatives Considered**:
- ❌ Use labels/tags: Not reliable, not all teams use consistent labels
- ❌ Use component field: Not semantically correct, components != types
- ❌ Hardcode "Bug" only: Inflexible, many orgs use "Defect" or custom names

---

### R2: Bug Type Configuration System

**Question**: How should users configure which JIRA issue types map to "bugs" in the app?

**Research Findings**:
- User requirement: Zero configuration for default use case (FR-017 clarification)
- Advanced users need custom mapping for "Defect", "Incident", custom types
- Configuration should be intuitive and persistent

**Decision**:
Implement issue type mapping configuration in `app_settings.json`:

```json
{
  "bug_analysis_config": {
    "enabled": true,
    "issue_type_mappings": {
      "Bug": "bug",
      "Defect": "bug",
      "Incident": "bug"
    },
    "default_bug_type": "Bug"
  }
}
```

**Rationale**:
- Default includes "Bug" type (zero config for 90% of users)
- Simple key-value mapping (JIRA type → app category)
- Extensible for custom types
- Persists across sessions

**Alternatives Considered**:
- ❌ Regex patterns: Too complex for users, error-prone
- ❌ Separate config file: Unnecessary fragmentation
- ❌ UI-only configuration: Lose settings on cache clear

---

### R3: Weekly Bug Statistics Calculation Approach

**Question**: How do we efficiently calculate weekly bug creation/closure statistics?

**Research Findings**:
- Existing `jira_to_csv_format()` already implements weekly aggregation
- Uses `created` date for bug creation week
- Uses `resolutiondate` for bug closure week
- Weekly bins aligned to project timeline

**Decision**:
Create `calculate_bug_statistics()` function that:
1. Filters issues by bug type mapping
2. Reuses existing weekly binning logic
3. Separates bug stats from general stats
4. Tracks: bugs_created, bugs_closed, points_created, points_closed per week

```python
def calculate_bug_statistics(
    issues: List[Dict],
    bug_type_mappings: Dict[str, str],
    story_points_field: str,
    date_from: datetime,
    date_to: datetime
) -> List[Dict]:
    """Calculate weekly bug statistics from JIRA issues."""
    # Filter for bug types
    # Bin by week
    # Aggregate counts and points
    # Return weekly data structure
```

**Rationale**:
- Reuses proven weekly aggregation logic
- Maintains consistency with existing statistics
- Separates concerns (bug stats vs general stats)

**Alternatives Considered**:
- ❌ Modify existing `jira_to_csv_format()`: Risk breaking existing functionality
- ❌ Daily granularity: Too noisy, not useful for bug trends
- ❌ Monthly granularity: Too coarse, misses important trends

---

### R4: Quality Insights Rule Engine Design

**Question**: How do we implement threshold-based quality insights without overcomplicating?

**Research Findings**:
- User requirement: Simple threshold rules + statistical analysis (Q3 clarification)
- No ML/AI complexity needed
- Insights should be actionable (not just observations)
- Spec defines specific thresholds: 70% resolution rate, 30% capacity, 3+ weeks trend

**Decision**:
Implement rule-based insights engine with three insight types:

```python
class InsightType(Enum):
    WARNING = "warning"          # Critical issues requiring attention
    RECOMMENDATION = "recommendation"  # Suggested improvements
    POSITIVE = "positive"        # Encouraging feedback

class InsightSeverity(Enum):
    CRITICAL = "critical"        # Immediate action needed
    HIGH = "high"               # Address soon
    MEDIUM = "medium"           # Monitor
    LOW = "low"                 # Informational

def generate_quality_insights(
    bug_metrics: Dict,
    weekly_stats: List[Dict]
) -> List[Insight]:
    """Generate actionable quality insights from bug data."""
    insights = []
    
    # Rule 1: Low resolution rate
    if bug_metrics["resolution_rate"] < 0.70:
        insights.append(Insight(
            type=InsightType.RECOMMENDATION,
            severity=InsightSeverity.HIGH,
            title="Low Bug Resolution Rate",
            message="Consider dedicating more capacity to bug resolution",
            metrics={"resolution_rate": bug_metrics["resolution_rate"]}
        ))
    
    # Rule 2: Increasing bug trend
    trend = calculate_trend(weekly_stats, window=4)
    if trend["bugs_created"] > trend["bugs_closed"]:
        insights.append(Insight(
            type=InsightType.WARNING,
            severity=InsightSeverity.CRITICAL,
            title="Bug Creation Exceeds Closure",
            message="Bug creation rate is trending upward - review testing practices",
            metrics={"trend_ratio": trend["ratio"]}
        ))
    
    # Additional rules for other scenarios...
    
    return sorted(insights, key=lambda x: x.severity)
```

**Rationale**:
- Simple, maintainable rule engine
- Aligns with spec examples
- Prioritizes insights by severity
- Statistical analysis via trend detection

**Alternatives Considered**:
- ❌ ML-based anomaly detection: Overcomplicated, user said no ML
- ❌ Complex scoring system: YAGNI, simple thresholds work fine
- ❌ Natural language generation: Unnecessary, template messages sufficient

---

### R5: Bug Forecasting Adaptation

**Question**: How do we adapt existing PERT-based forecasting for bug resolution timeline?

**Research Findings**:
- Existing forecasting uses PERT formula: (optimistic + 4*likely + pessimistic) / 6
- Bug forecasting simpler: just project closure rate forward
- Need optimistic and pessimistic estimates based on historical variance

**Decision**:
Create simplified forecasting for bugs:

```python
def forecast_bug_resolution(
    open_bugs: int,
    weekly_stats: List[Dict],
    confidence_level: float = 0.95
) -> Dict:
    """Forecast when open bugs will be resolved."""
    
    # Calculate closure rates from recent history
    closure_rates = [week["bugs_closed"] for week in weekly_stats[-8:]]
    
    # Statistical analysis
    avg_closure_rate = mean(closure_rates)
    std_dev = stdev(closure_rates)
    
    # Optimistic: avg + 1 std dev
    optimistic_rate = avg_closure_rate + std_dev
    optimistic_weeks = ceil(open_bugs / optimistic_rate) if optimistic_rate > 0 else None
    
    # Pessimistic: avg - 1 std dev
    pessimistic_rate = max(avg_closure_rate - std_dev, 0.1)  # Floor at 0.1
    pessimistic_weeks = ceil(open_bugs / pessimistic_rate)
    
    # Most likely: use average
    likely_weeks = ceil(open_bugs / avg_closure_rate) if avg_closure_rate > 0 else None
    
    return {
        "open_bugs": open_bugs,
        "avg_closure_rate": avg_closure_rate,
        "optimistic": {
            "weeks": optimistic_weeks,
            "completion_date": calculate_future_date(optimistic_weeks)
        },
        "pessimistic": {
            "weeks": pessimistic_weeks,
            "completion_date": calculate_future_date(pessimistic_weeks)
        },
        "most_likely": {
            "weeks": likely_weeks,
            "completion_date": calculate_future_date(likely_weeks)
        },
        "confidence": confidence_level
    }
```

**Rationale**:
- Reuses statistical approach (mean, standard deviation)
- Simpler than full PERT (appropriate for bug forecasting)
- Provides optimistic/pessimistic range as required by spec
- Handles edge cases (zero closure rate)

**Alternatives Considered**:
- ❌ Full PERT formula: Overcomplicated for linear bug closure projection
- ❌ Machine learning time series: User explicitly rejected ML
- ❌ Single point estimate: Spec requires optimistic/pessimistic range

---

### R6: Mock Bug Data Generation Strategy

**Question**: What mock data structure ensures comprehensive testing without external dependencies?

**Research Findings**:
- User requirement: Mock data fallback when public JIRA unavailable (Q2 clarification)
- Need realistic bug lifecycle: created → in progress → closed
- Need variety: multiple bug types, varying points, edge cases

**Decision**:
Create comprehensive mock dataset generator:

```python
def generate_mock_bug_data(
    num_weeks: int = 12,
    bugs_per_week_range: tuple = (5, 15),
    issue_types: List[str] = ["Bug", "Defect", "Incident"]
) -> List[Dict]:
    """Generate realistic mock bug data for testing."""
    
    mock_issues = []
    base_date = datetime.now() - timedelta(weeks=num_weeks)
    
    for week in range(num_weeks):
        week_date = base_date + timedelta(weeks=week)
        num_bugs = random.randint(*bugs_per_week_range)
        
        for _ in range(num_bugs):
            issue_type = random.choice(issue_types)
            
            # Realistic lifecycle
            created_date = week_date + timedelta(days=random.randint(0, 6))
            
            # 70% get resolved (matches healthy resolution rate)
            is_resolved = random.random() < 0.7
            resolution_date = (
                created_date + timedelta(days=random.randint(1, 21))
                if is_resolved else None
            )
            
            # Story points (some bugs have none)
            points = random.choice([None, 1, 2, 3, 5, 8, 13])
            
            mock_issues.append({
                "key": f"MOCK-{len(mock_issues)+1}",
                "fields": {
                    "issuetype": {"name": issue_type},
                    "created": created_date.isoformat(),
                    "resolutiondate": resolution_date.isoformat() if resolution_date else None,
                    "status": {"name": "Done" if is_resolved else "In Progress"},
                    "customfield_10016": points  # Story points
                }
            })
    
    # Add edge cases
    mock_issues.extend(generate_edge_case_bugs())
    
    return mock_issues

def generate_edge_case_bugs() -> List[Dict]:
    """Generate edge case bugs for testing."""
    return [
        # Bug with 100 story points (outlier)
        create_bug("EDGE-1", points=100),
        # Bug created before timeline but closed within
        create_bug("EDGE-2", created_offset_weeks=-20, resolved=True),
        # Bug with no points
        create_bug("EDGE-3", points=None),
        # Bug type changed (simulate via comment or custom field)
        create_bug("EDGE-4", type="Task", originally="Bug")
    ]
```

**Rationale**:
- Realistic distribution matches real projects
- Covers all edge cases from spec
- Deterministic seed for reproducible tests
- Easy to extend with new scenarios

**Alternatives Considered**:
- ❌ Static JSON file: Hard to maintain, no variation
- ❌ Record real JIRA data: Privacy concerns, size issues
- ❌ Minimal mock (10 bugs): Insufficient for trend testing

---

### R7: Mobile-First Bug Visualization Design

**Question**: How do we ensure bug charts are readable and usable on mobile devices?

**Research Findings**:
- Existing app follows mobile-first design (documented in copilot-instructions.md)
- Plotly charts support responsive config
- Touch interactions need minimum 44px targets
- Mobile users need simplified data views

**Decision**:
Apply existing mobile optimization patterns to bug charts:

```python
def create_bug_trend_chart(
    bug_stats: List[Dict],
    viewport_size: str = "mobile"
) -> dcc.Graph:
    """Create mobile-optimized bug trend chart."""
    
    config = {
        "displayModeBar": viewport_size != "mobile",
        "responsive": True,
        "scrollZoom": True,
        "doubleClick": "reset+autosize"
    }
    
    layout = {
        "font": {"size": 12 if viewport_size == "mobile" else 14},
        "margin": {"t": 20, "r": 10, "b": 40, "l": 40},
        "showlegend": viewport_size != "mobile",
        "hovermode": "x unified",  # Better for mobile
        "title": {
            "text": "Bug Trends",
            "font": {"size": 16 if viewport_size == "mobile" else 20}
        }
    }
    
    # Simplified data for mobile (show only last 8 weeks)
    if viewport_size == "mobile" and len(bug_stats) > 8:
        bug_stats = bug_stats[-8:]
    
    return dcc.Graph(
        figure={
            "data": create_bug_trend_traces(bug_stats),
            "layout": layout
        },
        config=config,
        style={"height": "400px" if viewport_size == "mobile" else "500px"}
    )
```

**Rationale**:
- Reuses existing mobile optimization patterns
- Maintains consistency with other charts
- Reduces cognitive load on small screens
- Touch-friendly interactions

**Alternatives Considered**:
- ❌ Separate mobile/desktop charts: Code duplication
- ❌ No mobile optimization: Poor UX on phones
- ❌ Tables instead of charts: Less visual, harder to interpret

---

## Technology Stack Decisions

### Selected Technologies

| Component       | Technology                             | Rationale                                        |
| --------------- | -------------------------------------- | ------------------------------------------------ |
| Data Processing | pandas 2.2.3                           | Already in use, efficient for weekly aggregation |
| Visualization   | Plotly 6.0.1                           | Already in use, excellent mobile support         |
| UI Framework    | Dash 3.1.1 + dash-bootstrap-components | Existing framework, component reuse              |
| Testing         | pytest + pytest-playwright             | Existing test infrastructure                     |
| Caching         | JSON files                             | Consistent with existing approach                |
| Config Storage  | app_settings.json                      | Existing settings file                           |

### Best Practices Applied

1. **Data Layer Separation**: Bug processing isolated from general statistics
2. **Component Reuse**: Leverage existing chart, card, and tab components
3. **Mobile-First**: Apply existing responsive patterns to new UI
4. **Test Coverage**: Unit tests for logic, integration tests for workflows
5. **Configuration**: Zero-config default with advanced options
6. **Performance**: Reuse memoization patterns from existing processing
7. **Error Handling**: Graceful fallbacks matching existing error patterns

---

## Integration Points

### Existing Systems to Integrate With

1. **JIRA Integration** (`data/jira_simple.py`):
   - Add `issuetype` to field fetch
   - Maintain backward compatibility

2. **Tab System** (`ui/tabs.py`):
   - Add new "Bug Analysis" tab
   - Follow existing tab patterns

3. **Callback Registration** (`callbacks/__init__.py`):
   - Register bug analysis callbacks
   - Use existing callback patterns

4. **Data Persistence** (`data/persistence.py`):
   - Extend unified data structure for bug stats
   - Maintain backward compatibility

5. **Timeline Filtering** (`data/processing.py`):
   - Reuse existing filter functions
   - Apply to bug statistics

---

## Risk Assessment

| Risk                        | Probability | Impact | Mitigation                                       |
| --------------------------- | ----------- | ------ | ------------------------------------------------ |
| JIRA API changes            | Low         | Medium | Use stable v2/v3 API, cache responses            |
| Performance with 1000+ bugs | Medium      | Medium | Implement pagination, optimize calculations      |
| Custom type names           | High        | Low    | Flexible mapping configuration                   |
| Mobile layout issues        | Low         | Medium | Follow existing mobile patterns, test on devices |
| Test data availability      | Medium      | Low    | Mock data generator as fallback                  |

---

## Phase 0 Completion

**Status**: ✅ **COMPLETE**

All technical decisions made and documented. Ready to proceed to Phase 1 (Design & Contracts).

**Key Outcomes**:
- Issue type field extraction approach defined
- Configuration system designed
- Statistical engine approach clarified
- Forecasting adaptation specified
- Mock data strategy established
- Mobile optimization approach confirmed
- All integration points identified

**Next Phase**: Generate data-model.md and contracts/
