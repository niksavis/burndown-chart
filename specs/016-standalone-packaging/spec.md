# Feature Specification: Standalone Executable Packaging

**Feature Branch**: `016-standalone-packaging`  
**Created**: 2025-12-23  
**Status**: Draft  
**Input**: User description: "Package app as standalone executable without Python, Git, or terminal dependencies. Includes automated build process and new update mechanism for packaged distribution."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download and Run (Priority: P1)

Non-technical users can download a single executable file, double-click to run the app, and immediately start using it without installing Python, Git, or any development tools.

**Why this priority**: Eliminates the largest barrier to adoption. Most users don't have Python installed and don't want to use terminals or IDEs. Single-click execution is essential for mainstream adoption.

**Independent Test**: Download executable on clean Windows system without Python, double-click file, verify app launches and displays dashboard within 5 seconds.

**Acceptance Scenarios**:

1. **Given** user downloads standalone executable on Windows without Python installed, **When** user double-clicks the file, **Then** app launches and displays main dashboard
2. **Given** app is running from executable, **When** user enters JIRA credentials in Settings, **Then** app connects and loads issues without errors
3. **Given** app launches for first time, **When** app initializes, **Then** database file is created in same directory as executable
4. **Given** user closes and reopens app, **When** app restarts, **Then** previous settings and data persist from database
5. **Given** user has no network connection, **When** app launches, **Then** app opens with cached data (no crash on offline mode)

---

### User Story 2 - Automated Build Process (Priority: P1)

Developers can trigger automated build process that packages Python app into standalone Windows executable with all dependencies bundled, producing distributable file ready for release.

**Why this priority**: Without automated packaging, manual builds are error-prone and time-consuming. Automation ensures consistent, reproducible releases and enables CI/CD workflows.

**Independent Test**: Run build command, verify executable is created with correct version, test executable launches successfully and passes smoke tests.

**Acceptance Scenarios**:

1. **Given** developer runs build command, **When** packaging process completes, **Then** standalone executable is created in `dist/` directory
2. **Given** build process runs, **When** executable is generated, **Then** all Python dependencies are bundled (Dash, Plotly, Waitress, etc.)
3. **Given** build completes, **When** executable metadata is inspected, **Then** version number matches app version from `bump_version.py`
4. **Given** executable is built, **When** file is scanned by antivirus, **Then** no false positives detected (proper code signing)
5. **Given** build fails, **When** error occurs, **Then** clear error message indicates what failed (missing dependencies, invalid config, etc.)

---

### User Story 3 - In-App Update Mechanism (Priority: P2)

Packaged app checks for updates on launch, notifies users when new version is available, and allows one-click update download without requiring Git or terminal commands.

**Why this priority**: Users expect modern apps to auto-update. Without this, users must manually download new versions, leading to fragmented version distribution and support complexity.

**Independent Test**: Simulate new version release, launch outdated executable, verify update notification appears and download works.

**Acceptance Scenarios**:

1. **Given** new version is released, **When** user launches outdated executable, **Then** notification appears: "Version X.Y.Z available - Download Update"
2. **Given** user clicks "Download Update", **When** download completes, **Then** app prompts to restart and apply update
3. **Given** update download fails (network error), **When** error occurs, **Then** app continues running current version and retries on next launch
4. **Given** user dismisses update notification, **When** app launches next time, **Then** notification appears again (persistent reminder)
5. **Given** user is on latest version, **When** app checks for updates, **Then** no notification appears and app continues normally

---

### User Story 4 - Local Data Persistence (Priority: P2)

Packaged executable creates and maintains database file in same directory as executable, allowing users to keep all data (settings, cache, metrics) portable with the executable.

**Why this priority**: Enables portable installation where users can move executable to different locations or machines. Critical for users who want to run app from USB drives or shared network folders.

**Independent Test**: Copy executable and database to new directory, run app, verify all data loads correctly from co-located database.

**Acceptance Scenarios**:

1. **Given** app launches for first time in directory, **When** initialization completes, **Then** `burndown.db` file is created in same directory
2. **Given** user moves executable and database to different directory, **When** app launches, **Then** app loads data from co-located database file
3. **Given** database file is missing, **When** app launches, **Then** app creates new empty database and prompts for initial setup
4. **Given** multiple users share app on network drive, **When** each user runs app, **Then** each user's instance uses separate database (user-specific path strategy)

---

### User Story 5 - Error Logging Without Terminal (Priority: P3)

Packaged app writes errors and diagnostics to log files in same directory, allowing users to troubleshoot issues or send logs to support without needing terminal access.

