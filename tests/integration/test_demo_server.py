import tempfile
import urllib.request
from pathlib import Path

from devtools.server import running_demo_server
from utils.demo_workspace import exclusive_workspace


def test_demo_server_serves_real_layout_and_releases_workspace(
    generated_demo: Path,
) -> None:
    with tempfile.TemporaryDirectory() as directory:
        with running_demo_server(generated_demo, Path(directory) / "server.log") as url:
            with urllib.request.urlopen(url + "/_dash-layout", timeout=10) as response:
                assert response.status == 200
                assert b"Acme Corp" in response.read()
            with urllib.request.urlopen(
                url + "/_dash-dependencies", timeout=10
            ) as response:
                assert response.status == 200
                assert b"tab-content" in response.read()
        with exclusive_workspace(generated_demo):
            assert (generated_demo / "burndown.db").is_file()
