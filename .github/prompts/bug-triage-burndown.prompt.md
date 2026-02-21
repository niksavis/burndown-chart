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
description: 'Triage and fix a burndown-chart bug with minimal, validated edits'
---

You are triaging a bug in burndown-chart.

Requirements:

- Read relevant architecture guidance before edits.
- Keep changes minimal and focused.
- Respect layering: callbacks delegate to data; visualization in visualization; UI in ui.
- Run targeted validation, then `get_errors` for touched files.

Deliver:

1. Root cause summary.
2. Files changed and why.
3. Validation results and any remaining risk.
