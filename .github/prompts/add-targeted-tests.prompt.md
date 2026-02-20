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
description: "Add targeted tests for changed behavior with isolation and clarity"
---

Add targeted tests for recent behavior changes.

Requirements:

- Follow existing test style and fixtures.
- Use isolated temporary directories where file I/O is needed.
- Avoid brittle assertions and over-mocking.
- No real customer data in test fixtures.

Validation:

- Run the smallest relevant test selection first.
- Summarize pass/fail and any known non-related failures.
