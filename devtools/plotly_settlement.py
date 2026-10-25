import argparse
import json
from pathlib import Path

from playwright.sync_api import Page, expect, sync_playwright

from devtools.browser_observer import BrowserObservation
from devtools.journeys import TAB_MARKERS, select_tab
from devtools.plotly_observation import (
    install_plotly_observation,
    wait_for_plotly_settlement,
)
from devtools.server import running_demo_server
from ui.tabs import TAB_CONFIG


def record_stage(page: Page, selector: str, output: Path, stage: str) -> dict:
    before = page.evaluate(
        "selector => window.burndownPlotlyProbe.snapshot(selector)", selector
    )
    page.screenshot(path=str(output / f"{stage}.png"), animations="disabled")
    after = page.evaluate(
        "selector => window.burndownPlotlyProbe.snapshot(selector)", selector
    )
    state = {"beforeScreenshot": before, "afterScreenshot": after}
    (output / f"{stage}.json").write_text(json.dumps(state, indent=2), encoding="utf-8")
    return state


def probe_graph(page: Page, graph_id: str, output: Path) -> None:
    output.mkdir(parents=True)
    selector = f"#{graph_id} .js-plotly-plot"
    page.wait_for_function(
        "selector => document.querySelector(selector)?.data?.length > 0", arg=selector
    )
    page.locator(f"#{graph_id}").evaluate(
        "element => window.scrollTo({top: element.getBoundingClientRect().top "
        "+ scrollY - 120, behavior: 'instant'})"
    )
    record_stage(page, selector, output, "current")
    wait_for_plotly_settlement(page, [selector])
    record_stage(page, selector, output, "passive")
    page.set_viewport_size({"width": 391, "height": 844})
    wait_for_plotly_settlement(page, [selector])
    page.set_viewport_size({"width": 390, "height": 844})
    wait_for_plotly_settlement(page, [selector])
    record_stage(page, selector, output, "resized")


def probe_preference(page: Page, url: str, output: Path) -> None:
    page.goto(url, wait_until="domcontentloaded")
    page.locator("#tab-content").wait_for(state="visible")
    install_plotly_observation(page)
    for tab_id, graph_id in (
        ("tab-burndown", "items-chart"),
        ("tab-sprint-tracker", "sprint-burnup-chart"),
    ):
        tab = next(tab for tab in TAB_CONFIG if tab["id"] == tab_id)
        select_tab(page, tab, mobile=True)
        expect(page.locator("#tab-content")).to_contain_text(
            TAB_MARKERS[tab_id], timeout=30000
        )
        if tab_id == "tab-sprint-tracker":
            page.locator("#toggle-sprint-charts").click()
        probe_graph(page, graph_id, output / graph_id)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe passive Plotly settlement")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    arguments = parser.parse_args()
    output = arguments.output.absolute()
    output.mkdir(parents=True, exist_ok=False)
    with running_demo_server(
        arguments.workspace.absolute(), output / "server.log"
    ) as url:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            try:
                for preference in ("light", "dark"):
                    context = browser.new_context(
                        viewport={"width": 390, "height": 844}, color_scheme=preference
                    )
                    try:
                        page = context.new_page()
                        observation = BrowserObservation()
                        observation.observe(context, page)
                        probe_preference(page, url, output / preference)
                        observation.assert_clean()
                    finally:
                        context.close()
            finally:
                browser.close()
    print(f"Plotly stage probe artifacts: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
