# Phase 1: Data Model

**Feature**: 008-metrics-performance  
**Date**: November 9, 2025  
**Prerequisites**: research.md complete

## Overview

This document defines the data structures and entities for logging, caching, and performance tracking infrastructure.

## Entity Definitions

### 1. Log Entry

**Purpose**: Represents a single log record with structured data and metadata

**Fields**:
- `timestamp` (str, ISO 8601): UTC timestamp when log entry was created
- `level` (str, enum): Log severity level - INFO, WARNING, ERROR, DEBUG, CRITICAL
- `module` (str): Python module name where log originated (e.g., "data.dora_calculator")
- `function` (str): Function name where log originated
- `line` (int): Line number in source file
- `message` (str): Log message content (after sensitive data redaction)
- `exception` (str, optional): Formatted exception stack trace if error
- `context` (dict, optional): Additional contextual data (request_id, user_action, data_volume, etc.)

**Validation Rules**:
- `timestamp` must be valid ISO 8601 format
- `level` must be one of standard Python logging levels
- `message` must not contain sensitive patterns (tokens, passwords, PII)
- `context` keys must be strings, values must be JSON-serializable

**State Transitions**: N/A (immutable once created)

**Example**:
```json
{
  "timestamp": "2025-11-09T14:30:45.123456Z",
  "level": "INFO",
  "module": "data.dora_calculator",
  "function": "calculate_deployment_frequency",
  "line": 125,
  "message": "Calculated deployment frequency for 850 issues in 1.234s",
  "context": {
    "operation": "deployment_frequency",
    "issue_count": 850,
    "duration_seconds": 1.234,
    "time_period_days": 30
  }
}
```

---

### 2. Log File

**Purpose**: Represents a physical log file with rotation metadata

**Fields**:
- `file_path` (str): Absolute path to log file (e.g., "logs/app.log")
- `size_bytes` (int): Current file size in bytes
- `creation_date` (datetime): When file was created
- `rotation_sequence` (int): Rotation number (0 = current, 1-5 = historical)
- `log_level_filter` (str, optional): If set, file only contains logs >= this level (e.g., "ERROR")
- `last_modified` (datetime): Last write timestamp

**Validation Rules**:
- `size_bytes` must be >= 0
- `rotation_sequence` must be 0-5 (current file + 5 backups)
- File must rotate when `size_bytes` exceeds 10MB (10,485,760 bytes)
- Files with `last_modified` > 30 days must be deleted

**State Transitions**:
- **Active** → **Rotating**: When size exceeds 10MB
- **Rotating** → **Archived**: Renamed to .log.N (sequence incremented)
- **Archived** → **Deleted**: When sequence > 5 or age > 30 days

**Example**:
```python
{
  "file_path": "/path/to/logs/app.log.2",
  "size_bytes": 10485760,  # Exactly 10MB
  "creation_date": datetime(2025, 11, 1, 10, 0, 0),
  "rotation_sequence": 2,
  "log_level_filter": None,  # Contains all levels
  "last_modified": datetime(2025, 11, 5, 16, 30, 0)
}
```

---

### 3. Cache Metadata

**Purpose**: Metadata for validating cached JIRA data

**Fields**:
- `cache_key` (str): MD5 hash of configuration (JQL + field mappings + time period)
- `creation_timestamp` (datetime): When cache entry was created
- `expiration_timestamp` (datetime): When cache becomes invalid (creation + 24 hours)
- `data_size_bytes` (int): Size of cached data in bytes
- `version_identifier` (str): Cache schema version (e.g., "2.0")
- `config_hash` (str): Hash of configuration used to generate this cache
- `issue_count` (int): Number of issues cached
- `jql_query` (str): Original JQL query (for debugging)

**Validation Rules**:
- `cache_key` must be 32-character hex string (MD5 hash)
- `expiration_timestamp` must be > `creation_timestamp`
- `version_identifier` must match current application cache version
- `config_hash` must match `cache_key` (consistency check)

**State Transitions**:
- **Valid** → **Expired**: When current time > expiration_timestamp
- **Valid** → **Invalidated**: When configuration changes (cache_key changes)
- **Expired/Invalidated** → **Deleted**: On next cache access

**Example**:
```json
{
  "cache_key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "creation_timestamp": "2025-11-09T14:30:45Z",
  "expiration_timestamp": "2025-11-10T14:30:45Z",
  "data_size_bytes": 1048576,
  "version_identifier": "2.0",
  "config_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
  "issue_count": 850,
  "jql_query": "project = ACME AND status = Done"
}
```

---

### 4. Fetch Operation

**Purpose**: Tracks a JIRA API data fetch operation for logging and diagnostics

**Fields**:
- `request_id` (str, UUID): Unique identifier for this fetch operation
- `jql_query` (str): JQL query executed
- `start_time` (datetime): When fetch started
- `end_time` (datetime): When fetch completed
- `duration_seconds` (float): Total execution time
- `data_volume_fetched` (int): Number of issues fetched
- `cache_hit` (bool): Whether data was served from cache
- `api_calls_made` (int): Number of JIRA API requests (pagination)
- `rate_limit_delays` (int): Number of times rate limit was hit
- `error` (str, optional): Error message if fetch failed

