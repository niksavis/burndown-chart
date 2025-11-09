# Phase 0: Research & Technical Decisions

**Feature**: 008-metrics-performance  
**Date**: November 9, 2025  
**Status**: Complete

## Overview

This document consolidates research findings for implementing comprehensive logging, cache optimization, and performance improvements for DORA and Flow metrics calculations.

## Research Areas

### 1. Python Logging Best Practices for Production Applications

**Decision**: Use `logging.handlers.RotatingFileHandler` with structured JSON formatting and custom filters

**Rationale**:
- **RotatingFileHandler**: Built-in Python stdlib solution, no external dependencies, supports size-based rotation (10MB limit) and backup count (5 files)
- **JSON formatting**: Machine-readable logs enable easy parsing, searching, and integration with log analysis tools
- **Custom filters**: `logging.Filter` subclass allows pre-processing log records to redact sensitive data before writing
- **Multi-handler pattern**: Single logger can output to console (development) and files (production) simultaneously
- **Performance**: Minimal overhead (<1ms per log entry), asynchronous handlers not needed for current scale

**Alternatives Considered**:
- **TimedRotatingFileHandler**: Time-based rotation (daily/weekly) - rejected because size-based rotation (10MB) is more predictable for storage management
- **External logging services (Elasticsearch, Splunk)**: Explicitly out of scope per spec
- **Third-party libraries (loguru, structlog)**: Add dependencies, stdlib solution sufficient for requirements

**Implementation Pattern**:
```python
import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime

class SensitiveDataFilter(logging.Filter):
    """Redact sensitive patterns before logging"""
    SENSITIVE_PATTERNS = [
        (r'Bearer\s+[A-Za-z0-9\-._~+/]+=*', 'Bearer [REDACTED]'),
        (r'"token":\s*"[^"]*"', '"token": "[REDACTED]"'),
        (r'"password":\s*"[^"]*"', '"password": "[REDACTED]"'),
    ]
    
    def filter(self, record):
        # Apply redaction to message
        for pattern, replacement in self.SENSITIVE_PATTERNS:
            record.msg = re.sub(pattern, replacement, str(record.msg))
        return True

class JSONFormatter(logging.Formatter):
    """Format log records as JSON"""
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
            'message': record.getMessage(),
        }
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        return json.dumps(log_data)

def setup_logging(log_dir='logs', max_bytes=10*1024*1024, backup_count=5):
    """Configure application logging with rotation and redaction"""
    os.makedirs(log_dir, exist_ok=True)
    
    # Main application log
    app_handler = RotatingFileHandler(
        f'{log_dir}/app.log', 
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    app_handler.setFormatter(JSONFormatter())
    app_handler.addFilter(SensitiveDataFilter())
    
    # Error-only log
    error_handler = RotatingFileHandler(
        f'{log_dir}/errors.log',
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(JSONFormatter())
    
    # Console handler (plain text for development)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)
    root_logger.addHandler(console_handler)
```

**References**:
- Python Logging Cookbook: https://docs.python.org/3/howto/logging-cookbook.html
- Rotating File Handler docs: https://docs.python.org/3/library/logging.handlers.html#rotatingfilehandler

---

### 2. Cache Invalidation Strategies for Configuration Changes

**Decision**: Use hash-based cache keys combining JQL query + field mappings + time period parameters

**Rationale**:
- **Deterministic invalidation**: Cache key changes automatically when configuration changes (JQL, field mappings, time period)
- **Granular caching**: Different configurations cache separately, no false invalidations
- **Simple implementation**: Hash function (`hashlib.md5`) creates stable keys from configuration dict
- **Metadata tracking**: Store cache creation timestamp and config hash in cache metadata for validation

**Alternatives Considered**:
- **Manual invalidation**: Require explicit cache clear on config change - rejected because error-prone (users forget)
- **Version-based invalidation**: Increment version number on changes - rejected because requires state tracking across sessions
- **Time-based only**: Rely solely on 24hr expiration - rejected because stale data persists until timeout

