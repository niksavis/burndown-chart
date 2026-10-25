import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


def _available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def _wait_for_layout(process: subprocess.Popen, url: str, log: Path) -> None:
    deadline = time.monotonic() + 90
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                f"Demo server stopped before readiness:\n{log.read_text(encoding='utf-8')[-8000:]}"
            )
        try:
            with urllib.request.urlopen(url + "/_dash-layout", timeout=1) as response:
                layout = json.load(response)
        except urllib.error.URLError:
            time.sleep(0.1)
            continue
        if not isinstance(layout, dict) or "props" not in layout:
            raise ValueError("Demo server returned an invalid Dash layout")
        return
    raise TimeoutError("Demo server did not provide a valid layout within 90 seconds")


@contextmanager
def running_demo_server(workspace: Path, log: Path) -> Iterator[str]:
    root = Path(__file__).resolve().parents[1]
    port = _available_port()
    command = [
        sys.executable,
        str(root / "dev.py"),
        "serve",
        "--workspace",
        str(workspace),
        "--port",
        str(port),
    ]
    with log.open("w", encoding="utf-8") as output:
        process = subprocess.Popen(
            command,
            cwd=root,
            env=os.environ.copy(),
            stdout=output,
            stderr=subprocess.STDOUT,
        )
        try:
            url = f"http://127.0.0.1:{port}"
            _wait_for_layout(process, url, log)
            yield url
        finally:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=15)
                except subprocess.TimeoutExpired as error:
                    process.kill()
                    process.wait(timeout=15)
                    raise RuntimeError(
                        "Demo server required forced shutdown"
                    ) from error
