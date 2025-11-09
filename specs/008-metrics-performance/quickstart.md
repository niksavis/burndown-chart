# Feature 008: Metrics Performance Optimization - Quickstart Guide

**Branch**: `008-metrics-performance`  
**Status**: Planning Phase  
**Prerequisites**: Feature 007 (DORA & Flow Metrics) must be complete

---

## 1. Overview

This feature optimizes logging, data fetching, and metric calculations for the DORA & Flow Metrics dashboard. It introduces:

- **Structured Logging**: File-based logs with rotation, JSON formatting, sensitive data redaction
- **Optimized Data Fetching**: Incremental updates, cache invalidation, rate limiting
- **Faster Calculations**: LRU caching, pre-computed indexes, shared calculation context

**Expected Improvements**:
- 40% faster data fetches via incremental updates
- 60% cache hit rate for repeated queries
- 2s calculation time for ≤1000 issues
- 5s calculation time for 1000-5000 issues

---

## 2. Setup

### 2.1 Install Dependencies

No new dependencies required - uses Python stdlib modules:

```powershell
.\.venv\Scripts\activate; pip install -r requirements.txt
```

**Logging Dependencies** (stdlib):
- `logging` - Core logging framework
- `logging.handlers.RotatingFileHandler` - Size-based log rotation
- `json` - JSON formatting for structured logs
- `re` - Regex for sensitive data redaction

**Performance Dependencies** (stdlib):
- `functools.lru_cache` - LRU caching for date parsing
- `hashlib.md5` - Cache key generation
- `time` - Performance timing

### 2.2 Configure Logging

Logging is configured automatically on application startup via `configuration/logging_config.py`:

**Default Configuration**:
- **Log Directory**: `logs/`
- **Log Files**:
  - `app.log` - All logs (INFO and above)
  - `errors.log` - Error logs only (ERROR and above)
  - Console - INFO and above
- **Rotation**: 10MB max size, 5 backup files
- **Retention**: 30 days (auto-cleanup on startup)
- **Format**: JSON with timestamp, level, module, message, context

**Example Log Entry** (`logs/app.log`):
```json
{
  "timestamp": "2025-11-09T14:30:45.123Z",
  "level": "INFO",
  "module": "data.dora_calculator",
  "message": "Starting DORA metrics calculation",
  "context": {
    "time_period_days": 30,
    "issue_count": 1234,
    "cache_hit": false
  }
}
```

**Manual Configuration** (if needed):
```python
from configuration.logging_config import setup_logging

# Custom log directory and rotation settings
setup_logging(
    log_dir="custom_logs/",
    max_bytes=20 * 1024 * 1024,  # 20MB
    backup_count=10  # Keep 10 backup files
)
```

### 2.3 Verify Setup

**Check Logging**:
```powershell
.\.venv\Scripts\activate; python -c "from configuration.logging_config import setup_logging; setup_logging(); import logging; logging.info('Test log entry')"
```

Expected output:
- Console: `INFO: Test log entry`
- File: `logs/app.log` created with JSON entry

**Check Log Cleanup**:
```powershell
# Create old log file
New-Item -Path "logs\old.log" -ItemType File -Force
(Get-Item "logs\old.log").LastWriteTime = (Get-Date).AddDays(-35)

# Run cleanup
.\.venv\Scripts\activate; python -c "from configuration.logging_config import cleanup_old_logs; cleanup_old_logs(max_age_days=30)"

# Verify deletion
Get-ChildItem logs\*.log
# old.log should be gone
```

---

## 3. Usage

### 3.1 Using New Logging

**In Application Code** (`data/dora_calculator.py`):
```python
import logging

logger = logging.getLogger(__name__)

def calculate_deployment_frequency(issues, field_mappings, time_period_days):
    logger.info("Starting deployment frequency calculation", extra={
        "issue_count": len(issues),
        "time_period_days": time_period_days
    })
    
    try:
        # ... calculation logic ...
        result = {"value": 5.2, "unit": "deployments/month"}
        
        logger.info("Deployment frequency calculated successfully", extra={
            "result": result
        })
        return result
        
    except Exception as e:
        logger.error("Deployment frequency calculation failed", extra={
            "error": str(e),
            "error_type": type(e).__name__
        }, exc_info=True)
        raise
```

