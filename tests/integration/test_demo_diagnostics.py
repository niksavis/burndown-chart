import json
import os
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path


def test_diagnostics_emit_json_restore_selection_and_fail_on_discrepancies(
    generated_demo: Path,
) -> None:
    root = Path(__file__).resolve().parents[2]
    result = subprocess.run(
        [
            sys.executable,
            str(root / "dev.py"),
            "diagnose",
            "--workspace",
            str(generated_demo),
        ],
        cwd=root,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
        timeout=120,
    )
    report = json.loads(result.stdout)
    failed = sum(not check["passed"] for check in report["checks"])
    assert report["failed"] == failed
    assert result.returncode == (1 if failed else 0)
    fractional = next(
        check
        for check in report["checks"]
        if check["calculation"] == "fractional-points"
    )
    assert fractional["expected"] == 6.5
    assert fractional["passed"] is (fractional["actual"] == 6.5)
    with closing(sqlite3.connect(generated_demo / "burndown.db")) as connection:
        selected = connection.execute(
            "SELECT value FROM app_state WHERE key = ?", ("active_profile_id",)
        ).fetchone()
        assert selected == ("demo-complete",)
