from pathlib import Path

from playwright.sync_api import Page

STATE_SCRIPT = Path(__file__).with_name("plotly_state.js")


def install_plotly_observation(page: Page) -> None:
    if not page.evaluate("Boolean(window.burndownPlotlyProbe)"):
        page.add_script_tag(
            content=STATE_SCRIPT.read_text(encoding="utf-8"), type="module"
        )
        page.wait_for_function("Boolean(window.burndownPlotlyProbe)")


def wait_for_plotly_settlement(page: Page, selectors: list[str]) -> None:
    _wait_for_settlement(page, "settled", selectors)


def wait_for_page_settlement(page: Page, root_selector: str) -> None:
    _wait_for_settlement(page, "pageSettled", root_selector)


def _wait_for_settlement(page: Page, method: str, selection: list[str] | str) -> None:
    install_plotly_observation(page)
    page.evaluate("window.burndownPlotlyProbe.reset()")
    page.wait_for_function(
        "({method, selection}) => window.burndownPlotlyProbe[method](selection)",
        arg={"method": method, "selection": selection},
        timeout=10000,
    )
