import os
import sys
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit

import pytest

from utils.offline import install_offline_policy
from utils.runtime import verification_mode


class OfflineProcessGuard:
    def pytest_configure(self, config: pytest.Config) -> None:
        if config.getoption("numprocesses", default=0):
            raise pytest.UsageError(
                "Offline verification runs in one process; remove pytest worker options"
            )


def refuse_normal_database(event: str, arguments: tuple[Any, ...]) -> None:
    if event != "sqlite3.connect":
        return
    database = os.fsdecode(arguments[0])
    if database == ":memory:":
        return
    if database.startswith("file:"):
        database = unquote(urlsplit(database).path)
    path = Path(database).resolve()
    root = Path(__file__).resolve().parents[1]
    protected = {
        root / "profiles" / "burndown.db",
        Path.cwd() / "profiles" / "burndown.db",
    }
    if path in {candidate.resolve() for candidate in protected}:
        raise PermissionError(
            "Verification refuses the normal database; use a temporary fixture"
        )


def main() -> int:
    if not verification_mode():
        raise RuntimeError(
            "Start isolated verification with python -m devtools.offline_pytest"
        )
    install_offline_policy()
    sys.addaudithook(refuse_normal_database)
    return int(pytest.main(sys.argv[1:], plugins=[OfflineProcessGuard()]))


if __name__ == "__main__":
    raise SystemExit(main())