**Logs Output** (`logs/app.log`):
```json
{"timestamp": "2025-11-09T14:30:45.123Z", "level": "INFO", "module": "data.dora_calculator", "message": "Starting DORA metrics calculation"}
{"timestamp": "2025-11-09T14:30:45.234Z", "level": "INFO", "module": "data.dora_calculator", "message": "Starting deployment frequency calculation", "context": {"issue_count": 1234, "time_period_days": 30}}
{"timestamp": "2025-11-09T14:30:46.456Z", "level": "INFO", "module": "data.dora_calculator", "message": "Deployment frequency calculated successfully", "context": {"result": {"value": 5.2, "unit": "deployments/month"}}}
{"timestamp": "2025-11-09T14:30:46.567Z", "level": "INFO", "module": "data.dora_calculator", "message": "DORA metrics calculation completed in 1.234s"}
```

### 3.2 Using Cache Management

**Load with Validation** (`data/jira_simple.py`):
```python
from data.cache_manager import load_cache_with_validation, save_cache, generate_cache_key
import logging

logger = logging.getLogger(__name__)

def fetch_jira_data_with_cache(jql_query, field_mappings, time_period_days):
    # Generate cache key from configuration
    cache_key = generate_cache_key(
        jql_query=jql_query,
        field_mappings=field_mappings,
        time_period_days=time_period_days
    )
    
    # Generate config hash for validation
    config_hash = hashlib.md5(
        json.dumps({
            "jql": jql_query,
            "fields": sorted(field_mappings.items()),
            "period": time_period_days
        }, sort_keys=True).encode()
    ).hexdigest()
    
    # Try to load from cache
    cache_valid, cached_data = load_cache_with_validation(
        cache_key=cache_key,
        config_hash=config_hash,
        max_age_hours=24,
        cache_dir="cache"
    )
    
    if cache_valid:
        logger.info(f"✓ Loaded {len(cached_data)} issues from cache (key: {cache_key[:8]}...)")
        return cached_data
    
    # Fetch fresh data from JIRA
    logger.info(f"Cache miss, fetching from JIRA (key: {cache_key[:8]}...)")
    issues = fetch_all_issues(jql_query)
    
    # Save to cache
    save_cache(
        cache_key=cache_key,
        data=issues,
        config_hash=config_hash,
        cache_dir="cache"
    )
    
    return issues
```

**Invalidate Cache on Config Change** (`callbacks/settings.py`, `callbacks/field_mapping.py`):
```python
import glob
import os
import logging

logger = logging.getLogger(__name__)

# In settings.py - when JQL changes
if old_jql != new_jql:
    try:
        cache_files = glob.glob("cache/*.json")
        for cache_file in cache_files:
            try:
                os.remove(cache_file)
            except Exception as e:
                logger.debug(f"Could not remove cache file {cache_file}: {e}")
        logger.info(f"✓ Invalidated {len(cache_files)} cache files due to JQL change")
    except Exception as e:
        logger.warning(f"Cache invalidation failed: {e}")

# In field_mapping.py - when field mappings change
try:
    cache_files = glob.glob("cache/*.json")
    for cache_file in cache_files:
        try:
            os.remove(cache_file)
        except Exception as e:
            logger.debug(f"Could not remove cache file {cache_file}: {e}")
    logger.info(f"✓ Invalidated {len(cache_files)} JIRA cache files due to field mapping changes")
except Exception as e:
    logger.warning(f"JIRA cache invalidation failed: {e}")
```

### 3.3 Cache Metadata Tracking

**Cache metadata is automatically saved to `app_settings.json`** (Feature 008 - T057):
```python
# Automatically tracked when caching JIRA responses
{
    "cache_metadata": {
        "last_cache_key": "a3c7f8e9...",  # MD5 hash of configuration
        "last_cache_timestamp": "2025-11-09T14:30:45.123Z",  # When cache was created
        "cache_config_hash": "9f8e7d6c..."  # Hash of JQL + fields + period
    }
}
```

