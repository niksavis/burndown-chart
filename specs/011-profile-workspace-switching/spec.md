# Feature Specification: Profile & Query Management System

**Feature Branch**: `011-profile-workspace-switching`  
**Created**: 2025-11-13  
**Status**: Draft  
**Input**: User description: "Multiple profiles feature that allows switching between profiles without having to get new data regardless if from JIRA or from CSV/JSON import"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Switch Between Queries Within Profile (Priority: P1)

As a project manager, I want to instantly switch between different time periods (last 12 weeks vs last 52 weeks) using the same forecast settings (PERT factor and deadline), so I can compare velocity trends without waiting 3-6 minutes for data to reload.

**Why this priority**: This is the core value proposition - eliminating 3-6 minute cache invalidation delays when users compare different data views. This is the most painful user experience issue currently blocking interactive analysis.

**Independent Test**: Can be fully tested by creating a profile with PERT factor 1.5 and deadline 2025-12-31, adding two queries with different JQL time periods, switching between them, and verifying that switching takes <50ms and both queries show same PERT/deadline in their forecasts.

**Acceptance Scenarios**:

1. **Given** a profile "Apache Kafka Analysis" with PERT factor 1.5 and deadline 2025-12-31 containing two queries ("Last 12 Weeks" and "Last 52 Weeks"), **When** user switches from "Last 12 Weeks" to "Last 52 Weeks", **Then** the dashboard reloads in <50ms showing cached data from the 52-week query with the same PERT factor (1.5) and deadline (2025-12-31) used in forecast calculations.

2. **Given** user is viewing "Last 52 Weeks" query with cached data, **When** user switches back to "Last 12 Weeks" query, **Then** the cached data from "Last 12 Weeks" is instantly loaded (<50ms) without triggering JIRA API calls or metric recalculation.

3. **Given** user switches between three different queries within same profile, **When** comparing the forecast charts, **Then** all queries show forecasts calculated with identical PERT factor and deadline settings, ensuring apples-to-apples comparison.

---

### User Story 2 - Create New Query in Profile (Priority: P1)

As a team lead, I want to create multiple JQL query variations within my profile (e.g., "Bugs Only", "High Priority", "Q4 Sprint"), so I can analyze different data slices without reconfiguring JIRA settings or field mappings each time.

**Why this priority**: This enables the core use case - analyzing multiple query variations with consistent settings. Without this, users can't benefit from the profile-level configuration reuse.

**Independent Test**: Can be fully tested by creating a profile, adding a new query with custom JQL string, verifying that the query inherits all profile settings (PERT factor, deadline, field mappings), and that the query has dedicated cache storage isolated from other queries.

**Acceptance Scenarios**:

1. **Given** a profile "Infrastructure Team" with configured JIRA connection and field mappings, **When** user creates a new query "Tech Debt Analysis" with JQL `type = "Technical Debt" AND created >= -12w`, **Then** the query is created with dedicated cache directory and inherits all profile settings without requiring user to re-enter JIRA credentials or field mappings.

2. **Given** user has created query "All Issues", **When** user creates second query "Bugs Only" with different JQL filter, **Then** both queries have isolated cache files and switching between them does not invalidate the other query's cache.

3. **Given** profile has PERT factor 1.5 and deadline 2025-12-31, **When** user creates 5 different queries with various JQL filters, **Then** all 5 queries automatically use the profile's PERT factor and deadline for forecast calculations without requiring per-query configuration.

---

### User Story 3 - Switch Between Profiles (Priority: P2)

As an analyst working with multiple JIRA instances (e.g., Company Production and Apache Open Source), I want to switch between profiles representing different organizations, so I can analyze different teams/projects with their appropriate settings (different PERT factors, JIRA credentials, field mappings).

**Why this priority**: This enables multi-tenancy use cases where users need to analyze different JIRA instances or teams with fundamentally different configurations. Less critical than P1 because single-profile multi-query workflow covers most users.

**Independent Test**: Can be fully tested by creating two profiles with different JIRA base URLs, PERT factors, and field mappings, switching between them, and verifying that each profile loads its own settings and queries without cross-contamination.

