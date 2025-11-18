# Field Mapping Architecture Proposal

## Executive Summary

**Problem**: Current simple `field → field` mappings cannot handle the complexity of real JIRA instances where:
- Same data comes from different sources (field, changelog, fixVersions)
- Different JIRAs use different field structures
- Conditions are needed (only production, only certain issue types)
- Some variables require calculation (changelog analysis)

**Solution**: Implement a **rule-based variable mapping system** with:
- Multiple source options per variable (priority-based)
- Conditional filters (project, issuetype, environment)
- Changelog extraction support
- Metric-driven UI (users configure variables, not fields)

**Scope**: 
- ✅ Backward compatible with existing simple mappings
- ✅ Progressive enhancement (simple → advanced)
- ✅ No hardcoded assumptions about JIRA structure

---

## Core Concept: Variables vs. Fields

### Current Approach (Field-to-Field)
```json
{
  "deployment_date": "customfield_10100",
  "incident_start": "created"
}
```

**Problem**: Assumes:
- One field maps to one variable
- Field always contains the right data
- No conditions needed
- No alternative sources

### Proposed Approach (Variable-with-Rules)
```json
{
  "deployment_timestamp": {
    "variable_type": "datetime",
    "metric_category": "dora",
    "sources": [
      {
        "priority": 1,
        "type": "field_value",
        "field": "customfield_10100"
      },
      {
        "priority": 2,
        "type": "changelog_timestamp",
        "field": "status",
        "condition": {"transition_to": "Deployed to Production"}
      },
      {
        "priority": 3,
        "type": "fixversion_releasedate",
        "field": "fixVersions",
        "selector": "first"
      }
    ],
    "filters": {
      "project": ["DEVOPS"],
      "environment_field": "customfield_10200",
      "environment_value": "Production"
    }
  }
}
```

**Benefits**:
- Multiple fallback sources
- Conditional logic
- Clear priority ordering
- Flexible extraction methods

---

## Data Model

### Variable Definition Schema

```python
from typing import Literal, List, Dict, Any, Optional
from pydantic import BaseModel

class FieldValueSource(BaseModel):
    """Direct field value extraction."""
    type: Literal["field_value"]
    field: str  # JIRA field ID (e.g., "customfield_10100" or "status")
    value_type: Literal["datetime", "string", "number", "boolean"] = "string"

class FieldValueMatchSource(BaseModel):
    """Field value equals condition."""
    type: Literal["field_value_match"]
    field: str
    operator: Literal["equals", "not_equals", "in", "not_in", "contains"]
    value: Any  # Can be string, number, list
    
class ChangelogEventSource(BaseModel):
    """Detect changelog event (returns boolean)."""
    type: Literal["changelog_event"]
    field: str  # Which field transitioned
    condition: Dict[str, Any]
    # Example: {"transition_to": "Done"} or {"transition_from": "To Do", "transition_to": "In Progress"}
    
class ChangelogTimestampSource(BaseModel):
    """Extract timestamp from changelog event."""
    type: Literal["changelog_timestamp"]
    field: str
    condition: Dict[str, Any]
    # Example: {"transition_to": "Deployed"} returns timestamp of that transition
    
class FixVersionSource(BaseModel):
    """Extract data from fixVersions array."""
    type: Literal["fixversion_releasedate"]
    field: Literal["fixVersions"]
    selector: Literal["first", "last", "all"] = "first"
    
class CalculatedSource(BaseModel):
    """Derived value from other sources."""
    type: Literal["calculated"]
    calculation: str  # "sum_changelog_durations", "timestamp_diff", etc.
    inputs: Dict[str, str]  # Map of input variable names
    parameters: Dict[str, Any]  # Calculation-specific parameters
    
class MappingFilter(BaseModel):
    """Conditional filters for when mapping applies."""
    project: Optional[List[str]] = None  # Project keys
    issuetype: Optional[List[str]] = None  # Issue type names
    environment_field: Optional[str] = None  # Field to check for environment
    environment_value: Optional[str] = None  # Required environment value
    custom_jql: Optional[str] = None  # Custom JQL filter
    
class SourceRule(BaseModel):
    """Single source with priority."""
    priority: int  # Lower number = higher priority
    source: FieldValueSource | FieldValueMatchSource | ChangelogEventSource | ChangelogTimestampSource | FixVersionSource | CalculatedSource
    filters: Optional[MappingFilter] = None
    
class VariableMapping(BaseModel):
    """Complete variable mapping definition."""
    variable_name: str  # e.g., "deployment_timestamp"
    variable_type: Literal["datetime", "boolean", "number", "duration", "category", "count"]
    metric_category: Literal["dora", "flow", "common"]
    description: str
    required: bool = True
    sources: List[SourceRule]
    fallback_source: Optional[SourceRule] = None
    validation_rules: Optional[Dict[str, Any]] = None
```

