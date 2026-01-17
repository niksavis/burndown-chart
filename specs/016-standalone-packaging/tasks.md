# Tasks: Standalone Executable Packaging

**Feature**: 016-standalone-packaging  
**Input**: Design documents from `specs/016-standalone-packaging/`  
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

## Format: `- [ ] [ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: User story label (US1-US8)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Initialize build infrastructure and dependencies

- [ ] T001 Add PyInstaller to requirements.in with version >=6.0.0 and comment explaining build-only dependency
- [ ] T002 [P] Create build/ directory structure with subdirectories for scripts and configuration
- [ ] T003 [P] Create updater/ directory with subdirectory structure for standalone updater executable
- [ ] T004 [P] Create licenses/ directory at repository root for bundled license files
- [ ] T005 Install PyInstaller and regenerate requirements.txt using pip-compile requirements.in

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before user story implementation

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create build/build_config.yaml defining PyInstaller settings (app name, version source, entry point, icon path, dependencies to include/exclude)
- [ ] T007 Create build/collect_licenses.ps1 script to run pip-licenses and generate licenses/THIRD_PARTY_LICENSES.txt
- [ ] T008 [P] Create build/app.spec PyInstaller specification for main app executable with all dependencies, assets, and exclusions configured
- [ ] T009 [P] Create build/updater.spec PyInstaller specification for updater executable with minimal dependencies
- [ ] T010 Create data/installation_context.py with InstallationContext dataclass to detect executable vs source, resolve database paths, and determine portable mode
- [ ] T011 Update app.py to use InstallationContext for database path resolution instead of hardcoded paths
- [ ] T012 Create assets/icon.ico application icon file (256x256) for Windows executable

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 3 - Automated Build Process (Priority: P1) 🎯 MVP

**Goal**: Developers can run build command to package Python app into Windows executables

**Independent Test**: Run build script, verify app.exe and updater.exe created in dist/, test executables launch successfully

### Implementation for User Story 3

- [ ] T013 [P] [US3] Create build/build.ps1 PowerShell script with commands to run PyInstaller for both app.spec and updater.spec
- [ ] T014 [P] [US3] Add build script parameters: -Clean (remove previous build), -Verbose (detailed output), -Test (run post-build tests), -Sign (code signing)
- [ ] T015 [P] [US3] Create build/package.ps1 script to create ZIP file dist/burndown-chart-windows-v{version}.zip containing both executables and licenses/
- [ ] T016 [US3] Add version extraction logic to build.ps1 reading from bump_version.py or **version** variable
- [ ] T017 [US3] Run build/collect_licenses.ps1 as part of build.ps1 to ensure licenses are up-to-date before packaging
- [ ] T018 [US3] Add validation in build.ps1 to verify no test dependencies (pytest, playwright, pip-tools) are imported by bundled code
- [ ] T019 [US3] Configure PyInstaller in app.spec to exclude test dependencies using excludes parameter
- [ ] T020 [US3] Configure PyInstaller in app.spec to bundle assets/ and licenses/ directories using datas parameter
- [ ] T021 [US3] Test build process: run build.ps1 on clean system, verify dist/ contains BurndownChart.exe (~80-100MB) and BurndownChartUpdater.exe (~10-15MB)
- [ ] T022 [US3] Create build/sign_executable.ps1 script for code signing with certificate (optional, for future use)

**Checkpoint**: At this point, build process produces working executables that can be tested locally

---

## Phase 4: User Story 1 - Download and Run (Priority: P1) 🎯 MVP

**Goal**: Non-technical users can double-click executable and immediately use app without Python installation

**Independent Test**: Copy dist/BurndownChart.exe to clean Windows system without Python, double-click, verify browser opens within 5 seconds

### Implementation for User Story 1

