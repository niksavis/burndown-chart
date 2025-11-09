# API Contracts: Logging Module

**Module**: `configuration/logging_config.py`  
**Purpose**: Centralized logging configuration with file rotation and sensitive data redaction

## Public API

### Function: `setup_logging`

**Purpose**: Initialize application logging with file handlers, rotation, and redaction filters

**Signature**:
```python
def setup_logging(
    log_dir: str = 'logs',
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    log_level: str = 'INFO'
) -> None
```

**Parameters**:
- `log_dir` (str): Directory for log files, created if doesn't exist
- `max_bytes` (int): Maximum size per log file before rotation (default 10MB)
- `backup_count` (int): Number of rotated backup files to keep (default 5)
- `log_level` (str): Minimum log level - 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'

**Returns**: None

**Side Effects**:
- Creates `log_dir` directory if it doesn't exist
- Configures root logger with handlers
- Sets up log file rotation
- Installs sensitive data redaction filter

**Example**:
```python
from configuration.logging_config import setup_logging

# Initialize logging at application startup
setup_logging(log_dir='logs', log_level='INFO')

# Use standard Python logging
import logging
logger = logging.getLogger(__name__)
logger.info("Application started")
```

**Error Handling**:
- Raises `OSError` if log directory cannot be created
- Raises `PermissionError` if log files cannot be written

---

### Function: `cleanup_old_logs`

**Purpose**: Delete log files older than specified age

**Signature**:
```python
def cleanup_old_logs(
    log_dir: str = 'logs',
    max_age_days: int = 30
) -> int
```

**Parameters**:
- `log_dir` (str): Directory containing log files
- `max_age_days` (int): Delete files older than this many days

**Returns**: Number of files deleted (int)

**Side Effects**:
- Deletes log files with modification time older than `max_age_days`
- Logs deletion operations

**Example**:
```python
from configuration.logging_config import cleanup_old_logs

# Delete logs older than 30 days
deleted_count = cleanup_old_logs(log_dir='logs', max_age_days=30)
print(f"Deleted {deleted_count} old log files")
```

**Error Handling**:
- Continues on individual file errors (permission denied, file not found)
- Logs warnings for files that cannot be deleted
- Returns count of successfully deleted files

---

### Class: `SensitiveDataFilter`

**Purpose**: Logging filter that redacts sensitive patterns before writing to file

**Inheritance**: `logging.Filter`

**Methods**:

#### `filter(record: logging.LogRecord) -> bool`

Redacts sensitive data patterns from log record message

**Parameters**:
- `record` (logging.LogRecord): Log record to filter

**Returns**: Always True (record is never dropped, only modified)

**Side Effects**: Modifies `record.msg` to replace sensitive patterns with redacted placeholders

**Redaction Patterns**:
- Bearer tokens: `Bearer [REDACTED]`
- API tokens in JSON: `"token": "[REDACTED]"`
- Passwords in JSON: `"password": "[REDACTED]"`
- API keys: `apikey=[REDACTED]`
- Email addresses: `[EMAIL_REDACTED]`

**Example**:
```python
from configuration.logging_config import SensitiveDataFilter
import logging

# Create logger with sensitive data filter
logger = logging.getLogger('my_app')
handler = logging.StreamHandler()
handler.addFilter(SensitiveDataFilter())
logger.addHandler(handler)

# This will be redacted
logger.info("Authorization: Bearer abc123token")
# Output: "Authorization: Bearer [REDACTED]"
```

---

### Class: `JSONFormatter`

**Purpose**: Format log records as JSON for structured logging

**Inheritance**: `logging.Formatter`

**Methods**:

#### `format(record: logging.LogRecord) -> str`

Convert log record to JSON string

**Parameters**:
- `record` (logging.LogRecord): Log record to format

**Returns**: JSON-formatted string

**JSON Structure**:
```json
{
  "timestamp": "2025-11-09T14:30:45.123456Z",
  "level": "INFO",
  "module": "data.dora_calculator",
  "function": "calculate_metrics",
  "line": 125,
  "message": "Calculated metrics successfully",
  "exception": null  // or stack trace if error
}
```

**Example**:
```python
from configuration.logging_config import JSONFormatter
import logging

handler = logging.FileHandler('app.log')
handler.setFormatter(JSONFormatter())
logger = logging.getLogger()
logger.addHandler(handler)

logger.info("User action", extra={'context': {'user_id': 123}})
# Writes JSON line to app.log
```

---

## Internal API (Not for external use)

### Function: `_get_sensitive_patterns() -> List[Tuple[str, str]]`

Returns list of (regex_pattern, replacement) tuples for redaction

---

## Module Configuration

**Log Files Created**:
- `logs/app.log` - All log levels (INFO, WARNING, ERROR)
- `logs/errors.log` - ERROR and CRITICAL only
- Console output - All log levels (development)

**Rotation Policy**:
- Size-based: 10MB per file
- Backup count: 5 files (.log, .log.1, .log.2, .log.3, .log.4, .log.5)
- Age-based: Files older than 30 days deleted

**Log Format**:
- Files: JSON (structured, machine-readable)
- Console: Human-readable text format

---

## Testing Contract

**Unit Tests** (`tests/unit/configuration/test_logging_config.py`):
- `test_setup_logging_creates_directory()` - Verify log directory creation
- `test_setup_logging_configures_handlers()` - Verify handlers added to root logger
- `test_log_rotation_triggers_at_max_size()` - Verify rotation at 10MB
- `test_backup_count_respected()` - Verify only 5 backup files kept
- `test_cleanup_old_logs_deletes_expired()` - Verify 30-day retention
- `test_sensitive_data_filter_redacts_tokens()` - Verify Bearer token redaction
- `test_sensitive_data_filter_redacts_passwords()` - Verify password redaction
- `test_json_formatter_structure()` - Verify JSON output format
- `test_json_formatter_includes_exception()` - Verify exception formatting

**Integration Tests** (`tests/integration/test_logging_workflow.py`):
- `test_end_to_end_logging_workflow()` - Full logging lifecycle test
- `test_log_files_persist_across_restarts()` - Verify persistence
- `test_concurrent_logging()` - Verify thread safety
