---
agent: "agent"
model: GPT-5.3-Codex
tools:
  [
    "codebase",
    "editFiles",
    "search",
    "usages",
    "changes",
    "runTasks",
    "runCommands",
  ]
description: "Perform a safe, layered Python refactor in burndown-chart"
---

Perform a safe refactor for the requested Python target.

Constraints:

- No behavior changes unless explicitly requested.
- Preserve public APIs and call signatures where possible.
- Enforce file/function size limits from architecture guidance.
- Avoid unrelated formatting/refactors.

Validation:

- Run the narrowest relevant tests first.
- Run `get_errors` on touched files.

Output:

- Refactor rationale, touched files, and validation summary.