- [ ] T023 [P] [US1] Modify app.py to detect if running from PyInstaller executable using sys.frozen attribute
- [ ] T024 [P] [US1] Add browser auto-launch logic to app.py using webbrowser.open() after server starts
- [ ] T025 [P] [US1] Add server readiness check in app.py: wait for port to accept connections (max 3s timeout) before opening browser
- [ ] T026 [P] [US1] Configure terminal window in app.spec to remain visible (console=True) for status messages and shutdown control
- [ ] T027 [US1] Update app.py to display clickable URL in terminal window always (even if browser opens)
- [ ] T028 [US1] Add environment variable check BURNDOWN_NO_BROWSER=1 to disable auto-launch for users who prefer terminal-only
- [ ] T029 [US1] Add graceful shutdown handler in app.py to catch Ctrl+C and close terminal signals (SIGINT, SIGTERM)
- [ ] T030 [US1] Update data/database.py to use InstallationContext.database_path for SQLite connection
- [ ] T031 [US1] Add database directory creation logic: ensure profiles/ directory exists before creating burndown.db
- [ ] T032 [US1] Test executable launch: verify terminal appears, server starts, browser opens automatically, app loads in browser
- [ ] T033 [US1] Test offline mode: disconnect network, launch executable, verify app opens with cached data (no crash)
- [ ] T034 [US1] Test persistence: configure JIRA settings, close app, reopen, verify settings persisted in database
- [ ] T035 [US1] Test browser independence: close browser tab, verify app server continues running, reopen URL in new tab

**Checkpoint**: Executable provides complete user experience - download, double-click, use immediately

---

## Phase 5: User Story 5 - Local Data Persistence (Priority: P2)

**Goal**: Database file created in same directory as executable for portable installation

**Independent Test**: Copy executable and profiles/ to USB drive, run from USB, verify data loads correctly

### Implementation for User Story 5

- [ ] T036 [P] [US5] Update InstallationContext.detect() to resolve database path relative to sys.executable when frozen
- [ ] T037 [US5] Add portable mode detection: check if database exists in same directory as executable
- [ ] T038 [US5] Update data/persistence/ modules to use InstallationContext.database_path consistently
- [ ] T039 [US5] Add database initialization check: create empty database if profiles/burndown.db missing on first run
- [ ] T040 [US5] Test portable installation: copy BurndownChart.exe to new directory, run, verify database created in profiles/ subdirectory
- [ ] T041 [US5] Test database migration: copy executable + existing profiles/ to different location, verify data loads correctly

**Checkpoint**: Portable installation works - users can move executable freely without losing data

---

## Phase 6: User Story 4 - Automatic Update Mechanism (Priority: P2)

**Goal**: App checks for updates on launch, downloads from GitHub, installs via updater executable

**Independent Test**: Mock newer version on GitHub, launch app, verify update notification appears, test download and installation

### Implementation for User Story 4

- [ ] T042 [P] [US4] Create data/update_manager.py with UpdateState enum and UpdateProgress dataclass from data-model.md
- [ ] T043 [P] [US4] Implement check_for_updates() function in data/update_manager.py to query GitHub releases API endpoint
- [ ] T044 [P] [US4] Add version comparison logic in data/update_manager.py using semantic versioning (strip 'v' prefix, compare X.Y.Z)
- [ ] T045 [P] [US4] Implement download_update() function in data/update_manager.py to download ZIP from GitHub release asset URL
- [ ] T046 [P] [US4] Add progress tracking in download_update() to update UpdateProgress.progress_percent during download
- [ ] T047 [US4] Add update check call in app.py on launch using background thread (threading.Thread with daemon=True)
- [ ] T048 [US4] Ensure update check is non-blocking: app UI must appear even if check times out after 2 seconds
- [ ] T049 [US4] Create ui/update_notification.py component with dbc.Alert showing "Version X.Y.Z available - Update Now" button
- [ ] T050 [US4] Create callbacks/app_update.py with callback to handle "Update Now" button click (delegate to data/update_manager.py)
- [ ] T051 [US4] Implement updater launcher in data/update_manager.py: extract ZIP, launch BurndownChartUpdater.exe with args, exit app
- [ ] T052 [P] [US4] Create updater/updater.py with main logic: wait for app.exe to exit, backup old exe, replace with new exe, relaunch
- [ ] T053 [P] [US4] Add error handling in updater.py: restore from .bak file if replacement fails
- [ ] T054 [P] [US4] Add timeout handling in updater.py: if app.exe doesn't exit within 10 seconds, show error and abort
- [ ] T055 [US4] Test update check: mock GitHub API response with newer version, verify notification appears in app footer
- [ ] T056 [US4] Test download: mock GitHub release ZIP, click "Update Now", verify download completes and progress shown
- [ ] T057 [US4] Test updater: create mock new exe, run updater, verify old exe backed up, new exe copied, app relaunched
- [ ] T058 [US4] Test error handling: simulate network failure during download, verify app continues running with error message
- [ ] T059 [US4] Test timeout: ensure update check completes within 2 seconds or times out gracefully without blocking UI