**Acceptance Scenarios**:

1. **Given** profile "Company Production" (JIRA: company.atlassian.net, PERT: 1.8) and profile "Apache Kafka" (JIRA: issues.apache.org, PERT: 1.5), **When** user switches from "Company Production" to "Apache Kafka", **Then** the dashboard reloads in <100ms with Apache Kafka's JIRA connection, field mappings, PERT factor, and the most recently used query from that profile.

2. **Given** user switches from profile A to profile B and back to profile A, **When** loading profile A for the second time, **Then** the cached data from profile A's last active query is instantly loaded without triggering JIRA API calls.

3. **Given** two profiles with different field mapping configurations (customfield_10001 vs customfield_20002 for story points), **When** switching between profiles, **Then** DORA/Flow metrics are calculated using each profile's respective field mappings without mixing configurations.

---

### User Story 4 - Create New Profile from Existing (Priority: P2)

As a user analyzing similar projects, I want to duplicate an existing profile with its JIRA configuration and field mappings, so I can quickly set up a new profile for a different project without re-entering all configuration details.

**Why this priority**: Improves setup efficiency for users managing multiple similar projects. Not as critical as P1/P2 because it's a convenience feature rather than core functionality.

**Independent Test**: Can be fully tested by duplicating a profile, verifying that JIRA config and field mappings are copied, modifying the duplicate's settings, and confirming that changes don't affect the original profile.

**Acceptance Scenarios**:

1. **Given** profile "Apache Kafka Analysis" with configured JIRA connection, field mappings, and PERT factor 1.5, **When** user duplicates the profile and names it "Apache Spark Analysis", **Then** the new profile is created with a copy of all JIRA config and field mappings but with empty query list and new unique profile ID.

2. **Given** user duplicates profile "Team A" to create "Team B", **When** user modifies Team B's PERT factor from 1.5 to 2.0, **Then** Team A's PERT factor remains unchanged at 1.5 (no shared state).

3. **Given** user duplicates profile with 3 queries, **When** choosing to clone queries, **Then** the new profile has copies of all 3 queries with their own isolated cache directories.

---

### User Story 5 - First-Time Migration (Priority: P1)

As an existing user with saved JIRA cache and project data, I want the system to automatically migrate my data to the new profile structure on first run, so I don't lose any existing analysis or cache when upgrading to profile support.

**Why this priority**: Critical for backward compatibility - prevents data loss and ensures smooth upgrade experience for existing users. Must work flawlessly or users will lose trust in the system.

**Independent Test**: Can be fully tested by simulating a pre-profile installation (root-level app_settings.json, jira_cache.json, etc.), starting the app, and verifying that all files are moved to profiles/default/ without data loss or corruption.

**Acceptance Scenarios**:

1. **Given** existing installation with app_settings.json, jira_cache.json, and project_data.json in repository root, **When** user launches app for first time after upgrade, **Then** system creates profiles/default/ directory, moves all root files to profiles/default/, creates profiles.json with default profile as active, and dashboard loads with all existing data intact.

2. **Given** migration has successfully completed, **When** user restarts the app, **Then** system detects profiles.json exists and does not attempt migration again (idempotent operation).

3. **Given** migration fails due to disk error, **When** system detects failure, **Then** original root files are restored from backup (.backup suffix) and user sees error message explaining migration failure and how to retry.

---

### Edge Cases

- **What happens when switching to a profile with no queries?** System displays message "This profile has no queries. Create your first query to get started." and shows "Create Query" button.

- **What happens when user tries to delete the only remaining profile?** System prevents deletion and shows error: "Cannot delete the only profile. Create another profile first."

- **What happens when user tries to delete the currently active profile?** System prevents deletion and shows error: "Cannot delete active profile. Switch to another profile first."

- **What happens when user tries to delete the last remaining query in a profile?** System prevents deletion and shows error: "Cannot delete the only query. Profiles must have at least one query."

