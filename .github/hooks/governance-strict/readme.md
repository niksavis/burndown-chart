# Governance Strict Hook

This hook set is the strict counterpart to `governance-warn-only`.

## Purpose

- Enforce final quality gate checks before completion.
- Fail fast when required governance confirmations are missing.

## Events used

- `sessionStart`
- `userPromptSubmitted`
- `sessionEnd`

## Enforcement behavior

- Requires explicit final confirmation markers for:
  - zero diagnostics (`get_errors`)
  - no customer data/secrets
  - architecture boundary compliance
- Intended for mature rollout after warn-only adoption.

## Notes

- Keep this profile in parallel with warn-only packs.
- If rollout issues appear, revert to warn-only profile.
