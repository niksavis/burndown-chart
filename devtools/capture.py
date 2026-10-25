import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Literal

from playwright.sync_api import (
    Browser,
    BrowserContext,
    Error,
    ViewportSize,
    sync_playwright,
)

from devtools.browser_observer import BrowserObservation
from devtools.journeys import capture_exported_report, capture_registered_tabs
from devtools.scenario_journeys import capture_scenarios, exercise_data_range
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
        if page.evaluate("matchMedia('(prefers-color-scheme: dark)').matches") != (
            theme == "dark"
        ):
            raise AssertionError(
                "Browser color preference does not match requested capture"
            )
        observation = BrowserObservation()
        observation.observe(context, page)
        tabs = capture_registered_tabs(page, url, output, mobile=mobile)
        page.wait_for_load_state("networkidle")
        page.goto(url, wait_until="domcontentloaded")
        expect_dashboard = page.locator("#tab-content")
        expect_dashboard.wait_for(state="visible")
        scenarios = capture_scenarios(page, output)
        exercise_data_range(page, output)
        page.wait_for_load_state("networkidle")
        sections = capture_exported_report(page, output)
        observation.assert_clean()
        return {
            "viewport": viewport,
            "color_scheme": theme,
            "tabs": tabs,
            "scenarios": scenarios,
            "report_sections": sections,
            "screenshots": sorted(path.name for path in output.glob("*.png")),
            "visual_review_required": True,
            "observation": asdict(observation),
        }
    except AssertionError, Error:
        _save_failure(context, output)
        raise
    finally:
        context.close()


def _save_failure(context: BrowserContext, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    if context.pages and not context.pages[-1].is_closed():
        failed_page = context.pages[-1]
        failed_page.screenshot(path=str(output / "failure.png"))
        (output / "failure.html").write_text(failed_page.content(), encoding="utf-8")


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