- **What happens when a profile's workspace directory is manually deleted or corrupted?** System detects missing directory on startup, shows warning "Profile X workspace is missing or corrupted. Switching to default profile.", and auto-switches to default profile.

- **What happens when two queries have identical JQL strings?** System allows this (queries are identified by unique IDs, not JQL strings). User may want to compare same data with different data_points_count or at different time snapshots.

- **What happens when user creates more than 50 profiles?** System prevents creation and shows error: "Maximum 50 profiles reached. Delete unused profiles to create new ones."

- **What happens when user creates more than 100 queries in a profile?** System prevents creation and shows error: "Maximum 100 queries per profile. Delete unused queries to create new ones."

- **How does system handle disk space exhaustion?** System checks available disk space before creating profile/query. If <100MB available, shows warning: "Low disk space. Profile creation may fail."

- **What happens when user switches profiles while JIRA data is loading?** System cancels the in-progress JIRA fetch operation, switches profiles, and starts fresh fetch for the new profile's active query.

## UI Design Decisions *(approved 2025-11-13)*

### Visual Design Choices

#### Profile & Query Selector Layout
- **Visual Hierarchy**: Equal visual weight for profile and query selectors (Option 1A)
  - Both use same dropdown size and button styling
  - Clear separation with labels ("Profile" vs "Query")
- **Layout Pattern**: Side-by-side on desktop (8-col dropdown + 4-col buttons), responsive stack on mobile <768px (Option 4A+B)
  - Desktop: `[Profile Dropdown (8 cols)] [Buttons (4 cols)]`
  - Mobile: Full-width dropdown, buttons below
- **Profile Metadata**: Tooltip on profile name showing JIRA URL, PERT factor, query count (Option 2A)
  - Hover/tap profile name → tooltip with details
  - Upgrade to inline display in Phase 8 polish
- **Loading States**: Reuse existing skeleton screen from `ui/empty_states.py` (Option 3A)
  - Shows placeholder cards during profile/query switch
  - Consistent with existing app loading patterns
- **Modal Style**: Centered Bootstrap modals with dimmed background (Option 5A)
  - Matches existing JIRA config modal style
  - Consistent user experience
- **Empty State**: Inline message with CTA button when profile has no queries (Option 6A)
  - Shows in query selector area: "🔍 No queries in this profile yet. [Create Your First Query →]"
  - Reuses existing empty state patterns
- **Name Validation**: Real-time validation in modal forms (Option 7A)
  - Live feedback as user types: "✓ Name available" or "✗ Name already exists"
  - Prevents form submission errors
- **Mobile Navigation**: Vertical stack using Bootstrap responsive classes (Option 8A)
  - Profile selector full-width, query selector below, buttons stack
  - Leverages existing responsive patterns

### Component Structure

```
Settings Panel (Collapsible)
├── JIRA Integration Header (unchanged)
├── Profile Selector (NEW)
│   ├── Label: "Profile"
│   ├── Dropdown: Shows all profiles with tooltip on hover
│   └── Button Group: [Create] [Duplicate] [Delete]
├── Query Selector (REPLACES "Saved Queries")
│   ├── Label: "Query"
│   ├── Dropdown: Shows queries in active profile
│   └── Button Group: [Create] [Duplicate] [Delete]
├── JQL Query Editor (unchanged - populated from selected query)
└── Action Buttons (unchanged)
```

### Responsive Behavior

**Desktop (≥768px)**:
- Profile: `[Dropdown (8 cols)] [Buttons (4 cols)]`
- Query: `[Dropdown (8 cols)] [Buttons (4 cols)]`

**Mobile (<768px)**:
- Profile: `[Dropdown (12 cols)]`
           `[Buttons (12 cols, centered)]`
- Query: `[Dropdown (12 cols)]`
         `[Buttons (12 cols, centered)]`

## Requirements *(mandatory)*

### Functional Requirements

#### Profile Management

