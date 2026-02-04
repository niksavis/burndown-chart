# Profile Management Guide

**Audience**: Users managing multiple workspaces and developers supporting profile behavior
**Part of**: [Documentation Index](readme.md)

## Overview

Profiles provide isolated workspaces for different projects or teams. Each profile stores its own configuration, field mappings, parameters, and cached data.

## Key Behaviors

- Switching profiles updates the active configuration and cached datasets.
- Profiles isolate JIRA configuration, mappings, and parameter settings.
- A default profile is created during migration from legacy file storage.

## Limits

- Maximum profiles: 50.

## Common Actions

- Create profile: Use the profile selector controls in the settings panel.
- Duplicate profile: Copies configuration and mappings; queries can be duplicated separately.
- Delete profile: Only allowed when it is not the active profile and at least one profile remains.

## Related Documentation

- [Query Management Guide](query_management.md)
- [JIRA Configuration Guide](jira_configuration.md)
