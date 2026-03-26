---
name: release-management
description: 'Execute release preparation and changelog updates safely. Use when drafting release notes, preparing version bumps, validating release prerequisites, or checking release workflow completeness before tagging or publishing.'
---

# Skill: Release Management

Use for release prep, changelog updates, and version workflow.

## Objectives

- Keep release process consistent.
- Produce concise user-facing changelog entries.
- Prevent process drift from repository release standards.

## Workflow

1. Generate changelog preview JSON:
   `source .venv/Scripts/activate && python regenerate_changelog.py --preview --json`
2. Update `changelog.md` with flat user-benefit bullets (bold major features).
3. Validate release prerequisites and pending blockers:
   `bd ready --json` — confirm no open blockers; `bd stats` for summary.
4. Commit changelog updates before running release.py.
5. Run release script with semantic bump:
   `source .venv/Scripts/activate && python release.py patch|minor|major`
   (This updates version files, regenerates version info, updates codebase context metrics, commits, tags, and pushes.)
6. Summarize what was validated and what remains manual.

See `.github/instructions/release-workflow.instructions.md` for canonical release constraints.

## Guardrails

- Activate venv in same command for Python execution.
- Do not include secrets/customer identifiers in release artifacts.
- Preserve release script contract unless explicitly requested.
