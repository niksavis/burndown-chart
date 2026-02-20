# Codebase Context Metrics

**Last Updated**: 2026-02-20

Purpose: provide lightweight context-sizing guidance for human and AI contributors.

| Category               | Files | Lines  | Tokens    |
| ---------------------- | ----- | ------ | --------- |
| **Total**              | 669   | 213.6K | **~1.9M** |
| Code (Python + JS/CSS) | 445   | 154.8K | ~1.4M     |
| Python (no tests)      | 362   | 142.0K | ~1.3M     |
| Frontend (JS/CSS)      | 83    | 12.8K  | ~81.7K    |
| Tests                  | 149   | 42.9K  | ~375.4K   |
| Documentation (MD)     | 75    | 15.9K  | ~124.1K   |

## Agent Guidance

- **Recommended strategy**: `strict-chunking`
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 149 test files (20% of codebase)

## Task-to-Folder Routing

Use this quick reference to identify which folders to focus on for different task types:

| Task Type            | Primary Folders                               | Typical File Count | Documentation                                |
| -------------------- | --------------------------------------------- | ------------------ | -------------------------------------------- |
| Python backend logic | `data/`, `callbacks/`                         | 3-8                | `docs/architecture/python_guidelines.md`     |
| JavaScript/Frontend  | `assets/`, `ui/`                              | 2-5                | `docs/architecture/javascript_guidelines.md` |
| Chart/Visualization  | `visualization/`, `data/`                     | 3-6                | Chart-specific docs in `docs/`               |
| Database/Persistence | `data/persistence/`, `data/migration/`        | 4-10               | `docs/sqlite_persistence.md`                 |
| JIRA Integration     | `data/jira/`, `callbacks/jira_*`              | 3-7                | `docs/jira_configuration.md`                 |
| UI Components        | `ui/`, `assets/`                              | 2-5                | `docs/design_system.md`                      |
| Build/Release        | `build/`, root (`release.py`)                 | 3-6                | `docs/release_process.md`                    |
| Updater System       | `updater/`, `data/update_manager.py`          | 3-5                | `docs/updater_architecture.md`               |
| Configuration        | `configuration/`, `data/config_validation.py` | 2-4                | Config module docstrings                     |
| Testing              | `tests/`, source being tested                 | 2-10               | Test file docstrings                         |
| Documentation        | `docs/`, related code                         | 1-3                | `docs/readme.md`                             |

## Context Loading Strategy

For detailed file routing and context loading strategies, see:

- **[.github/context-routing-map.md](../.github/context-routing-map.md)** - Comprehensive task-to-file mapping
- **[.github/prompts/context-map-burndown.prompt.md](../.github/prompts/context-map-burndown.prompt.md)** - Context mapping prompt
