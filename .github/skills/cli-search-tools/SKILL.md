---
name: cli-search-tools
description: 'Optimally use rg (ripgrep), fd, jq, and yq for code exploration, file discovery, and structured data querying in any repository. Use when asked to search code, find files, grep for patterns, explore a codebase structure, parse JSON or YAML configs, inspect package.json or pyproject.toml, extract API response data, find all usages of a function or variable, or filter results across file types. Works with any language, framework, or project structure.'
---

# CLI Search Tools

Four focused tools that cover nearly all read-only codebase exploration and structured data tasks. Prefer these over native shell search commands — they are faster, smarter, and composable.

| Tool | Purpose                      | Best for                                               |
| ---- | ---------------------------- | ------------------------------------------------------ |
| `rg` | Fast regex content search    | Finding where identifiers, strings, or patterns appear |
| `fd` | Fast file/directory finder   | Discovering files by name, extension, or location      |
| `jq` | JSON stream processor        | Parsing, filtering, and transforming JSON data         |
| `yq` | YAML/JSON/XML/TOML processor | Reading and querying structured config files           |

## When to Use This Skill

- Searching for function, class, or variable usages across a codebase
- Finding files by name, extension, or directory pattern
- Parsing `package.json`, `pyproject.toml`, `*.yaml`, or any structured config
- Extracting data from API JSON responses or log files
- Exploring an unfamiliar codebase efficiently before making changes
- Combining search and structured parsing in a pipeline

## Prerequisites

Check availability before use:

```bash
# Windows (Git Bash) or macOS/Linux
rg --version && fd --version && jq --version && yq --version
```

```powershell
# Windows (PowerShell fallback)
rg --version; fd --version; jq --version; yq --version
```

**Install if missing:**

```bash
# Windows (Git Bash or PowerShell — winget)
winget install BurntSushi.ripgrep.MSVC sharkdp.fd jqlang.jq MikeFarah.yq
```

```bash
# macOS/Linux (Homebrew)
brew install ripgrep fd jq yq
```

## Tool Selection Guide

```
Search file CONTENTS for text or pattern?  → rg
FIND files by name, extension, location?   → fd
Query or transform JSON data?              → jq
Query or transform YAML / TOML / XML?      → yq
Find files, then search their contents?    → fd | rg  (or rg with globs)
Search and parse JSON in rg output?        → rg --json | jq
```

---

## rg — Content Search

### Essentials

```bash
rg "pattern"                    # Search all files
rg -i "pattern"                 # Case-insensitive
rg -F "exact.string"            # Fixed string (no regex; faster for literals)
rg -w "word"                    # Whole-word match
rg -l "pattern"                 # List matching filenames only
rg -c "pattern"                 # Count matches per file
rg -C 3 "pattern"               # 3 lines of context around each match
rg -n "pattern"                 # Show line numbers (default; explicit)
```

### Filter by File Type

```bash
rg "pattern" --type py          # Python files
rg "pattern" --type js          # JavaScript
rg "pattern" --type ts          # TypeScript
rg "pattern" --type json        # JSON
rg "pattern" --type yaml        # YAML
rg --type-list                  # List all known type aliases
rg "pattern" -g "*.test.ts"     # Include glob
rg "pattern" -g "!*.test.ts"    # Exclude glob
```

### Scope and Exclusion

```bash
rg "pattern" src/               # Scope to directory
rg "pattern" -g "!node_modules/**"   # Exclude directory
rg "pattern" --hidden           # Include hidden files
rg "pattern" --max-depth 3      # Limit traversal depth
rg "pattern" -L                 # Follow symlinks
```

### Structured Output (for Piping)

```bash
# JSON output — most robust for programmatic consumption
rg "pattern" --json | jq 'select(.type=="match") | .data.path.text'

# Null-delimited filenames — safe for filenames with spaces
rg -l0 "pattern" | xargs -0 wc -l

# No filename prefix (useful in single-file mode)
rg "pattern" --no-filename src/module.py
```

### Code Exploration Patterns

```bash
# All function definitions
rg "^def " --type py
rg "^(export )?function " --type js
rg "^(export )?(async )?function\b" --type ts

# All class definitions
rg "^class " --type py
rg "^(export )?(abstract )?class " --type ts

# All usages of an identifier
rg "\bmyFunction\b"

# All TODO / FIXME comments
rg "TODO|FIXME|HACK|XXX"

# All imports of a specific module
rg "from mymodule import|import mymodule" --type py

# All error / exception handling blocks
rg "except .+:" --type py
rg "catch\s*\(" --type ts
```

---

## fd — File Discovery

### Essentials

```bash
fd "config"                     # Substring match on filename (smart-case)
fd -e py                        # By extension
fd -e yaml -e yml               # Multiple extensions
fd "\.test\.(ts|js)$"           # Regex pattern
fd -t d "src"                   # Directories only
fd -t f "readme"                # Files only
```

### Scoping and Exclusion

```bash
fd "pattern" src/               # Scope to directory
fd "pattern" --exclude node_modules --exclude .git
fd -H "pattern"                 # Include hidden files
fd "pattern" --max-depth 2      # Limit depth
fd "pattern" --absolute-path    # Output absolute paths
```

### Output and Piping