### Storage Format (JSON)

**Profile-level settings** (`profiles/{profile_id}/app_settings.json`):

```json
{
  "variable_mappings": {
    "deployment_timestamp": {
      "variable_type": "datetime",
      "metric_category": "dora",
      "description": "When deployment occurred",
      "required": true,
      "sources": [
        {
          "priority": 1,
          "source": {
            "type": "field_value",
            "field": "customfield_10100",
            "value_type": "datetime"
          }
        },
        {
          "priority": 2,
          "source": {
            "type": "changelog_timestamp",
            "field": "status",
            "condition": {"transition_to": "Deployed to Production"}
          }
        },
        {
          "priority": 3,
          "source": {
            "type": "fixversion_releasedate",
            "field": "fixVersions",
            "selector": "first"
          }
        }
      ],
      "filters": {
        "project": ["DEVOPS"],
        "environment_field": "customfield_10200",
        "environment_value": "Production"
      }
    },
    
    "deployment_event": {
      "variable_type": "boolean",
      "metric_category": "dora",
      "description": "Whether issue represents a deployment",
      "required": true,
      "sources": [
        {
          "priority": 1,
          "source": {
            "type": "field_value_match",
            "field": "issuetype",
            "operator": "equals",
            "value": "Deployment"
          }
        },
        {
          "priority": 2,
          "source": {
            "type": "changelog_event",
            "field": "status",
            "condition": {"transition_to": "Deployed"}
          }
        }
      ]
    },
    
    "work_type_category": {
      "variable_type": "category",
      "metric_category": "flow",
      "description": "Flow distribution category",
      "required": true,
      "sources": [
        {
          "priority": 1,
          "source": {
            "type": "field_value",
            "field": "issuetype",
            "value_type": "string"
          }
        }
      ],
      "category_mapping": {
        "Feature": ["Story", "Epic", "New Feature"],
        "Defect": ["Bug", "Production Bug"],
        "Risk": ["Risk", "Security Issue"],
        "Tech Debt": ["Technical Debt", "Refactoring"]
      }
    },
    
    "active_time": {
      "variable_type": "duration",
      "metric_category": "flow",
      "description": "Time spent in active work states",
      "required": true,
      "sources": [
        {
          "priority": 1,
          "source": {
            "type": "calculated",
            "calculation": "sum_changelog_durations",
            "inputs": {
              "field": "status",
              "statuses": ["In Progress", "In Review", "Testing"]
            }
          }
        },
        {
          "priority": 2,
          "source": {
            "type": "field_value",
            "field": "timetracking",
            "value_type": "number"
          }
        }
      ]
    }
  }
}
```

---

## Variable Extraction Engine

### Core Function: `extract_variable_value()`

