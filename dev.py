import argparse
import os
import runpy
import subprocess
import sys
from pathlib import Path

from utils.business_time import DEFAULT_DEMO_AS_OF
from utils.demo_workspace import (
    exclusive_workspace,
    publish_demo_database,
    reset_demo_workspace,
)
from utils.offline import install_offline_policy


def _build_seed(workspace: Path, empty: bool) -> None:
    environment = {
        **os.environ,
        "BURNDOWN_DEMO_MODE": "1",
        "BURNDOWN_DEMO_WORKSPACE": str(workspace),
        "BURNDOWN_AS_OF": DEFAULT_DEMO_AS_OF,
    }
    command = [sys.executable, "-m", "data.demo.seed"]
    if empty:
        command.append("--empty")
    subprocess.run(command, env=environment, stdout=sys.stderr, check=True)


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Offline synthetic development workspace"
    )
    parser.add_argument(
        "action",
        nargs="?",
        default="serve",
        choices=["serve", "seed", "reset", "diagnose"],
    )
    parser.add_argument(
        "--workspace", type=Path, default=Path(__file__).parent / "profiles" / "demo"
    )
    parser.add_argument(
        "--empty",
        action="store_true",
        help="Initialize an empty workspace on first launch",
    )
    parser.add_argument("--port", type=int, default=8050)
    parser.add_argument("--confirm-demo-reset", action="store_true")
    arguments = parser.parse_args()
    workspace = arguments.workspace.absolute()
    if workspace != workspace.resolve():
        parser.error("The demo workspace cannot contain symbolic links")
    if not 1 <= arguments.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if arguments.action == "reset" and not arguments.confirm_demo_reset:
        parser.error("Reset requires --confirm-demo-reset and a marked demo workspace")
    arguments.workspace = workspace
    return arguments


def main() -> int:
    arguments = _arguments()
    workspace = arguments.workspace
    os.environ.update(
        BURNDOWN_DEMO_MODE="1",
        BURNDOWN_DEMO_WORKSPACE=str(workspace),
        BURNDOWN_AS_OF=DEFAULT_DEMO_AS_OF,
    )
    install_offline_policy()
    with exclusive_workspace(workspace):
        if arguments.action == "reset":
            reset_demo_workspace(workspace)
            print("Demo database reset; start dev.py to generate it again")
            return 0
        generated = publish_demo_database(
            workspace, lambda path: _build_seed(path, arguments.empty)
        )
        outcome = "generated" if generated else "preserved"
        print(
            f"Offline demo {outcome}; evaluation date {DEFAULT_DEMO_AS_OF}",
            flush=True,
            file=sys.stderr,
        )
        if arguments.action == "seed":
            return 0
        if arguments.action == "diagnose":
            runpy.run_module("devtools.diagnostics", run_name="__main__")
            return 0
        sys.argv = [
            "app.py",
            "--prod",
            "--host",
            "127.0.0.1",
            "--port",
            str(arguments.port),
        ]
        runpy.run_module("app", run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