**Implementation Pattern**:
```python
import hashlib
import json
from typing import Dict, Any, Optional, Tuple
from datetime import datetime, timedelta

def generate_cache_key(jql_query: str, field_mappings: Dict, time_period_days: int) -> str:
    """Generate deterministic cache key from configuration"""
    config_data = {
        'jql': jql_query,
        'fields': sorted(field_mappings.items()),  # Sort for consistency
        'period': time_period_days
    }
    config_str = json.dumps(config_data, sort_keys=True)
    return hashlib.md5(config_str.encode()).hexdigest()

def load_cache_with_validation(
    jql_query: str, 
    field_mappings: Dict, 
    time_period_days: int,
    max_age_hours: int = 24
) -> Tuple[bool, Optional[Dict]]:
    """Load cache if valid, return (cache_hit, data)"""
    cache_key = generate_cache_key(jql_query, field_mappings, time_period_days)
    cache_file = f"cache/{cache_key}.json"
    
    if not os.path.exists(cache_file):
        return False, None
    
    with open(cache_file, 'r') as f:
        cache_data = json.load(f)
    
    # Validate age
    cache_timestamp = datetime.fromisoformat(cache_data['metadata']['timestamp'])
    age = datetime.now() - cache_timestamp
    if age > timedelta(hours=max_age_hours):
        return False, None  # Expired
    
    # Validate config hash
    if cache_data['metadata']['config_hash'] != cache_key:
        return False, None  # Config mismatch
    
    return True, cache_data['data']

def save_cache(jql_query: str, field_mappings: Dict, time_period_days: int, data: Dict):
    """Save data to cache with metadata"""
    cache_key = generate_cache_key(jql_query, field_mappings, time_period_days)
    cache_file = f"cache/{cache_key}.json"
    
    cache_data = {
        'metadata': {
            'timestamp': datetime.now().isoformat(),
            'config_hash': cache_key,
            'data_size': len(json.dumps(data))
        },
        'data': data
    }
    
    os.makedirs('cache', exist_ok=True)
    with open(cache_file, 'w') as f:
        json.dump(cache_data, f)
```

**References**:
- Cache invalidation patterns: https://martinfowler.com/bliki/TwoHardThings.html
- Python hashlib documentation: https://docs.python.org/3/library/hashlib.html

---

### 3. JIRA API Rate Limiting Best Practices

**Decision**: Implement token bucket algorithm with request queue and exponential backoff

**Rationale**:
- **Token bucket**: Allows burst requests up to limit (100 req/10s) while smoothing long-term rate
- **Request queue**: Prevents dropping requests, queues them for execution when tokens available
- **Exponential backoff**: Handles 429 (rate limit) responses with increasing retry delays (1s, 2s, 4s, 8s)
- **Proactive limiting**: Avoid hitting rate limit by tracking request rate, more efficient than reactive retries

**Alternatives Considered**:
- **Fixed delay between requests**: Simple but inefficient (wastes time when under limit)
- **Reactive only (retry on 429)**: Triggers rate limit errors, poor user experience
- **Third-party libraries (ratelimit, tenacity)**: Add dependencies, stdlib + simple implementation sufficient

**Implementation Pattern**:
```python
import time
from collections import deque
from typing import Callable, Any
import requests

class JiraRateLimiter:
    """Token bucket rate limiter for JIRA API (100 req/10s)"""
    
    def __init__(self, max_requests=100, time_window=10):
        self.max_requests = max_requests
        self.time_window = time_window  # seconds
        self.request_timestamps = deque(maxlen=max_requests)
    
    def wait_if_needed(self):
        """Block until a request token is available"""
        now = time.time()
        
        # Remove timestamps outside time window
        cutoff = now - self.time_window
        while self.request_timestamps and self.request_timestamps[0] < cutoff:
            self.request_timestamps.popleft()
        
        # If at limit, wait until oldest request expires
        if len(self.request_timestamps) >= self.max_requests:
            sleep_time = self.request_timestamps[0] + self.time_window - now
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        # Record this request
        self.request_timestamps.append(time.time())
    
    def execute_with_backoff(self, request_func: Callable, max_retries=5) -> Any:
        """Execute request with exponential backoff on rate limit"""
        retry_count = 0
        base_delay = 1  # seconds
        
        while retry_count < max_retries:
            self.wait_if_needed()
            
            try:
                response = request_func()
                
                if response.status_code == 429:  # Rate limited
                    delay = base_delay * (2 ** retry_count)
                    time.sleep(delay)
                    retry_count += 1
                    continue
                
                return response
                
            except requests.exceptions.RequestException as e:
                if retry_count >= max_retries - 1:
                    raise
                delay = base_delay * (2 ** retry_count)
                time.sleep(delay)
                retry_count += 1
        
        raise Exception(f"Max retries ({max_retries}) exceeded")

# Usage
rate_limiter = JiraRateLimiter(max_requests=100, time_window=10)

def fetch_jira_issues(jql_query):
    def request_func():
        return requests.get(
            f"{jira_url}/search",
            headers={"Authorization": f"Bearer {token}"},
            params={"jql": jql_query}
        )
    
    return rate_limiter.execute_with_backoff(request_func)
```

