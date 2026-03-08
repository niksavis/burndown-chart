#!/usr/bin/env python3
"""
validate.py - Quality gate for burndown-chart.

Runs checks appropriate for the current usage context.  Called automatically
by the git hooks installed via install_hooks.py.  Also safe to run manually
at any time.

Modes (choose one):
    python validate.py             # pre-push: full suite (default)
    python validate.py --commit    # pre-commit: ruff lint + format only (~5s)
    python validate.py --fast      # ruff + djlint + pyright + bandit + eslint
    python validate.py --fix       # auto-fix ruff + djlint where possible

Full gate (pre-push) includes:
    ruff, djlint, pyright, bandit, pip-audit, vulture, prettier,
    eslint, markdownlint, pytest with coverage threshold (~44%)

Platform-agnostic: works on Windows, macOS, and Linux.
"""

import argparse
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent
VENV_BIN = ROOT / ".venv" / ("Scripts" if platform.system() == "Windows" else "bin")
PYTHON = VENV_BIN / ("python.exe" if platform.system() == "Windows" else "python")
NPX = shutil.which("npx")


def _run(label: str, cmd: list[str], *, check: bool = True) -> int:
    """Run a command and return its exit code. Print status."""
    print(f"\n[validate] {label}")
    resolved = [str(VENV_BIN / cmd[0]) if _is_venv_tool(cmd[0]) else cmd[0]] + cmd[1:]
    try:
        result = subprocess.run(resolved, cwd=ROOT)
    except KeyboardInterrupt:
        print(f"[validate] {label}: INTERRUPTED")
        # Preserve shell convention for interrupted processes.
        return 130
    status = "OK" if result.returncode == 0 else "FAIL"
    print(f"[validate] {label}: {status}")
    return result.returncode


def _is_venv_tool(name: str) -> bool:
    tool_names = {
        "ruff",
        "pyright",
        "djlint",
        "pytest",
        "bandit",
        "pip-audit",
        "vulture",
    }
    return name in tool_names


def _staged_py_files() -> list[str]:
    """Return a list of staged .py file paths relative to ROOT.

    Returns an empty list when not inside a git repository or when there are
    no staged Python files, so callers can skip ruff gracefully.
    """
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
        cwd=ROOT,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return []
    return [f for f in result.stdout.splitlines() if f.endswith(".py")]


def check_ruff(fix: bool = False, files: list[str] | None = None) -> int:
    args = ["ruff", "check"] + (files if files else ["."])
    if fix:
        args.append("--fix")
    return _run("ruff (lint)", args)


def check_ruff_format(fix: bool = False, files: list[str] | None = None) -> int:
    args = ["ruff", "format"] + (files if files else ["."])
    if not fix:
        args.append("--check")
    return _run("ruff (format)", args)


def check_djlint(fix: bool = False) -> int:
    html_files = "report_assets/**/*.html"
    if fix:
        return _run("djlint (reformat)", ["djlint", "--reformat", html_files])
    return _run("djlint (check)", ["djlint", "--check", html_files])


def check_pyright() -> int:
    return _run(
        "pyright (type check)",
        ["pyright", "data/", "callbacks/", "ui/", "visualization/", "tests/"],
    )


def check_markdownlint() -> int:
    if NPX is None:
        print("[validate] markdownlint: SKIP (npx not found)")
        return 0
    return _run(
        "markdownlint",
        [
            NPX,
            "markdownlint-cli2",
            "**/*.md",
            "#node_modules",
            "#.venv",
            "#build",
            "#cache",
            "#logs",
            "#profiles",
        ],
    )


def check_bandit() -> int:
    candidates = ["data/", "callbacks/", "ui/", "visualization/", "app.py"]
    targets = [t for t in candidates if (ROOT / t.rstrip("/")).exists()]
    return _run(
        "bandit (security lint)",
        [
            "bandit",
            "-r",
            *targets,
            "-c",
            "pyproject.toml",
            "--severity-level",
            "medium",
            "--confidence-level",
            "medium",
        ],
    )


def check_pip_audit() -> int:
    import json

    baseline = ROOT / ".pip-audit-baseline.json"
    # --no-deps: audit packages as listed without resolving in an isolated env.
    # requirements.txt is already compiled (all transitive deps explicit), so
    # dependency resolution is unnecessary and would create a slow temp environment.
    cmd = ["pip-audit", "-r", "requirements.txt", "--no-deps"]
    if baseline.exists():
        try:
            data = json.loads(baseline.read_text(encoding="utf-8"))
            for dep in data.get("dependencies", []):
                for vuln in dep.get("vulns", []):
                    cmd += ["--ignore-vuln", vuln["id"]]
        except Exception:
            pass
    return _run("pip-audit (dependency audit)", cmd)