```python
from typing import Any, Optional, Dict, List
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class VariableExtractor:
    """Extract variable values from JIRA issues using mapping rules."""
    
    def __init__(self, variable_mappings: Dict[str, VariableMapping]):
        self.mappings = variable_mappings
        
    def extract_value(
        self, 
        variable_name: str, 
        issue: Dict[str, Any],
        changelog: Optional[List[Dict]] = None
    ) -> Optional[Any]:
        """Extract variable value from issue using priority-ordered sources.
        
        Args:
            variable_name: Name of variable to extract (e.g., "deployment_timestamp")
            issue: JIRA issue dictionary
            changelog: Optional changelog history
            
        Returns:
            Extracted value or None if no source succeeded
        """
        if variable_name not in self.mappings:
            logger.warning(f"Unknown variable: {variable_name}")
            return None
            
        mapping = self.mappings[variable_name]
        
        # Check filters first (applies to all sources)
        if mapping.filters and not self._check_filters(issue, mapping.filters):
            logger.debug(f"Issue {issue.get('key')} filtered out for {variable_name}")
            return None
        
        # Try each source in priority order
        for source_rule in sorted(mapping.sources, key=lambda s: s.priority):
            try:
                value = self._extract_from_source(
                    source_rule.source, 
                    issue, 
                    changelog
                )
                
                if value is not None:
                    logger.debug(
                        f"Extracted {variable_name} from priority {source_rule.priority} source: {value}"
                    )
                    return value
                    
            except Exception as e:
                logger.warning(
                    f"Failed to extract {variable_name} from source priority {source_rule.priority}: {e}"
                )
                continue
        
        # Try fallback source if available
        if mapping.fallback_source:
            try:
                value = self._extract_from_source(
                    mapping.fallback_source.source,
                    issue,
                    changelog
                )
                if value is not None:
                    logger.debug(f"Extracted {variable_name} from fallback source: {value}")
                    return value
            except Exception as e:
                logger.warning(f"Fallback source failed for {variable_name}: {e}")
        
        logger.debug(f"No value extracted for {variable_name} from issue {issue.get('key')}")
        return None
    
    def _check_filters(self, issue: Dict[str, Any], filters: MappingFilter) -> bool:
        """Check if issue passes filter conditions."""
        fields = issue.get("fields", {})
        
        # Project filter
        if filters.project:
            project_key = issue.get("fields", {}).get("project", {}).get("key")
            if project_key not in filters.project:
                return False
        
        # Issue type filter
        if filters.issuetype:
            issuetype_name = fields.get("issuetype", {}).get("name")
            if issuetype_name not in filters.issuetype:
                return False
        
        # Environment filter
        if filters.environment_field and filters.environment_value:
            env_value = fields.get(filters.environment_field)
            if env_value != filters.environment_value:
                return False
        
        # Custom JQL filter (would need JQL evaluation)
        if filters.custom_jql:
            # TODO: Implement JQL evaluation
            pass
        
        return True
    
    def _extract_from_source(
        self, 
        source: Any,
        issue: Dict[str, Any], 
        changelog: Optional[List[Dict]]
    ) -> Optional[Any]:
        """Extract value using specific source type."""
        
        if isinstance(source, FieldValueSource):
            return self._extract_field_value(source, issue)
            
        elif isinstance(source, FieldValueMatchSource):
            return self._extract_field_match(source, issue)
            
        elif isinstance(source, ChangelogEventSource):
            return self._extract_changelog_event(source, issue, changelog)
            
        elif isinstance(source, ChangelogTimestampSource):
            return self._extract_changelog_timestamp(source, issue, changelog)
            
        elif isinstance(source, FixVersionSource):
            return self._extract_fixversion(source, issue)
            
        elif isinstance(source, CalculatedSource):
            return self._extract_calculated(source, issue, changelog)
            
        else:
            logger.error(f"Unknown source type: {type(source)}")
            return None
    
    def _extract_field_value(self, source: FieldValueSource, issue: Dict) -> Optional[Any]:
        """Extract direct field value."""
        fields = issue.get("fields", {})
        value = fields.get(source.field)
        
        if value is None:
            return None
        
        # Type conversion if needed
        if source.value_type == "datetime":
            return self._parse_datetime(value)
        elif source.value_type == "number":
            return float(value) if value else None
        elif source.value_type == "boolean":
            return bool(value)
        else:
            return value
    
    def _extract_field_match(self, source: FieldValueMatchSource, issue: Dict) -> bool:
        """Check if field value matches condition."""
        fields = issue.get("fields", {})
        
        # Handle nested fields (e.g., "status.name")
        field_parts = source.field.split(".")
        value = fields
        for part in field_parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return False
        
        # Apply operator
        if source.operator == "equals":
            return value == source.value
        elif source.operator == "not_equals":
            return value != source.value
        elif source.operator == "in":
            return value in source.value
        elif source.operator == "not_in":
            return value not in source.value
        elif source.operator == "contains":
            return source.value in value if value else False
        else:
            return False
    
    def _extract_changelog_event(
        self, 
        source: ChangelogEventSource, 
        issue: Dict, 
        changelog: Optional[List[Dict]]
    ) -> bool:
        """Check if changelog contains matching transition event."""
        if not changelog:
            return False
        
        for history_item in changelog:
            for item in history_item.get("items", []):
                if item.get("field") == source.field:
                    if "transition_to" in source.condition:
                        if item.get("toString") == source.condition["transition_to"]:
                            return True
                    if "transition_from" in source.condition:
                        if item.get("fromString") == source.condition["transition_from"]:
                            if "transition_to" in source.condition:
                                if item.get("toString") == source.condition["transition_to"]:
                                    return True
        return False
    
    def _extract_changelog_timestamp(
        self,
        source: ChangelogTimestampSource,
        issue: Dict,
        changelog: Optional[List[Dict]]
    ) -> Optional[datetime]:
        """Extract timestamp when changelog event occurred."""
        if not changelog:
            return None
        
        for history_item in changelog:
            for item in history_item.get("items", []):
                if item.get("field") == source.field:
                    if "transition_to" in source.condition:
                        if item.get("toString") == source.condition["transition_to"]:
                            return self._parse_datetime(history_item.get("created"))
        return None
    
    def _extract_fixversion(self, source: FixVersionSource, issue: Dict) -> Optional[datetime]:
        """Extract release date from fixVersions."""
        fields = issue.get("fields", {})
        fix_versions = fields.get("fixVersions", [])
        
        if not fix_versions:
            return None
        
        dates = []
        for version in fix_versions:
            if isinstance(version, dict):
                release_date = version.get("releaseDate")
                if release_date:
                    parsed_date = self._parse_datetime(release_date)
                    if parsed_date:
                        dates.append(parsed_date)
        
        if not dates:
            return None
        
        if source.selector == "first":
            return min(dates)
        elif source.selector == "last":
            return max(dates)
        elif source.selector == "all":
            return dates
        else:
            return dates[0] if dates else None
    
    def _extract_calculated(
        self,
        source: CalculatedSource,
        issue: Dict,
        changelog: Optional[List[Dict]]
    ) -> Optional[Any]:
        """Calculate derived value."""
        if source.calculation == "sum_changelog_durations":
            return self._calculate_status_durations(
                source.inputs.get("field", "status"),
                source.inputs.get("statuses", []),
                changelog
            )
        # Add more calculation types as needed
        return None
    
    def _calculate_status_durations(
        self,
        field: str,
        statuses: List[str],
        changelog: Optional[List[Dict]]
    ) -> Optional[float]:
        """Sum time spent in specified statuses (returns days)."""
        if not changelog:
            return None
        
        total_duration = 0.0
        current_status = None
        current_start = None
        
        for history_item in sorted(changelog, key=lambda h: h.get("created", "")):
            for item in history_item.get("items", []):
                if item.get("field") == field:
                    # If we were tracking a status, calculate duration
                    if current_status in statuses and current_start:
                        end_time = self._parse_datetime(history_item.get("created"))
                        if end_time and current_start:
                            duration = (end_time - current_start).total_seconds() / 86400  # days
                            total_duration += duration
                    
                    # Update current status
                    current_status = item.get("toString")
                    current_start = self._parse_datetime(history_item.get("created"))
        
        return total_duration if total_duration > 0 else None
    
    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except:
                return None
        return None
```

