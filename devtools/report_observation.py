from pathlib import Path

from playwright.sync_api import Page

SCRIPT = Path(__file__).with_name("report_state.js")


def install_report_observation(page: Page) -> None:
    page.wait_for_function(
        "typeof Chart !== 'undefined' && Object.keys(Chart.instances).length > 0"
    )
    if not page.evaluate("Boolean(window.burndownReportProbe)"):
        page.add_script_tag(content=SCRIPT.read_text(encoding="utf-8"), type="module")
        page.wait_for_function("Boolean(window.burndownReportProbe)")


def wait_for_report_settlement(page: Page) -> None:
    install_report_observation(page)
    page.evaluate("window.burndownReportProbe.reset()")
    page.wait_for_function("window.burndownReportProbe.settled()", timeout=10000)
