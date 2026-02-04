# JIRA Configuration Guide

**Audience**: Users configuring JIRA access and developers supporting configuration flows
**Part of**: [Documentation Index](readme.md)

## Overview

JIRA configuration is managed in the settings panel. It separates connection settings from query definitions so users can reuse a single connection across multiple queries.

## Configuration Fields

- Base URL: The JIRA instance URL without REST path suffix.
- API version: Select the REST API version used for search requests.
- API token: Personal access token for authentication.
- Cache limits: Maximum cache size and retention behavior.
- API page size: Maximum results per API call.
- Estimate field: Story points field used for velocity and points metrics.

## Connection Testing

Use the Test Connection action to validate:

- Base URL correctness.
- API version compatibility.
- Token validity.

If the test fails, check network access and token permissions.

## Where This Appears

- Settings panel: JIRA configuration section.
- Query workflows: JQL editor uses the saved configuration to fetch data.

## Developer Notes

- Connection settings are stored in profile-specific settings.
- API path composition is handled internally based on the selected API version.
