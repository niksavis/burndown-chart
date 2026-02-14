# Changelog

## v2.12.1

*Released: 2026-02-14*

### Features

- **Chart Date Standardization**: All charts now use consistent ISO week format (2026-W07) for better readability and international compatibility
- **Offline Report Support**: HTML reports now work completely offline with local copies of Font Awesome, Bootstrap, Chart.js, and other assets for easy sharing without internet access

### Improvements

- Chart labels consistently rotate 45° to the right across all visualizations for uniform appearance
- Bug Analysis chart legends positioned properly to prevent overlap with axis labels on mobile devices
- Vendor dependency version tracking with automated download script for reproducible builds
- Browser tab title and favicon load without flicker for smoother user experience
- Toast notification headers include Font Awesome icons for better visual feedback
- CodeMirror JQL editor works offline with local mode definitions
- Normalized header spacing and input heights across all UI panels

### Bug Fixes

- Font Awesome 6.7.2 eliminates glyph bounding box console warnings
- Test suite now validates PERT forecast traces correctly (all 65 visualization tests passing)

## v2.12.0

*Released: 2026-02-12*

### Features

- **EWMA Forecast**: New EWMA (Exponentially Weighted Moving Average) forecasting model provides weighted trend analysis with future markers for more accurate projections
- **Import/Export Enhancements**: Import and export operations now include changelog data for better profile portability and data integrity
- **Profile Conflict Resolution**: Multiple export modes provide flexible conflict resolution options during profile management

### Improvements

- Unified recommendation signals across the dashboard for more consistent insights

### Bug Fixes

- Scope tracking now aligns with report naming conventions for accuracy
- Baseline calculations corrected to prevent negative values in burndown charts
- Metrics refresh properly updates delta changelog

### Documentation

- Clarified scope change rate formula in health metrics documentation

## v2.11.0

*Released: 2026-02-10*

### Features

- **Progressive Current Week Blending**: Metrics now use intelligent blending to eliminate Monday reliability drops. Flow Velocity and DORA metrics smoothly transition from forecast (Monday) to actual values (Friday) throughout the week, providing stable and trustworthy metrics every day. UI shows transparent breakdown with blend ratios.
- **Expanded Report Insights**: HTML reports now include 24+ actionable recommendations across velocity trends, WIP management, quality signals, and deployment maturity
- **Mobile Overflow Menu**: Bottom navigation now includes overflow menu for better touch-friendly navigation and responsive design
- **Panel Collapse Controls**: Expanded settings panels now have collapse buttons for easier navigation

### Improvements

- Dashboard cards enriched with weekly breakdowns and business-friendly labels
- Adjusted trend lines in charts show blended values for better current week visualization
- Decimal formatting improved for items and points cards with preserved precision
- Burndown chart date labels now display in chronological order in reports
- Timestamp fetch optimized for faster dropdown performance

### Documentation

- Progressive blending algorithm documented across Flow Metrics, DORA Metrics, Metrics Index, and Correlation Guide
- Added Current Week Calculations section explaining blending impact on validation rules

## v2.10.0

*Released: 2026-02-09*

### Features

- **Sprint Tracker Sorting**: Sprint progress bars now sort issues by health priority (blocked → aging → active → todo → completed) with completed issues ordered by completion time, showing recently completed items first
- **Active Work Completed Items**: Active Work timeline displays completed epics and issues grouped by week with completion counts and progress metrics
- **Epic Grouping**: Active Work timeline groups issues under their parent epics with improved visual hierarchy and standalone epic support

### Improvements

- Sprint Scope Changes legend uses click-to-show tooltips for better usability
- Completed items UI enhanced with status icons and week-based organization
- Epic counts and issue counts shown for each completed week

### Documentation

- Aligned agent guidance with Beads v0.49.6 workflow
- Removed spec-kit tooling and reorganized documentation

## v2.9.3

*Released: 2026-02-07*

### Improvements

- Cards, insights, and accents use more consistent typography and tones for easier scanning
- Tooltips and chart layouts are steadier to reduce visual jitter while browsing metrics

### Bug Fixes

- Metrics filtering now stays aligned so detail views match your selected filters
- Detail charts load on demand without jumping heights during render
- Auto-update verifies package integrity and refreshes required support files

## v2.9.2

*Released: 2026-02-06*

### Improvements

- **Update Packaging Migration**: Releases now publish separate legacy and new Windows ZIPs, the app auto-selects the correct asset, and legacy executables are removed after a successful update

## v2.9.1

*Released: 2026-02-05*

### Features

- **Active Work Epic Ordering**: Active Work timeline uses hybrid epic ordering so related epics stay grouped in a consistent sequence
- **Burndown Rebrand**: Application branding now reflects the Burndown name across the experience

### Improvements

- Active Work points badge color updated for clearer contrast

### Bug Fixes

- Active Work timeline no longer counts pre-start idle time in duration tracking

### Documentation

- Added SQLite query guidance to repository rules

## v2.9.0

