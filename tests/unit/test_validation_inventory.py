from unittest.mock import patch

import pytest

import validate


@pytest.mark.parametrize("include_performance", [False, True])
def test_validation_runs_all_test_layers_with_the_offline_runner(
    include_performance: bool,
) -> None:
    with patch.object(validate, "_run", return_value=0) as run:
        assert validate.check_coverage(include_performance=include_performance) == 0
    command = run.call_args.args[1]
    assert command[:4] == [
        str(validate.PYTHON),
        "-m",
        "devtools.offline_pytest",
        "tests/",
    ]
    assert "tests/unit/" not in command
    assert f"--cov-fail-under={validate.COVERAGE_RATCHET_PERCENT}" in command
    assert ("not performance" in command) is (not include_performance)


def test_static_gate_reuses_hook_scope_and_checks_project_files() -> None:
    import subprocess
    from pathlib import Path
    from tempfile import TemporaryDirectory

    with TemporaryDirectory() as directory:
        root = Path(directory)
        (root / ".pre-commit-consumer.yaml").write_text(
            "repos:\n- hooks:\n  - id: prettier\n"
            '    files: "\\\\.(js|json)$"\n'
            '    exclude: "^generated/"\n',
            encoding="utf-8",
        )
        names = ["app.js", "settings.json", "readme.md", "generated/runtime.js"]
        for name in names:
            path = root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("", encoding="utf-8")
        result = subprocess.CompletedProcess([], 0, stdout=("\0".join(names)).encode())
        with (
            patch.object(validate, "ROOT", root),
            patch.object(validate.subprocess, "run", return_value=result),
        ):
            assert validate._hook_files("prettier") == ["app.js", "settings.json"]
