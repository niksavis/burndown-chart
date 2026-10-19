import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

import run_consumer_hooks


def test_missing_venv_refuses_to_report_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TemporaryDirectory() as directory:
        monkeypatch.setattr(run_consumer_hooks, "PYTHON", Path(directory) / "python")
        with pytest.raises(SystemExit, match="Create .venv"):
            run_consumer_hooks.main()


def test_a_consumer_check_failure_reaches_the_commit_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with TemporaryDirectory() as directory:
        python = Path(directory) / "python"
        python.touch()
        monkeypatch.setattr(run_consumer_hooks, "PYTHON", python)
        monkeypatch.setattr(
            run_consumer_hooks.subprocess,
            "run",
            lambda *args, **kwargs: subprocess.CompletedProcess(args, 17),
        )

        assert run_consumer_hooks.main() == 17
