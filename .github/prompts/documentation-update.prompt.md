---
agent: 'agent'
description: 'Generate documentation updates that stay accurate and helpful'
---

Update documentation for this change in `burndown-chart`.

Change description: ${input:change}

## Output format

1. **Files to update**: List specific doc files that need updates (max 5)
2. **Content changes**: For each file, provide updated sections with:
   - What changed (1-2 sentences)
   - New/updated content (markdown)
   - Reason for change (accuracy, completeness, clarity)
3. **Cross-references**: Other docs to check for consistency
4. **Validation**: How to verify docs match implementation

## Documentation principles

- **Accuracy first**: Docs must match actual code behavior
- **Completeness**: Cover common use cases and edge cases
- **Conciseness**: Respect reader's time, no fluff
- **Examples**: Show code examples for complex topics
- **Up-to-date**: Remove outdated content, add deprecation notices
- **Linked**: Cross-reference related docs

## Documentation types

### Architecture docs (`docs/architecture/`)

Update when: Code structure, patterns, or guidelines change
Focus: How and why, not what (code already shows what)

### Feature docs (`docs/`)

Update when: User-facing behavior changes
Focus: How users accomplish tasks, screenshots if helpful

### API/Integration docs

Update when: Public interfaces, data formats, or endpoints change
Focus: Contract definitions, request/response examples

### README and quickstart

Update when: Installation, setup, or first-run experience changes
Focus: Getting started quickly, minimal barrier to entry

## Common update patterns

### New feature

- Add section to relevant feature doc
- Update README if user-facing
- Add to metrics_index.md if new metric
- Update screenshots if UI changed

### Breaking change

- Add deprecation notice to old approach
- Document migration path
- Update examples to new API
- Add to changelog.md

### Bug fix

- Update docs if behavior description was wrong
- Add edge case documentation if missing
- No update needed if docs already correct

### Refactor (no behavior change)

- Usually no doc update needed
- Update if internal architecture docs reference old structure

## Validation checklist

- [ ] Code behavior matches doc description
- [ ] Examples are tested and work
- [ ] Links are not broken (relative paths)
- [ ] Markdown formatting correct
- [ ] No customer data in examples
- [ ] Cross-references updated
- [ ] Run `get_errors` on changed .md files

## Related files

- `docs/readme.md` - Documentation index
- `docs/metrics_index.md` - Metrics documentation index
- `readme.md` - Main README
- `changelog.md` - Change history
