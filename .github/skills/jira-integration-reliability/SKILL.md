---
name: "jira-integration-reliability"
description: "Implement reliable Jira data flow and error handling changes"
---

# Skill: Jira Integration Reliability

Use for Jira query, fetch, cache, and metadata flow changes.

## Objectives

- Keep Jira integrations resilient and observable.
- Handle API errors gracefully.
- Prevent customer-data leakage in logs.

## Workflow

1. Map entry points in `data/` and callback delegates.
2. Implement minimal handling improvements (timeouts/retries/validation).
3. Ensure logs are sanitized and actionable.
4. Validate with targeted tests and diagnostics.

## Guardrails

- Use repository Jira paths (no ad-hoc alternate entry points).
- Avoid logging full payloads containing sensitive fields.
- Keep callback files as routing-only delegates.