**References**:
- Token bucket algorithm: https://en.wikipedia.org/wiki/Token_bucket
- JIRA Cloud rate limiting: https://developer.atlassian.com/cloud/jira/platform/rate-limiting/
- Exponential backoff: https://cloud.google.com/iot/docs/how-tos/exponential-backoff

---

### 4. Python Performance Optimization for Data Processing

**Decision**: Use `functools.lru_cache` for date parsing, pre-computed field mapping index, and shared calculation memoization

**Rationale**:
- **LRU cache**: Built-in decorator, zero-config caching for pure functions (date parsing, field lookups)
- **Field mapping index**: Pre-compute dict lookup from JIRA field names to configured custom fields, O(1) access
- **Lazy evaluation**: Don't calculate metrics not requested by user
- **Batch operations**: Process issues in single pass rather than multiple iterations
- **Memory-efficient**: Use generators for large datasets, avoid loading entire results into memory

**Alternatives Considered**:
- **Manual caching**: More control but reinvents stdlib functionality
- **External caching (Redis)**: Out of scope, adds infrastructure complexity
- **Async processing**: Adds complexity, current scale doesn't require it

**Implementation Pattern**:
```python
from functools import lru_cache
from typing import Dict, List, Optional
from datetime import datetime

# Date parsing cache (LRU cache size based on typical dataset)
@lru_cache(maxsize=10000)
def parse_jira_date(date_string: str) -> Optional[datetime]:
    """Parse JIRA date string to datetime (cached)"""
    try:
        # Try ISO format first
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except:
        try:
            # Fallback to JIRA format
            return datetime.strptime(date_string, '%Y-%m-%dT%H:%M:%S.%f%z')
        except:
            return None

class FieldMappingIndex:
    """Pre-computed index for fast field lookups"""
    
    def __init__(self, field_mappings: Dict[str, str]):
        self._mappings = field_mappings
        self._index = self._build_index(field_mappings)
    
    def _build_index(self, mappings: Dict) -> Dict:
        """Build reverse lookup index"""
        index = {}
        for logical_name, jira_field in mappings.items():
            index[logical_name] = jira_field
            index[jira_field] = logical_name  # Bidirectional
        return index
    
    def get_jira_field(self, logical_name: str) -> Optional[str]:
        """O(1) lookup of JIRA field by logical name"""
        return self._index.get(logical_name)
    
    def get_logical_name(self, jira_field: str) -> Optional[str]:
        """O(1) lookup of logical name by JIRA field"""
        return self._index.get(jira_field)

# Shared calculation results (avoid redundant filtering)
class CalculationContext:
    """Share intermediate results across metric calculations"""
    
    def __init__(self, issues: List[Dict], field_index: FieldMappingIndex):
        self.issues = issues
        self.field_index = field_index
        self._filtered_cache = {}
    
    def filter_issues(self, filter_func, cache_key: str) -> List[Dict]:
        """Filter issues with caching"""
        if cache_key not in self._filtered_cache:
            self._filtered_cache[cache_key] = [
                issue for issue in self.issues if filter_func(issue)
            ]
        return self._filtered_cache[cache_key]
    
    def get_completed_issues(self, time_period_days: int) -> List[Dict]:
        """Get issues completed in time period (shared across metrics)"""
        cutoff = datetime.now() - timedelta(days=time_period_days)
        return self.filter_issues(
            lambda issue: self._is_completed_after(issue, cutoff),
            cache_key=f'completed_{time_period_days}'
        )

# Performance timing decorator
def log_performance(operation_name: str):
    """Decorator to log execution time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"{operation_name} completed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(f"{operation_name} failed after {duration:.3f}s: {e}")
                raise
        return wrapper
    return decorator

# Usage
@log_performance("DORA metrics calculation")
def calculate_dora_metrics(issues, field_mappings, time_period_days):
    field_index = FieldMappingIndex(field_mappings)
    context = CalculationContext(issues, field_index)
    
    # Metrics share filtered results
    deployment_freq = calculate_deployment_frequency(context, time_period_days)
    lead_time = calculate_lead_time(context, time_period_days)
    
    return {"deployment_frequency": deployment_freq, "lead_time": lead_time}
```