- **FR-001**: System MUST allow users to create new profiles with unique names (1-100 characters)
- **FR-002**: System MUST allow users to switch between profiles in <100ms by updating the active profile pointer
- **FR-003**: System MUST allow users to delete profiles (except active profile and when only one profile exists)
- **FR-004**: System MUST allow users to duplicate existing profiles, copying JIRA configuration and field mappings but creating new unique profile ID
- **FR-005**: System MUST prevent creating more than 50 profiles per installation
- **FR-006**: System MUST store profile-level settings (PERT factor, deadline, data_points_count, JIRA connection, field mappings) that are shared by all queries within the profile

#### Query Management

- **FR-007**: System MUST allow users to create new queries within a profile by providing JQL string and query name (1-100 characters)
- **FR-008**: System MUST allow users to switch between queries within a profile in <50ms by updating the active query pointer
- **FR-009**: System MUST allow users to delete queries (except active query and when only one query exists in profile)
- **FR-010**: System MUST allow users to duplicate existing queries within same profile
- **FR-011**: System MUST prevent creating more than 100 queries per profile
- **FR-012**: System MUST create dedicated cache directory for each query (jira_cache.json, project_data.json, metrics_snapshots.json, cache/)
- **FR-013**: System MUST inherit profile-level settings (PERT factor, deadline, field mappings) for all queries in the profile

#### Cache Isolation

- **FR-014**: System MUST maintain isolated cache files for each query (no cross-contamination between queries)
- **FR-015**: System MUST preserve cached data when switching between queries (no cache invalidation)
- **FR-016**: System MUST preserve cached data when switching between profiles (no cache invalidation)
- **FR-017**: System MUST load cached data for a query when switching back to it without triggering JIRA API calls

#### Data Points Count vs JQL Time Period

- **FR-018**: System MUST support JQL time period filter in query (e.g., `created >= -52w`) that determines what data to fetch from JIRA
- **FR-019**: System MUST support profile-level `data_points_count` setting (number of recent weeks to analyze/show in charts) that filters fetched data post-fetch
- **FR-020**: System MUST apply `data_points_count` filter consistently across all queries in profile for fair velocity comparison
- **FR-021**: System MUST use same `data_points_count` analysis window for velocity calculations across all queries in profile

#### First-Run Migration

- **FR-022**: System MUST detect if profiles.json exists on startup
- **FR-023**: System MUST automatically migrate existing root-level data files (app_settings.json, jira_cache.json, project_data.json) to profiles/default/ directory on first run if profiles.json doesn't exist
- **FR-024**: System MUST create backup copies of root files (.backup suffix) before migration
- **FR-025**: System MUST restore from backup if migration fails
- **FR-026**: System MUST be idempotent (no re-migration if profiles.json already exists)

#### Profile & Query Persistence

- **FR-027**: System MUST store profiles registry in profiles.json at repository root with active profile ID and active query ID
- **FR-028**: System MUST store profile configuration in profiles/{profile_id}/profile.json with forecast settings, JIRA config, field mappings, and queries list
- **FR-029**: System MUST store query configuration in profiles/{profile_id}/queries/{query_id}/query.json with JQL string and metadata
- **FR-030**: System MUST update last_used timestamp for profiles and queries when accessed
- **FR-031**: System MUST use atomic file writes for profiles.json to prevent corruption

#### UI Integration

- **FR-032**: System MUST display profile selector dropdown in settings panel showing all profiles with equal visual weight to query selector
- **FR-033**: System MUST display query selector dropdown showing all queries in active profile (replaces current "Saved Queries" section)
- **FR-034**: System MUST provide "Create Profile" button that opens centered Bootstrap modal dialog for profile creation
- **FR-035**: System MUST provide "Create Query" button that opens centered Bootstrap modal dialog for query creation
- **FR-036**: System MUST provide "Duplicate Profile" button that clones active profile
- **FR-037**: System MUST provide "Delete Profile" button (disabled when active or only one profile)
- **FR-038**: System MUST provide "Duplicate Query" button that clones active query
- **FR-039**: System MUST provide "Delete Query" button (disabled when active or only one query in profile)
- **FR-040**: System MUST display profile metadata (JIRA URL, PERT factor, query count) in tooltip on profile name hover/tap
- **FR-041**: System MUST use existing skeleton screen loading pattern during profile/query switches
- **FR-042**: System MUST show inline empty state message with "Create Your First Query" CTA when profile has no queries
- **FR-043**: System MUST provide real-time name validation in creation modals showing "✓ Name available" or "✗ Name already exists"
- **FR-044**: System MUST use responsive layout: side-by-side (8-col dropdown + 4-col buttons) on desktop, vertical stack on mobile <768px
- **FR-045**: System MUST position profile selector above query selector in settings panel
- **FR-046**: System MUST populate JQL editor with selected query's JQL string automatically on query switch

