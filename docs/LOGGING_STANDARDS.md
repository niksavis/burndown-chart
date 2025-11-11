# Logging Standards

## Overview

This document defines logging standards for the burndown-chart application to ensure consistent, useful, and maintainable logs.

## Logging Levels

### ERROR
**When**: Failures requiring investigation or preventing normal operation  
**Format**: `[Module] Operation failed: reason (context)`  
**Include**: Error details, relevant IDs, what was being attempted

```python
# ✅ GOOD
logger.error(f"[JIRA] Fetch failed: HTTP {status_code} ({url})")
logger.error(f"[Cache] Invalid data: missing 'issues' key (file: {cache_file})")

# ❌ BAD
logger.error("Error!")
logger.error(f"❌ Error saving unified project data: {e}")
```

### WARNING
**When**: Recoverable issues, unexpected states, deprecated usage  
**Format**: `[Module] Unexpected condition: what happened`  
**Include**: What was expected vs what happened

```python
# ✅ GOOD
logger.warning(f"[JIRA] No issues found matching JQL: {jql[:50]}...")
logger.warning(f"[Config] Field mapping missing: {field_name} (using default)")

# ❌ BAD
logger.warning("⚠️ Invalid unified data structure, using defaults")
logger.warning(f"Failed to check production environment on issue: {e}")
```

### INFO
**When**: Significant state changes, major operations completed  
**Format**: `[Module] Operation: outcome (metrics)`  
**Include**: Counts, durations, success indicators

```python
# ✅ GOOD
logger.info(f"[JIRA] Fetched {len(issues)} issues in {duration:.1f}s")
logger.info(f"[Cache] Hit: {issue_count} issues (key: {cache_key[:8]}...)")
logger.info(f"[Metrics] Calculated 9 metrics for week {week_label}")

# ❌ BAD
logger.info("✅ Saved unified project data")
logger.info(f"Task started: {task_name} (ID: {task_id})")
logger.info(f"CFR Debug: deployment_issues count = {deployment_count}")
```

### DEBUG
**When**: Detailed troubleshooting information (disabled in production)  
**Format**: `[Module] Detail: specific value or state`  
**Include**: Internal state, intermediate values, flow tracking

```python
# ✅ GOOD
logger.debug(f"[Cache] Filter key generated: {filter_key}")
logger.debug(f"[DORA] Deployment issue: {issue_key} matched environment filter")

# ❌ BAD
logger.debug(f"Using {type(grouped_dict).__name__} as input")
```

## Message Format

### Structure
```
[Module] Action: Result (context)
```

- **[Module]**: Short identifier (Cache, JIRA, DORA, Metrics, Config)
- **Action**: What happened (Fetched, Loaded, Calculated, Saved)
- **Result**: Outcome with key metrics
- **Context**: Optional clarifying details

### Length
- Target: 60-80 characters
- Maximum: 100 characters
- Use abbreviations when needed (e.g., "CFR" not "Change Failure Rate")

### Examples

```python
# Data operations
logger.info(f"[JIRA] Fetched {count} issues in {duration:.1f}s")
logger.info(f"[Cache] Hit: {count} issues (age: {age_hours}h)")
logger.info(f"[Cache] Miss: {cache_key[:8]}... (fetching from JIRA)")

# Configuration
logger.info(f"[Config] Loaded settings from {filename}")
logger.warning(f"[Config] Missing field: {field_name} (using default: {default})")

# Calculations
logger.info(f"[DORA] Deployment freq: {value:.1f}/month (Elite tier)")
logger.info(f"[Flow] Velocity: {value:.1f} items/week ({count} completed)")

# Errors
logger.error(f"[JIRA] API failed: HTTP {status_code} ({url[:50]}...)")
logger.error(f"[Metrics] Calculation failed: {metric_name} ({error_type})")
```

## Data Privacy & Security

### 🔒 Automatic Protection (SensitiveDataFilter)

The `SensitiveDataFilter` in `configuration/logging_config.py` automatically redacts:

✅ **Automatically filtered**:
- API tokens: `"token": "abc123"` → `"token": "[REDACTED]"`
- Passwords: `"password": "pass"` → `"password": "[REDACTED]"`
- Bearer tokens: `Bearer xyz...` → `Bearer [REDACTED]`
- API keys: `api_key=sk-...` → `api_key: [REDACTED]`
- Production URLs: `https://jira.company.com` → `https://jira.example.com`
- Email addresses: `user@company.com` → `***@company.com`

**This filter applies to all log handlers automatically.**

### ⚠️ Still Requires Manual Care

**The filter CANNOT protect:**

1. **Customer-identifying information in code logic**
   - Company names in conditional logic
   - Project keys used for filtering
   - Custom field values (summaries, descriptions)

2. **Sensitive data in aggregates**
   - "Fetched issues for ProjectX" (reveals customer project)
   - "User john.doe completed 5 tasks" (reveals employee)

