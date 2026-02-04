# Windows Installation Guide

**Audience**: Windows users running the standalone executable
**Part of**: [Documentation Index](readme.md)

## Overview

The Windows release ships as a standalone executable. No Python installation is required.

## Install and Run

1. Download the latest Windows release archive from GitHub.
2. Extract the archive to a writable folder.
3. Run the main executable.
4. The app opens in your default browser.

## Data Storage

- A database file is created next to the executable.
- Logs are written to a logs/ directory in the same folder.

## Updates

- The app checks for updates on startup.
- When an update is available, follow the in-app prompt to download and apply it.

## Related Documentation

- [Release Process](release_process.md)
- [Updater Architecture](updater_architecture.md)
