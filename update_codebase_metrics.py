#!/usr/bin/env python3
"""
Calculate codebase context metrics and write dedicated artifacts.

Run manually when context metrics need refreshing:
python update_codebase_metrics.py

Calculates:
- Total tokens (all tracked files)
- Code only (Python, JavaScript, CSS)
- Documentation (Markdown files)
- Tests (test_*.py, *_test.py files)
- Configuration (YAML, JSON, TOML files)
"""

import json
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
CONTEXT_METRICS_MD = PROJECT_ROOT / "docs" / "codebase_context_metrics.md"
CONTEXT_METRICS_JSON = PROJECT_ROOT / ".github" / "codebase_context_metrics.json"

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
    "ui/dashboard.py",
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


def get_context_strategy(total_tokens: int) -> str:
    """Return recommended context strategy based on estimated token volume."""
    if total_tokens <= 120_000:
        return "single-pass"
    if total_tokens <= 500_000:
        return "targeted-chunking"
    return "strict-chunking"


def generate_metrics_markdown(metrics: dict[str, dict[str, int]]) -> str:
    """Generate markdown report for codebase context metrics."""
    today = datetime.now().strftime("%Y-%m-%d")
    context_strategy = get_context_strategy(metrics["total"]["tokens"])
    total_files = metrics["total"]["files"]
    total_lines = format_number(metrics["total"]["lines"])
    total_tokens = format_number(metrics["total"]["tokens"])
    code_files = metrics["code"]["files"]
    code_lines = format_number(metrics["code"]["lines"])
    code_tokens = format_number(metrics["code"]["tokens"])
    python_files = metrics["python"]["files"]
    python_lines = format_number(metrics["python"]["lines"])
    python_tokens = format_number(metrics["python"]["tokens"])
    frontend_files = metrics["frontend"]["files"]
    frontend_lines = format_number(metrics["frontend"]["lines"])
    frontend_tokens = format_number(metrics["frontend"]["tokens"])
    test_files = metrics["tests"]["files"]
    test_lines = format_number(metrics["tests"]["lines"])
    test_tokens = format_number(metrics["tests"]["tokens"])
    docs_files = metrics["docs"]["files"]
    docs_lines = format_number(metrics["docs"]["lines"])
    docs_tokens = format_number(metrics["docs"]["tokens"])
    tests_pct = metrics["tests"]["tokens"] / metrics["total"]["tokens"] * 100

    section = f"""# Codebase Context Metrics

**Last Updated**: {today}

Purpose: provide lightweight context-sizing guidance for human and AI contributors.

| Category | Files | Lines | Tokens |
|----------|-------|-------|--------|
| **Total** | {total_files} | {total_lines} | **~{total_tokens}** |
| Code (Python + JS/CSS) | {code_files} | {code_lines} | ~{code_tokens} |
| Python (no tests) | {python_files} | {python_lines} | ~{python_tokens} |
| Frontend (JS/CSS) | {frontend_files} | {frontend_lines} | ~{frontend_tokens} |
| Tests | {test_files} | {test_lines} | ~{test_tokens} |
| Documentation (MD) | {docs_files} | {docs_lines} | ~{docs_tokens} |

## Agent Guidance

- **Recommended strategy**: `{context_strategy}`
- **Too large for context**: Use targeted `semantic_search`, avoid broad reads
- **File size check**: Prefer reading <500 lines per file
- **Module focus**: Target specific folders (data/, ui/, callbacks/, etc.)
- **Test coverage**: {test_files} test files ({tests_pct:.0f}% of codebase)

"""
    return section


def write_metrics_files(metrics: dict[str, dict[str, int]], markdown_text: str) -> None:
    """Write dedicated markdown and JSON metrics artifacts."""
    CONTEXT_METRICS_MD.parent.mkdir(parents=True, exist_ok=True)
    CONTEXT_METRICS_JSON.parent.mkdir(parents=True, exist_ok=True)

    CONTEXT_METRICS_MD.write_text(markdown_text, encoding="utf-8")

    payload = {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "recommended_strategy": get_context_strategy(metrics["total"]["tokens"]),
        "metrics": metrics,
        "guidance": {
            "max_lines_per_read": 500,
            "use_semantic_search": True,
            "focus_folders": ["data", "ui", "callbacks", "visualization"],
        },
    }
    CONTEXT_METRICS_JSON.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )

    print(f"[OK] Updated {CONTEXT_METRICS_MD.relative_to(PROJECT_ROOT)}")
    print(f"[OK] Updated {CONTEXT_METRICS_JSON.relative_to(PROJECT_ROOT)}")


def commit_changes() -> bool:
    """Commit context metrics artifact changes to git if modified."""
    import subprocess

    try:
        # Check if metrics artifacts were modified
        result = subprocess.run(
            [
                "git",
                "status",
                "--porcelain",
                "docs/codebase_context_metrics.md",
                ".github/codebase_context_metrics.json",
            ],
            capture_output=True,
            text=True,
            cwd=PROJECT_ROOT,
        )

        if not result.stdout.strip():
            print("[OK] No changes to commit (metrics already up to date)")
            return True

        # Stage metrics artifacts
        subprocess.run(
            [
                "git",
                "add",
                "docs/codebase_context_metrics.md",
                ".github/codebase_context_metrics.json",
            ],
            check=True,
            cwd=PROJECT_ROOT,
        )

        # Commit the changes
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "docs(metrics): update codebase context metrics",
            ],
            check=True,
            cwd=PROJECT_ROOT,
        )

        print("[OK] Changes committed to git")
        return True

    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Could not commit changes: {e}")
        print("  (context metrics artifacts were updated but not committed)")
        return False
    except Exception as e:
        print(f"[WARNING] Git operation failed: {e}")
        return False


def main() -> None:
    """Calculate metrics and update dedicated context metrics artifacts."""
    print("Calculating codebase metrics...")

    metrics = calculate_metrics()

    # Print to console
    print(f"\n{'=' * 60}")
    print("CODEBASE METRICS")
    print(f"{'=' * 60}")
    print(
        "Total:      "
        f"{metrics['total']['files']:3} files | "
        f"{format_number(metrics['total']['tokens']):>6} tokens"
    )
    print(
        "Code:       "
        f"{metrics['code']['files']:3} files | "
        f"{format_number(metrics['code']['tokens']):>6} tokens"
    )
    print(
        "Tests:      "
        f"{metrics['tests']['files']:3} files | "
        f"{format_number(metrics['tests']['tokens']):>6} tokens"
    )
    print(
        "Docs:       "
        f"{metrics['docs']['files']:3} files | "
        f"{format_number(metrics['docs']['tokens']):>6} tokens"
    )
    print(f"{'=' * 60}\n")

    # Update dedicated metrics artifacts
    metrics_markdown = generate_metrics_markdown(metrics)
    write_metrics_files(metrics, metrics_markdown)

    # Commit changes to git
    commit_changes()

    print("[SUCCESS] Context metrics artifacts updated")


if __name__ == "__main__":
    main()