**Checkpoint**: Update mechanism fully functional - users can stay current with one-click updates

---

## Phase 7: User Story 8 - License Transparency (Priority: P3)

**Goal**: Users can view all dependency licenses in-app, distribution includes bundled license files

**Independent Test**: Open About dialog, verify all 55 dependencies listed with licenses and repository links

### Implementation for User Story 8

- [ ] T060 [P] [US8] Run build/collect_licenses.ps1 to generate licenses/THIRD_PARTY_LICENSES.txt with all dependency licenses
- [ ] T061 [P] [US8] Create licenses/LICENSE.txt containing app's MIT license text
- [ ] T062 [P] [US8] Create licenses/NOTICE.txt listing all Apache 2.0 dependencies (dash-bootstrap-components, requests, python-dateutil, etc.) per Apache 2.0 requirements
- [ ] T063 [P] [US8] Create ui/about_dialog.py with dbc.Modal containing tabs: App Info, Open Source Licenses, Changelog
- [ ] T064 [P] [US8] Implement Licenses tab in ui/about_dialog.py: read licenses/THIRD_PARTY_LICENSES.txt and display as formatted table
- [ ] T065 [P] [US8] Add search/filter functionality in Licenses tab to filter dependencies by name or license type
- [ ] T066 [US8] Add About button to app footer (existing footer component) that opens About modal
- [ ] T067 [US8] Create callback in callbacks/about_dialog.py to handle About button click and modal open/close
- [ ] T068 [US8] Verify licenses/ directory bundled in executable: check app.spec datas parameter includes licenses folder
- [ ] T069 [US8] Test About dialog: open app, click About in footer, verify modal opens with all tabs populated
- [ ] T070 [US8] Test license display: verify all 55 dependencies appear in Licenses tab with correct license types
- [ ] T071 [US8] Test bundled files: extract executable package, verify licenses/ directory exists with all 3 files (LICENSE.txt, NOTICE.txt, THIRD_PARTY_LICENSES.txt)

**Checkpoint**: Professional license attribution complete - legal compliance and user transparency achieved

---

## Phase 8: User Story 7 - Error Logging (Priority: P3)

**Goal**: Errors written to log files for troubleshooting without terminal access

**Independent Test**: Trigger error (invalid JIRA credentials), verify error logged to profiles/logs/app.log with timestamp

### Implementation for User Story 7

- [ ] T072 [P] [US7] Update configuration/logging_config.py to add file handler writing to profiles/logs/app.log
- [ ] T073 [P] [US7] Add log directory creation logic: ensure profiles/logs/ exists before writing logs
- [ ] T074 [P] [US7] Configure log rotation in logging_config.py: RotatingFileHandler with maxBytes=10MB and backupCount=10
- [ ] T075 [P] [US7] Ensure all error handlers use logger.exception() to capture stack traces in log files
- [ ] T076 [US7] Update InstallationContext to include logs_path property pointing to profiles/logs/
- [ ] T077 [US7] Test error logging: trigger JIRA connection error, verify error written to profiles/logs/app.log
- [ ] T078 [US7] Test log rotation: generate >10MB of logs, verify old logs rotated to app.log.1, app.log.2, etc.

**Checkpoint**: Error logging functional - users can troubleshoot or send logs to support

---

## Phase 9: User Story 2 - Automated GitHub Release Process (Priority: P1) 🎯 MVP

**Goal**: Automated workflow builds executables, creates GitHub release, uploads assets