```bash
# Execute a command for each result
fd -e py --exec rg "TODO" {}

# Null-delimited output — safe for filenames with spaces
fd -0 "pattern" | xargs -0 wc -l

# Collect results into a list
fd -e json --max-depth 1
```

### Common Discovery Tasks

```bash
# Test files
fd "test_" -e py
fd "\.spec\.(ts|js)$"
fd "\.test\.(ts|js)$"

# Config files at repo root
fd -e yaml -e yml -e toml -e json --max-depth 2

# All documentation
fd -e md

# Recently modified files (last 7 days)
fd --changed-within 7d

# Large files (over 1 MB)
fd --size +1mb
```

---

## jq — JSON Query

### Essentials

```bash
jq '.'                          # Pretty-print
jq '.field'                     # Top-level field
jq '.parent.child'              # Nested field
jq '.[0]'                       # First array element
jq '.items[]'                   # Iterate array
jq -r '.version'                # Raw string output (strip quotes)
jq -c '.items[]'                # Compact (one object per line)
```

### Filtering and Conditions

```bash
jq '.items[] | select(.status == "active")'
jq '.items[] | select(.id != null)'
jq '.items[] | select(.count > 10)'
jq '.items[] | select(.name | contains("api"))'
```

### Common Repo Tasks

```bash
# package.json
jq '.version' package.json
jq '.dependencies | keys' package.json
jq '.scripts' package.json

# Parse rg --json output
rg "pattern" --json | jq -r 'select(.type=="match") | .data.path.text' | sort -u

# Count matches per file from rg JSON
rg "pattern" --json \
  | jq -r 'select(.type=="match") | .data.path.text' \
  | sort | uniq -c | sort -rn

# Summarize JSON config keys
jq 'keys' file.json
```

### Transformation

```bash
# Project/reshape
jq '[.items[] | {id: .id, label: .name}]'

# Flatten nested arrays
jq '[.items[] | .tags[]] | unique'

# Group and count
jq '[.items[] | .status] | group_by(.) | map({status: .[0], count: length})'

# Modify a field
jq '.version = "2.0.0"' file.json

# Delete a field
jq 'del(.private)' package.json
```

---

## yq — YAML / TOML / XML Query

### Essentials

```bash
yq '.'                          # Pretty-print YAML
yq '.field' file.yaml           # Top-level field
yq '.parent.child' config.yaml  # Nested field
yq '.tool.ruff.line-length' pyproject.toml   # TOML field
yq '.version' package.json      # JSON (yq handles all formats)
```

### Common Config Exploration

```bash
# GitHub Actions
yq '.jobs | keys' .github/workflows/ci.yml
yq '.jobs.build.steps[].name' .github/workflows/ci.yml
yq '.on' .github/workflows/release.yml

# Docker Compose
yq '.services | keys' docker-compose.yml
yq '.services.app.environment' docker-compose.yml

# pyproject.toml
yq '.project.version' pyproject.toml
yq '.project.dependencies' pyproject.toml
yq '.tool.ruff.line-length' pyproject.toml

# Kubernetes manifests
yq '.metadata.name' deployment.yaml
yq '.spec.containers[].image' deployment.yaml

# Multi-document YAML: select by kind
yq 'select(.kind == "Deployment") | .metadata.name' manifests.yaml
```

### Format Conversion

```bash
# YAML → JSON (pipe to jq)
yq -o=json file.yaml | jq '.field'

# JSON → YAML
yq -o=yaml file.json

# TOML → JSON (pipe to jq)
yq -o=json pyproject.toml | jq '.tool.ruff'
```

---

## Combined Power Patterns

```bash
# Find Python files containing a deprecated call
fd -e py --exec rg -l "old_function" {} | sort

# Find all GitHub Actions workflows that reference a specific action
fd -e yml -e yaml .github/ --exec rg -l "uses: actions/checkout" {}

# Summarize all JSON configs at the repo root
fd -e json --max-depth 1 --exec sh -c 'echo "=== {} ==="; jq "keys" {}'

# Find all TODO comments and report with context
rg -n "TODO|FIXME" -C 1 --type py

# Get all unique import targets across a Python project
rg "^from (.+) import|^import (.+)" --type py -o --no-filename | sort -u

# Parse rg JSON output for structured analysis
rg "def test_" --json --type py \
  | jq -r 'select(.type=="match") | "\(.data.path.text):\(.data.line_number)"'

# Inspect all pyproject.toml dependency lists across a monorepo
fd "pyproject.toml" --exec yq '.project.dependencies' {}
```

---

## Output Format Tips for AI Agent Use

- Prefer `rg --json | jq` over parsing plain rg output — handles filenames with colons or spaces
- Use `jq -r` for raw strings when embedding results in further shell commands
- Use `fd -0 | xargs -0` for filenames that may contain spaces
- Use `yq -o=json | jq` when you need YAML data fed into a jq pipeline
- Use `rg -l` (filenames only) when building a file list to pass to other tools
- On Windows PowerShell, pipe works the same; prefer single quotes inside double-quoted `-e` expressions

## References

- Advanced patterns reference: `references/advanced-patterns.md`
- ripgrep guide: https://github.com/BurntSushi/ripgrep/blob/master/GUIDE.md
- jq manual: https://jqlang.org/jq/manual/
- yq documentation: https://mikefarah.gitbook.io/yq/
- fd documentation: https://github.com/sharkdp/fd#readme
