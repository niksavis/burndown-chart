"""Process utilities for updater."""

from __future__ import annotations

import os
import subprocess
import sys
import time
from collections.abc import Callable

StatusFn = Callable[[str], None]


def wait_for_process_exit(pid: int, status: StatusFn, timeout: int = 10) -> bool:
    """Wait for a process to exit.

    Args:
        pid: Process ID to wait for
        status: Callback for status output
        timeout: Maximum time to wait in seconds

    Returns:
        True if process exited, False if timeout
    """
    status(f"Waiting for process {pid} to exit (timeout: {timeout}s)...")

    try:
        import psutil

        start_time = time.time()
        while time.time() - start_time < timeout:
            if not psutil.pid_exists(pid):
                status(f"Process {pid} has exited")
                return True
            time.sleep(0.1)
    except ImportError:
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if sys.platform == "win32":
                    result = subprocess.run(
                        ["tasklist", "/FI", f"PID eq {pid}"],
                        capture_output=True,
                        text=True,
                        timeout=1,
                    )
                    if str(pid) not in result.stdout:
                        status(f"Process {pid} has exited")
                        return True
                else:
                    os.kill(pid, 0)

                time.sleep(0.2)
            except (ProcessLookupError, OSError):
                status(f"Process {pid} has exited")
                return True
            except Exception as e:
                status(f"Warning: Error checking process status: {e}")
                time.sleep(0.2)

    status(f"Timeout waiting for process {pid} to exit")
    return False
