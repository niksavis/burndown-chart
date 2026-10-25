import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def run_demo_seed(workspace: Path, log: Path, *, empty: bool = False) -> None:
    command = [
        sys.executable,
        str(PROJECT_ROOT / "dev.py"),
        "seed",
        "--workspace",
        str(workspace),
    ]
    if empty:
        command.append("--empty")
    with log.open("w", encoding="utf-8") as output:
        result = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            env=os.environ.copy(),
            stdout=output,
            stderr=subprocess.STDOUT,
            timeout=300,
        )
    assert result.returncode == 0, log.read_text(encoding="utf-8")[-12000:]


@pytest.fixture(scope="session")
def generated_demo_template() -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        workspace = root / "demo"
        run_demo_seed(workspace, root / "seed.log")
        yield workspace


@pytest.fixture
def generated_demo(generated_demo_template: Path) -> Iterator[Path]:
    with tempfile.TemporaryDirectory() as directory:
        workspace = Path(directory)
        for name in ("burndown.db", ".demo-workspace"):
            shutil.copyfile(generated_demo_template / name, workspace / name)
        yield workspace
