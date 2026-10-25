import sys

import pytest

from utils.offline import install_offline_policy


class OfflineProcessGuard:
    def pytest_configure(self, config: pytest.Config) -> None:
        if config.getoption("numprocesses", default=0):
            raise pytest.UsageError(
                "Offline verification runs in one process; remove pytest worker options"
            )


def main() -> int:
    install_offline_policy()
    return int(pytest.main(sys.argv[1:], plugins=[OfflineProcessGuard()]))


if __name__ == "__main__":
    raise SystemExit(main())