#### Validation & Safety

- **FR-047**: System MUST validate profile names are unique (case-insensitive) with real-time feedback in creation modal
- **FR-048**: System MUST validate query names are unique within profile (case-insensitive) with real-time feedback in creation modal
- **FR-049**: System MUST validate JQL syntax before creating query (basic syntax check)
- **FR-050**: System MUST validate PERT factor is between 1.0 and 3.0
- **FR-051**: System MUST show confirmation dialog before deleting profile (requiring user to type profile name)
- **FR-052**: System MUST show confirmation dialog before deleting query (requiring user to type query name)

### Key Entities

- **Profile**: Represents a collection of queries with shared configuration settings
  - Attributes: id (UUID), name, description, created_at, last_used, PERT factor, deadline, data_points_count, JIRA config (base_url, token, api_version, points_field), field mappings (DORA/Flow custom fields), project config (devops_projects, development_projects, issue type mappings), queries list
  - Relationships: Has many queries, belongs to profiles registry

- **Query**: Represents a JQL query variation with dedicated cache
  - Attributes: id (UUID), name, description, JQL query string, created_at, last_used
  - Relationships: Belongs to profile, has dedicated cache directory
  - Inherited from profile: PERT factor, deadline, data_points_count, JIRA config, field mappings

- **Profiles Registry**: Global registry of all profiles and active selections
  - Attributes: version, active_profile_id, active_query_id, profiles list
  - Stored in: profiles.json (repository root)

- **Cache Data**: Cached JIRA data and calculated metrics for a query
  - Files: jira_cache.json (JIRA issues), project_data.json (statistics), metrics_snapshots.json (DORA/Flow metrics), cache/*.json (metric calculation cache)
  - Relationships: Belongs to specific query, isolated from other queries

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can switch between queries within a profile in under 50 milliseconds (measured from query selection to dashboard reload completion)

- **SC-002**: Users can switch between profiles in under 100 milliseconds (measured from profile selection to dashboard reload completion)

- **SC-003**: Users can switch back to previously viewed query without triggering JIRA API calls or metric recalculation (cache hit rate >90%)

- **SC-004**: Users can compare velocity trends across different time periods (e.g., 12 weeks vs 52 weeks) using identical PERT factor and deadline settings within 10 seconds total (including both query switches)

- **SC-005**: Existing users' data is automatically migrated to profiles/default/ on first run with 100% data preservation (no data loss or corruption)

- **SC-006**: System supports at least 50 profiles and 100 queries per profile without performance degradation (profile switch remains <100ms, query switch remains <50ms)

- **SC-007**: Profile creation completes in under 500 milliseconds (measured from "Create Profile" button click to new profile appearing in dropdown)

- **SC-008**: Query creation completes in under 500 milliseconds (measured from "Create Query" button click to new query appearing in dropdown)

- **SC-009**: Users can create 5 different JQL query variations within a profile in under 3 minutes (including time to enter JQL strings and query names)

- **SC-010**: Cache isolation guarantees 100% data integrity (no cross-contamination between queries - verified by comparing cache file contents)

- **SC-011**: System prevents 100% of accidental data loss scenarios (cannot delete active profile/query, cannot delete last profile/query, confirmation dialogs for all destructive actions)

- **SC-012**: Migration from single-workspace to profiles completes in under 5 seconds for typical installation (50MB of cached data)