3. **Context that implies customer identity**
   - Specific JQL patterns unique to customers
   - Custom field IDs that map to specific customers

### 🛡️ Developer Responsibilities

Even with automatic filtering, developers must:

1. **Never log field VALUES** - only log field NAMES or METADATA
2. **Never log full JQL** - log length or sanitized version
3. **Never log issue summaries/descriptions**
4. **Test URL sanitization** - verify example.com replacement works

### NEVER Log Sensitive Data

**Prohibited content in logs:**

1. **Authentication credentials**
   - API tokens, passwords, secret keys
   - Session IDs, authentication headers
   - OAuth tokens, refresh tokens

2. **Customer-identifying information**
   - Real company/organization names
   - Production domain names (jira.realcompany.com)
   - Employee names, email addresses
   - User IDs from production systems

3. **JIRA field values that may contain PII**
   - Issue summaries/descriptions
   - Comment text
   - Attachment names
   - Custom field values (unless known to be safe)

4. **Configuration secrets**
   - Database connection strings with passwords
   - Webhook URLs with embedded tokens
   - API endpoints with customer identifiers

### ✅ Safe to Log

- **Metadata**: Issue keys (PROJ-123), field IDs (customfield_10001), status names
- **Aggregates**: Counts, averages, percentages, durations
- **Generic identifiers**: Cache keys (first 8 chars), hash values
- **Structure info**: Field names, JSON keys, data types
- **Placeholder data**: "example.com", "test-token-***", "user-***"

### Data Sanitization Examples

```python
# ❌ DANGEROUS - Logs real credentials
logger.info(f"JIRA URL: {config['base_url']}")  # https://jira.realcompany.com
logger.info(f"Token: {config['token']}")  # sk-real-token-12345

# ✅ SAFE - Sanitized
logger.info(f"[JIRA] Connected: {sanitize_url(config['base_url'])}")  # https://jira.example.com
logger.info(f"[JIRA] Auth configured: {'Yes' if config.get('token') else 'No'}")

# ❌ DANGEROUS - Logs customer data
logger.info(f"Fetched issue: {issue['key']} - {issue['summary']}")  # May contain customer info

# ✅ SAFE - Only metadata
logger.info(f"[JIRA] Fetched: {issue['key']} (type: {issue['fields']['issuetype']['name']})")

# ❌ DANGEROUS - Full JQL may contain customer project names
logger.info(f"JQL query: {jql}")  # project = CUSTOMER-PROJECT AND summary ~ "internal"

# ✅ SAFE - Sanitized or truncated
logger.debug(f"[JIRA] JQL length: {len(jql)} chars")
logger.info(f"[JIRA] Query: {sanitize_jql(jql)}")  # project = EXAMPLE-PROJ AND ...

# ❌ DANGEROUS - Error may contain sensitive data in URL
logger.error(f"Request failed: {url}")  # https://api.company.com/users/john.doe@company.com

# ✅ SAFE - Sanitized error
logger.error(f"[API] Request failed: {sanitize_url(url)} (HTTP {status_code})")
```

### Sanitization Helper Functions

```python
def sanitize_url(url: str) -> str:
    """Replace real domain with example.com placeholder."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return f"{parsed.scheme}://jira.example.com{parsed.path}"

def sanitize_jql(jql: str, max_length: int = 50) -> str:
    """Truncate JQL and replace project names with placeholders."""
    import re
    # Replace project names
    sanitized = re.sub(r'project\s*=\s*[A-Z]+-[A-Z]+', 'project = PROJ', jql, flags=re.IGNORECASE)
    # Truncate
    if len(sanitized) > max_length:
        return sanitized[:max_length] + "..."
    return sanitized

def mask_token(token: str) -> str:
    """Mask token showing only first/last 4 chars."""
    if not token or len(token) < 12:
        return "***"
    return f"{token[:4]}...{token[-4:]}"

def log_safe_count(items: list, item_type: str) -> None:
    """Log count instead of content."""
    logger.info(f"[Data] Loaded {len(items)} {item_type}")
```

### Pre-Commit Checklist

Before committing code with logging:

- [ ] No API tokens, passwords, or secrets in log messages
- [ ] No customer company names or domains
- [ ] No real JIRA project keys (use PROJ, EXAMPLE, TEST)
- [ ] No issue summaries or descriptions
- [ ] URLs sanitized (example.com instead of real domains)
- [ ] JQL queries sanitized or truncated
- [ ] Only metadata and aggregates logged

## What NOT to Log

### ❌ Avoid These Patterns

1. **Emojis**: `✅`, `❌`, `⚠️`, `📥`, `⏱️`
   - Clutter logs, don't add value
   - Use proper log levels instead

2. **Debug prefixes in messages**: "Debug:", "CFR Debug:"
   - Use logger.debug() instead

3. **Overly verbose**: Full stack traces for expected conditions
   - Reserve for unexpected errors

4. **Too frequent**: Every loop iteration, every small step
   - Batch into summary logs

