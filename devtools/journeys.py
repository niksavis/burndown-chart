import re
from pathlib import Path

from playwright.sync_api import Page, expect

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


def select_tab(page: Page, tab: TabConfig, *, mobile: bool) -> None:
    if mobile:
        primary = page.locator(f"#bottom-nav-{tab['id']}")
        if primary.count():
            primary.click()
        else:
            page.locator("#bottom-nav-more-menu").click()
            page.locator(f"#overflow-menu-{tab['id']}").click()
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
        page.evaluate("window.scrollTo(0, 0)")
        page.screenshot(path=str(output / f"{tab['id']}.png"), animations="disabled")
        captured.append(tab["id"])
        if tab["id"] == "tab-dashboard":
            budget = page.locator(".budget-section")
            expect(budget).to_contain_text("Budget", timeout=30000)
            budget.screenshot(path=str(output / "budget.png"), animations="disabled")
    return captured
