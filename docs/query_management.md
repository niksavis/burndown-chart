# Query Management Guide

**Audience**: Users working with multiple data slices and developers supporting query workflows
**Part of**: [Documentation Index](readme.md)

## Overview

Queries define the JQL used to fetch issues. Each profile can contain multiple queries with isolated caches while sharing the profile-level configuration.

## Key Behaviors

- Switching queries updates data without changing profile settings.
- Each query has its own cache and metrics snapshots.
- Query names and JQL are stored per profile.

## Limits

- Maximum queries per profile: 100.

## Common Actions

- Create query: Use the query creation controls and the JQL editor.
- Duplicate query: Creates a new query with the same JQL in the current profile.
- Delete query: Removes query configuration and its cached data.

## Related Documentation

- [JQL Editor Guide](jql_editor.md)
- [Profile Management Guide](profile_management.md)
