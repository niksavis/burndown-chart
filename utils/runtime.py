import os
from pathlib import Path


def demo_mode() -> bool:
    return os.environ.get("BURNDOWN_DEMO_MODE") == "1"


def demo_workspace() -> Path | None:
    if not demo_mode():
        return None
    value = os.environ.get("BURNDOWN_DEMO_WORKSPACE")
    if not value:
        raise ValueError("Demo mode requires a workspace; start with python dev.py")
    return Path(value).resolve()


def profiles_directory() -> Path:
    return runtime_workspace() or Path("profiles").absolute()


def verification_mode() -> bool:
    return bool(os.environ.get("BURNDOWN_TEST_WORKSPACE"))


def runtime_workspace() -> Path | None:
    workspace = demo_workspace()
    if workspace is not None:
        return workspace
    verification = os.environ.get("BURNDOWN_TEST_WORKSPACE")
    return Path(verification).resolve() if verification else None
