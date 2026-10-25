import json
import tempfile
from pathlib import Path
from typing import Literal

import pytest
from playwright.sync_api import Page, sync_playwright

from devtools.plotly_settlement import probe_preference
from devtools.server import running_demo_server


@pytest.mark.parametrize("preference", ["light", "dark"])
def test_passive_plotly_settlement_preserves_data_and_fits_mobile_sprint(
    generated_demo: Path, preference: Literal["light", "dark"]
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        output = Path(directory)
        with running_demo_server(generated_demo, output / "server.log") as url:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch()
                try:
                    page = browser.new_page(
                        viewport={"width": 390, "height": 844},
                        color_scheme=preference,
                    )
                    probe_preference(page, url, output)
                    assert_loading_restarts_the_quiet_interval(page)
                finally:
                    browser.close()
        for graph in ("items-chart", "sprint-burnup-chart"):
            passive = json.loads((output / graph / "passive.json").read_text())
            resized = json.loads((output / graph / "resized.json").read_text())
            before = passive["beforeScreenshot"]
            after = passive["afterScreenshot"]
            assert before == after
            assert before["traces"] == resized["afterScreenshot"]["traces"]
            assert before["axes"] == resized["afterScreenshot"]["axes"]
            assert before["width"] == resized["afterScreenshot"]["width"]
            assert before["svg"]["width"] == pytest.approx(
                before["graph"]["width"], abs=1
            )


def assert_loading_restarts_the_quiet_interval(page: Page) -> None:
    states = page.evaluate("""() => {
        let tick = 0;
        Object.defineProperty(performance, 'now', {value: () => tick});
        const probe = window.burndownPlotlyProbe;
        const selectors = ['#sprint-burnup-chart .js-plotly-plot'];
        probe.reset();
        const states = [probe.settled(selectors)];
        const marker = document.createElement('div');
        marker.setAttribute('data-dash-is-loading', 'true');
        document.body.append(marker);
        tick = 800;
        states.push(probe.settled(selectors));
        marker.remove();
        states.push(probe.settled(selectors));
        tick = 1299;
        states.push(probe.settled(selectors));
        tick = 1300;
        states.push(probe.settled(selectors));
        return states;
    }""")
    assert states == [False, False, False, False, True]
