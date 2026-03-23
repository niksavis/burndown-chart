# Codebase Context Metrics

**Last Updated**: 2026-03-23

Purpose: provide lightweight context-sizing guidance for human and AI contributors.

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 861 | 234.3K | **~2.1M** |
| Code (Python + JS/CSS) | 598 | 166.2K | ~1.5M |
| Python (no tests) | 510 | 153.3K | ~1.4M |
| Frontend (JS/CSS) | 88 | 12.9K | ~85.9K |
| Tests | 159 | 44.8K | ~406.8K |
| Documentation (MD) | 104 | 23.3K | ~186.4K |

## Agent Guidance

- **Recommended strategy**: `strict-chunking`
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 159 test files (20% of codebase)