**Validation Rules**:
- `end_time` must be >= `start_time`
- `duration_seconds` must equal `end_time - start_time`
- `api_calls_made` must be >= 0
- If `cache_hit` is True, `api_calls_made` must be 0

**State Transitions**:
- **Initiated** → **In Progress**: When first API call starts
- **In Progress** → **Completed**: When all data fetched successfully
- **In Progress** → **Failed**: When error occurs

**Example**:
```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "jql_query": "project = ACME AND updated >= -30d",
  "start_time": "2025-11-09T14:30:45.000Z",
  "end_time": "2025-11-09T14:32:12.500Z",
  "duration_seconds": 87.5,
  "data_volume_fetched": 1250,
  "cache_hit": false,
  "api_calls_made": 13,
  "rate_limit_delays": 2,
  "error": null
}
```

---

### 5. Calculation Performance

**Purpose**: Tracks performance metrics for DORA and Flow metric calculations

**Fields**:
- `metric_type` (str, enum): Type of metric - "deployment_frequency", "lead_time", "cfr", "mttr", "flow_velocity", "flow_time", "flow_efficiency", "flow_load", "flow_distribution"
- `start_time` (datetime): When calculation started
- `end_time` (datetime): When calculation completed
- `duration_seconds` (float): Total execution time
- `input_data_size` (int): Number of issues processed
- `result_data_size` (int): Size of result object in bytes
- `cache_hits` (int): Number of cached intermediate results used
- `cache_misses` (int): Number of values calculated (not cached)

**Validation Rules**:
- `metric_type` must be one of the defined metric types
- `duration_seconds` must be > 0
- `input_data_size` must be >= 0
- Must meet performance targets: ≤2s for ≤1000 issues, ≤5s for 1000-5000 issues

**State Transitions**: N/A (immutable measurement)

**Example**:
```json
{
  "metric_type": "deployment_frequency",
  "start_time": "2025-11-09T14:30:45.000Z",
  "end_time": "2025-11-09T14:30:46.234Z",
  "duration_seconds": 1.234,
  "input_data_size": 850,
  "result_data_size": 256,
  "cache_hits": 42,
  "cache_misses": 8
}
```

---

### 6. Performance Threshold

**Purpose**: Defines expected performance targets for validation

**Fields**:
- `metric_type` (str, enum): Type of metric (same as Calculation Performance)
- `target_duration_seconds` (float): Expected maximum duration
- `actual_duration_seconds` (float): Measured duration
- `threshold_status` (str, enum): Result - "pass", "fail", "warning"
- `dataset_size_category` (str, enum): Size bucket - "small" (≤1000), "medium" (1000-5000), "large" (>5000)

**Validation Rules**:
- `threshold_status` = "pass" if `actual_duration_seconds` <= `target_duration_seconds`
- `threshold_status` = "warning" if `actual_duration_seconds` <= `target_duration_seconds` * 1.2 (within 20%)
- `threshold_status` = "fail" if `actual_duration_seconds` > `target_duration_seconds` * 1.2

**State Transitions**: N/A (evaluation result)

**Example**:
```json
{
  "metric_type": "flow_velocity",
  "target_duration_seconds": 2.0,
  "actual_duration_seconds": 1.8,
  "threshold_status": "pass",
  "dataset_size_category": "small"
}
```

---

## Data Relationships

```
┌─────────────────┐
│   Log Entry     │──┬──> Written to ──> Log File
└─────────────────┘  │
                     └──> Filtered by ──> Sensitive Data Filter
                     
┌─────────────────┐
│ Cache Metadata  │────> Validates ──> Cached JIRA Data
└─────────────────┘

┌─────────────────┐       ┌──────────────────────┐
│ Fetch Operation │──────>│ Calculation Performance│
└─────────────────┘       └──────────────────────┘
         │                         │
         └────> Produces ──────────┘
                  JIRA Issues
                  
┌──────────────────────┐       ┌─────────────────────┐
│Calculation Performance│──────>│Performance Threshold│
└──────────────────────┘       └─────────────────────┘
                                (validates against)
```

## Storage Format

All entities persist to JSON files:

- **Log Entries**: Append to `logs/app.log`, `logs/errors.log`, `logs/performance.log` (JSON lines format, one entry per line)
- **Cache Metadata**: Embedded in cache files as `metadata` key (e.g., `jira_cache.json`, `cache/<cache_key>.json`)
- **Fetch Operation**: Logged to `logs/performance.log` as structured log entry
- **Calculation Performance**: Logged to `logs/performance.log` as structured log entry
- **Performance Threshold**: Evaluated in-memory, violations logged to `logs/performance.log`

## Validation Rules Summary

| Entity                  | Key Validation                                         |
| ----------------------- | ------------------------------------------------------ |
| Log Entry               | No sensitive patterns in message                       |
| Log File                | Size ≤ 10MB before rotation, age ≤ 30 days             |
| Cache Metadata          | config_hash matches cache_key, not expired             |
| Fetch Operation         | end_time >= start_time, cache_hit ↔ api_calls_made = 0 |
| Calculation Performance | Duration meets target (2s/5s)                          |
| Performance Threshold   | Status derived from actual vs target duration          |

## Next Steps

Proceed to create API contracts and quickstart guide.
