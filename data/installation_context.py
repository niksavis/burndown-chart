import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstallationContext:
    is_frozen: bool
    executable_dir: Path
    database_path: Path
    logs_path: Path
    is_portable: bool

    @classmethod
    def detect(cls) -> InstallationContext:

        is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

        if is_frozen:
            executable_dir = Path(sys.executable).parent
        else:
            executable_dir = Path(__file__).parent.parent

        portable_db_path = executable_dir / "profiles" / "burndown.db"
        is_portable = portable_db_path.parent.exists() or not is_frozen

        if is_portable or not is_frozen:
            database_path = executable_dir / "profiles" / "burndown.db"
        else:
            database_path = executable_dir / "profiles" / "burndown.db"

        logs_path = executable_dir / "logs"

        database_path.parent.mkdir(parents=True, exist_ok=True)
        logs_path.mkdir(parents=True, exist_ok=True)

        return cls(
            is_frozen=is_frozen,
            executable_dir=executable_dir,
            database_path=database_path,
            logs_path=logs_path,
            is_portable=is_portable,
        )

    def __repr__(self) -> str:
        return (
            f"InstallationContext("
            f"frozen={self.is_frozen}, "
            f"portable={self.is_portable}, "
            f"exe_dir={self.executable_dir}, "
            f"db={self.database_path})"
        )


_context: InstallationContext | None = None


def get_installation_context() -> InstallationContext:

    global _context
    if _context is None:
        _context = InstallationContext.detect()
    return _context
