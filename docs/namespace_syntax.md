# Namespace Syntax for JIRA Field Mapping

The namespace syntax provides a human-readable way to reference JIRA fields across projects. This unified syntax simplifies field mapping configuration for DORA metrics, Flow metrics, and custom calculations.

## Quick Reference

| Pattern                    | Description                 | Example                           |
| -------------------------- | --------------------------- | --------------------------------- |
| `*.field`                  | Field from any project      | `*.created`                       |
| `PROJECT.field`            | Field from specific project | `DevOps.customfield_10100`        |
| `*.field.property`         | Object property             | `*.status.name`                   |
| `*.Field:Value.DateTime`   | Changelog timestamp         | `*.Status:Deployed.DateTime`      |
| `PROJECT1\|PROJECT2.field` | Multiple projects           | `DevOps\|Platform.resolutiondate` |

## Basic Syntax

### Pattern Structure

```
[ProjectFilter.]FieldName[.Property][:ChangelogValue][.Extractor]
```

**Components**:
- **ProjectFilter**: Project key, `*` (wildcard), or multiple keys with `|`
- **FieldName**: Standard field name or `customfield_XXXXX`
- **Property**: Object property path (dot-separated)
- **ChangelogValue**: Status/field value for changelog queries (after `:`)
- **Extractor**: `DateTime`, `Occurred`, or property name

## Field Types

### 1. Simple Scalar Fields

Direct field access for string, number, date, and datetime fields.

```
*.created                    # Issue creation date (any project)
DevOps.resolutiondate        # Resolution date from DevOps project
*.customfield_10100          # Custom datetime field
*.customfield_10016          # Story points (number)
```

### 2. Object Fields

Access properties of complex object fields using dot notation.

```
*.status.name                # Status name (e.g., "In Progress")
*.priority.id                # Priority ID
*.issuetype.name             # Issue type name
*.project.key                # Project key
*.assignee.displayName       # Assignee display name
```

**Common Object Properties**:

| Field       | Properties                                 |
| ----------- | ------------------------------------------ |
| `status`    | `name`, `id`, `statusCategory.key`         |
| `priority`  | `name`, `id`                               |
| `issuetype` | `name`, `id`                               |
| `project`   | `key`, `name`, `id`                        |
| `assignee`  | `displayName`, `emailAddress`, `accountId` |
| `reporter`  | `displayName`, `emailAddress`, `accountId` |

### 3. Array Fields

For multi-value fields, the first element is returned by default.

```
*.fixVersions.releaseDate    # First fix version's release date
*.fixVersions.name           # First fix version name
*.components.name            # First component name
*.labels                     # First label (string)
```

**Common Array Properties**:

| Field         | Properties                              |
| ------------- | --------------------------------------- |
| `fixVersions` | `name`, `releaseDate`, `released`, `id` |
| `components`  | `name`, `id`, `description`             |

### 4. Changelog Fields

Access historical field changes using the `:` operator.

```
*.Status:Deployed.DateTime       # When status changed to "Deployed"
*.Status:InProgress.Occurred     # Did status ever become "In Progress"?
DevOps.Status:Done.DateTime      # When DevOps issues were marked Done
*.Assignee:john@example.DateTime # When assigned to specific user
```

**Changelog Extractors**:

| Extractor   | Returns       | Description                          |
| ----------- | ------------- | ------------------------------------ |
| `.DateTime` | ISO timestamp | When the transition occurred         |
| `.Occurred` | boolean       | Whether the transition ever happened |

## Project Filtering

### Single Project

```
DevOps.customfield_10100     # Only from DevOps project
PLATFORM.status.name         # Only from PLATFORM project
```

### Wildcard (All Projects)

```
*.created                    # From any project
*.status.name                # Status from any project
```

### Multiple Projects

Use the pipe `|` delimiter to match multiple specific projects.

```
DevOps|Platform.customfield_10100     # From either project
DevOps|Platform|Mobile.resolutiondate # From any of three projects
```

## Real-World Examples

### DORA Metrics Configuration