**Independent Test**: Push tag to GitHub, verify workflow builds executables, creates release with proper structure

### Implementation for User Story 2

- [ ] T079 [P] [US2] Create .github/workflows/release.yml workflow file triggered on tag push (tags: v*)
- [ ] T080 [P] [US2] Configure workflow to run on windows-latest runner with Python 3.13 setup
- [ ] T081 [P] [US2] Add workflow steps: checkout code, setup Python, install dependencies, run build/build.ps1
- [ ] T082 [P] [US2] Add workflow step to run build/collect_licenses.ps1 to ensure licenses are current
- [ ] T083 [P] [US2] Add workflow step to run build/package.ps1 to create ZIP file for release
- [ ] T084 [US2] Add changelog generation step in workflow using github.event.commits or GitHub GraphQL API for PR titles
- [ ] T085 [US2] Add workflow step to create GitHub release using actions/create-release with title "Burndown Chart v{version}"
- [ ] T086 [US2] Add workflow step to upload ZIP asset to release using actions/upload-release-asset
- [ ] T087 [US2] Create release notes template with sections: Installation Instructions (Windows Standalone vs Run from Source)
- [ ] T088 [US2] Add installation instructions to release body: Windows (download ZIP, extract, run exe) vs Source (clone repo, install Python, run commands)
- [ ] T089 [US2] Add workflow error handling: fail gracefully with clear message if build fails, don't publish partial release
- [ ] T090 [US2] Test workflow locally: use act or manual trigger to verify workflow steps execute correctly
- [ ] T091 [US2] Create test tag v2.5.1-test, push to GitHub, verify workflow runs and creates test release
- [ ] T092 [US2] Verify release structure: title correct, changelog present, ZIP asset uploaded, installation instructions clear
- [ ] T093 [US2] Test update mechanism integration: verify app.py can query new release from GitHub API and detect update

**Checkpoint**: Automated releases working - developers can release with git tag push

---

## Phase 10: User Story 6 - Cross-Platform Distribution (Priority: P3)

**Goal**: Linux/macOS users can download source ZIP and run using Python commands

**Independent Test**: Download source ZIP on Linux, extract, run python app.py, verify app launches

### Implementation for User Story 6

- [ ] T094 [P] [US6] Update README.md with clear sections: "Windows (Standalone)" and "All Platforms (From Source)"
- [ ] T095 [P] [US6] Add installation instructions for source approach: download ZIP, extract, create venv, install requirements, run app.py
- [ ] T096 [US6] Verify source distribution works on Linux: test on Ubuntu VM without packaging, just python app.py
- [ ] T097 [US6] Verify source distribution works on macOS: test on macOS without packaging
- [ ] T098 [US6] Update release workflow to include source ZIP link (GitHub auto-generates source archives)
- [ ] T099 [US6] Add note in release instructions: source users should git pull or re-download ZIP for updates (no auto-update)

**Checkpoint**: Source distribution documented and tested - Linux/macOS users have clear path

---

## Phase 11: Polish & Cross-Cutting Concerns

**Purpose**: Final touches, testing, documentation

- [ ] T100 [P] Create README.txt for inclusion in Windows ZIP with quick start instructions (double-click app.exe, open browser to URL)
- [ ] T101 [P] Add application metadata to app.spec: version, company name, copyright, description for Windows file properties
- [ ] T102 [P] Update main README.md with "Download" section linking to latest GitHub release
- [ ] T103 [P] Create tests/unit/build/test_build_config.py to validate build configuration YAML schema
- [ ] T104 [P] Create tests/unit/data/test_update_manager.py to test version comparison logic and update state machine
- [ ] T105 [P] Create tests/unit/data/test_installation_context.py to test path resolution for frozen vs source modes
- [X] T106 [P] Create tests/integration/test_executable_launch.py to test executable launches without errors (smoke test)
- [ ] T107 Test executable on clean Windows 10 VM: verify launches, browser opens, database created, settings persist
- [ ] T108 Test executable on clean Windows 11 VM: verify all functionality works
- [ ] T109 Test antivirus scan: run Windows Defender scan on unsigned executable, document any warnings
- [ ] T110 [P] Update docs/ with packaging documentation: how to build, how to release, troubleshooting guide
- [ ] T111 [P] Add CHANGELOG.md entry for feature: "Standalone Windows executable packaging with auto-update"
- [ ] T112 Verify executable size <100MB: if over, investigate large dependencies or enable UPX compression in app.spec
- [X] T113 Performance benchmark: measure launch time, browser open time, update check time against requirements (See spec.md Performance Benchmarks section - all requirements met)
- [ ] T114 Create quickstart video or GIF: download → double-click → app opens (for release page)