**Why this priority**: Enables self-service troubleshooting and support. Without terminal output, users have no visibility into errors when things go wrong.

**Independent Test**: Trigger error condition (invalid JIRA credentials), close app, verify error logged to file with timestamp and details.

**Acceptance Scenarios**:

1. **Given** app encounters error, **When** error occurs, **Then** error details are written to `logs/app.log` with timestamp
2. **Given** user reports issue, **When** support asks for logs, **Then** user can send `logs/` directory without technical knowledge
3. **Given** log files grow large, **When** app launches, **Then** old logs are rotated (keep last 10 files or 10MB)

---

### Edge Cases

- What happens when executable runs from read-only location (CD-ROM, protected system folder)?
- How does system handle file size limits for single-file executable (large dependencies)?
- What if Windows Defender or antivirus blocks execution (unsigned executable)?
- How does app behave when required system DLLs are missing on user's machine?
- What if user runs multiple versions of executable simultaneously from different directories?
- How does update mechanism work when user doesn't have write permissions to executable directory?
- What if download server for updates is unreachable or returns invalid data?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide automated build script that packages Python app into standalone Windows executable
- **FR-002**: Build process MUST bundle all Python dependencies (Dash, Plotly, Waitress, Bootstrap Components, etc.) into single executable
- **FR-003**: Executable MUST run on Windows 10+ without requiring Python installation
- **FR-004**: Executable MUST create database file in same directory on first launch
- **FR-005**: Executable MUST detect co-located database file and use it for persistence across launches
- **FR-006**: Executable MUST include app version metadata visible in Windows file properties
- **FR-007**: Build process MUST digitally sign executable to prevent antivirus false positives
- **FR-008**: Executable MUST write error logs and diagnostics to `logs/` subdirectory in executable location
- **FR-009**: App MUST check for updates on launch by querying version endpoint (GitHub releases or hosted JSON)
- **FR-010**: App MUST display in-app notification when new version is available with "Download Update" button
- **FR-011**: Update download MUST retrieve new executable and prompt user to restart with new version
- **FR-012**: App MUST handle update download failures gracefully and continue running current version
- **FR-013**: Update mechanism MUST NOT require Git, terminal commands, or Python installation
- **FR-014**: App MUST detect read-only installation directory and prompt user to run from writable location
- **FR-015**: Build process MUST produce executable <100MB in size for reasonable download times
- **FR-016**: Executable MUST display splash screen during initialization to indicate app is loading
- **FR-017**: App MUST support portable mode where database and logs stay with executable regardless of location
- **FR-018**: Build script MUST validate all dependencies are included before finalizing executable
- **FR-019**: Update endpoint MUST serve version metadata including version number, release date, download URL, and changelog
- **FR-020**: App MUST allow users to skip version updates and not be forced to upgrade

### Key Entities

- **Build Configuration**: Defines packaging settings (entry point, included files, dependencies, icon, version metadata)
- **Update Manifest**: Contains version information, download URL, release notes, minimum required version
- **Installation Context**: Tracks executable location, database path, logs path, read-only status, user permissions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users without Python installed can download and run app within 2 minutes of receiving executable file
- **SC-002**: Executable file size under 100MB for practical download over typical internet connections
- **SC-003**: App launches within 5 seconds on systems without Python (comparable to native apps)
- **SC-004**: Automated build process completes in under 10 minutes from code to distributable executable
- **SC-005**: 90% of Windows 10+ systems run executable without requiring additional installations or configurations
- **SC-006**: Update check completes within 2 seconds without blocking app launch or user interface
- **SC-007**: Update download and installation completes within 5 minutes for typical executable size
- **SC-008**: Zero data loss when upgrading between versions using new update mechanism
- **SC-009**: Error logs capture 100% of unhandled exceptions with stack traces for debugging
- **SC-010**: Portable installation allows users to move executable and database to new location without configuration changes

## Scope & Boundaries *(optional)*

### In Scope

- Windows executable packaging (PyInstaller or similar tool)
- Single-file executable with bundled dependencies
- Automated build script for reproducible packaging
- Digital code signing for executable
- In-app update notification and download mechanism
- Local database persistence in executable directory
- Error logging to files without terminal
- Version metadata in executable properties
- Splash screen during initialization
- Portable installation mode

### Out of Scope

- macOS or Linux executable packaging (Windows only for this feature)
- Installer/MSI packages (direct executable distribution)
- Auto-update without user interaction (manual download and restart)
- Cloud-based configuration sync across devices
- Multiple simultaneous installations on same machine
- Rollback to previous version after update
- Delta updates (full executable download required)
- Integration with Windows Store or package managers

