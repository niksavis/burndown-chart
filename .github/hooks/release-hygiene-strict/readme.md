# Release Hygiene Strict Hook

Strict hook profile for release and changelog quality enforcement.

## Purpose

- Tighten release workflow and changelog quality checks.
- Require explicit release validation outcomes in final responses.

## Events used

- `sessionStart`
- `userPromptSubmitted`
- `sessionEnd`

## Notes

- Use with `governance-strict` for strict-mode parity.
- If strict mode is noisy, revert to `release-hygiene-warn-only` and tune messages.