**References**:
- functools.lru_cache: https://docs.python.org/3/library/functools.html#functools.lru_cache
- Python performance tips: https://wiki.python.org/moin/PythonSpeed/PerformanceTips
- Big O notation: https://en.wikipedia.org/wiki/Big_O_notation

---

### 5. Log File Cleanup and Retention Policies

**Decision**: Use scheduled cleanup function triggered at application startup to delete files older than 30 days

**Rationale**:
- **Startup cleanup**: Runs once per application start, minimal performance impact
- **Simple implementation**: Single function with `os.path.getmtime()` and `os.unlink()`
- **No external scheduler needed**: Application startup is frequent enough (daily in typical usage)
- **Defensive**: Handles missing files, permission errors gracefully

**Alternatives Considered**:
- **OS-level cron/scheduled tasks**: Platform-dependent, requires system configuration
- **Background thread**: Adds complexity, overkill for simple daily cleanup
- **Manual cleanup only**: Requires admin intervention, leads to unbounded growth

**Implementation Pattern**:
```python
import os
import glob
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

def cleanup_old_logs(log_dir='logs', max_age_days=30):
    """Delete log files older than max_age_days"""
    try:
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        cutoff_timestamp = cutoff_time.timestamp()
        
        # Find all log files (including rotated ones)
        log_files = glob.glob(f'{log_dir}/*.log*')
        
        deleted_count = 0
        for log_file in log_files:
            try:
                file_mtime = os.path.getmtime(log_file)
                if file_mtime < cutoff_timestamp:
                    os.unlink(log_file)
                    deleted_count += 1
                    logger.info(f"Deleted old log file: {log_file}")
            except (OSError, PermissionError) as e:
                logger.warning(f"Failed to delete {log_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleanup complete: deleted {deleted_count} log files older than {max_age_days} days")
    
    except Exception as e:
        logger.error(f"Log cleanup failed: {e}", exc_info=True)

# Call at application startup (in app.py or configuration/__init__.py)
def initialize_logging():
    """Initialize logging configuration and cleanup old logs"""
    setup_logging()
    cleanup_old_logs(max_age_days=30)
```

**References**:
- os.path.getmtime: https://docs.python.org/3/library/os.path.html#os.path.getmtime
- glob pattern matching: https://docs.python.org/3/library/glob.html

---

## Summary of Decisions

| Area                     | Decision                                        | Key Technology                                           |
| ------------------------ | ----------------------------------------------- | -------------------------------------------------------- |
| Logging                  | Rotating file handler with JSON formatting      | `logging.handlers.RotatingFileHandler`, `logging.Filter` |
| Sensitive data redaction | Custom logging filter with regex patterns       | `re.sub()` in `logging.Filter.filter()`                  |
| Cache invalidation       | Hash-based cache keys from configuration        | `hashlib.md5()`, config dict hashing                     |
| Rate limiting            | Token bucket with exponential backoff           | `collections.deque`, retry logic                         |
| Performance optimization | LRU cache, pre-computed indexes, shared context | `functools.lru_cache`, dict index                        |
| Log retention            | Startup cleanup function                        | `os.path.getmtime()`, `os.unlink()`                      |

## Next Steps

Proceed to Phase 1: Design data models and implementation contracts based on these research findings.
