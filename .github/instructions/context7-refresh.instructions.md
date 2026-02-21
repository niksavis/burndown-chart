---
applyTo: 'callbacks/**/*.py,data/**/*.py,ui/**/*.py,visualization/**/*.py,assets/**/*.js,**/*.ts,**/*.tsx,docs/**/*.md'
description: 'Require Context7 refresh workflow for external API and library-version sensitive tasks'
---

# Context7 Refresh Instructions

Use this instruction when a task depends on external library/framework/API behavior that may be version-sensitive.
This applies during research, planning, and implementation phases.

## Trigger Conditions

Apply Context7 workflow when **any** of the following are true:

### Must run Context7

- Task changes code that calls a third-party framework/library API (new usage or behavior change).
- Task updates dependency versions, migration paths, or deprecation handling.
- Task writes or updates documentation that claims "latest", "current", "recommended", or "best practice" for external technologies.
- Task updates guidelines or technical documentation in any repository location where external technology behavior is described (for example `docs/architecture/*_guidelines.md` for CSS/HTML/JavaScript/Python/SQL).
- Task includes unknown/uncertain framework symbols, methods, or configuration keys.
- Task needs latest official API definitions or current code examples to avoid stale guidance.

### May skip Context7

- Pure formatting, spelling, grammar, or wording changes with no technical claims.
- Internal repository process docs that do not describe external framework/library/API behavior.
- Local refactors that do not alter third-party API usage.

## Required Workflow

1. Invoke Context7 bootstrap retrieval before implementation.
2. Retrieve focused docs for exact symbols/features needed.
3. Extract version/freshness cues when available.
4. Apply results to implementation decisions.

For must-run scenarios, do not skip Context7 retrieval.

## Skip Conditions

You may skip Context7 retrieval only for purely local refactors with no third-party API behavior changes.
If skipped, state the reason clearly in completion notes.

## Output Requirements

- State whether Context7 retrieval ran.
- Summarize key API facts used.
- Identify any remaining uncertainty.
- Include evidence: Context7 library IDs and topic queries used.

## Unavailable Context7

- In must-run scenarios: stop and report the blocker instead of proceeding with ungrounded changes.
- In may-skip scenarios: proceed with local context only and explicitly mark reduced confidence.

## Safety

- Never include API keys, tokens, or credentials in repo files.
- This repository defaults to keyless personal Context7 MCP, and optional API-key configurations are allowed for users who enable them locally.
