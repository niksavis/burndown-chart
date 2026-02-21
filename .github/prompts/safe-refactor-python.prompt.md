---
agent: 'agent'
model: GPT-5.3-Codex
tools:
  [
    'search/codebase',
    'edit/editFiles',
    'search',
    'search/usages',
    'search/changes',
    'execute/createAndRunTask',
    'execute/runTask',
    'read/getTaskOutput',
    'execute/getTerminalOutput',
    'execute/runInTerminal',
    'read/terminalLastCommand',
    'read/terminalSelection',
  ]
description: 'Perform a safe, layered Python refactor in burndown-chart'
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
