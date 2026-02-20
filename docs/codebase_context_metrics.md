# Codebase Context Metrics

**Last Updated**: 2026-02-20

Purpose: provide lightweight context-sizing guidance for human and AI contributors.

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 669 | 213.6K | **~1.9M** |
| Code (Python + JS/CSS) | 445 | 154.8K | ~1.4M |
| Python (no tests) | 362 | 142.0K | ~1.3M |
| Frontend (JS/CSS) | 83 | 12.8K | ~81.7K |
| Tests | 149 | 42.9K | ~375.4K |
| Documentation (MD) | 75 | 15.9K | ~124.1K |

## Agent Guidance

- **Recommended strategy**: `strict-chunking`
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 149 test files (20% of codebase)