*Released: 2026-02-05*

### Features

- **Active Work Timeline**: New Active Work tab visualizes parent and epic progress over time with status health indicators, badges, and a dedicated timeline view
- **Configurable Parent Tracking**: Choose the parent link field and parent issue types so rollups match your JIRA hierarchy
- **Weekly Progress Help Refresh**: Improved help layout with clearer guidance for weekly progress

### Improvements

- Tab labels are more stable and accessible, with reordered tabs for a clearer navigation flow
- Active Work legend, headers, and icon styling are aligned for a more consistent timeline view

### Bug Fixes

- Update notification toast can be dismissed without breaking update flow
- Weekly Progress help modal reliably opens again after recent changes
- Parent summaries now resolve correctly by querying all issues and using the right project settings
- Scope calculations exclude parent-only issue types and honor development projects configuration
- Active Work timeline no longer registers stale callbacks and avoids UI syntax errors

### Documentation

- Architecture and help documentation reorganized for easier reference

## v2.8.0

*Released: 2026-02-03*

### Features

- **Sprint Tracker Tab**: New dedicated tab showing sprint progress with comprehensive visualizations including timeline view of issue status changes throughout the sprint, progress bars with scope change indicators (added/removed issues), and sprint dropdown with [Active]/[Closed]/[Future] status grouping
- **Sprint Burnup Chart**: Dual y-axis chart tracking both issue count and story points over time with daily snapshots of sprint progress
- **Clickable JIRA Links**: Issue keys in Sprint Tracker progress bars now link directly to JIRA, opening issues in your browser when JIRA connection is verified - makes it easy to jump from chart to detailed issue information
- **Sprint Field Auto-Detection**: Automatically detects sprint field in JIRA configuration with visual confirmation in Field Mapping modal, eliminating manual sprint field configuration
- **Required Pace Enhancements**: Added progress bar visualization showing pace vs required pace, moved to Delivery Forecast row for better visibility, displays uncapped percentages when forecast exceeds deadline to show true progress magnitude, and integrated into Actionable Insights panel with specific pace recommendations

### Improvements

- Sprint charts positioned after Weekly Data tab for logical data flow
- Required velocity reference lines added to weekly velocity charts for at-a-glance pace assessment
- Improved loading states with retry mechanism for Update Data button (prevents console warnings during app startup)
- Enhanced update state handling to invalidate stale pending updates on version mismatch

### Bug Fixes

- Fixed metrics recalculation when field mappings change - DORA/Flow metrics now properly refresh when field configuration updates
- Restored changelog persistence for Flow/DORA metrics - historical data now correctly maintained across sessions
- Fixed card hover effects pattern to prevent unintended interactions on Actionable Insights panel

### Technical Improvements

- Comprehensive code refactoring split large monolithic files (3000+ lines) into focused, maintainable modules following new architectural guidelines
- Added architecture documentation with file size limits and coding standards for Python, JavaScript, HTML, CSS, and SQL
- CSS modularization: split 6700-line stylesheet into 57 focused component files for better maintainability

## v2.7.20

*Released: 2026-01-29*

### Features

- **Unified Field Mapping**: Relocated Estimate field from JIRA Configuration modal to Field Mapping modal under General Options, consolidating all field mappings in one location for easier configuration

### Improvements

- **Codebase Maintenance**: Removed deprecated JSON file caching code and cleaned up test file structure for improved maintainability

## v2.7.19

*Released: 2026-01-29*

### Features

- **Query Timestamps**: Query dropdown now shows when each query was last updated (e.g., "Just now", "2 hours ago") making it easy to see data freshness at a glance
- **Improved Loading Indicators**: Replaced static violet folder icon with animated spinner during long-running operations for better visual feedback

### Bug Fixes

- **Query Selection Workflow**: Update Data now automatically switches to dropdown-selected query even when Load Query Data button hasn't been clicked, preventing data from saving to wrong query and ensuring correct query data loads automatically
- **Footer Visual Fix**: Fixed gradient background tiling issue in application footer
- **Date Picker UX**: Unified date picker implementation across all date fields and resolved focus/interaction issues
- **Auto-Update Reliability**: App now forces page reload after update completion to prevent race conditions and ensure all components reinitialize properly

## v2.7.18

*Released: 2026-01-27*

### Bug Fixes

- **Health Score Consistency**: Fixed 1-6% discrepancy between app and report health scores - both now use last statistics date (most recent Monday) instead of current datetime for schedule calculations, ensuring identical results and stable scores between data updates
- **Delivery Dimension Accuracy**: Fixed report showing incorrect velocity trend (stable 0% instead of declining -60%) due to hardcoded placeholder value - now correctly passes recent_velocity_change from dashboard calculations to all three health score computations

### Documentation

- **Health Formula Transparency**: Clarified that schedule adherence calculations use last statistics date as reference point, explaining why health scores remain stable throughout the day and only change when new weekly data arrives

## v2.7.17

*Released: 2026-01-27*

### Features