### Prerequisites

This feature depends on Feature 015 (SQLite Database Migration) being completed first. The packaged executable requires database persistence to work independently without JSON files.

## Dependencies & Assumptions *(optional)*

### Dependencies

- **Feature 015 (SQLite Persistence)**: Packaged app requires database-based persistence since JSON file operations may not work reliably in bundled executable environment
- PyInstaller or equivalent packaging tool for Python to executable conversion
- Code signing certificate for Windows executable signing
- Hosting infrastructure for update manifest and executable downloads (GitHub Releases recommended)

### Assumptions

- Users run Windows 10 or later (64-bit)
- Users have permissions to run executables (not restricted by corporate policies)
- Executable can write to its own directory for database and logs (not installed to Program Files)
- Internet connection available for update checks (offline mode supported but no updates)
- GitHub Releases or similar public hosting available for distribution
- Code signing certificate can be obtained for production releases

## Risk Assessment *(optional)*

### Technical Risks

- **Executable Size Bloat** (Medium Impact, High Likelihood): Bundling all dependencies may exceed 100MB target. Mitigate with dependency analysis, exclusion of unnecessary packages, and compression.
- **Antivirus False Positives** (High Impact, Medium Likelihood): Unsigned or improperly signed executables trigger Windows Defender. Mitigate with proper code signing certificate and reputation building.
- **Update Mechanism Complexity** (Medium Impact, High Likelihood): Replacing running executable is tricky on Windows. Mitigate with staged update process (download, prompt restart, replace on relaunch).
- **Missing System Dependencies** (Medium Impact, Low Likelihood): Some Windows systems lack required DLLs. Mitigate by bundling Visual C++ redistributables or using static linking.

### User Impact Risks

- **Download Size Barriers** (Low Impact, Medium Likelihood): 100MB executable may deter users on slow connections. Mitigate with compressed download and progress indication.
- **Security Concerns** (High Impact, Low Likelihood): Users may distrust unsigned executable from unknown source. Mitigate with code signing, HTTPS downloads, and clear documentation.
- **Update Notification Fatigue** (Low Impact, Medium Likelihood): Frequent update prompts annoy users. Mitigate with configurable update frequency and skip version option.

## Testing Strategy *(optional)*

### Unit Tests

- Test build script components (dependency detection, version extraction, file inclusion)
- Test update manifest parsing and validation
- Test portable database path detection logic
- Test log file rotation and cleanup

### Integration Tests

- Test full build process end-to-end (source code to executable)
- Test executable launches successfully on clean Windows VM
- Test database creation and persistence in executable directory
- Test update notification flow with mock update server
- Test update download and installation process
- Test portable mode (copy executable + database to new location)

### System Tests

- Test on multiple Windows versions (Windows 10, 11)
- Test on systems with/without Python installed
- Test with different antivirus software (Windows Defender, Norton, McAfee)
- Test in restricted environments (limited user permissions)
- Test read-only installation scenarios
- Test concurrent instances of executable

### User Acceptance Tests

- Verify non-technical users can download and run without help
- Verify update notification is clear and actionable
- Verify error messages are helpful when problems occur
- Verify app performance matches development mode
- Verify portable installation works as expected

## Implementation Notes *(optional)*

### Packaging Tool Selection

Recommended approach: **PyInstaller** with single-file mode
- Industry standard for Python to executable
- Good support for Dash and Plotly
- Can produce single-file executables
- Supports custom icons and version metadata

Alternative: **py2exe** or **cx_Freeze** if PyInstaller issues arise

### Update Mechanism Architecture

1. **Update Check**: Query GitHub Releases API or hosted JSON manifest on launch
2. **Version Comparison**: Compare current version (embedded in executable) with latest available
3. **Download**: Use requests library to download new executable to temp directory
4. **Staging**: Store downloaded executable as `app_new.exe` in same directory
5. **Restart Prompt**: Notify user and offer to restart application
6. **Replacement**: On relaunch, detect staged update, replace current executable, delete staged file

### Database Path Strategy

Portable mode priority:
1. Check for database in executable directory
2. If not found, check user AppData directory
3. If neither exists, create in executable directory (if writable)
4. If not writable, fallback to user AppData and warn about portability

### Code Signing Process

1. Obtain code signing certificate (Sectigo, DigiCert, etc.)
2. Sign executable during build: `signtool.exe sign /f cert.pfx /p password app.exe`
3. Verify signature: `signtool.exe verify /pa app.exe`
4. Build reputation over time to reduce SmartScreen warnings
