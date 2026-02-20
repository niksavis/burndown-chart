---
name: "release-management"
description: "Execute release preparation and changelog updates safely"
---

# Skill: Release Management

Use for release prep, changelog updates, and version workflow.

## Objectives

- Keep release process consistent.
- Produce concise user-facing changelog entries.
- Prevent process drift from repository release standards.

## Workflow

1. Generate changelog preview JSON.
2. Update `changelog.md` with flat benefit-focused bullets.
3. Validate release script inputs and constraints.
4. Summarize what was validated and what remains manual.

## Guardrails

- Activate venv in same command for Python execution.
- Do not include secrets/customer identifiers in release artifacts.
- Preserve release script contract unless explicitly requested.
