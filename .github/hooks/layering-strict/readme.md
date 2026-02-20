# Layering Strict Hook

Strict hook profile for enforcing architecture boundary discipline.

## Purpose

- Reinforce layered architecture checks in all sessions.
- Require explicit reporting of boundary validation before completion.

## Events used

- `sessionStart`
- `userPromptSubmitted`
- `sessionEnd`

## Notes

- Use with `governance-strict` for strict-mode parity.
- If false positives occur, revert to `layering-warn-only` and refine messages.
