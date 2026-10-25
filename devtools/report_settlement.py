import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from devtools.browser_observer import BrowserObservation
from devtools.report_observation import (
    install_report_observation,
    wait_for_report_settlement,
)


def record_stage(
    page: Page, output: Path, stage: str, *, viewport: bool = False
) -> None:
    section = page.locator(".container > .section").nth(1)
    if viewport:
        section.evaluate(
            "element => window.scrollTo({top: element.getBoundingClientRect().top "
            "+ scrollY, behavior: 'instant'})"
        )
        wait_for_report_settlement(page)
    before = page.evaluate("window.burndownReportProbe.snapshot()")
    if viewport:
        page.screenshot(path=str(output / f"{stage}.png"), animations="disabled")
    else:
        section.screenshot(path=str(output / f"{stage}.png"), animations="disabled")
    after = page.evaluate("window.burndownReportProbe.snapshot()")
    (output / f"{stage}.json").write_text(
        json.dumps({"before": before, "after": after}, indent=2), encoding="utf-8"
    )


def probe_report(page: Page, report: Path, output: Path) -> None:
    output.mkdir(parents=True)
    page.goto(report.as_uri(), wait_until="load")
    install_report_observation(page)
    page.evaluate(
        "Object.values(Chart.instances).forEach(chart => {chart.stop(); chart.update('none');})"
    )
    record_stage(page, output, "stopped")
    wait_for_report_settlement(page)
    record_stage(page, output, "stopped-stable")
    page.goto(report.as_uri(), wait_until="load")
    wait_for_report_settlement(page)
    record_stage(page, output, "natural", viewport=True)


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect report chart geometry")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    report = arguments.report.absolute()
    output = arguments.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        try:
            for theme in ("light", "dark"):
                context = browser.new_context(
                    viewport={"width": 1440, "height": 1000}, color_scheme=theme
                )
                try:
                    page = context.new_page()
                    observer = BrowserObservation()
                    observer.observe(context, page)
                    probe_report(page, report, output / theme)
                    observer.assert_clean()
                finally:
                    context.close()
        finally:
            browser.close()
    print(f"Report chart probe artifacts: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
