# Test Utilities

This directory contains utilities for safe testing that prevent tests from modifying the real application configuration.

## Test Isolation

### `test_isolation.py`

Provides context managers and utilities to ensure tests never modify real app files:

- `isolated_app_settings()` - Creates temporary `app_settings.json` for testing
- `isolated_project_data()` - Creates temporary `project_data.json` for testing  
- `isolated_jira_cache()` - Creates temporary `jira_cache.json` for testing
- `mock_jira_api_calls()` - Mocks JIRA API calls to prevent external requests

### Usage Example

```python
from tests.utils.test_isolation import isolated_app_settings, mock_jira_api_calls

def test_my_function():
    with isolated_app_settings({"pert_factor": 2.0}):
        with mock_jira_api_calls():
            # Your test code here
            # Safe to test without affecting real config
            pass
```

## Guidelines

1. **Never modify real config files** - Always use isolation utilities
2. **Never make real API calls** - Always mock external services  
3. **Clean up after tests** - Use context managers for automatic cleanup
4. **Use temp directories** - For any file operations in tests
