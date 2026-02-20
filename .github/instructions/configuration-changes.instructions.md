---
applyTo: 'configuration/**/*.py,data/config_validation.py,data/smart_defaults.py'
description: 'Enforce safe configuration management patterns'
---

# Configuration Changes Instructions

Apply these rules when changing configuration modules, validation, or default values.

## Configuration architecture

Configuration is divided into several modules:

1. **Runtime config**: `configuration/settings.py` - App runtime settings
2. **Chart config**: `configuration/chart_config.py` - Visualization defaults
3. **Metrics config**: `configuration/metrics_config.py` - Metrics calculation params
4. **DORA config**: `configuration/dora_config.py` - DORA metrics thresholds
5. **Flow config**: `configuration/flow_config.py` - Flow metrics parameters
6. **Logging config**: `configuration/logging_config.py` - Logging setup
7. **Server config**: `configuration/server.py` - Dash server settings
8. **Help content**: `configuration/help_content.py` - Help text and tooltips

User-specific config is persisted in `profiles/burndown.db` (`app_state` table).

## Core principles

- Configuration must have sensible defaults (app works out-of-the-box)
- Validate all user-provided config values
- Never crash on invalid config (log warning, use default)
- Keep config schema versioned and backward-compatible
- Document all config options and their effects

## Validation patterns

### Required fields

```python
# ✓ GOOD: Explicit validation with defaults
def validate_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and normalize configuration."""
    validated = {
        'timeout': config.get('timeout', 30),
        'max_results': config.get('max_results', 1000),
    }

    # Validate ranges
    if not 1 <= validated['timeout'] <= 300:
        logger.warning(f"Invalid timeout {validated['timeout']}, using default 30")
        validated['timeout'] = 30

    return validated

# ❌ BAD: Assume config is complete and valid
timeout = config['timeout']  # May KeyError
max_results = config['max_results']  # May be invalid
```

### Type safety

```python
# ✓ GOOD: Type validation with fallback
def get_int_config(key: str, default: int) -> int:
    """Get integer config value with validation."""
    value = config.get(key, default)
    try:
        return int(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid int for {key}: {value}, using {default}")
        return default

# ❌ BAD: No type checking
return config.get(key, default)  # May be string "30" instead of int 30
```

## Default value patterns

### Smart defaults

```python
# ✓ GOOD: Context-aware defaults
def get_default_time_period(project_type: str) -> int:
    """Get default time period based on project type."""
    if project_type == 'kanban':
        return 90  # 90 days for continuous flow
    else:  # scrum
        return 14  # Sprint length

# Document in help text
HELP_TEXT = "Default: 90 days for Kanban, 14 days for Scrum"

# ❌ BAD: Hard-coded defaults everywhere
time_period = config.get('time_period', 30)  # Why 30?
```

### Configuration discovery

```python
# ✓ GOOD: Provide introspection
def get_config_schema() -> Dict[str, Any]:
    """Return configuration schema with defaults and validation rules."""
    return {
        'timeout': {
            'type': 'int',
            'default': 30,
            'min': 1,
            'max': 300,
            'description': 'JIRA API request timeout in seconds'
        },
        # ...
    }
```

## Persistence patterns

### Save config

```python
# ✓ GOOD: Atomic config save with validation
def save_config(key: str, value: Any) -> None:
    """Save configuration value with validation."""
    # Validate first
    validated_value = validate_config_value(key, value)

    # Persist atomically
    with transaction():
        execute_query(
            "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
            (key, json.dumps(validated_value))
        )

    logger.info(f"Config saved: {key} = {validated_value}")

# ❌ BAD: Save without validation
execute_query(
    "INSERT OR REPLACE INTO app_state (key, value) VALUES (?, ?)",
    (key, json.dumps(value))
)
```

### Load config

```python
# ✓ GOOD: Load with fallback to defaults
def load_config(key: str, default: Any = None) -> Any:
    """Load configuration value with default fallback."""
    result = execute_query(
        "SELECT value FROM app_state WHERE key = ?",
        (key,)
    )

    if result:
        try:
            return json.loads(result[0][0])
        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON for config {key}, using default")
            return default
    else:
        return default

# ❌ BAD: Load without error handling
value = json.loads(result[0][0])  # May crash
```

## Migration patterns

### Schema versioning

```python
# ✓ GOOD: Version config schema
CONFIG_VERSION = 2

def migrate_config(old_config: Dict[str, Any], old_version: int) -> Dict[str, Any]:
    """Migrate config from old version to current."""
    if old_version < 2:
        # Rename field
        if 'old_field' in old_config:
            old_config['new_field'] = old_config.pop('old_field')

    old_config['_version'] = CONFIG_VERSION
    return old_config

# Load with migration
config = load_config('my_config', {})
config_version = config.get('_version', 1)
if config_version < CONFIG_VERSION:
    config = migrate_config(config, config_version)
    save_config('my_config', config)
```

## Security considerations

### Sensitive config

```python
# ✓ GOOD: Never log sensitive values
def save_jira_token(token: str) -> None:
    """Save JIRA API token securely."""
    save_config('jira_token', token)
    logger.info("JIRA token saved")  # Don't log the token!

# ✓ GOOD: Mask in UI
def display_token(token: str) -> str:
    """Display token with masking."""
    if len(token) > 8:
        return f"{token[:4]}...{token[-4:]}"
    return "****"

# ❌ BAD: Log sensitive data
logger.info(f"Saved token: {token}")
```

### Config injection prevention

```python
# ✓ GOOD: Validate config sources
def load_user_config(config_dict: Dict[str, Any]) -> None:
    """Load user-provided config with validation."""
    ALLOWED_KEYS = {'timeout', 'max_results', 'theme'}

    for key, value in config_dict.items():
        if key not in ALLOWED_KEYS:
            logger.warning(f"Ignoring unknown config key: {key}")
            continue

        validated_value = validate_config_value(key, value)
        save_config(key, validated_value)

# ❌ BAD: Accept any config key
for key, value in config_dict.items():
    save_config(key, value)  # May overwrite system config
```

## Help text patterns

### Tooltip content

```python
# ✓ GOOD: Informative, concise tooltips
TOOLTIPS = {
    'timeout': "Maximum time to wait for JIRA API response (1-300 seconds)",
    'max_results': "Maximum issues to fetch per request (1-1000)",
}

# Include in help_content.py
# Reference in UI components via help_system
```

## Before completion

1. Verify all config values have defaults
2. Confirm validation logic covers invalid inputs
3. Check backward compatibility with old config
4. Test config save/load roundtrip
5. Verify no sensitive data logged
6. Update help text if config options changed
7. Run `get_errors` on changed files
8. Test with both default config and custom config

## Related artifacts

- `configuration/help_content.py` - Help text and tooltips
- `data/config_validation.py` - Validation utilities
- `data/smart_defaults.py` - Smart default logic
- `ui/help_system.py` - Help system UI
- `.github/skills/sqlite-persistence-safety/SKILL.md` - Persistence patterns
