---
name: sqlite-persistence-safety
description: 'Implement safe and maintainable SQLite persistence changes. Use when updating SQL queries, repository data-access logic, schema migrations, or database integrity and performance behavior.'
---

# Skill: SQLite Persistence Safety

Use this skill for changes under `data/persistence/` and SQL-related logic.

## Objectives

- Preserve data integrity.
- Enforce parameterized SQL and safe migrations.
- Keep persistence changes isolated from UI/callback concerns.

## Repository Context

- SQLite is the sole persistence backend (file-based, portable, ships with the executable).
- Schema changes must be migration-safe: the app opens existing user databases on upgrade.
- No ORM — all queries are hand-written SQL via `sqlite3` module.
- Migration scripts live in `data/persistence/sqlite/migrations/`.

## Workflow

1. Identify impacted repository/data access paths in `data/persistence/`.
2. Apply minimal SQL/query changes with parameterized access only.
3. For schema changes, add a migration script and ensure it runs on startup via the migration runner.
4. Validate read/write behavior with targeted tests using `tempfile.TemporaryDirectory()`.
5. Run diagnostics and summarize persistence risks.

## Guardrails

- No raw string SQL interpolation with user input.
- No customer data in tests or fixtures.
- Keep migration-related changes reversible when practical.
- Test with a fresh (empty) database AND an existing database to verify migrations.
