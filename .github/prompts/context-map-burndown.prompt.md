---
agent: "agent"
description: "Map the smallest set of files needed before implementing a change in burndown-chart"
---

Create a context map for this task in `burndown-chart` before editing code.

Task: ${input:task}

Output format:

1. Goal summary (1-2 lines)
2. Candidate files to inspect first (max 10), with reason per file
3. Primary edit files (ordered)
4. Validation commands/checks to run after edits
5. Risks and assumptions

Constraints:

- Prefer minimal file set and targeted changes.
- Respect architecture layers: callbacks routes only; logic in data; ui in ui; charts in visualization.
- Include `get_errors` in validation checks.
