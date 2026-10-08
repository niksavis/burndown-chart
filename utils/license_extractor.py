import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_license_on_first_run() -> None:

    is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")
    if not is_frozen:
        logger.debug("Not running as frozen executable, skipping LICENSE extraction")
        return

    executable_dir = Path(sys.executable).parent
    license_dest = executable_dir / "LICENSE.txt"

    if license_dest.exists():
        logger.debug(f"LICENSE.txt already exists at {license_dest}")
        return

    try:
        meipass = Path(sys._MEIPASS)  # type: ignore[attr-defined]
        license_source = meipass / "LICENSE"

        if not license_source.exists():
            logger.warning(
                f"LICENSE file not found in bundle at {license_source}. "
                "This may indicate a packaging issue."
            )
            return

        license_text = license_source.read_text(encoding="utf-8")
        license_dest.write_text(license_text, encoding="utf-8")

        logger.info(f"LICENSE.txt extracted to {license_dest}")
        print(f"LICENSE.txt extracted to {license_dest}")

    except Exception as e:
        logger.error(f"Failed to extract LICENSE.txt: {e}", exc_info=True)
        print(f"WARNING: Failed to extract LICENSE.txt - {e}")