---

## User Interface Design

### Metric-Driven Configuration Wizard

Users don't need to understand variables - they configure metrics:

```
┌─────────────────────────────────────────────────────────┐
│ Configure Metric: Deployment Frequency                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│ Step 1: How do you identify deployments?                │
│                                                          │
│ ○ We have a custom deployment date field                │
│   └─ Field: [customfield_10100 - Deployment Date ▼]     │
│                                                          │
│ ○ We use status transitions                             │
│   └─ Status: [Deployed to Production       ▼]           │
│   └─ Extract timestamp: [✓]                             │
│                                                          │
│ ○ We use fix versions with release dates                │
│   └─ Field: [fixVersions]                               │
│   └─ Which version: [● First  ○ Last  ○ All]            │
│                                                          │
│ ○ Issue type indicates deployment                       │
│   └─ Issue type: [Deployment               ▼]           │
│                                                          │
│ [✓] Allow multiple sources (priority order)             │
│                                                          │
│─────────────────────────────────────────────────────────│
│                                                          │
│ Step 2: Add filters (optional)                          │
│                                                          │
│ Only count deployments where:                           │
│ └─ Project: [DEVOPS, BACKEND    ] (comma-separated)     │
│ └─ Environment: [customfield_10200 ▼] = [Production ▼]  │
│                                                          │
│─────────────────────────────────────────────────────────│
│                                                          │
│ Step 3: Test configuration                              │
│                                                          │
│ ✓ Found 23 deployments in last 7 days                   │
│                                                          │
│ Sample issues:                                           │
│ • DEVOPS-123: Deploy v2.1 to Production (2025-11-15)    │
│ • DEVOPS-124: Deploy v2.2 to Production (2025-11-17)    │
│ • DEVOPS-125: Deploy v2.3 to Production (2025-11-18)    │
│                                                          │
│ [Preview More Issues]                                    │
│                                                          │
│─────────────────────────────────────────────────────────│
│                                                          │
│           [Cancel]          [Save Configuration]         │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Advanced Rule Editor (Optional)

For power users who want full control:

```json
{
  "variable": "deployment_timestamp",
  "sources": [
    {
      "priority": 1,
      "type": "field_value",
      "field": "customfield_10100"
    },
    {
      "priority": 2,
      "type": "changelog_timestamp",
      "field": "status",
      "condition": {"transition_to": "Deployed"}
    }
  ],
  "filters": {
    "project": ["DEVOPS"],
    "environment_field": "customfield_10200",
    "environment_value": "Production"
  }
}
```

---

## Migration Strategy

### Phase 1: Add Variable Layer (Backward Compatible)

Convert existing simple mappings to variable format:

**Before** (`app_settings.json`):
```json
{
  "field_mappings": {
    "deployment_date": "customfield_10100",
    "incident_start": "created"
  }
}
```

**After** (interpreted as):
```json
{
  "variable_mappings": {
    "deployment_timestamp": {
      "variable_type": "datetime",
      "sources": [{
        "priority": 1,
        "source": {"type": "field_value", "field": "customfield_10100"}
      }]
    },
    "incident_detected_timestamp": {
      "variable_type": "datetime",
      "sources": [{
        "priority": 1,
        "source": {"type": "field_value", "field": "created"}
      }]
    }
  }
}
```

**Compatibility function**:
```python
def convert_legacy_mappings(field_mappings: Dict[str, str]) -> Dict[str, VariableMapping]:
    """Convert old field mappings to new variable mappings."""
    # Map old field names to new variable names
    FIELD_TO_VARIABLE = {
        "deployment_date": "deployment_timestamp",
        "incident_detected_at": "incident_detected_timestamp",
        "incident_resolved_at": "service_restored_timestamp",
        # ... etc
    }
    
    variable_mappings = {}
    for old_field, jira_field in field_mappings.items():
        var_name = FIELD_TO_VARIABLE.get(old_field, old_field)
        variable_mappings[var_name] = VariableMapping(
            variable_name=var_name,
            variable_type="datetime",  # Default assumption
            sources=[{
                "priority": 1,
                "source": FieldValueSource(
                    type="field_value",
                    field=jira_field
                )
            }]
        )
    
    return variable_mappings
