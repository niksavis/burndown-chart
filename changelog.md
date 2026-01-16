# Changelog

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

