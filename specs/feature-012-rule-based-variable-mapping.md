# Feature 012: Rule-Based Variable Mapping System

## Overview

**Status**: ✅ **COMPLETE** - All phases implemented and tested  
**Branch**: `012-rule-based-variable-mapping`  
**Dependencies**: Feature 011 (Profile Workspace Switching)  
**Release**: v3.0-stable

## Problem Statement

Field mapping system had critical limitations:

1. **Hardcoded Field Access**: Metrics directly accessed standard JIRA fields without configuration
2. **No Conditional Logic**: Couldn't filter by project, issue type, or environment
3. **Single Source Only**: Each variable could only map to one field (no fallbacks)
4. **No Changelog Support**: Couldn't extract timestamps from status transitions
5. **JIRA Diversity**: One-size-fits-all didn't work across different JIRA configurations

## Solution: Namespace Syntax

Instead of complex wizard UI, we implemented a **namespace syntax** for field mapping:

```
[Project.]Field[.Property][:ChangelogValue][.Extractor]
```

**Examples**:
- `customfield_10016` - Simple field access
- `DevOps.customfield_10016` - Project-specific field
- `DevOps|Platform.customfield_10016` - Multi-project field
- `Status:Done.timestamp` - Changelog timestamp extraction
- `Status:In Progress->Done.duration` - Status transition duration

**Documentation**: See `docs/namespace_syntax.md` for complete syntax reference.

## Architecture

### Components Implemented

| Component               | File                                 | Purpose                                       |
| ----------------------- | ------------------------------------ | --------------------------------------------- |
| Namespace Parser        | `data/namespace_parser.py`           | Parse namespace strings to SourceRule objects |
| Autocomplete Provider   | `data/namespace_autocomplete.py`     | Server-side suggestions from JIRA metadata    |
| Clientside Autocomplete | `assets/namespace_autocomplete*.js`  | Browser-side filtering (avoids focus loss)    |
| Namespace Input         | `ui/namespace_input.py`              | Reusable UI component                         |
| JIRA Metadata Store     | `callbacks/jira_metadata.py`         | App-level metadata caching                    |
| Variable Extractor      | `data/variable_mapping/extractor.py` | Priority-ordered value extraction             |
| Variable Models         | `data/variable_mapping/models.py`    | Pydantic models for all source types          |
| Metric Variables        | `configuration/metric_variables.py`  | DORA + Flow variable catalog                  |

### Source Types

1. **FieldValueSource** - Direct field access
2. **FieldValueMatchSource** - Conditional field matching
3. **ChangelogTimestampSource** - Extract transition timestamp
4. **ChangelogEventSource** - Detect if transition occurred
5. **FixVersionSource** - Fix version date extraction
6. **CalculatedSource** - Derived values

## Implementation Summary

### Phase 1-2: Backend (Complete)
- Variable extraction with priority-ordered sources
- All DORA metrics use VariableExtractor
- All Flow metrics use VariableExtractor
- Backward compatibility with legacy field_mappings

### Phase 3: UI (Complete)
- Namespace text inputs replace dropdowns
- Clientside autocomplete with JIRA metadata
- Real-time syntax validation
- Validate button for testing configurations

### Phase 4: Testing (Complete)
- 1254 tests passing (2 skipped - intentionally flaky)
- 40 namespace parser unit tests
- User documentation: `docs/namespace_syntax.md`

## Troubleshooting

### Missing Fields After Auto-Configure

**Symptom**: Some DORA/Flow fields are empty after auto-configure.

**Cause**: Not all JIRA instances have deployment/environment custom fields. This is expected.

**Solutions**:
1. For missing DORA fields: Use namespace syntax to map to existing fields
2. For missing environment fields: Configure manually or use JQL filters
3. Manual configuration: Enter field ID directly (e.g., `customfield_10042`)

### Java Class Names in Environment Dropdown

**Symptom**: Dropdown shows Java class names like `com.atlassian.jira.plugin...`

**Fix**: Fixed in v3.0 - Java class patterns are filtered from detection.

## References

- `docs/namespace_syntax.md` - User documentation
- `docs/field_mapping_requirements.md` - Original problem analysis
- `docs/metric_variable_mapping_spec.md` - Variable catalog

## Change Log

- 2025-11-28: **FEATURE COMPLETE** - All phases implemented and tested
- 2025-11-28: Phase 3 complete - Namespace syntax UI with clientside autocomplete
- 2025-11-28: Phase 4 complete - 1254 tests passing, documentation created
- 2025-11-26: Phase 2 complete - All metrics use VariableExtractor
- 2025-11-18: Feature created
