# Codebase Context Metrics

**Last Updated**: 2026-02-27

Purpose: provide lightweight context-sizing guidance for human and AI contributors.

| Category               | Files | Lines  | Tokens    |
| ---------------------- | ----- | ------ | --------- |
| **Total**              | 701   | 225.4K | **~1.9M** |
| Code (Python + JS/CSS) | 453   | 160.8K | ~1.4M     |
| Python (no tests)      | 370   | 148.2K | ~1.3M     |
| Frontend (JS/CSS)      | 83    | 12.6K  | ~80.4K    |
| Tests                  | 148   | 42.9K  | ~370.2K   |
| Documentation (MD)     | 100   | 21.7K  | ~164.7K   |

## Agent Guidance

- **Recommended strategy**: `strict-chunking`
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 148 test files (19% of codebase)
