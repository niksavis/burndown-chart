"""
Installation Context Module

Detects whether the application is running from source or as a PyInstaller executable,
and provides appropriate paths for database, logs, and other resources.
"""

import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass
class InstallationContext:
    """
    Installation context information for the application.

    Attributes:
        is_frozen: True if running as PyInstaller executable, False if running from source
        executable_dir: Directory containing the executable or main script
        database_path: Full path to the SQLite database file
        logs_path: Directory for log files
        is_portable: True if database exists in same directory as executable
    """

    is_frozen: bool
    executable_dir: Path
    database_path: Path
    logs_path: Path
    is_portable: bool

    @classmethod
    def detect(cls) -> "InstallationContext":
        """
        Detect the current installation context.

        Returns:
            InstallationContext with appropriate paths for the current environment
        """
        # Detect if running from PyInstaller bundle
        is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

        if is_frozen:
            # Running as PyInstaller executable
            executable_dir = Path(sys.executable).parent
        else:
            # Running from source
            executable_dir = Path(__file__).parent.parent

        # Check for portable mode: database in same directory as executable
        portable_db_path = executable_dir / "profiles" / "burndown.db"
        is_portable = portable_db_path.parent.exists() or not is_frozen

        # Determine database path
        if is_portable or not is_frozen:
            # Portable mode or source mode: use profiles/ subdirectory
            database_path = executable_dir / "profiles" / "burndown.db"
            logs_path = executable_dir / "profiles" / "logs"
        else:
            # Installed mode (future): use %APPDATA% or similar
            # For now, always use portable mode
            database_path = executable_dir / "profiles" / "burndown.db"
            logs_path = executable_dir / "profiles" / "logs"

        # Ensure directories exist
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
        """String representation for debugging."""
        return (
            f"InstallationContext("
            f"frozen={self.is_frozen}, "
            f"portable={self.is_portable}, "
            f"exe_dir={self.executable_dir}, "
            f"db={self.database_path})"
        )


# Global instance for easy access
_context: InstallationContext | None = None


def get_installation_context() -> InstallationContext:
    """
    Get the global installation context instance.

    Returns:
        The singleton InstallationContext instance
    """
    global _context
    if _context is None:
        _context = InstallationContext.detect()
    return _context