**View Cache Metadata**:
```powershell
# Load and display cache metadata
.\.venv\Scripts\activate; python -c "from data.persistence import load_app_settings; import json; settings = load_app_settings(); print(json.dumps(settings.get('cache_metadata', {}), indent=2))"
```

Expected output:
```json
{
  "last_cache_key": "a3c7f8e9d4c2b1a0...",
  "last_cache_timestamp": "2025-11-09T14:30:45.123456",
  "cache_config_hash": "9f8e7d6c5b4a3210..."
}
```

---

## 4. Testing

### 4.1 Run Unit Tests

**All Tests**:
```powershell
.\.venv\Scripts\activate; pytest tests/unit/ -v
```

**Logging Tests Only**:
```powershell
.\.venv\Scripts\activate; pytest tests/unit/configuration/test_logging_config.py -v
```

Expected output:
```
test_setup_logging_creates_log_directory PASSED
test_setup_logging_creates_log_files PASSED
test_rotating_file_handler_rotation PASSED
test_json_formatter_output PASSED
test_sensitive_data_filter_redacts_tokens PASSED
test_sensitive_data_filter_redacts_passwords PASSED
test_cleanup_old_logs_deletes_old_files PASSED
test_cleanup_old_logs_preserves_recent_files PASSED
========================= 8 passed =========================
```

**Cache Tests Only**:
```powershell
.\.venv\Scripts\activate; pytest tests/unit/data/test_cache_manager.py -v
```

Expected output:
```
test_generate_cache_key_consistency PASSED
test_generate_cache_key_changes_on_input PASSED
test_load_cache_with_validation_success PASSED
test_load_cache_with_validation_expired PASSED
test_load_cache_with_validation_config_mismatch PASSED
test_save_cache_creates_file PASSED
test_save_cache_includes_metadata PASSED
test_invalidate_cache_deletes_file PASSED
test_cache_invalidation_trigger_detects_jql_changes PASSED
test_cache_invalidation_trigger_detects_field_changes PASSED
test_cache_invalidation_trigger_detects_period_changes PASSED
========================= 11 passed in 0.27s =========================
```

### 4.2 Run Integration Tests

**Full Workflow Test**:
```powershell
.\.venv\Scripts\activate; pytest tests/integration/ -v -s
```

**Note**: Integration tests for incremental fetch and rate limiting (T042-T044) are currently stub implementations marked with `pytest.skip`.

Expected workflow:
1. Application starts, logging configured
2. Old logs cleaned up (>30 days deleted)
3. JIRA data fetched with rate limiting
4. Data cached with metadata
5. Metrics calculated with performance logging
6. Results logged to `logs/app.log`
7. Sensitive data redacted in logs

---

## 5. Performance Verification

### 5.1 Monitor Log Files

**Check Log Rotation**:
```powershell
Get-ChildItem logs\*.log | Select-Object Name, Length, LastWriteTime

# Expected output:
# Name         Length      LastWriteTime
# ----         ------      -------------
# app.log      8234567     2025-11-09 14:30:45
# app.log.1    10485760    2025-11-08 10:15:30  (rotated when hit 10MB)
# errors.log   123456      2025-11-09 12:00:00
```

**Analyze Log Content**:
```powershell
# Parse JSON logs
Get-Content logs\app.log | ForEach-Object { $_ | ConvertFrom-Json } | Select-Object timestamp, level, module, message | Format-Table

# Filter error logs
Get-Content logs\errors.log | ForEach-Object { $_ | ConvertFrom-Json } | Where-Object { $_.level -eq "ERROR" } | Format-List
```

### 5.2 Measure Cache Performance

**Check Cache Hit Rate**:
```powershell
# Count cache hits vs misses in logs
$logs = Get-Content logs\app.log | ForEach-Object { $_ | ConvertFrom-Json }
$cache_hits = ($logs | Where-Object { $_.message -like "*loaded from cache*" }).Count
$cache_misses = ($logs | Where-Object { $_.message -like "*Cache miss*" }).Count
$total = $cache_hits + $cache_misses

Write-Output "Cache Hit Rate: $([math]::Round($cache_hits / $total * 100, 2))%"
# Target: 60% hit rate
```

