#!/usr/bin/env python3
"""
Calculate codebase metrics and update agents.md.

Called automatically by release.py to keep metrics fresh.
Can also be run manually: python update_codebase_metrics.py

Calculates:
- Total tokens (all tracked files)
- Code only (Python, JavaScript, CSS)
- Documentation (Markdown files)
- Tests (test_*.py, *_test.py files)
- Configuration (YAML, JSON, TOML files)
"""

import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
AGENTS_MD = PROJECT_ROOT / "agents.md"

# File patterns to exclude
EXCLUDE_PATTERNS = [
    "__pycache__",
    ".venv",
    "node_modules",
    "build/app",
    "build/updater",
    ".min.",
]

# Representative files for calibrating token ratio (cover all layers & sizes)
CALIBRATION_FILES = [
    # Configuration (small to large)
    "configuration/__init__.py",
    "configuration/logging_config.py",
    "configuration/metrics_config.py",
    "configuration/chart_config.py",
    # Data layer (small to large)
    "data/installation_context.py",
    "data/jira_query_manager.py",
    "data/field_mapper.py",
    "data/metrics_cache.py",
    "data/metrics_calculator.py",
    "data/processing.py",
    "data/flow_metrics.py",
    "data/dora_metrics.py",
    "data/bug_insights.py",
    # UI layer (small to large)
    "ui/icon_utils.py",
    "ui/error_utils.py",
    "ui/layout.py",
    "ui/jira_config_modal.py",
    "ui/metric_cards.py",
    "ui/dashboard_comprehensive.py",
    "ui/dora_flow_combined_dashboard.py",
    "ui/budget_cards.py",
    # Callbacks (small to large)
    "callbacks/progress_bar.py",
    "callbacks/jira_config.py",
    "callbacks/__init__.py",
    "callbacks/visualization.py",
    "callbacks/query_management.py",
    # Visualization (small to large)
    "visualization/elements.py",
    "visualization/dora_charts.py",
    "visualization/charts.py",
    "visualization/bug_charts.py",
    # Tests (small to large)
    "tests/conftest.py",
    "tests/unit/test_caching_dataframes.py",
    "tests/unit/data/test_metrics_calculator.py",
    "tests/integration/test_dashboard_metrics.py",
    "tests/unit/data/test_flow_metrics_clean.py",
    # Utils (small)
    "utils/__init__.py",
    "utils/caching.py",
    "utils/dataframe_utils.py",
    # Frontend (JS/CSS)
    "assets/jql_editor_native.js",
    "assets/namespace_autocomplete.js",
    "assets/custom.css",
    "assets/quality_insights.js",
    # Root scripts (small to medium)
    "app.py",
    "release.py",
    "update_codebase_metrics.py",
    "regenerate_changelog.py",
]


def should_exclude(file_path: Path) -> bool:
    """Check if file should be excluded from metrics."""
    path_str = str(file_path)
    return any(pattern in path_str for pattern in EXCLUDE_PATTERNS)


