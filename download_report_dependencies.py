#!/usr/bin/env python3
"""
Download dependencies for offline HTML reports.
This script downloads Bootstrap, Font Awesome, and Chart.js libraries.

Versions are defined in report_dependencies.txt - update that file to change versions.

Usage:
    python download_report_dependencies.py
"""

import re
import sys
from pathlib import Path

import requests


def parse_dependencies(deps_file: Path) -> dict[str, str]:
    """Parse report_dependencies.txt to extract library versions."""
    versions = {}
    if not deps_file.exists():
        print(f"⚠️  Warning: {deps_file} not found, using default versions")
        return {
            "bootstrap": "5.3.0",
            "font-awesome": "6.4.0",
            "chart.js": "4.4.0",
            "chartjs-plugin-annotation": "3.0.1",
        }

    for line in deps_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            match = re.match(r"^([\w\-\.]+)==([\d\.]+)", line)
            if match:
                versions[match.group(1)] = match.group(2)
    return versions


def download_file(url: str, output_path: Path) -> bool:
    """Download a file from URL to output path."""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        output_path.write_bytes(response.content)
        return True
    except requests.RequestException as e:
        print(f"  ⚠️  Warning: Could not download {output_path.name}: {e}")
        return False


def main() -> int:
    """Download all report dependencies."""
    # Parse version configuration
    deps_file = Path("report_dependencies.txt")
    versions = parse_dependencies(deps_file)
    print(f"📋 Using versions from {deps_file}:")
    for lib, ver in versions.items():
        print(f"   {lib} {ver}")
    print()

    # Create assets directory for report dependencies
    assets_dir = Path("report_assets")
    assets_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory: {assets_dir}")
    print()

    # Download Bootstrap CSS
    bootstrap_ver = versions.get("bootstrap", "5.3.0")
    print(f"📦 Downloading Bootstrap CSS {bootstrap_ver}...")
    bootstrap_url = f"https://cdn.jsdelivr.net/npm/bootstrap@{bootstrap_ver}/dist/css/bootstrap.min.css"
    bootstrap_path = assets_dir / "bootstrap.min.css"
    if download_file(bootstrap_url, bootstrap_path):
        print(f"  ✓ Downloaded: {bootstrap_path}")
    print()

    # Download Font Awesome CSS
    fontawesome_ver = versions.get("font-awesome", "6.4.0")
    print(f"📦 Downloading Font Awesome CSS {fontawesome_ver}...")
    fontawesome_url = f"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/{fontawesome_ver}/css/all.min.css"
    fontawesome_path = assets_dir / "font-awesome.min.css"
    if download_file(fontawesome_url, fontawesome_path):
        print(f"  ✓ Downloaded: {fontawesome_path}")
    print()

    # Download Font Awesome fonts
    print(f"📦 Downloading Font Awesome fonts {fontawesome_ver}...")
    fonts_dir = assets_dir / "webfonts"
    fonts_dir.mkdir(parents=True, exist_ok=True)

    font_files: list[str] = [
        "fa-solid-900.woff2",
        "fa-solid-900.ttf",
        "fa-regular-400.woff2",
        "fa-regular-400.ttf",
        "fa-brands-400.woff2",
        "fa-brands-400.ttf",
    ]

    for font in font_files:
        font_url = f"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/{fontawesome_ver}/webfonts/{font}"
        font_path = fonts_dir / font
        if download_file(font_url, font_path):
            print(f"  ✓ Downloaded: {font_path}")
    print()

    # Download Chart.js
    chartjs_ver = versions.get("chart.js", "4.4.0")
    print(f"📦 Downloading Chart.js {chartjs_ver}...")
    chartjs_url = (
        f"https://cdn.jsdelivr.net/npm/chart.js@{chartjs_ver}/dist/chart.umd.min.js"
    )
    chartjs_path = assets_dir / "chart.umd.min.js"
    if download_file(chartjs_url, chartjs_path):
        print(f"  ✓ Downloaded: {chartjs_path}")
    print()

    # Download Chart.js Annotation Plugin
    annotation_ver = versions.get("chartjs-plugin-annotation", "3.0.1")
    print(f"Downloading Chart.js Annotation Plugin {annotation_ver}...")
    annotation_url = f"https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@{annotation_ver}/dist/chartjs-plugin-annotation.min.js"
    annotation_path = assets_dir / "chartjs-plugin-annotation.min.js"
    if download_file(annotation_url, annotation_path):
        print(f"  Downloaded: {annotation_path}")
    print()

    print("All dependencies downloaded successfully!")
    print(f"Files saved to: {assets_dir}")
    print()
    print(
        "Note: Font Awesome fonts are automatically embedded in CSS by "
        "report_assets_embedder.py"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