5. **Redundant**: Logging what's already in return values
   - Trust calling code to log at appropriate level

## Migration Examples

### Before/After: JIRA Fetch

```python
# ❌ BEFORE
logger.info(f"📥 Downloading changelog: {current}/{total} issues (page {page + 1}/{total_pages})")

# ✅ AFTER
logger.debug(f"[JIRA] Fetching changelog page {page + 1}/{total_pages}")
logger.info(f"[JIRA] Changelog fetched: {current}/{total} issues in {duration:.1f}s")
```

### Before/After: Cache Operations

```python
# ❌ BEFORE
logger.info(f"✓ Loaded {len(cached_data)} issues from cache (key: {cache_key[:8]}...)")
logger.info(f"Cache miss, fetching from JIRA (key: {cache_key[:8]}...)")

# ✅ AFTER
logger.info(f"[Cache] Hit: {len(cached_data)} issues (key: {cache_key[:8]}...)")
logger.debug(f"[Cache] Miss: {cache_key[:8]}... (fetching from JIRA)")
```

### Before/After: Metrics Calculation

```python
# ❌ BEFORE
logger.info(f"CFR Debug: deployment_issues count = {deployment_count}")
logger.info(f"CFR Debug: incident_issues count = {len(incident_issues)}")

# ✅ AFTER
logger.debug(f"[DORA] CFR inputs: {deployment_count} deployments, {len(incident_issues)} incidents")
logger.info(f"[DORA] CFR: {value:.1f}% (tier: {tier}, {deployment_count} deployments)")
```

### Before/After: File Operations

```python
# ❌ BEFORE
logger.info(f"✅ Saved unified project data")
logger.error(f"❌ Error saving unified project data: {e}")

# ✅ AFTER
logger.info(f"[Persist] Saved {data_type}: {item_count} items")
logger.error(f"[Persist] Save failed: {data_type} ({str(e)})")
```

## Performance Logging

For performance-critical operations, use structured format:

```python
# Operation timing
logger.info(f"[JIRA] POST search: {duration:.2f}s ({page_size} issues/page)")
logger.info(f"[Metrics] Calculated {count} metrics in {duration:.3f}s")

# Performance warnings
if duration > threshold:
    logger.warning(f"[JIRA] Slow fetch: {duration:.1f}s (expected <{threshold}s)")
```

## Error Logging

Always include actionable context:

```python
# ✅ GOOD - Actionable
logger.error(f"[JIRA] Auth failed: check token in app_settings.json")
logger.error(f"[Config] Invalid JSON: {filename} (line {line_no})")

# ❌ BAD - Not actionable
logger.error("Error!")
logger.error(f"Failed: {e}")
```

## Implementation Checklist

When refactoring logging:

- [ ] Remove all emojis
- [ ] Use consistent `[Module]` prefixes
- [ ] Ensure log level matches severity
- [ ] Include relevant metrics (counts, durations)
- [ ] Keep messages concise (< 100 chars)
- [ ] Make errors actionable
- [ ] Move verbose details to DEBUG
- [ ] Batch frequent operations

## Multi-line Statements

When logging statements span multiple lines, add module prefix to clarify which component owns the log:

### ❌ Before (Ambiguous)
```python
logger.info(
    f"Calculated deployment frequency: {value:.2f} deployments/month "
    f"(tier: {tier}, period: {days} days)"
)
```

### ✅ After (Clear)
```python
logger.info(
    f"[DORA] Deployment frequency: {value:.2f}/month "
    f"(tier: {tier}, period: {days}d)"
)
```

### Complex Calculations

```python
# ❌ BEFORE - Hard to identify source
logger.info(
    f"Calculated change failure rate: {cfr:.1f}% "
    f"({failed_deployments}/{total_deployments} failures)"
)

# ✅ AFTER - Clear ownership
logger.info(
    f"[DORA] CFR: {cfr:.1f}% "
    f"({failed_deployments}/{total_deployments} failures)"
)
```

### Configuration Loading

```python
# ❌ BEFORE
logger.info(
    f"Field mappings loaded: deployment_date={mappings.get('deployment_date')}, "
    f"incident_start={mappings.get('incident_start')}"
)

# ✅ AFTER
logger.info(
    f"[Config] Loaded {len(mappings)} field mappings "
    f"(deployment_date, incident_start, ...)"
)
```

### Guideline

- Always include `[Module]` prefix on first line
- Keep total message under 100 characters when possible
- Use second line for optional details
- Prefer single-line when message fits in 80 chars

## Module Prefixes

Standard prefixes for consistency:

- `[JIRA]` - JIRA API operations
- `[Cache]` - Cache operations
- `[Config]` - Configuration loading/saving
- `[Persist]` - File persistence operations
- `[DORA]` - DORA metrics calculations
- `[Flow]` - Flow metrics calculations
- `[Metrics]` - General metrics operations
- `[Callback]` - Dash callback operations
- `[UI]` - UI component operations
- `[Chart]` - Chart generation
