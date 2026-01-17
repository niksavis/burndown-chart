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


def generate_version_info(version_str):
    """Generate version_info.txt content"""
    version_tuple = version_to_tuple(version_str)
    filevers_str = ", ".join(str(v) for v in version_tuple)

    return f"""# UTF-8
#
# Windows version information file for BurndownChart executable
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
        StringStruct(u'FileDescription', u'Burndown Chart'),
        StringStruct(u'FileVersion', u'{version_str}'),
        StringStruct(u'InternalName', u'BurndownChart'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2025-2026 Niksa Visic. Licensed under MIT License.'),
        StringStruct(u'OriginalFilename', u'BurndownChart.exe'),
        StringStruct(u'ProductName', u'Burndown Chart'),
        StringStruct(u'ProductVersion', u'{version_str}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
"""


def main():
    """Main entry point"""
    version_str = get_version()
    content = generate_version_info(version_str)

    # Write to build/version_info.txt
    output_file = Path(__file__).parent / "version_info.txt"
    output_file.write_text(content, encoding="utf-8")

    print(f"Generated {output_file} for version {version_str}")


if __name__ == "__main__":
    main()
