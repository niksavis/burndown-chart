# Changelog

## v2.7.2

*Released: 2026-01-26*

### Bug Fixes

- **Auto-Update Reliability**: Fixed updater crash on admin accounts when antivirus software locks files during download - now implements graceful retry logic with proper error handling for file access violations

### Other Changes

- **Developer Experience**: Enhanced AI agent documentation with visual checkpoint barriers to enforce virtual environment activation, preventing command execution failures

## v2.7.1

*Released: 2026-01-26*

### Bug Fixes

- **DORA Metrics**: Fixed badge colors to use performance tier colors (elite/high/medium/low) instead of gray, improving visual clarity and alignment with industry standards
- **Logging**: Reduced error log noise on first-time startup by handling missing statistics file gracefully

### Other Changes

- **Developer Experience**: Added /speckit.beads slash command for automated tasks-to-beads conversion workflow, regenerated Speckit configuration files
- **Documentation**: Updated codebase metrics in agents.md, improved markdown highlighting by removing chatagent wrapper

## v2.7.0

*Released: 2026-01-26*

### Features

- **Consolidated Burndown Charts**: Unified Items and Points charts into single Burndown tab with improved layout, removed redundant standalone tabs for cleaner navigation
- **Statistics Data Tab**: Relocated statistics table to dedicated tab with enhanced editing capabilities, add-row functionality, and user warnings for better data management
- **Executive Report Redesign**: Phase 1 design overhaul with semantic color system for all metrics, improved Health Overview table with seamless visualization, distinct colors for created/closed items in charts
- **Enhanced Sticky Panel**: Active button states with visual hierarchy, swapped settings/parameters button positions, improved panel visibility and form controls
- **Refined UI Design System**: Standardized plotly toolbar across charts, improved tab titles and layout consistency, enhanced button visibility and aesthetics, consistent section title spacing
- **Mobile Experience**: Backdrop appears immediately when panel opens, improved touch-friendly interactions

### Bug Fixes

- **Import/Export Reliability**: Fixed settings preservation on import/profile switch, corrected budget calculation after import, proper metrics and issues export for health score consistency
- **Health Score Accuracy**: Black pill badges always shown on progress bars, correct baseline calculation and metric naming
- **Flow Metrics**: Added None check for fix_versions iteration to prevent crashes
- **Profile Management**: Handle empty state when last profile is deleted, reload data after profile deletion/switch
- **Statistics Table**: Prevented save loop that restored manual edits after Update Data, resolved duplicate ID errors
- **Chart Rendering**: Increased legend spacing to prevent toolbar overlap, fixed Net Scope Change legend positioning
- **Toast Notifications**: Improved positioning flush with page top, refined width for better readability

### Other Changes

- **Build Optimization**: Excluded ML/AI libraries from PyInstaller bundle for smaller executable size
- **Code Quality**: Removed statistics table relocation artifacts, cleaned up callback references

## v2.6.5

*Released: 2026-01-22*

### Bug Fixes

- **Flow Metrics Cache Consistency**: Fixed Flow and DORA metrics displaying stale data after changing status mappings or other field configurations - metrics now update immediately when Save Mappings clicked, showing "No Metrics" state until recalculation. Ensures cache cleared consistently across all operations: Save Mappings, Force Refresh, and Update Data

## v2.6.4

*Released: 2026-01-19*

### Bug Fixes

- **Silent Update Failures**: Fixed updates failing silently when stale temp directories from previous failed attempts blocked new extractions - now uses unique extraction directories with automatic cleanup, updater output logged to %TEMP%\burndown_chart_updater.log for debugging, consistent burndown_chart_* namespace prevents collisions with other applications

## v2.6.3

*Released: 2026-01-19*

### Bug Fixes

- **Report Generation**: Fixed "Generate Report" button not working in packaged executable - report_assets directory now properly bundled, template and asset paths correctly resolved for frozen executables, added user-friendly toast notification when no profile/data exists
- **System Tray Icon**: Fixed missing system tray icon in packaged executable by explicitly declaring pystray and PIL dependencies in PyInstaller configuration

## v2.6.2

*Released: 2026-01-18*

### Bug Fixes

- **Self-Updating Updater**: Fixed updater not updating itself - both application and updater now update automatically, ensuring you always have the latest version without manual intervention. Download state persists across app restarts with graceful fallback if temp files deleted

## v2.6.1

*Released: 2026-01-17*

### Bug Fixes

- Fixed Settings Panel parameters not being restored on import (total_items, estimated_items, total_points, estimated_points now properly imported from project_scope)

## v2.6.0

*Released: 2026-01-17*

### Features

- **System Tray Integration**: Application now runs silently in the background with system tray icon, includes Open and Quit menu options, no terminal window, automatic browser launch when ready, proper process termination when quitting
- **Seamless Update Experience**: Auto-reconnect overlay appears during updates to keep users informed, successful update notifications confirm completion, browser reconnects automatically after updates without manual refresh, updater sets database flag to prevent duplicate browser tabs
- **Developer Workflow Improvements**: Incremental changelog generation with JSON export option for LLM-assisted polishing, comprehensive release documentation, improved testing infrastructure with integration tests for executable launch and update workflows

