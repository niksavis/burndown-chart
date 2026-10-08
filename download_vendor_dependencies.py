#!/usr/bin/env python3


import re
import sys
from pathlib import Path

import requests


def parse_dependencies(deps_file: Path) -> dict[str, str]:
    versions = {}
    if not deps_file.exists():
        print(f"⚠️  Warning: {deps_file} not found, using default versions")
        return {
            "bootstrap": "5.3.3",
            "bootswatch": "5.3.3",
            "fontawesome-free": "6.5.1",
            "codemirror": "5.65.16",
        }

    for line in deps_file.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            match = re.match(r"^([\w\-\.]+)==([\d\.]+)", line)
            if match:
                versions[match.group(1)] = match.group(2)
    return versions


def download_file(url: str, output_path: Path) -> bool:
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(response.content)
        return True
    except requests.RequestException as e:
        print(f"  ⚠️  Warning: Could not download {output_path.name}: {e}")
        return False


def download_bootstrap(version: str, vendor_dir: Path) -> None:
    print(f"📦 Downloading Bootstrap {version}...")
    bootstrap_dir = vendor_dir / "bootstrap"

    css_url = (
        f"https://cdn.jsdelivr.net/npm/bootstrap@{version}/dist/css/bootstrap.min.css"
    )
    css_path = bootstrap_dir / "css" / "bootstrap.min.css"
    if download_file(css_url, css_path):
        print(f"  ✓ Downloaded: {css_path.relative_to(vendor_dir.parent)}")

    js_url = f"https://cdn.jsdelivr.net/npm/bootstrap@{version}/dist/js/bootstrap.bundle.min.js"
    js_path = bootstrap_dir / "js" / "bootstrap.bundle.min.js"
    if download_file(js_url, js_path):
        print(f"  ✓ Downloaded: {js_path.relative_to(vendor_dir.parent)}")

    map_url = f"https://cdn.jsdelivr.net/npm/bootstrap@{version}/dist/js/bootstrap.bundle.min.js.map"
    map_path = bootstrap_dir / "js" / "bootstrap.bundle.min.js.map"
    if download_file(map_url, map_path):
        print(f"  ✓ Downloaded: {map_path.relative_to(vendor_dir.parent)}")

    print()


def download_bootswatch(version: str, vendor_dir: Path) -> None:
    print(f"📦 Downloading Bootswatch {version}...")
    bootswatch_dir = vendor_dir / "bootswatch"

    theme = "flatly"
    theme_dir = bootswatch_dir / theme

    files = [
        "bootstrap.min.css",
        "_variables.scss",
        "_bootswatch.scss",
    ]

    for file in files:
        url = f"https://cdn.jsdelivr.net/npm/bootswatch@{version}/dist/{theme}/{file}"
        file_path = theme_dir / file
        if download_file(url, file_path):
            print(f"  ✓ Downloaded: {file_path.relative_to(vendor_dir.parent)}")

    print()


def download_fontawesome(version: str, vendor_dir: Path) -> None:
    print(f"📦 Downloading Font Awesome {version}...")
    fa_dir = vendor_dir / "fontawesome"

    css_files = {
        "fontawesome.min.css": "fontawesome.min.css",
        "solid.min.css": "solid.min.css",
        "brands.min.css": "brands.min.css",
    }

    for local_name, cdn_name in css_files.items():
        css_url = f"https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@{version}/css/{cdn_name}"
        css_path = fa_dir / "css" / local_name
        if download_file(css_url, css_path):
            print(f"  ✓ Downloaded: {css_path.relative_to(vendor_dir.parent)}")

    webfonts_dir = fa_dir / "webfonts"
    font_files: list[str] = [
        "fa-solid-900.woff2",
        "fa-solid-900.ttf",
        "fa-regular-400.woff2",
        "fa-regular-400.ttf",
        "fa-brands-400.woff2",
        "fa-brands-400.ttf",
        "fa-v4compatibility.woff2",
        "fa-v4compatibility.ttf",
    ]

    for font in font_files:
        font_url = f"https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@{version}/webfonts/{font}"
        font_path = webfonts_dir / font
        if download_file(font_url, font_path):
            print(f"  ✓ Downloaded: {font_path.relative_to(vendor_dir.parent)}")

    print()


def download_codemirror(version: str, vendor_dir: Path) -> None:
    print(f"📦 Downloading CodeMirror {version}...")
    cm_dir = vendor_dir / "codemirror"

    core_files = {
        "codemirror.min.js": "lib/codemirror.js",
        "codemirror.min.css": "lib/codemirror.css",
    }

    for local_name, cdn_path in core_files.items():
        url = f"https://cdn.jsdelivr.net/npm/codemirror@{version}/{cdn_path}"
        file_path = cm_dir / local_name
        if download_file(url, file_path):
            print(f"  ✓ Downloaded: {file_path.relative_to(vendor_dir.parent)}")

    sql_mode_url = f"https://cdn.jsdelivr.net/npm/codemirror@{version}/mode/sql/sql.js"
    sql_mode_path = cm_dir / "mode" / "sql" / "sql.min.js"
    if download_file(sql_mode_url, sql_mode_path):
        print(f"  ✓ Downloaded: {sql_mode_path.relative_to(vendor_dir.parent)}")

    print()


def main() -> int:
    deps_file = Path("vendor_dependencies.txt")
    versions = parse_dependencies(deps_file)
    print(f"📋 Using versions from {deps_file}:")
    for lib, ver in versions.items():
        print(f"   {lib} {ver}")
    print()

    vendor_dir = Path("assets") / "vendor"
    vendor_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Using vendor directory: {vendor_dir}")
    print()

    bootstrap_ver = versions.get("bootstrap", "5.3.3")
    download_bootstrap(bootstrap_ver, vendor_dir)

    bootswatch_ver = versions.get("bootswatch", "5.3.3")
    download_bootswatch(bootswatch_ver, vendor_dir)

    fontawesome_ver = versions.get("fontawesome-free", "6.5.1")
    download_fontawesome(fontawesome_ver, vendor_dir)

    codemirror_ver = versions.get("codemirror", "5.65.16")
    download_codemirror(codemirror_ver, vendor_dir)

    print("✓ All vendor dependencies downloaded successfully!")
    print(f"📁 Files saved to: {vendor_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
