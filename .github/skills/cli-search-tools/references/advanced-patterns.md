# Advanced CLI Search Tool Patterns

Reference for complex, less-common, or tool-combination patterns. Load this when the standard SKILL.md patterns are insufficient.

---

## rg — Advanced Patterns

### Multiline Search

```bash
# Match patterns spanning multiple lines
rg -U "def foo\([^)]*\)\s*:" --type py

# Find function followed by a specific decorator pattern
rg -U "@deprecated\n.+def " --type py
```

### Replacement / Rewrite (dry-run inspection)

```bash
# Show what rg would replace (does NOT modify files)
rg "old_name" --replace "new_name" --passthru src/

# Preview replacements inline, then pipe to file
rg "old_name" --replace "new_name" --no-filename src/module.py > /tmp/preview.py
```

### Stats and Summary

```bash
# Summary line count only
rg "pattern" --count-matches

# Print stats (files searched, lines searched, matches)
rg "pattern" --stats

# Suppress output, only show stats
rg "pattern" --stats -q
```

### Ignore Files

```bash
# Skip .gitignore rules (search everything)
rg "pattern" --no-ignore

# Use a custom ignore file
rg "pattern" --ignore-file .myignore

# Search only tracked git files (via git + rg)
git ls-files | xargs rg "pattern"
```

### Max Matches and Limits

```bash
# Stop after N total matches
rg "pattern" --max-count 20

# Limit match length (avoid huge single-line matches)
rg "pattern" --max-columns 200

# Only show filenames with more than N matches
rg -c "pattern" | awk -F: '$2 > 5'
```

---

## fd — Advanced Patterns

### Size and Time Filters

```bash
# Files modified in last 24 hours
fd --changed-within 24h

# Files NOT modified in last 30 days
fd --changed-before 30d

# Files between 10KB and 1MB
fd --size +10k --size -1m

# Empty files
fd --size 0b
```

### Permission and Ownership

```bash
# Executable files
fd --type x

# Readable files matching pattern
fd -e sh --type x
```

### Parallel Execution

```bash
# Run command on each result in parallel (--threads N)
fd -e py --exec-batch rg "TODO" {} +

# Batch mode: pass all results as arguments at once
fd -e json --exec-batch jq '.' {} +
```

### Integration with git

```bash
# Find untracked files (not in .gitignore)
fd --no-ignore-vcs -t f | grep -v ".git"

# Find changed files (use git diff instead, but fd can scope)
fd "\.py$" --changed-within 1d
```

---

## jq — Advanced Patterns

### Path Expressions

```bash
# Get path to a value
jq 'path(.a.b.c)' file.json

# Get all paths in document
jq '[paths]' file.json

# Get all string leaf values
jq '[leaf_paths as $p | {path: $p, value: getpath($p)} | select(.value | type == "string")]' file.json
```

### Reduce and Aggregation

```bash
# Sum a field across all items
jq '[.items[].count] | add' file.json

# Max value
jq '[.items[].score] | max' file.json

# Reduce with accumulator
jq 'reduce .items[] as $i (0; . + $i.count)' file.json
```

### Environment Variables in jq

```bash
# Pass shell variable into jq
VERSION="1.2.3"
jq --arg ver "$VERSION" '.version = $ver' package.json

# Pass numeric value
jq --argjson limit 10 '.items[] | select(.count > $limit)' file.json

# Read from file
jq --slurpfile extra extras.json '.items + $extra[0].items' file.json
```

### Streaming and Large Files

```bash
# Stream large JSON without loading all into memory
jq -c '.[]' large.json | while read -r line; do echo "$line" | jq '.id'; done

# First N items only
jq '.items[:10]' file.json

# Last N items
jq '.items[-5:]' file.json
```

### Null Safety

```bash
# Default when field missing
jq '.field // "default"' file.json

# Skip null items
jq '.items[] | select(. != null)' file.json

# Safe nested access
jq '.a?.b?.c?' file.json
```

### Multiple Files

```bash
# Process multiple files with filename context
jq -r '"\(input_filename): \(.version)"' package.json other/package.json

# Slurp: read all files into an array
jq -s '.' *.json

# Slurp and merge
jq -s 'add' config1.json config2.json
```

---

## yq — Advanced Patterns

### In-Place Editing

```bash
# Modify a YAML file in place
yq -i '.version = "2.0.0"' pyproject.toml

# Add a key
yq -i '.project.keywords += ["new-keyword"]' pyproject.toml

# Delete a key
yq -i 'del(.debug)' config.yaml
```

### Multi-document YAML

```bash
# Count documents in multi-doc file
yq '. | document_index' multi.yaml | tail -1

# Process each document separately
yq -s '.' multi.yaml

# Filter by kind (Kubernetes)
yq 'select(.kind == "Service")' manifests.yaml
yq 'select(.kind == "Deployment") | .metadata.labels' manifests.yaml
```

### Merging YAML/JSON

```bash
# Merge two YAML files (second overrides first)
yq eval-all 'select(fileIndex == 0) * select(fileIndex == 1)' base.yaml override.yaml

# Merge and output as JSON
yq eval-all -o=json 'select(fileIndex == 0) * select(fileIndex == 1)' a.yaml b.yaml
```

### TOML-specific Patterns

```bash
# Read all tool configurations from pyproject.toml
yq '.tool | keys' pyproject.toml

# Read ruff configuration
yq '.tool.ruff' pyproject.toml

# Read pytest configuration
yq '.tool.pytest."ini_options"' pyproject.toml

# Convert TOML to JSON for complex jq queries
yq -o=json pyproject.toml | jq '.tool | to_entries[] | .key'
```

---

## Cross-Tool Pipelines

### Codebase Health Snapshot

```bash
# Count lines of code by type
fd -e py --exec wc -l {} | awk '{sum += $1} END {print sum " total Python lines"}'
fd -e ts -e js --exec wc -l {} | awk '{sum += $1} END {print sum " total JS/TS lines"}'

# Top files by TODO count
rg -c "TODO|FIXME" --type py | sort -t: -k2 -rn | head -10
```

### Dependency Analysis

```bash
# All direct Python imports in a package
rg "^import |^from " --type py --no-filename | sort -u

# Which files import a specific module
rg -l "\bmodule_name\b" --type py

# All external packages referenced in source
rg "^from (\w+)" --type py -o --no-filename \
  | sed 's/from //' | sort -u
```

### Config Validation Pipeline

```bash
# Validate all JSON files are parseable
fd -e json --exec sh -c 'jq empty {} && echo "OK: {}" || echo "FAIL: {}"'

# Validate all YAML files are parseable
fd -e yaml -e yml --exec sh -c 'yq . {} > /dev/null && echo "OK: {}" || echo "FAIL: {}"'
```

### Git + Search Combinations

```bash
# Search only staged files
git diff --cached --name-only | xargs rg "pattern"

# Search only files changed in last commit
git diff HEAD~1 --name-only | xargs rg "pattern"

# Find large files recently added to git
git ls-files | xargs fd --absolute-path --size +500k
```

### Windows PowerShell Notes

Most commands work identically on PowerShell. Key differences:

```powershell
# Use semicolons to chain commands (not &&)
rg --version; fd --version

# PowerShell pipe (|) passes objects; use | Select-String for text processing
# Prefer piping through jq/yq for structured output instead

# For null-delimited output, PowerShell does not have xargs -0
# Use fd --exec directly instead
fd -e py --exec rg "TODO" {}

# String quoting: single quotes inside double-quoted expressions
rg "pattern" -g "!node_modules/**"
```