def estimate_tokens_heuristic(text: str) -> int:
    """
    Heuristic token estimation based on common tokenization patterns.

    Approximates how tokenizers split code:
    - Words/identifiers split on boundaries
    - Special characters often get their own tokens
    - Common operators might be single tokens
    """
    tokens = 0

    # Split into potential tokens
    # This pattern splits on whitespace and keeps special chars separate
    pattern = r"\w+|[^\w\s]"
    potential_tokens = re.findall(pattern, text)

    for token in potential_tokens:
        if len(token) <= 4:
            # Short tokens typically = 1 token
            tokens += 1
        else:
            # Longer identifiers might split (conservative estimate)
            tokens += max(1, len(token) // 4)

    return tokens


def calculate_token_ratio() -> float:
    """
    Calculate the chars-per-token ratio by testing representative files.

    Returns:
        Average chars per token across calibration files (e.g., 4.26)
    """
    total_chars = 0
    total_tokens = 0
    files_tested = 0

    for file_path_str in CALIBRATION_FILES:
        file_path = PROJECT_ROOT / file_path_str
        if not file_path.exists():
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            chars = len(content)
            tokens = estimate_tokens_heuristic(content)

            if tokens > 0:
                total_chars += chars
                total_tokens += tokens
                files_tested += 1
        except Exception:
            continue

    if total_tokens == 0:
        # Fallback to standard OpenAI estimate if calibration fails
        print("[WARNING] Token ratio calibration failed, using default 4.0")
        return 4.0

    ratio = total_chars / total_tokens
    print(
        f"[OK] Token ratio calibrated on {files_tested} files: {ratio:.2f} chars/token"
    )
    return ratio


def count_tokens(files: list[Path], divisor: float) -> tuple[int, int, int]:
    """Count characters, lines, and estimated tokens for files.

    Args:
        files: List of file paths to analyze
        divisor: Chars-per-token ratio (dynamically calculated)

    Returns:
        tuple[chars, lines, tokens] using the provided divisor
    """
    total_chars = 0
    total_lines = 0

    for file_path in files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            total_chars += len(content)
            total_lines += content.count("\n") + 1
        except Exception:
            continue

    tokens = int(total_chars / divisor)
    return total_chars, total_lines, tokens


def get_files_by_pattern(pattern: str) -> list[Path]:
    """Get all files matching glob pattern, excluding blacklisted paths."""
    return [
        f for f in PROJECT_ROOT.rglob(pattern) if f.is_file() and not should_exclude(f)
    ]


def calculate_metrics() -> dict[str, dict[str, int]]:
    """Calculate comprehensive codebase metrics."""

    # First, calibrate the token ratio on representative files
    divisor = calculate_token_ratio()

    # Get files by category
    python_files = get_files_by_pattern("*.py")
    js_files = get_files_by_pattern("*.js")
    css_files = get_files_by_pattern("*.css")
    md_files = get_files_by_pattern("*.md")

    # Filter test files from Python
    test_files = [f for f in python_files if "test" in f.stem or f.parts[-2] == "tests"]
    code_python_files = [f for f in python_files if f not in test_files]

    # Calculate metrics
    metrics = {}

    # Total (all tracked files)
    all_files = python_files + js_files + css_files + md_files
    chars, lines, tokens = count_tokens(all_files, divisor)
    metrics["total"] = {
        "files": len(all_files),
        "lines": lines,
        "chars": chars,
        "tokens": tokens,
    }

    # Code only (Python, JS, CSS - no tests, no docs)
    code_files = code_python_files + js_files + css_files
    chars, lines, tokens = count_tokens(code_files, divisor)
    metrics["code"] = {
        "files": len(code_files),
        "lines": lines,
        "chars": chars,
        "tokens": tokens,
    }

    # Documentation only
    chars, lines, tokens = count_tokens(md_files, divisor)
    metrics["docs"] = {
        "files": len(md_files),
        "lines": lines,
        "chars": chars,
        "tokens": tokens,
    }

    # Tests only
    chars, lines, tokens = count_tokens(test_files, divisor)
    metrics["tests"] = {
        "files": len(test_files),
        "lines": lines,
        "chars": chars,
        "tokens": tokens,
    }

    # Python only (excluding tests)
    chars, lines, tokens = count_tokens(code_python_files, divisor)
    metrics["python"] = {
        "files": len(code_python_files),
        "lines": lines,
        "chars": chars,
        "tokens": tokens,
    }

    # Frontend only (JS + CSS)
    frontend_files = js_files + css_files
    chars, lines, tokens = count_tokens(frontend_files, divisor)
    metrics["frontend"] = {
        "files": len(frontend_files),
        "lines": lines,
        "chars": chars,
        "tokens": tokens,
    }

    return metrics


def format_number(num: int) -> str:
    """Format large numbers with K/M suffix."""
    if num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    else:
        return str(num)


def generate_metrics_section(metrics: dict[str, dict[str, int]]) -> str:
    """Generate the metrics markdown section."""
    today = datetime.now().strftime("%Y-%m-%d")

    section = f"""## Codebase Metrics

**Last Updated**: {today}

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | {metrics["total"]["files"]} | {format_number(metrics["total"]["lines"])} | **~{format_number(metrics["total"]["tokens"])}** |
| Code (Python + JS/CSS) | {metrics["code"]["files"]} | {format_number(metrics["code"]["lines"])} | ~{format_number(metrics["code"]["tokens"])} |
| Python (no tests) | {metrics["python"]["files"]} | {format_number(metrics["python"]["lines"])} | ~{format_number(metrics["python"]["tokens"])} |
| Frontend (JS/CSS) | {metrics["frontend"]["files"]} | {format_number(metrics["frontend"]["lines"])} | ~{format_number(metrics["frontend"]["tokens"])} |
| Tests | {metrics["tests"]["files"]} | {format_number(metrics["tests"]["lines"])} | ~{format_number(metrics["tests"]["tokens"])} |
| Documentation (MD) | {metrics["docs"]["files"]} | {format_number(metrics["docs"]["lines"])} | ~{format_number(metrics["docs"]["tokens"])} |

**Agent Guidance**:
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: {metrics["tests"]["files"]} test files ({metrics["tests"]["tokens"] / metrics["total"]["tokens"] * 100:.0f}% of codebase)

"""
    return section


def update_agents_md(metrics_section: str) -> None:
    """Update or insert metrics section in agents.md."""

    if not AGENTS_MD.exists():
        print(f"ERROR: {AGENTS_MD} not found")
        return

    content = AGENTS_MD.read_text(encoding="utf-8")

    # Check if metrics section exists
    metrics_pattern = r"## Codebase Metrics\n\n.*?(?=\n## |\Z)"

    if re.search(metrics_pattern, content, re.DOTALL):
        # Replace existing section
        updated = re.sub(
            metrics_pattern, metrics_section.rstrip() + "\n\n", content, flags=re.DOTALL
        )
    else:
        # Insert after title and before first section
        lines = content.split("\n")
        insert_pos = 0

        # Find position after title and blank lines
        for i, line in enumerate(lines):
            if line.startswith("# "):
                # Insert after title and its following blank lines
                insert_pos = i + 1
                while insert_pos < len(lines) and not lines[insert_pos].strip():
                    insert_pos += 1
                break

        lines.insert(insert_pos, metrics_section)
        updated = "\n".join(lines)

    AGENTS_MD.write_text(updated, encoding="utf-8")
    print(f"[OK] Updated {AGENTS_MD.relative_to(PROJECT_ROOT)}")


def commit_changes() -> bool:
    """Commit agents.md changes to git if modified."""
    import subprocess

    try:
        # Check if agents.md was modified
        result = subprocess.run(
            ["git", "status", "--porcelain", "agents.md"],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        if not result.stdout.strip():
            print("[OK] No changes to commit (metrics already up to date)")
            return True

        # Stage agents.md
        subprocess.run(
            ["git", "add", "agents.md"],
            check=True,
            cwd=PROJECT_ROOT,
        )

        # Commit the changes
        subprocess.run(
            ["git", "commit", "-m", "docs(metrics): update codebase metrics"],
            check=True,
            cwd=PROJECT_ROOT,
        )

        print("[OK] Changes committed to git")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Could not commit changes: {e}")
        print("  (agents.md was updated but not committed)")
        return False
    except Exception as e:
        print(f"[WARNING] Git operation failed: {e}")
        return False


def main() -> None:
    """Calculate metrics and update agents.md."""
    print("Calculating codebase metrics...")

    metrics = calculate_metrics()

    # Print to console
    print(f"\n{'=' * 60}")
    print("CODEBASE METRICS")
    print(f"{'=' * 60}")
    print(
        f"Total:      {metrics['total']['files']:3} files | {format_number(metrics['total']['tokens']):>6} tokens"
    )
    print(
        f"Code:       {metrics['code']['files']:3} files | {format_number(metrics['code']['tokens']):>6} tokens"
    )
    print(
        f"Tests:      {metrics['tests']['files']:3} files | {format_number(metrics['tests']['tokens']):>6} tokens"
    )
    print(
        f"Docs:       {metrics['docs']['files']:3} files | {format_number(metrics['docs']['tokens']):>6} tokens"
    )
    print(f"{'=' * 60}\n")

    # Update agents.md
    metrics_section = generate_metrics_section(metrics)
    update_agents_md(metrics_section)

    # Commit changes to git
    commit_changes()

    print("[SUCCESS] Metrics updated in agents.md")


if __name__ == "__main__":
    main()
