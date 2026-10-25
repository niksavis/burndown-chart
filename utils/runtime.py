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
    return demo_workspace() or Path("profiles").absolute()
