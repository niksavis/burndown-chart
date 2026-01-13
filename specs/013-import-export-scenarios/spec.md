# Feature Specification: Enhanced Import/Export Options

**Feature Branch**: `013-import-export-scenarios`  
**Created**: December 18, 2025  
**Completed**: December 19, 2025  
**Status**: ✅ DELIVERED (v2.3.0)  
**Input**: User description: "Allow multiple scenarios for exporting and importing data: (1) import/export profile and query configuration without data, (2) import/export full profile with data of currently selected query, (3) checkbox to export JIRA token or not (default unchecked)"

**See [COMPLETION.md](COMPLETION.md) for detailed delivery report including bonus features and bug fixes.**

## User Scenarios & Testing

### User Story 1 - Share Configuration Without Credentials (Priority: P1)

A user wants to share their JIRA query configuration and profile settings with team members without exposing their API token. They export the configuration with the "Include JIRA Token" checkbox unchecked (default), share the file, and recipients import it to replicate the same setup with their own credentials.

**Why this priority**: Security-first approach prevents accidental credential leakage, which is the most critical risk when sharing configurations.

**Independent Test**: Can be fully tested by exporting a profile with default settings (token excluded), sharing the file, and importing it on another system. Delivers immediate value by enabling secure configuration sharing.

**Acceptance Scenarios**:

1. **Given** user has configured a profile with JIRA credentials, **When** user exports with "Include JIRA Token" unchecked (default), **Then** exported file contains all configuration but JIRA token field is empty or omitted
2. **Given** user receives exported configuration without token, **When** user imports the file, **Then** system prompts for JIRA token entry and preserves all other settings
3. **Given** user exports with token excluded, **When** recipient imports the configuration, **Then** all query definitions, field mappings, and settings are preserved exactly

---

### User Story 2 - Export Configuration Only for Team Standardization (Priority: P2)

A team lead wants to distribute standardized JIRA query configurations to team members without any project data. They export only the configuration (profile settings and query definitions), and team members import it to align on the same queries and metrics tracking approach.

**Why this priority**: Enables team collaboration and standardization without data overhead, commonly needed for onboarding and alignment.

**Independent Test**: Can be tested by exporting configuration-only, confirming file size is minimal (no cached data included), importing on clean system, and verifying queries work when connected to JIRA.

**Acceptance Scenarios**:

1. **Given** user selects "Export Configuration Only" option, **When** export completes, **Then** exported file contains profile settings and query definitions but no cached JIRA data
2. **Given** user imports configuration-only file, **When** import completes, **Then** all query definitions and settings are loaded, but no historical data appears until "Update Data" is triggered
3. **Given** configuration-only export is created, **When** user inspects file size, **Then** file is significantly smaller than full export (no jira_cache.json or project_data.json included)

---

### User Story 3 - Share Complete Snapshot for Offline Review (Priority: P2)

A consultant wants to share complete project status with a client who doesn't have JIRA access. They export the full profile with all data from the currently selected query, and the client imports it to browse charts, metrics, and historical data offline without needing JIRA connectivity.

**Why this priority**: Enables offline analysis and sharing with non-JIRA users, important for reporting and stakeholder communication.

**Independent Test**: Can be tested by exporting full data, importing on disconnected system (no JIRA credentials), and verifying all charts/metrics render correctly without any "Update Data" operation.

**Acceptance Scenarios**:

1. **Given** user has active query with cached data, **When** user selects "Export Full Profile with Data", **Then** exported file includes profile settings, query configuration, and all cached data for selected query
2. **Given** user imports full profile with data, **When** import completes on system without JIRA access, **Then** all charts, metrics, and historical data display correctly without requiring "Update Data"
3. **Given** full export includes data timestamp, **When** user imports it, **Then** UI displays clear indication of when data was last fetched (data age visibility)

---

### User Story 4 - Secure Sharing with Token Inclusion Option (Priority: P3)