def check_vulture() -> int:
    # All config (paths, min_confidence, ignore_names) comes from [tool.vulture]
    # in pyproject.toml so no flags are needed here.
    return _run("vulture (dead code)", ["vulture"])


def check_prettier(fix: bool = False) -> int:
    if NPX is None:
        print("[validate] prettier: SKIP (npx not found)")
        return 0
    mode = "--write" if fix else "--check"
    return _run(
        "prettier (format)",
        [
            NPX,
            "prettier",
            mode,
            "--ignore-path",
            ".prettierignore",
            "**/*.{js,css,json,yml,yaml}",
        ],
    )


def check_eslint() -> int:
    if NPX is None:
        print("[validate] eslint: SKIP (npx not found)")
        return 0
    return _run("eslint (JS lint)", [NPX, "eslint", "assets/"])


def check_coverage() -> int:
    return _run(
        "pytest (coverage)",
        [
            "pytest",
            "tests/unit/",
            "-n",
            "auto",
            "--cov=data",
            "--cov=ui",
            "--cov=visualization",
            "--cov-config=pyproject.toml",
            "--cov-report=term-missing",
            "--cov-fail-under=44",
            "-q",
        ],
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="burndown-chart quality gate")
    parser.add_argument(
        "--commit",
        action="store_true",
        help="Pre-commit mode: ruff lint + format only (~5s, run on every commit)",
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip markdownlint and pytest (ruff + djlint + pyright only)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix ruff and djlint violations where possible",
    )
    args = parser.parse_args()

    system = platform.system()
    print(f"[validate] Platform: {system} | Python: {sys.version.split()[0]}")
    print(f"[validate] Root: {ROOT}")

    if not PYTHON.exists():
        print(f"[validate] ERROR: venv not found at {VENV_BIN}")
        print("[validate] Run: python -m venv .venv")
        print("[validate]       pip install -r requirements-dev.txt")
        return 1

    failures: list[str] = []

    if args.commit:
        # Pre-commit gate: check staged files only so every commit stays snappy.
        staged = _staged_py_files()
        if not staged:
            print("[validate] pre-commit: no staged Python files to check.")
            return 0
        print(f"[validate] pre-commit: checking {len(staged)} staged file(s)")
        checks: list[tuple[str, int]] = [
            ("ruff (lint)", check_ruff(fix=args.fix, files=staged)),
            ("ruff (format)", check_ruff_format(fix=args.fix, files=staged)),
        ]
    elif args.fast:
        checks = [
            ("ruff (lint)", check_ruff(fix=args.fix)),
            ("ruff (format)", check_ruff_format(fix=args.fix)),
            ("djlint", check_djlint(fix=args.fix)),
            ("pyright", check_pyright()),
            ("bandit", check_bandit()),
            ("prettier (format)", check_prettier(fix=args.fix)),
            ("eslint", check_eslint()),
        ]
    else:
        # Pre-push gate: full suite.
        checks = [
            ("ruff (lint)", check_ruff(fix=args.fix)),
            ("ruff (format)", check_ruff_format(fix=args.fix)),
            ("djlint", check_djlint(fix=args.fix)),
            ("pyright", check_pyright()),
            ("bandit", check_bandit()),
            ("pip-audit", check_pip_audit()),
            ("vulture", check_vulture()),
            ("prettier (format)", check_prettier(fix=args.fix)),
            ("eslint", check_eslint()),
            ("markdownlint", check_markdownlint()),
            ("pytest (coverage)", check_coverage()),
        ]

    for name, code in checks:
        if code == 130:
            print("\n" + "=" * 60)
            print(f"[validate] INTERRUPTED during: {name}")
            print("[validate] Validation was interrupted before completion.")
            return 130
        if code != 0:
            failures.append(name)

    print("\n" + "=" * 60)
    if failures:
        print(f"[validate] FAILED: {', '.join(failures)}")
        print("[validate] Fix all failures before pushing.")
        return 1

    mode = "commit" if args.commit else ("fast" if args.fast else "full")
    print(f"[validate] ALL CHECKS PASSED (mode: {mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
