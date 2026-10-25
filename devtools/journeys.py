import math
import re
from pathlib import Path
from shutil import copyfile

from playwright.sync_api import Locator, Page, expect

from devtools.plotly_observation import (
    wait_for_page_settlement,
    wait_for_plotly_settlement,
)
from devtools.report_observation import wait_for_report_settlement
from ui.tabs import TAB_CONFIG, TabConfig

TAB_MARKERS = {
    "tab-dashboard": "Project Health",
    "tab-burndown": "Weekly Items Trend",
    "tab-scope-tracking": "Scope Change",
    "tab-bug-analysis": "Bug Trends Over Time",
    "tab-flow-metrics": "Flow Velocity",
    "tab-dora-metrics": "Deployment Frequency",
    "tab-active-work-timeline": "Summary",
    "tab-sprint-tracker": "Select Sprint",
    "tab-statistics-data": "Weekly Progress Data",
}


def capture_viewports(page: Page, region: Locator, output: Path, prefix: str) -> None:
    viewport = page.viewport_size
    if viewport is None:
        raise ValueError("UI capture requires a bounded viewport")
    bounds = region.evaluate(
        "element => ({top: element.getBoundingClientRect().top + window.scrollY, "
        "height: element.getBoundingClientRect().height})"
    )
    step = max(200, viewport["height"] - 320)
    count = math.ceil(bounds["height"] / step)
    if count > 100:
        raise ValueError("Capture region exceeds one hundred viewports")
    for index in range(count):
        page.evaluate(
            "top => window.scrollTo({top, behavior: 'instant'})",
            arg=max(0, bounds["top"] - 200 + index * step),
        )
        page.screenshot(
            path=str(output / f"{prefix}-{index + 1}.png"), animations="disabled"
        )


def select_tab(page: Page, tab: TabConfig, *, mobile: bool) -> None:
    page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
    if mobile:
        primary = page.locator(f"#bottom-nav-{tab['id']}")
        if primary.count():
            primary.click()
        else:
            page.locator("#bottom-nav-more-menu").click()
            expect(page.locator("#mobile-overflow-menu")).to_have_css(
                "transform", "matrix(1, 0, 0, 1, 0, 0)"
            )
            page.locator(f"#overflow-menu-{tab['id']}").click()
            expect(page.locator("#mobile-overflow-overlay")).to_be_hidden()
    else:
        page.get_by_role("tab", name=re.compile(re.escape(tab["label"]) + "$")).click()


def wait_for_tab(page: Page, tab_id: str) -> None:
    expect(page.locator("#tab-content")).to_contain_text(
        TAB_MARKERS[tab_id], timeout=30000
    )
    if tab_id in {"tab-flow-metrics", "tab-dora-metrics"}:
        category = "flow" if tab_id == "tab-flow-metrics" else "dora"
        page.wait_for_function(
            "selector => document.querySelector(selector)?.innerText.trim().length > 40",
            arg=f"#{category}-metrics-cards-container",
            timeout=30000,
        )
    expect(page.locator(".dash-error-card")).to_have_count(0)
    wait_for_page_settlement(page, "#tab-content")


def capture_registered_tabs(
    page: Page, url: str, output: Path, *, mobile: bool
) -> list[str]:
    registered = {tab["id"] for tab in TAB_CONFIG}
    if registered != set(TAB_MARKERS):
        raise ValueError(
            "Browser readiness checks do not match the registered tab inventory"
        )
    output.mkdir(parents=True, exist_ok=True)
    page.goto(url, wait_until="domcontentloaded")
    expect(page.locator("#demo-mode-banner")).to_contain_text("2026-01-29")
    captured = []
    for index, tab in enumerate(TAB_CONFIG):
        if index:
            select_tab(page, tab, mobile=mobile)
        wait_for_tab(page, tab["id"])
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        page.wait_for_function("window.scrollY === 0")
        page.screenshot(path=str(output / f"{tab['id']}.png"), animations="disabled")
        captured.append(tab["id"])
        if tab["id"] == "tab-dashboard":
            budget = page.locator(".budget-section")
            expect(budget).to_contain_text("Budget", timeout=30000)
            capture_viewports(page, budget, output, "budget")
        capture_viewports(
            page, page.locator("#tab-content"), output, tab["id"] + "-page"
        )
        if tab["id"] == "tab-sprint-tracker":
            page.locator("#toggle-sprint-charts").click()
            expect(page.locator("#sprint-charts-collapse")).to_be_visible()
            page.wait_for_function(
                "document.querySelector('#sprint-burnup-chart .js-plotly-plot')?.data?.length > 0",
                timeout=30000,
            )
            wait_for_plotly_settlement(
                page, ["#sprint-charts-collapse .js-plotly-plot"]
            )
            capture_viewports(
                page, page.locator("#sprint-charts-collapse"), output, "sprint-charts"
            )
    return captured


def capture_exported_report(page: Page, output: Path) -> list[str]:
    button = page.locator("#generate-report-button")
    if not page.locator("#data-tabs").is_visible():
        page.locator("#toggle-import-export-panel").click()
    expect(page.locator("#data-tabs")).to_be_visible(timeout=30000)
    page.locator("#data-tabs").get_by_role("tab", name="Reports", exact=True).click()
    expect(button).to_be_visible(timeout=30000)
    with page.expect_download(timeout=60000) as pending:
        button.click()
    report = (output / "report.html").absolute()
    pending.value.save_as(report)
    page.wait_for_load_state("networkidle")
    page.goto(report.as_uri(), wait_until="load")
    expect(page).to_have_title(re.compile("Acme Corp.*Project Report"))
    expect(page.get_by_role("heading", name="Project Health Overview")).to_be_visible()
    wait_for_report_settlement(page)
    sections = page.locator(".container > .section")
    titles = []
    for index in range(sections.count()):
        section = sections.nth(index)
        title = section.locator("h2").inner_text().strip()
        titles.append(title)
        prefix = f"report-section-{index + 1}-page"
        capture_viewports(page, section, output, prefix)
        copyfile(
            output / f"{prefix}-1.png",
            output / f"report-section-{index + 1}.png",
        )
    if len(titles) != 8:
        raise AssertionError(f"Expected eight exported report sections, got {titles}")
    return titles