### Bug Fixes

- Fixed temp directory creation in updater and tests to use system temp with static folder names (prevents temp folder bloat)
- Fixed test environment variable handling to preserve system variables like TEMP (resolves Windows popup errors)
- Fixed sqlite3 module missing from updater executable (added to hiddenimports)
- Fixed About dialog changelog rendering to support flat bullet format only (removed sub-bullet indentation)
- Fixed CI-generated release notes to remove redundant headers
- Fixed tray icon path for frozen executable to use correct resource location

## v2.5.4

*Released: 2026-01-14*

### Features

- **Standalone Windows Executable**: No Python installation required - single executable file (~106MB) with all dependencies included, portable installation with settings stored alongside executable, automatic browser launch
- **Automatic Updates**: Application checks for new versions and can update itself with one-click download and installation, seamless update process with automatic restart
- **About Dialog**: View application information, changelog, and licenses with search functionality for third-party software licenses

### Bug Fixes

- Improved update notifications to be less intrusive
- Fixed version comparison for pre-release versions
- Various stability improvements

## v2.5.0

*Released: 2026-01-13*

### Features

- **Budget Tracking**: Complete budget management system with query-level settings, cost breakdown by flow type, weekly trends, and baseline velocity tracking. Includes Budget Tab in settings with revision history and comprehensive metrics guide.
- **AI Prompt Generator**: Export privacy-safe project summaries for ChatGPT/Claude analysis with flexible formatting and improved styling
- **Enhanced Dashboard**: Improved project health card with better styling, recent completions view (4-week), deadline risk analysis with PERT forecasting insights
- **Points Tracking**: Enhanced visibility logic with data validation for filtered periods, improved error handling and user messaging
- **Database Migration**: Migrated to SQLite backend for better performance and data persistence (legacy JSON files cleaned up automatically)

### Bug Fixes

- Fixed date handling consistency in deadline calculations and metric displays
- Resolved SQLite test isolation issues and data points slider clamping
- Fixed budget section styling and data display for unavailable metrics
- Improved health score calculation accuracy with optimized polling intervals
- Corrected database queries for remaining work calculations (migrated from legacy cache)
- Fixed date format normalization to prevent duplicate entries

### Other Changes

- Enhanced DORA and Flow metrics with improved error state handling
- Improved JIRA issue filtering for dashboard consistency  
- Better logging and statistics tracking throughout the application

## v2.4.4

*Released: 2025-12-29*

### Features

- Added baseline tracking for trend indicators to better visualize metric changes over time

## v2.4.3

*Released: 2025-12-29*

### Bug Fixes

- Fixed zero-activity week handling in charts and PERT calculations - now correctly shows weeks with no progress instead of skipping them

## v2.4.2

*Released: 2025-12-29*

### Bug Fixes

- Resolved type errors and improved logging consistency

## v2.4.1

*Released: 2025-12-22*

### Features

- Minor stability improvements and performance optimizations

## v2.4.0

*Released: 2025-12-22*

### Features

- **Improved Health Score**: Implemented smooth statistical formula with detailed explanations in executive summary
- **Enhanced Documentation**: Comprehensive installation and JIRA integration guide in README
- **Version Management**: Automated version bumping process with git tag enforcement

## v2.3.0

*Released: 2025-12-19*

### Features

- **Enhanced Import/Export**: Profile conflict resolution with multiple export modes (Config Only, Full Data with all queries)
- **Improved User Experience**: User-friendly filenames and comprehensive backup options

## v2.2.2

*Released: 2025-12-19*

### Features

- **Auto-Update System**: Automatic version checking with in-app notifications for new releases
- **Improved Data Refresh**: Statistics reload automatically after JIRA data updates complete

### Bug Fixes

- Fixed UI refresh to reflect updated statistics immediately after data sync

## v2.2.1

*Released: 2025-12-18*

### Features

- **HTML Reports**: Standalone offline reports with all charts and metrics for easy sharing
- **DORA & Flow Metrics**: Industry-standard DevOps and team efficiency tracking dashboards
- **Multi-Project Support**: Profile management with workspace isolation and duplication
- **Mobile Experience**: Touch-friendly navigation with drawer menu and responsive design
- **JQL Editor**: Syntax highlighting with real-time validation (CodeMirror integration)
- **AI Export**: Privacy-safe project summaries for ChatGPT/Claude analysis

### Bug Fixes

- Fixed metrics calculations and data isolation issues
- Improved chart rendering, tab switching, and report generation stability
- Fixed deadline marker display and forecast visualization accuracy
- Improved mobile layout responsiveness and date picker alignment
- Fixed statistics table editing and data persistence
