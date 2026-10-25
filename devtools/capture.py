import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from playwright.sync_api import Browser, ViewportSize, sync_playwright

from devtools.browser_observer import BrowserObservation
from devtools.journeys import capture_exported_report, capture_registered_tabs
from devtools.server import running_demo_server


def capture_view(
    browser: Browser,
    url: str,
    output: Path,
    *,
    mobile: bool,
    theme: Literal["light", "dark"],
) -> dict:
    viewport: ViewportSize = (
        {"width": 390, "height": 844} if mobile else {"width": 1440, "height": 1000}
    )
    context = browser.new_context(
        viewport=viewport, color_scheme=theme, service_workers="block"
    )
    try:
        page = context.new_page()
        observation = BrowserObservation()
        observation.observe(context, page)
        tabs = capture_registered_tabs(page, url, output, mobile=mobile)
        sections = capture_exported_report(page, output)
        observation.assert_clean()
        return {
            "viewport": viewport,
            "color_scheme": theme,
            "tabs": tabs,
            "report_sections": sections,
            "screenshots": sorted(path.name for path in output.glob("*.png")),
            "visual_review_required": True,
            "observation": asdict(observation),
        }
    finally:
        context.close()


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture the offline demo UI matrix")
    parser.add_argument("--workspace", type=Path, default=Path("profiles/demo"))
    parser.add_argument("--output", required=True, type=Path)
    arguments = parser.parse_args()
    output = arguments.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    results = {}
    with running_demo_server(
        arguments.workspace.absolute(), output / "server.log"
    ) as url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for mobile in (False, True):
                    for theme in ("light", "dark"):
                        name = f"{'mobile' if mobile else 'desktop'}-{theme}"
                        results[name] = capture_view(
                            browser, url, output / name, mobile=mobile, theme=theme
                        )
                        print(f"Captured {name}", flush=True)
            finally:
                browser.close()
    (output / "manifest.json").write_text(
        json.dumps(results, indent=2), encoding="utf-8"
    )
    print(f"Browser assertions passed; inspect screenshots in {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
