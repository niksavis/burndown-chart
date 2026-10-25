import os
import subprocess
import sys
import tempfile
from pathlib import Path


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="burndown-verification-") as directory:
        environment = os.environ.copy()
        for name in ("BURNDOWN_DEMO_MODE", "BURNDOWN_DEMO_WORKSPACE", "BURNDOWN_AS_OF"):
            environment.pop(name, None)
        environment["BURNDOWN_TEST_WORKSPACE"] = str(Path(directory) / "profiles")
        result = subprocess.run(
            [sys.executable, "-m", "devtools.offline_pytest_worker", *sys.argv[1:]],
            env=environment,
            check=False,
        )
        return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