---

## Dependency Graph (User Story Completion Order)

```
Setup (Phase 1) → Foundational (Phase 2)
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
    US3 (Build)     US1 (Run)      US5 (Persistence)
    [P1 - MVP]      [P1 - MVP]     [P2]
        ↓               ↓               ↓
        └───────────────┼───────────────┘
                        ↓
                    US4 (Updates) ← requires US3 executable + US1 runtime
                    [P2]
                        ↓
        ┌───────────────┼───────────────┐
        ↓               ↓               ↓
    US8 (Licenses)  US7 (Logging)  US2 (CI/CD)
    [P3]            [P3]            [P1 - MVP]
        ↓               ↓               ↓
        └───────────────┼───────────────┘
                        ↓
                    US6 (Cross-Platform)
                    [P3]
                        ↓
                    Polish (Phase 11)
```

**Critical Path for MVP**: Setup → Foundational → US3 (Build) → US1 (Run) → US2 (CI/CD)

---

## Parallel Execution Examples

### After Foundational Phase Complete:

**Parallel Track 1** (US3 Build):
- T013-T022 can run in parallel (different files)

**Parallel Track 2** (US1 Run):
- T023-T026 can run in parallel (app.py, browser launch, terminal config)

**Parallel Track 3** (US5 Persistence):
- T036-T037 can run in parallel (InstallationContext updates)

### After US3 + US1 Complete:

**Parallel Track 1** (US4 Updates):
- T042-T046, T052-T054 can run in parallel (update manager + updater code)

**Parallel Track 2** (US8 Licenses):
- T060-T063 can run in parallel (license files + About dialog UI)

**Parallel Track 3** (US7 Logging):
- T072-T075 can run in parallel (logging configuration)

---

## Implementation Strategy

**MVP Scope** (Deliver First):
1. Setup + Foundational (T001-T012)
2. US3: Automated Build (T013-T022)
3. US1: Download and Run (T023-T035)
4. US2: GitHub Release Automation (T079-T093)

**MVP Delivers**: Working Windows executable users can download from GitHub releases, double-click to run, with automated build/release process

**Post-MVP** (Deliver Incrementally):
1. US5: Portable installation (T036-T041)
2. US4: Auto-update mechanism (T042-T059)
3. US8: License display (T060-T071)
4. US7: Error logging (T072-T078)
5. US6: Cross-platform docs (T094-T099)
6. Polish & Testing (T100-T114)

---

## Task Summary

- **Total Tasks**: 114
- **Setup Phase**: 5 tasks
- **Foundational Phase**: 7 tasks (BLOCKING)
- **US3 (Build - P1)**: 10 tasks
- **US1 (Run - P1)**: 13 tasks
- **US5 (Persistence - P2)**: 6 tasks
- **US4 (Updates - P2)**: 18 tasks
- **US8 (Licenses - P3)**: 12 tasks
- **US7 (Logging - P3)**: 7 tasks
- **US2 (CI/CD - P1)**: 15 tasks
- **US6 (Cross-Platform - P3)**: 6 tasks
- **Polish**: 15 tasks

**Parallelizable Tasks**: 52 tasks marked with [P]

**Independent Test Criteria**:
- Each user story has clear acceptance criteria
- Test tasks verify functionality without dependencies on other stories
- Integration tests ensure end-to-end workflows work

---

**Status**: ✅ Complete - All tasks defined with IDs, story labels, file paths, and priorities. Ready for import into Beads.
