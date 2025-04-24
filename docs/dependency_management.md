# Dependency Management Guide

This guide explains how to manage dependencies in the Burndown Chart project using our `manage_pip_tools.py` utility with the pip-tools workflow (requirements.in and requirements.txt).

## Understanding the Workflow

Our project uses:

- `requirements.in`: Contains high-level dependencies with flexible version constraints
- `requirements.txt`: Generated from requirements.in with pinned versions for reproducible builds

We use pip-tools (`pip-compile`) to generate requirements.txt from requirements.in.

## Using the manage_pip_tools.py Utility

### 1. Analyzing Dependencies

To analyze requirements.in for outdated packages and check against known unused packages:

```bash
python tools/manage_pip_tools.py analyze requirements.in unused_dependencies.md
```

This will generate a `requirements_analysis.md` file with:

- Outdated packages compared to latest available versions
- Potentially unused packages (cross-referenced with unused_dependencies.md)
- Suggested actions for both

### 2. Cleaning Unused Dependencies

After reviewing the analysis, you can clean up unused dependencies:

```bash
python tools/manage_pip_tools.py clean requirements.in unused_dependencies.md
```

This will:

1. Remove packages listed in unused_dependencies.md from requirements.in
2. Create a backup of the original requirements.in file
3. Automatically regenerate requirements.txt

### 3. Updating Outdated Packages

To update all outdated packages to their latest versions:

```bash
python tools/manage_pip_tools.py update requirements.in
```

This will:

1. Update version constraints in requirements.in
2. Create a backup of the original file
3. Regenerate requirements.txt

### 4. Manually Compiling Requirements

If you've manually modified requirements.in and want to regenerate requirements.txt:

```bash
python tools/manage_pip_tools.py compile requirements.in
```

## Best Practices

1. **Always review analysis before cleaning**: The `analyze` command is non-destructive and helps you make informed decisions

2. **Check backups**: All modifications create backups with timestamps if you need to revert changes

3. **Verify after updates**: After updating dependencies, run tests to verify everything still works

4. **Re-pin requirements regularly**: Even without changes, periodically re-pin requirements to get security updates

## Handling False Positives in Unused Dependencies

The unused_dependencies.md file may contain false positives. Packages that appear unused but are actually required include:

1. Dash components (`dash-bootstrap-components`, `dash-core-components`) - These are essential for the UI

2. Pandas - Used for data processing throughout the application

3. Indirect dependencies required by other packages

Always verify that packages are truly unused before removal!