**Deployment Frequency** - When issues are deployed:
```
DevOps.Status:Deployed.DateTime
```

**Lead Time for Changes** - Code commit to deployment:
```
# Start: Code commit date (custom field)
DevOps.customfield_10100

# End: Deployment timestamp
DevOps.Status:Deployed.DateTime
```

**Change Failure Rate** - Track deployment and incident events:
```
# Deployment events
DevOps.Status:Deployed.Occurred

# Incident events  
Ops.Status:Incident.Occurred
```

### Cross-Project Aggregation

**Velocity Across Teams**:
```
# Story points from multiple projects
DevOps|Platform|Mobile.customfield_10016

# Completion dates across teams
DevOps|Platform|Mobile.resolutiondate
```

**Release Planning**:
```
# Next release date
*.fixVersions.releaseDate

# Release scope (version name)
*.fixVersions.name
```

## Grammar Specification

```ebnf
namespace_path ::= [project_filter "."] field_path [changelog_spec] [extractor_spec]

project_filter ::= project_key | "*" | project_key ("|" project_key)*
project_key    ::= /[A-Z][A-Z0-9_]*/

field_path     ::= field_name ("." property_name)*
field_name     ::= standard_field | "customfield_" /[0-9]+/
property_name  ::= /[a-zA-Z][a-zA-Z0-9_]*/

changelog_spec ::= ":" transition_value ["." changelog_extractor]
transition_value ::= /[^.]+/
changelog_extractor ::= "DateTime" | "Occurred"

extractor_spec ::= "." extractor_name
extractor_name ::= "DateTime" | "Occurred" | property_name
```

## Platform Compatibility

The namespace syntax works identically on both JIRA Cloud and JIRA Data Center.

| Field Category                          | Compatibility |
| --------------------------------------- | ------------- |
| Scalar (string, number, date, datetime) | Identical     |
| Select (single option)                  | Identical     |
| Multi-Select (array of options)         | Identical     |
| Labels (array of strings)               | Identical     |
| User fields                             | Identical     |
| Changelog                               | Identical     |

**Note**: JIRA has no native boolean type. Checkbox fields are stored as strings (`"Yes"`/`"No"`) or option arrays.

## Autocomplete Support

When configuring field mappings in the UI, autocomplete suggestions are provided based on your JIRA instance:

1. **Project suggestions**: Type to filter available projects
2. **Field suggestions**: Shows all fields (standard and custom) with their display names
3. **Property suggestions**: Context-aware properties based on field type
4. **Status suggestions**: Available workflow statuses for changelog queries

## Validation

### Syntax Validation

The parser validates:
- Project keys follow JIRA format (uppercase letters, numbers, underscores)
- Field names are valid identifiers or custom field IDs
- Changelog operator `:` is followed by a valid value
- Extractors are recognized (DateTime, Occurred, or valid property names)

### Error Messages

Invalid syntax produces clear error messages:

```
Error: Invalid namespace syntax "DevOps..status"
       Unexpected empty segment after project filter

Error: Invalid namespace syntax "*.Status:Deployed.Invalid"
       Unknown extractor "Invalid". Expected: DateTime, Occurred
```

## Case Sensitivity

- **Project keys**: Case-sensitive (must match exactly)
- **Field names**: Case-sensitive for custom fields, case-insensitive for standard fields
- **Status values**: Case-sensitive in changelog queries

```
DevOps.status.name      # Correct
devops.status.name      # May not match if project key is "DevOps"
*.Status:deployed       # May not match if status is "Deployed"
```

## Limitations

Current implementation does not support:

- Explicit array indexing (`*.fixVersions[0].name`)
- Array filtering (`*.fixVersions[released=true].releaseDate`)
- Multi-value extraction (`*.fixVersions[*].name`)
- Calculated fields (`$LeadTime(field1, field2)`)
- Duration calculations (`*.Status:InProgress.Duration`)

These features may be added in future releases based on user demand.

---

*Document Version: 1.0 | Last Updated: December 2025*
