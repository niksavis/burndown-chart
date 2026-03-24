# Codebase Context Metrics

**Last Updated**: 2026-03-24

Purpose: provide lightweight context-sizing guidance for human and AI contributors.

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | 864 | 234.8K | **~2.1M** |
| Code (Python + JS/CSS) | 599 | 166.4K | ~1.5M |
| Python (no tests) | 510 | 153.5K | ~1.4M |
| Frontend (JS/CSS) | 89 | 12.9K | ~86.4K |
| Tests | 160 | 44.9K | ~407.4K |
| Documentation (MD) | 105 | 23.5K | ~188.7K |

## Agent Guidance

- **Recommended strategy**: `strict-chunking`
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: 160 test files (20% of codebase)

