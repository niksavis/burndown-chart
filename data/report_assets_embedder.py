"""Utility to embed external CSS/JS dependencies into HTML reports for offline use."""

import base64
import re
import sys
from pathlib import Path


def embed_report_dependencies() -> dict:
    """
    Read and prepare CSS/JS dependencies for embedding in HTML reports.

    Returns:
        dict with keys: 'bootstrap_css', 'chartjs', 'chartjs_annotation', 'fontawesome_css'
    """
    # Handle PyInstaller frozen executable path
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        assets_dir = Path(sys._MEIPASS) / "report_assets"  # type: ignore[attr-defined]
    else:
        assets_dir = Path(__file__).parent.parent / "report_assets"

    # Read CSS files
    bootstrap_css = (assets_dir / "bootstrap.min.css").read_text(encoding="utf-8")
    fontawesome_css = (assets_dir / "font-awesome.min.css").read_text(encoding="utf-8")

    # Read JS files
    chartjs = (assets_dir / "chart.umd.min.js").read_text(encoding="utf-8")
    chartjs_annotation = (assets_dir / "chartjs-plugin-annotation.min.js").read_text(
        encoding="utf-8"
    )

    # Embed fonts as base64 in Font Awesome CSS
    fontawesome_css = _embed_fonts_in_css(fontawesome_css, assets_dir / "webfonts")

    return {
        "bootstrap_css": bootstrap_css,
        "fontawesome_css": fontawesome_css,
        "chartjs": chartjs,
        "chartjs_annotation": chartjs_annotation,
    }


def _embed_fonts_in_css(css_content: str, fonts_dir: Path) -> str:
    """
    Replace url(../webfonts/...) references in CSS with base64 data URIs.

    Args:
        css_content: CSS file content
        fonts_dir: Directory containing font files

    Returns:
        Modified CSS with embedded fonts
    """
    # Find all url() references to font files
    url_pattern = r"url\((\.\.\/webfonts\/[^)]+)\)"

    def replace_url(match):
        rel_path = match.group(1)  # e.g., "../webfonts/fa-solid-900.woff2"
        filename = rel_path.split("/")[-1]  # e.g., "fa-solid-900.woff2"

        font_path = fonts_dir / filename
        if not font_path.exists():
            # Keep original if font file not found
            return match.group(0)

        # Read font file as binary
        font_data = font_path.read_bytes()

        # Determine MIME type
        if filename.endswith(".woff2"):
            mime_type = "font/woff2"
        elif filename.endswith(".woff"):
            mime_type = "font/woff"
        elif filename.endswith(".ttf"):
            mime_type = "font/ttf"
        else:
            mime_type = "application/octet-stream"

        # Encode as base64
        b64_data = base64.b64encode(font_data).decode("ascii")

        # Return data URI
        return f"url(data:{mime_type};base64,{b64_data})"

    # Replace all font URLs with data URIs
    modified_css = re.sub(url_pattern, replace_url, css_content)

    return modified_css
