import re
from pathlib import Path

from playwright.sync_api import Page, expect

from data.demo.config import SCENARIOS


def select_scenario(page: Page, scenario: str) -> None:
    label = f"Acme Corp - {scenario}"
    dropdown = page.locator("#profile-selector")
    if not dropdown.is_visible():
        page.locator("#settings-button").click()
    wait_for_open_panel(page, "settings-collapse")
    expect(dropdown).to_be_visible()
    dropdown.click()
    expect(dropdown).to_have_attribute("aria-expanded", "true")
    page.get_by_role("option", name=label, exact=True).click()
    expect(page.get_by_text(f"Switched to profile: {label}", exact=True)).to_be_visible(
        timeout=30000
    )
    page.wait_for_load_state("networkidle")
    expect(page.locator(f'[title="Profile: {label}"]')).to_be_attached(timeout=30000)
    if dropdown.is_visible():
        page.locator("#settings-collapse-btn").click()
        expect(page.locator("#settings-collapse")).to_be_hidden()
    if scenario != "empty":
        select_all_history(page)


def select_all_history(page: Page) -> None:
    open_parameters(page)
    slider = page.locator('#data-points-input [role="slider"]')
    expect(slider).to_be_visible()
    maximum = slider.get_attribute("aria-valuemax")
    if maximum is None:
        raise ValueError("Data range slider has no accessible maximum")
    slider.press("End")
    expect(slider).to_have_attribute("aria-valuenow", maximum)
    expect(page.locator(f'[title^="Data Points: {maximum} weeks"]')).to_be_attached(
        timeout=30000
    )
    page.wait_for_load_state("networkidle")
    close_parameters(page)


def open_parameters(page: Page) -> None:
    panel = page.locator("#parameter-collapse")
    if not panel.is_visible():
        page.locator("#btn-expand-parameters").click()
    wait_for_open_panel(page, "parameter-collapse")


def wait_for_open_panel(page: Page, panel_id: str) -> None:
    expect(page.locator(f"#{panel_id}")).to_have_class(
        re.compile(r"\bshow\b"), timeout=30000
    )


def close_parameters(page: Page) -> None:
    page.locator("#parameter-collapse-btn").click()
    expect(page.locator("#parameter-collapse")).to_be_hidden()
    page.wait_for_load_state("networkidle")


def capture_scenarios(page: Page, output: Path) -> list[str]:
    captured = []
    for scenario in (*SCENARIOS[1:], "complete"):
        select_scenario(page, scenario)
        assert_scenario_data(page, scenario)
        expect(page.locator(".dash-error-card")).to_have_count(0)
        page.evaluate("window.scrollTo({top: 0, behavior: 'instant'})")
        page.screenshot(
            path=str(output / f"scenario-{scenario}.png"), animations="disabled"
        )
        captured.append(scenario)
        print(f"Captured scenario {scenario}", flush=True)
    return captured


def assert_scenario_data(page: Page, scenario: str) -> None:
    content = page.locator("#tab-content")
    if scenario == "empty":
        expect(content).to_contain_text(
            "No data available. Please load project data first.", timeout=30000
        )
        expect(content.get_by_text("Project Health", exact=True)).to_have_count(0)
        return
    expect(content).to_contain_text("Project Health", timeout=30000)
    counts = {
        "complete": (32, 16),
        "singleton": (1, 0),
        "zero-delivery": (0, 48),
        "stalled": (16, 32),
        "completed": (48, 0),
    }
    if scenario in counts:
        for label, value in zip(
            ("Completed", "Remaining"), counts[scenario], strict=True
        ):
            metric = content.get_by_text(label, exact=True).first.locator("..")
            expect(metric.locator(".mt-3.mb-1")).to_have_text(str(value), timeout=30000)


def exercise_data_range(page: Page, output: Path) -> None:
    open_parameters(page)
    page.wait_for_load_state("networkidle")
    slider = page.locator('#data-points-input [role="slider"]')
    expect(slider).to_be_visible()
    previous = slider.get_attribute("aria-valuenow")
    if previous is None:
        raise ValueError("Data range slider has no accessible value")
    slider.press("Home")
    expect(slider).to_have_attribute("aria-valuenow", "4")
    expect(page.locator('[title^="Data Points: 4 weeks"]')).to_be_attached(
        timeout=30000
    )
    page.wait_for_load_state("networkidle")
    close_parameters(page)
    expect(page.locator("#tab-content")).to_contain_text("Project Health")
    page.screenshot(path=str(output / "range-four-weeks.png"), animations="disabled")
    open_parameters(page)
    page.wait_for_load_state("networkidle")
    if previous == slider.get_attribute("aria-valuemax"):
        slider.press("End")
    else:
        for value in range(5, int(previous) + 1):
            slider.press("ArrowRight")
            expect(slider).to_have_attribute("aria-valuenow", str(value))
            expect(
                page.locator(f'[title^="Data Points: {value} weeks"]')
            ).to_be_attached(timeout=30000)
            page.wait_for_load_state("networkidle")
    expect(slider).to_have_attribute("aria-valuenow", previous)
    expect(page.locator(f'[title^="Data Points: {previous} weeks"]')).to_be_attached(
        timeout=30000
    )
    page.wait_for_load_state("networkidle")
    close_parameters(page)
