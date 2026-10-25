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
