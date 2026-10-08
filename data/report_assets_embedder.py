import base64
import re
import sys
from pathlib import Path


def embed_report_dependencies() -> dict:

    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        assets_dir = Path(sys._MEIPASS) / "report_assets"  # type: ignore[attr-defined]
    else:
        assets_dir = Path(__file__).parent.parent / "report_assets"

    bootstrap_css = _strip_source_map_comments(
        (assets_dir / "bootstrap.min.css").read_text(encoding="utf-8")
    )
    fontawesome_css = _strip_source_map_comments(
        (assets_dir / "font-awesome.min.css").read_text(encoding="utf-8")
    )

    chartjs = _strip_source_map_comments(
        (assets_dir / "chart.umd.min.js").read_text(encoding="utf-8")
    )
    chartjs_annotation = _strip_source_map_comments(
        (assets_dir / "chartjs-plugin-annotation.min.js").read_text(encoding="utf-8")
    )

    fontawesome_css = _embed_fonts_in_css(fontawesome_css, assets_dir / "webfonts")

    return {
        "bootstrap_css": bootstrap_css,
        "fontawesome_css": fontawesome_css,
        "chartjs": chartjs,
        "chartjs_annotation": chartjs_annotation,
    }


def _strip_source_map_comments(content: str) -> str:

    content = re.sub(r"/\*#\s*sourceMappingURL=[^\*]+\*/", "", content)
    content = re.sub(r"//# sourceMappingURL=\S+", "", content)
    return content


def _embed_fonts_in_css(css_content: str, fonts_dir: Path) -> str:

    url_pattern = r"url\((\.\.\/webfonts\/[^)]+)\)"

    def replace_url(match):
        rel_path = match.group(1)
        filename = rel_path.split("/")[-1]

        font_path = fonts_dir / filename
        if not font_path.exists():
            return match.group(0)

        font_data = font_path.read_bytes()

        if filename.endswith(".woff2"):
            mime_type = "font/woff2"
        elif filename.endswith(".woff"):
            mime_type = "font/woff"
        elif filename.endswith(".ttf"):
            mime_type = "font/ttf"
        else:
            mime_type = "application/octet-stream"

        b64_data = base64.b64encode(font_data).decode("ascii")

        return f"url(data:{mime_type};base64,{b64_data})"

    modified_css = re.sub(url_pattern, replace_url, css_content)

    return modified_css
