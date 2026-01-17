"""
License Extraction Utility

Extracts LICENSE.txt from frozen executable on first run.
Ensures users have easy access to license terms.
"""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_license_on_first_run() -> None:
    """
    Extract LICENSE.txt to executable directory on first run.

    Only runs when:
    1. Application is frozen (running as PyInstaller executable)
    2. LICENSE.txt does not exist in the executable directory

    The LICENSE file is bundled in the executable and extracted to make
    it easily accessible to users without opening the executable bundle.

    Note: Third-party licenses remain bundled in the executable and are
    accessible via the About dialog. This extraction is only for the main
    project license.
    """
    # Only proceed if running as frozen executable
    is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    if not is_frozen:
        logger.debug("Not running as frozen executable, skipping LICENSE extraction")
        return

    # Determine paths
    executable_dir = Path(sys.executable).parent
    license_dest = executable_dir / "LICENSE.txt"

    # Check if LICENSE already exists
    if license_dest.exists():
        logger.debug(f"LICENSE.txt already exists at {license_dest}")
        return

    # Extract LICENSE from bundled resources
    try:
        # PyInstaller bundles resources in _MEIPASS directory
        # Type ignore: _MEIPASS is set by PyInstaller at runtime
        meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        license_source = meipass / "LICENSE"

        if not license_source.exists():
            logger.warning(
                f"LICENSE file not found in bundle at {license_source}. "
                "This may indicate a packaging issue."
            )
            return

        # Read from bundle and write to executable directory
        license_text = license_source.read_text(encoding="utf-8")
        license_dest.write_text(license_text, encoding="utf-8")

        logger.info(f"LICENSE.txt extracted to {license_dest}")
        print(f"LICENSE.txt extracted to {license_dest}")

    except Exception as e:
        # Log error but don't crash - this is not critical for app functionality
        logger.error(f"Failed to extract LICENSE.txt: {e}", exc_info=True)
        print(f"WARNING: Failed to extract LICENSE.txt - {e}")