```

### Phase 2: Enhance Metric Calculators

Update DORA/Flow calculators to use variable extractor:

```python
def calculate_deployment_frequency(issues, variable_mappings, time_window_days=7):
    """Calculate deployment frequency using variable mappings."""
    extractor = VariableExtractor(variable_mappings)
    
    deployments = []
    for issue in issues:
        # Extract deployment event (boolean)
        is_deployment = extractor.extract_value("deployment_event", issue)
        if not is_deployment:
            continue
        
        # Extract deployment timestamp
        deployment_time = extractor.extract_value("deployment_timestamp", issue)
        if not deployment_time:
            logger.warning(f"Deployment {issue['key']} has no timestamp")
            continue
        
        # Extract success flag (optional)
        is_successful = extractor.extract_value("deployment_successful", issue)
        if is_successful is False:
            continue  # Skip failed deployments
        
        deployments.append({
            "key": issue["key"],
            "timestamp": deployment_time,
            "successful": is_successful
        })
    
    # Calculate frequency
    return len(deployments) / time_window_days
```

### Phase 3: Build Metric Configuration UI

Create wizard-style UI that:
1. Asks metric-specific questions
2. Translates answers to variable mappings
3. Tests mappings on sample data
4. Saves to profile settings

---

## Benefits Summary

### For Users
✅ **Simpler**: Configure what metrics need, not how fields map  
✅ **Flexible**: Multiple ways to provide same data  
✅ **Validated**: Test mappings before saving  
✅ **Guided**: Wizard explains what each mapping does

### For Developers
✅ **No Hardcoding**: All JIRA-specific logic in configuration  
✅ **Extensible**: Easy to add new variable types  
✅ **Testable**: Clear separation of extraction logic  
✅ **Maintainable**: Metric calculations use variables, not fields

### For Accuracy
✅ **Context-Aware**: Filters ensure right data is used  
✅ **Fallback Sources**: If primary source fails, try alternatives  
✅ **Changelog Support**: Can derive data from issue history  
✅ **Validation**: Type checking and business rules

---

## Next Steps

1. **Review Architecture**: Confirm approach meets requirements
2. **Implement Data Model**: Create Pydantic models for variable mappings
3. **Build Extractor**: Implement VariableExtractor with all source types
4. **Update Calculators**: Convert DORA/Flow metrics to use variables
5. **Create UI Wizard**: Metric-driven configuration interface
6. **Migration Tool**: Convert existing field mappings to variables
7. **Documentation**: User guide for configuring metrics

---

## Questions for Discussion

1. **Scope of initial release**: Start with basic sources (field_value, changelog_timestamp) or implement all types?
2. **UI complexity**: Simple wizard only, or also provide advanced JSON editor?
3. **Migration timeline**: Migrate all users at once, or support both systems in parallel?
4. **Performance**: Cache extracted values per issue to avoid re-extraction?
5. **Validation**: How strict should type validation be (error vs. warning)?

This architecture enables true metric flexibility while maintaining user-friendliness and backward compatibility.
