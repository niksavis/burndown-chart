---
name: "sqlite-persistence-safety"
description: "Implement safe and maintainable SQLite persistence changes"
---

# Skill: SQLite Persistence Safety

Use this skill for changes under `data/persistence/` and SQL-related logic.

## Objectives

- Preserve data integrity.
- Enforce parameterized SQL and safe migrations.
- Keep persistence changes isolated from UI/callback concerns.

## Workflow

1. Identify impacted repository/data access paths.
2. Apply minimal SQL/query changes with parameters only.
3. Validate read/write behavior with targeted tests.
4. Run diagnostics and summarize persistence risks.

## Guardrails

- No raw string SQL interpolation with user input.
- No customer data in tests or fixtures.
- Keep migration-related changes reversible when practical.
