# Feature Specification: JIRA Configuration Separation

**Feature Branch**: `003-jira-config-separation`  
**Created**: October 21, 2025  
**Status**: Draft  
**Input**: User description: "I want to improve the Data Source part of the app by extracting the JIRA API setup in a dedicated setup page or modal dialog which will include the JIRA API Endpoint, but the user must only provide the web address and the app will internally attach the rest, such as /rest/api/2/search or /rest/api/3/search, depending which version it is and user will be able to check the connection. Next would be the personal access token that will also be moved to the dedicated setup page, and settings for cache size limit and max results per API call, and points fiellds too. The only Jira specific thing left in the Data Source would be JQL Query. This should simplify the UI by hiding a setup behind a new jira configuration page that user only needs to do once. In summary, this feature separates the jira api configuration from the jql query editing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Initial JIRA Configuration (Priority: P1)

As a first-time user, I need to configure my JIRA connection settings once so that I can start querying data without repeatedly entering connection details.

**Why this priority**: This is the foundational setup that enables all JIRA integration features. Without this, users cannot connect to JIRA at all.

**Independent Test**: Can be fully tested by opening the configuration interface, entering valid JIRA credentials, testing the connection, and verifying successful connection feedback. Delivers immediate value by establishing JIRA connectivity.

**Acceptance Scenarios**:

1. **Given** I am a new user with no JIRA configuration, **When** I open the app, **Then** I should be prompted to configure JIRA settings before accessing data source features
2. **Given** I am in the JIRA configuration interface, **When** I enter only the base JIRA web address (e.g., "https://mycompany.atlassian.net"), **Then** the system should automatically append the appropriate API path
3. **Given** I have entered my JIRA base URL and personal access token, **When** I click "Test Connection", **Then** I should receive clear feedback indicating whether the connection succeeded or failed with specific error messages
4. **Given** I have successfully tested my connection, **When** I save the configuration, **Then** the settings should be persisted and I should be able to access the JQL query interface
5. **Given** I have saved my configuration, **When** I return to the app later, **Then** my JIRA connection should be remembered and I should not need to re-enter credentials

---

### User Story 2 - Modifying Existing Configuration (Priority: P2)

As an existing user, I need to update my JIRA configuration settings (token, cache limits, API version) when my environment changes, without disrupting my saved JQL queries.

**Why this priority**: Supports ongoing maintenance and changing environments (token expiration, company migration, performance tuning), but assumes initial setup is already complete.

**Independent Test**: Can be tested by accessing the configuration page with existing settings, modifying specific values, saving, and verifying the changes take effect without affecting JQL queries.

**Acceptance Scenarios**:

1. **Given** I have existing JIRA configuration, **When** I access the configuration page, **Then** I should see all my current settings pre-filled
2. **Given** I am viewing my configuration, **When** I update my personal access token and test the connection, **Then** the system should validate the new token without affecting my saved JQL queries
3. **Given** I want to optimize performance, **When** I adjust cache size limits or max results per API call, **Then** the changes should take effect immediately for subsequent queries
4. **Given** I need to change API versions, **When** I switch between API v2 and v3, **Then** the system should automatically update the endpoint path and inform me of any compatibility considerations
5. **Given** I have made configuration changes, **When** I cancel without saving, **Then** the system should revert to my previous settings

---

### User Story 3 - Simplified JQL Query Workflow (Priority: P3)

As a regular user, I want the Data Source interface to focus only on JQL query editing, so that I can quickly create and test queries without being distracted by configuration settings.

**Why this priority**: Improves daily workflow efficiency after initial setup is complete. This is a quality-of-life improvement that depends on P1 and P2 being implemented first.

**Independent Test**: Can be tested by accessing the Data Source page with valid JIRA configuration and verifying only JQL query fields are visible, with a clear link to configuration settings.

**Acceptance Scenarios**:

