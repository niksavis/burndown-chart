---
applyTo: '**/*.py,tests/**/*.py,release.py,regenerate_changelog.py'
description: 'Enforce shell + venv command patterns for Python tasks (Git Bash, PowerShell, WSL)'
---

# Terminal + Python Environment Instructions

When executing Python commands in this repository, choose the appropriate shell and
activate the virtual environment in the same command invocation.

## Shell Priority (Windows)

1. **Git Bash** (primary) — Unix commands work natively; default VS Code terminal.
2. **PowerShell** — fallback when Git Bash is unavailable.
3. **WSL (bash/zsh)** — for Linux-native workflows.

## Activation Patterns

| Shell | Activation |
|---|---|
| Git Bash (Windows) | `source .venv/Scripts/activate` |
| PowerShell (Windows) | `.venv\Scripts\Activate.ps1; <command>` |
| macOS / Linux / WSL | `source .venv/bin/activate` |

Alternatively, call the venv interpreter directly (no activation needed):

| Shell | Direct call |
|---|---|
| Git Bash / macOS / Linux / WSL | `.venv/bin/python <args>` or `.venv/Scripts/python.exe <args>` |
| PowerShell | `.venv\Scripts\python.exe <args>` |

## Rules

- Do not assume terminal state persists between commands — always activate in the same invocation.
- Git Bash: use Unix utilities (`grep`, `find`, `cat`, `rg`, `fd`).
- PowerShell: use `Get-ChildItem`, `Select-String`, `Copy-Item -Force` when Git Bash is unavailable.
- Never use `python -c "..."` inline snippets in PowerShell for complex quoting; write a temporary `.py` file instead.

## Fallback Strategy

If the default Git Bash profile is unavailable, switch to PowerShell (`PowerShell (.venv)` profile)
or the built-in Ubuntu (WSL) terminal in VS Code.

## VS Code Terminal Activation

`python.terminal.activateEnvironment` is set to `false` — VS Code must NOT auto-inject
venv activation into all terminals (it breaks WSL and plain shell profiles).

Only the explicitly named `.venv` profiles activate the virtual environment:

| Profile | Activation mechanism |
|---|---|
| `Git Bash (.venv)` | `--init-file .venv/Scripts/activate` (no `--login`; sourced instead of `~/.bashrc`) |
| `PowerShell (.venv)` | `-NoExit -Command & '.venv\Scripts\Activate.ps1'` |

Plain `Git Bash`, `PowerShell`, and the Ubuntu (WSL) built-in profile do **not** activate
the venv automatically.

If commands fail:

1. Re-check venv activation pattern for the active shell.
2. Re-run with explicit command and concise diagnostics.
3. Avoid introducing workaround scripts unless requested.
