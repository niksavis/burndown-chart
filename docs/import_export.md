# Import and Export Guide

**Audience**: Users sharing configurations and developers supporting data portability
**Part of**: [Documentation Index](readme.md)

## Overview

Import and export workflows support three scenarios:

- Configuration-only export (no cached data).
- Full export with cached data for the active query.
- Optional inclusion of JIRA tokens for private migrations.

## Export Modes

### Configuration Only

- Includes profile settings, field mappings, and queries.
- Excludes cached JIRA data and metrics snapshots.
- Designed for sharing setup without data.

### Full Export With Data

- Includes profile settings, queries, and cached data for the active query.
- Enables offline analysis and sharing without JIRA access.
- Preserves metrics snapshots and derived statistics.

### Token Inclusion

- Optional checkbox controls whether JIRA tokens are included.
- Default is excluded to prevent credential leakage.

## Import Behavior

- Validates package structure before applying changes.
- Prompts for tokens when missing in the package.
- Handles profile name conflicts with a user-selected strategy.

## Related Documentation

- [HTML Reporting Guide](html_reporting.md)
- [Profile Management Guide](profile_management.md)
