"""
Generate Windows version information file for PyInstaller.

Reads the version from configuration/__init__.py and creates a version_info.txt
file with Windows file metadata that PyInstaller embeds into the executable.
"""

import sys
from pathlib import Path


def get_version():
    """Read version from configuration/__init__.py"""
    config_file = Path(__file__).parent.parent / "configuration" / "__init__.py"

    if not config_file.exists():
        print(f"Error: Configuration file not found: {config_file}", file=sys.stderr)
        sys.exit(1)

    with open(config_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("__version__"):
                # Extract version from line like: __version__ = "2.5.0"
                version_str = line.split("=")[1].strip().strip('"').strip("'")
                return version_str

    print(
        "Error: Could not find __version__ in configuration/__init__.py",
        file=sys.stderr,
    )
    sys.exit(1)


def version_to_tuple(version_str):
    """Convert version string to 4-part tuple"""
    parts = version_str.split(".")
    # Pad with zeros if needed (2.5.0 -> 2.5.0.0)
    parts += ["0"] * (4 - len(parts))
    return tuple(int(p) for p in parts[:4])


def generate_version_info(version_str, exe_type="main"):
    """Generate version_info.txt content.

    Args:
        version_str: Version string (e.g., "2.6.2")
        exe_type: "main" for Burndown.exe or "updater" for BurndownUpdater.exe
    """
    version_tuple = version_to_tuple(version_str)
    filevers_str = ", ".join(str(v) for v in version_tuple)

    if exe_type == "updater":
        file_description = "Burndown Updater"
        internal_name = "BurndownUpdater"
        original_filename = "BurndownUpdater.exe"
        product_name = "Burndown Updater"
    else:
        file_description = "Burndown"
        internal_name = "Burndown"
        original_filename = "Burndown.exe"
        product_name = "Burndown"

    return f"""# UTF-8
#
# Windows version information file for {product_name}
# This file is used by PyInstaller to embed metadata into the .exe
#
# Auto-generated from configuration/__init__.py version: {version_str}

VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({filevers_str}),
    prodvers=({filevers_str}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
    ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Niksa Visic'),
        StringStruct(u'FileDescription', u'{file_description}'),
        StringStruct(u'FileVersion', u'{version_str}'),
        StringStruct(u'InternalName', u'{internal_name}'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025-2026 Niksa Visic'),
        StringStruct(u'OriginalFilename', u'{original_filename}'),
        StringStruct(u'ProductName', u'{product_name}'),
        StringStruct(u'ProductVersion', u'{version_str}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def main():
    """Main entry point - generates version info for both executables"""
    version_str = get_version()

    # Generate for main executable
    content_main = generate_version_info(version_str, exe_type="main")
    output_file_main = Path(__file__).parent / "version_info.txt"
    output_file_main.write_text(content_main, encoding="utf-8")
    print(f"Generated {output_file_main} for version {version_str}")

    # Generate for updater executable
    content_updater = generate_version_info(version_str, exe_type="updater")
    output_file_updater = Path(__file__).parent / "version_info_updater.txt"
    output_file_updater.write_text(content_updater, encoding="utf-8")
    print(f"Generated {output_file_updater} for version {version_str}")


if __name__ == "__main__":
    main()
