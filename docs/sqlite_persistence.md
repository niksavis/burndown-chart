# SQLite Persistence Guide

**Audience**: Developers maintaining persistence and advanced users troubleshooting data storage
**Part of**: [Documentation Index](readme.md)

## Overview

The application stores all state in SQLite to replace legacy JSON persistence. Data is isolated by profile and query.

## Database Location

- Default database file: profiles/burndown.db
- The backend selects paths based on the installation context.

## Data Categories

- Profiles and queries
- App settings and state
- JIRA issues and changelog entries
- Project statistics and metrics snapshots
- Task progress data

## Migration

On first run after migration support, legacy JSON data is imported into the database. Backups are created before migration.

## Developer Notes

- WAL mode is enabled for concurrency and performance.
- Schema management and migrations live under data/persistence/.

## Related Documentation

- [Caching System](caching_system.md)
- [Release Process](release_process.md)
