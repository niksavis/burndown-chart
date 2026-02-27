# Codebase Context Metrics

**Last Updated**: 2026-02-27

Purpose: provide lightweight context-sizing guidance for human and AI contributors.

| Category               | Files | Lines  | Tokens    |
| ---------------------- | ----- | ------ | --------- |
| **Total**              | 703   | 226.3K | **~1.9M** |
| Code (Python + JS/CSS) | 454   | 161.5K | ~1.4M     |
| Python (no tests)      | 371   | 148.9K | ~1.3M     |
| Frontend (JS/CSS)      | 83    | 12.6K  | ~80.4K    |
| Tests                  | 149   | 43.2K  | ~372.5K   |
| Documentation (MD)     | 100   | 21.7K  | ~164.6K   |

## Agent Guidance

- **Recommended strategy**: `strict-chunking`
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 149 test files (19% of codebase)