A power user managing multiple environments wants to export their complete setup including credentials for personal backup or migration to another workstation. They explicitly check "Include JIRA Token" checkbox to export credentials along with configuration and data.

**Why this priority**: Advanced use case for personal backup/migration, less common than secure sharing scenarios but valuable for power users.

**Independent Test**: Can be tested by exporting with token included, importing on new system, and immediately accessing JIRA without re-entering credentials.

**Acceptance Scenarios**:

1. **Given** user checks "Include JIRA Token" during export, **When** export completes, **Then** exported file contains JIRA token in profile configuration
2. **Given** user imports file with included token, **When** import completes, **Then** system automatically connects to JIRA without prompting for credentials
3. **Given** token is included in export, **When** user examines export UI, **Then** clear warning message indicates security implications of including credentials

---

### Edge Cases

- What happens when user imports configuration-only but profile already exists with same name? (Merge strategy or overwrite prompt)
- How does system handle importing full data when disk space is insufficient?
- What happens when imported configuration references custom JIRA fields that don't exist on recipient's JIRA instance?
- How does system handle version incompatibility (importing newer format into older app version)?
- What happens when user tries to import full data but changes profile before import completes?
- How does system handle corrupted or partial export files during import?
- What happens when imported query JQL is invalid on recipient's JIRA instance?

## Requirements

### Functional Requirements

- **FR-001**: System MUST provide three distinct export modes: "Configuration Only", "Full Profile with Data", and existing export behavior (now labeled appropriately)
- **FR-002**: System MUST display "Include JIRA Token" checkbox on export dialog, defaulting to unchecked
- **FR-003**: System MUST strip JIRA token from exported file when "Include JIRA Token" is unchecked
- **FR-004**: System MUST include JIRA token in exported file when "Include JIRA Token" is checked
- **FR-005**: System MUST display security warning near "Include JIRA Token" checkbox explaining credential exposure risk
- **FR-006**: Configuration-only export MUST include profile settings, query definitions, field mappings, JQL queries, and budget data (if present)
- **FR-007**: Configuration-only export MUST exclude all cached JIRA data (jira_cache.json, project_data.json)
- **FR-008**: Full profile export MUST include profile settings, query configuration, budget data (if present), and cached data for currently selected query only
- **FR-009**: System MUST prompt for JIRA token during import when imported file lacks token
- **FR-010**: System MUST preserve all query definitions, field mappings, and settings exactly during configuration import
- **FR-011**: Import process MUST validate file structure before applying changes
- **FR-012**: System MUST display clear indication of data age/timestamp after importing full profile with data
- **FR-013**: Export dialog MUST clearly label each export mode with brief description of what's included
- **FR-014**: System MUST handle profile name conflicts during import with user-selectable strategy (merge, overwrite, rename)
- **FR-015**: System MUST log all import/export operations with timestamp and mode used for audit trail

### Key Entities

- **Export Package**: Container format for exported data, includes metadata (version, timestamp, mode, token_included flag), profile configuration, query definitions, and optionally cached data
- **Export Mode**: Enumeration of export types (CONFIG_ONLY, FULL_DATA, LEGACY), determines what data is included in package
- **Import Context**: State information during import process, includes source file path, detected mode, conflict resolution strategy, and credential prompting status

## Success Criteria

### Measurable Outcomes

- **SC-001**: Users can export configuration-only package in under 3 seconds regardless of cached data size
- **SC-002**: Configuration-only exports are at least 90% smaller than full data exports when cache contains >100 issues
- **SC-003**: 100% of exports with "Include JIRA Token" unchecked result in files with token stripped from profile configuration
- **SC-004**: Users can successfully import and use configuration-only exports on fresh installation and connect to JIRA with their own credentials within 2 minutes
- **SC-005**: Users importing full profile with data can view all charts and metrics immediately without triggering "Update Data"
- **SC-006**: Export dialog clearly indicates which mode is selected, reducing user errors by 80% compared to single-option export
- **SC-007**: 95% of users understand token inclusion implications from security warning before making export choice