**Verify Cache Files**:
```powershell
Get-ChildItem cache\*.json | Select-Object Name, Length, LastWriteTime

# Check cache metadata
$cache = Get-Content cache\dora_metrics_cache.json | ConvertFrom-Json
$cache.metadata | Format-List

# Expected output:
# cache_key       : a1b2c3d4e5f6...
# created_at      : 2025-11-09T14:30:45.123Z
# expires_at      : 2025-11-10T14:30:45.123Z
# config_hash     : 9f8e7d6c5b4a...
# cache_version   : 2.0
```

### 5.3 Measure Calculation Performance

**Time Metric Calculations**:
```powershell
.\.venv\Scripts\activate; python -c "
from data.dora_calculator import calculate_dora_metrics
from data.jira_simple import fetch_all_issues
from data.field_mapper import get_field_mappings
import time

issues = fetch_all_issues()
field_mappings = get_field_mappings()

start = time.time()
metrics = calculate_dora_metrics(issues, field_mappings, 30)
duration = time.time() - start

print(f'Issue count: {len(issues)}')
print(f'Duration: {duration:.3f}s')
print(f'Target: {"<2s" if len(issues) <= 1000 else "<5s"}')
print(f'Status: {"✅ PASS" if (len(issues) <= 1000 and duration < 2) or (len(issues) > 1000 and duration < 5) else "❌ FAIL"}')
"
```

Expected output:
```
Issue count: 1234
Duration: 1.567s
Target: <5s
Status: ✅ PASS
```

---

## 6. Troubleshooting

### 6.1 Logging Issues

**Problem**: Logs not appearing in files

**Solution**:
```powershell
# Re-initialize logging
.\.venv\Scripts\activate; python -c "from configuration.logging_config import setup_logging; setup_logging()"
```

**Problem**: Sensitive data not redacted

**Solution**:
```powershell
# Check SensitiveDataFilter patterns
.\.venv\Scripts\activate; python -c "from configuration.logging_config import SensitiveDataFilter; filter = SensitiveDataFilter(); print('Patterns:', len(filter.SENSITIVE_PATTERNS))"

# Test redaction
.\.venv\Scripts\activate; python -c "from configuration.logging_config import SensitiveDataFilter; import logging; filter = SensitiveDataFilter(); record = logging.LogRecord('test', logging.INFO, '', 0, 'Token: Bearer abc123', (), None); filter.filter(record); print(record.msg)"
```

Expected: `Token: Bearer [REDACTED]`

### 6.2 Cache Issues

**Problem**: Cache not invalidating on config changes

**Solution**:
```powershell
# Manually delete cache files
Remove-Item cache\*.json

# Check cache invalidation trigger
.\.venv\Scripts\activate; python -c "
from data.cache_manager import CacheInvalidationTrigger

trigger = CacheInvalidationTrigger()
should_invalidate = trigger.should_invalidate(
    cache_file='cache/dora_metrics_cache.json',
    current_jql='project = TEST',
    current_field_mappings={'deployment_date': 'customfield_10001'},
    current_time_period=30
)
print(f'Should invalidate: {should_invalidate}')
"
```

**Problem**: Cache hit rate too low

**Solution**:
- Check if JQL query changes frequently (each change generates new cache key)
- Check if field mappings change frequently
- Increase cache expiration time (currently 24 hours in `load_cache_with_validation()`)
- Verify cache files are being created in `cache/` directory
- Check cache metadata in `app_settings.json` → `cache_metadata`

---

## 7. Next Steps

After setup and verification:

1. **Monitor Performance**: Track calculation times in production
2. **Tune Cache Settings**: Adjust expiration time based on usage patterns
3. **Review Logs**: Regularly check `logs/errors.log` for issues
4. **Benchmark Regularly**: Run performance tests to detect regressions

**Related Documentation**:
- [Feature Spec](spec.md) - Full feature requirements
- [Implementation Plan](plan.md) - Technical implementation details
- [Logging API](contracts/logging_api.md) - Logging module reference
- [Cache API](contracts/cache_api.md) - Cache management reference
- [Performance API](contracts/performance_api.md) - Performance utilities reference