1. **Given** I have completed JIRA configuration, **When** I navigate to the Data Source interface, **Then** I should see only JQL query fields and related query management features
2. **Given** I am editing a JQL query, **When** I need to verify my connection settings, **Then** I should have easy access to view (but not necessarily edit inline) my current JIRA endpoint
3. **Given** I am working with multiple JQL queries, **When** I switch between them, **Then** the configuration settings should remain consistent and not require re-entry
4. **Given** I encounter a connection error while querying, **When** the error suggests a configuration issue, **Then** I should see a clear link to the configuration page with context about the specific issue

---

### Edge Cases

- What happens when a user enters an invalid JIRA URL format (missing protocol, internal URL, typos)?
- How does the system handle connection test timeouts or network failures?
- What happens when a personal access token expires while the user is actively querying?
- How does the system behave if cache size limit is set to an extremely low value (e.g., 1KB) or extremely high value (e.g., 10GB)?
- What happens when switching from API v2 to v3 with existing cached data that uses v2 endpoints?
- How does the system handle concurrent configuration changes (e.g., user opens config in multiple browser tabs)?
- What happens when a user tries to query data without completing initial configuration?
- How does the system validate and sanitize the "points field" custom field name input?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a dedicated configuration interface (modal dialog or separate page) for JIRA API settings
- **FR-002**: System MUST accept only the base JIRA web address from users (e.g., "https://mycompany.atlassian.net" or "https://jira.example.com")
- **FR-003**: System MUST automatically append the appropriate API endpoint path based on selected API version ("/rest/api/2/search" for v2 or "/rest/api/3/search" for v3)
- **FR-004**: System MUST provide API version selection (v2 or v3) within the configuration interface
- **FR-005**: System MUST include a "Test Connection" feature that validates JIRA endpoint and token before saving configuration
- **FR-006**: System MUST provide clear feedback for connection test results, including specific error messages for common failure scenarios (invalid token, unreachable endpoint, authentication failure)
- **FR-007**: System MUST accept and securely store personal access tokens for JIRA authentication
- **FR-008**: System MUST include configuration options for cache size limit (in MB or records)
- **FR-009**: System MUST include configuration option for maximum results per API call
- **FR-010**: System MUST include configuration field for JIRA custom field name used for story points
- **FR-011**: System MUST persist all configuration settings across application sessions
- **FR-012**: System MUST remove JIRA API endpoint, token, cache settings, and points field configuration from the Data Source interface
- **FR-013**: Data Source interface MUST retain only JQL query editing functionality after configuration separation
- **FR-014**: System MUST provide easy access to the configuration interface from the Data Source page (button, link, or menu item)
- **FR-015**: System MUST validate JIRA URL format and provide helpful error messages for invalid formats
- **FR-016**: System MUST handle token expiration gracefully by prompting users to update their token in the configuration interface
- **FR-017**: System MUST allow users to modify configuration settings without losing existing JQL query profiles
- **FR-018**: System MUST prompt unconfigured users to complete JIRA setup before allowing access to JQL query features

### Key Entities

- **JIRA Configuration**: Represents the complete JIRA connection setup including base URL, API version, authentication token, cache settings, API call limits, and custom field mappings. This is created once and modified occasionally.
- **Connection Test Result**: Represents the outcome of a connection validation attempt, including success/failure status, response time, error details, and JIRA server information (if successful).
- **JQL Query Profile**: Existing entity representing saved JQL queries, which should remain independent of configuration changes and continue to function after configuration is separated.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users complete initial JIRA configuration in under 3 minutes, including connection testing
- **SC-002**: 95% of connection tests provide actionable feedback within 10 seconds
- **SC-003**: Users can modify configuration settings and return to JQL query editing in under 1 minute
- **SC-004**: Zero loss of existing JQL query profiles during configuration migration
- **SC-005**: Data Source interface complexity is reduced by removing at least 5 configuration fields
- **SC-006**: Users who have completed initial setup can create new JQL queries without encountering configuration prompts
- **SC-007**: Configuration errors are detected and reported before users attempt to query data, reducing failed query attempts by 60%
- **SC-008**: 90% of users successfully complete connection testing on their first attempt with valid credentials