- **Visual Loading Feedback**: Added purple fade indicator in sticky banner folder icon when switching queries or adjusting data sliders, providing immediate visual feedback during data recalculation - complements existing orange spinner for background Update Data operations

### Improvements

- **Toast Notifications**: Enhanced toast styling with optimized width (400px) to prevent header wrapping and improve readability across all notification types

### Bug Fixes

- **Health Metric Calculation**: Corrected inverted schedule buffer calculation that was showing buffer as concern instead of advantage - now properly reflects project health when ahead of schedule

## v2.7.16

*Released: 2026-01-26*

### Bug Fixes

- **Update Available Notification**: Fixed notification not appearing when new version is ready to download - restores the toast that alerts you when updates are available

## v2.7.15

*Released: 2026-01-26*

### Bug Fixes

- **Update Success Toast**: Fixed visual appearance to match other toast notifications - was using wrong header styling and class order causing transparency and color differences from normal Dash Bootstrap toasts

## v2.7.14

*Released: 2026-01-26*

### Bug Fixes

- **Update Success Toast**: Fixed JavaScript error preventing toast from displaying - variable declaration was missing line break, putting second let statement inside a comment causing ReferenceError when trying to show success message

## v2.7.13

*Released: 2026-01-26*

### Bug Fixes

- **Update Success Toast**: Fixed success toast not appearing after update - app was clearing the database flag during startup before browser could read it, now uses two separate flags with distinct lifecycles (one for preventing duplicate browser tabs cleared at startup, one for showing success message cleared after JavaScript displays toast)
- **Release Process**: Fixed git tag pointing to intermediate commit instead of final release state - tag now created after ALL commits (version, changelog, version_info, metrics) complete

## v2.7.12

*Released: 2026-01-26*

### Bug Fixes

- **Update Success Toast**: Fixed success toast not appearing after update - app was clearing the database flag during startup before browser could read it, now uses two separate flags with distinct lifecycles (one for preventing duplicate browser tabs cleared at startup, one for showing success message cleared after JavaScript displays toast)

## v2.7.11

*Released: 2026-01-26*

### Bug Fixes

- **Update Success Toast**: Fixed case sensitivity mismatch between updater and app - updater writes "true" but app checked for "True", causing success toast to never appear after updates
- **Release Process**: Fixed orphaned git tags issue where tags pointed to wrong commits, causing GitHub Actions to build outdated code - tag now created after all commits complete
- **Changelog Generation**: Added preview mode to regenerate_changelog.py enabling changelog creation before tagging, preventing need to force-move tags after polishing

## v2.7.10

*Released: 2026-01-26*

### Bug Fixes

- **Update Success Toast**: Fixed critical crash in /api/version endpoint that prevented success toast from showing after update completes - corrected backend API method calls and import paths

## v2.7.9

*Released: 2026-01-26*

### Bug Fixes

- **Update Success Toast**: Fixed "Successfully updated" toast disappearing immediately after update (0.1s flash) - toast now persists on screen after app restarts by checking post-update state from database instead of lost JavaScript memory
- **Unnecessary Page Reload**: Removed automatic page reload after non-update reconnections - Dash handles reconnection automatically, eliminating unnecessary refreshes

## v2.7.8

*Released: 2026-01-26*

### Bug Fixes

- **Toast Notifications**: Eliminated 3 stacked toast messages that briefly appeared after update completes - now shows single success message only

### Other Changes

- **Diagnostics**: Added comprehensive toast creation logging to identify source of any remaining toast issues

## v2.7.7

*Released: 2026-01-26*

### Bug Fixes

- **Toast Notifications**: Fixed flashing toast messages after update completes - now shows single success toast only
- **Export Error Messages**: Fixed white-on-white text formatting in export error toasts, now properly readable

## v2.7.6

*Released: 2026-01-26*

### Bug Fixes

- **Update Overlay Reliability**: Completely resolved update overlay interruptions - clicking Update now shows overlay immediately, stays visible during update process, and displays single success toast when complete (no more duplicate notifications or interrupted overlay)

## v2.7.5

*Released: 2026-01-26*

### Bug Fixes

- **Update Overlay**: Replaced timer-based overlay with disconnect-driven state machine - overlay now waits for actual server shutdown before polling, adapting automatically to slow/fast machines (no more arbitrary timeouts)

## v2.7.4

*Released: 2026-01-26*

### Bug Fixes

- **Update Overlay**: Fixed race condition where reconnecting overlay failed to appear when clicking Update button - overlay now triggers instantly via direct clientside callback instead of store-based mechanism

## v2.7.3

*Released: 2026-01-26*

### Features

- **Update Experience**: Update overlay now appears immediately after clicking Update button, providing instant feedback
- **Version Information**: Footer version info automatically updates after successful app update without requiring browser refresh
- **Update Notifications**: Toast message now displays after update completes without requiring app restart or browser refresh

### Bug Fixes

- **Points Calculation**: Fixed issue where story points were occasionally not calculated during Update Data operation

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
