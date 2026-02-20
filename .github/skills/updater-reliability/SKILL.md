---
name: 'updater-reliability'
description: 'Implement safe and reliable updater system changes'
---

# Skill: Updater Reliability

Use this skill when working on the two-phase update mechanism or updater components.

## Goals

- Maintain reliability of the two-phase update flow
- Prevent update failures that could brick installations
- Keep updater simple and robust
- Enable both app and updater self-updating

## Architecture overview

**Two-phase update mechanism**:

1. **Phase 1 (App)**: Downloads update, extracts to staging, copies updater to temp, launches temp updater
2. **Phase 2 (Temp Updater)**: Waits for app exit, replaces Burndown.exe and BurndownUpdater.exe, launches new app, self-terminates

**Key insight**: Temp updater runs from different location (temp dir), so it can replace both original files without Windows file locking issues.

## Workflow

1. **Read updater architecture**: Load `docs/updater_architecture.md`
2. **Identify change scope**: App-side vs updater-side vs shared
3. **Apply minimal changes**: Preserve two-phase flow integrity
4. **Test thoroughly**: Simulate update in test environment
5. **Validate**: Check both successful and failed update scenarios

## Key files

### App-side (phase 1)

- `data/update_manager.py` - Update orchestration
- `callbacks/app_update.py` - Update UI callbacks
- `ui/update_notification.py` - Update notification UI
- `data/version_tracker.py` - Version comparison

### Updater-side (phase 2)

- `updater/updater.py` - Main updater logic
- `updater/file_ops.py` - File replacement operations
- `build/updater.spec` - Updater build config

### Shared

- `data/installation_context.py` - Detect installation type
- `build/generate_version_info.py` - Version info for both executables

## Enforcement points

### Update state machine

States must follow this flow:

```

CHECKING → AVAILABLE → DOWNLOADING → READY → INSTALLING → INSTALLED
↓ ↓ ↓ ↓
ERROR CANCELLED ERROR ERROR

```

Never skip states or create invalid transitions.

### File safety

```python
# ✓ GOOD: Atomic file operations with rollback
def replace_file_safely(source, dest):
    backup = dest + '.backup'
    try:
        shutil.copy2(dest, backup)  # Backup original
        shutil.copy2(source, dest)  # Replace
        os.remove(backup)           # Clean up
    except Exception as e:
        if os.path.exists(backup):
            shutil.copy2(backup, dest)  # Rollback
        raise

# ❌ BAD: Direct replacement without backup
shutil.copy2(source, dest)
```

### Process synchronization

```python
# ✓ GOOD: Wait for app exit before replacement
max_wait = 30  # seconds
start = time.time()
while process_exists(app_pid):
    if time.time() - start > max_wait:
        raise TimeoutError("App did not exit")
    time.sleep(0.5)

# ❌ BAD: Replace while app still running
replace_files()  # May fail with "file in use" error
```

### Logging

Updater logs go to dedicated file (critical for debugging failed updates):

```python
# ✓ GOOD: Updater-specific log file
log_path = temp_dir / "updater.log"
logging.basicConfig(filename=log_path, level=logging.DEBUG)

# Log all steps for debugging
logger.info(f"Replacing {dest} with {source}")
logger.info(f"App PID: {app_pid}, waiting for exit...")
```

## Critical paths

### Download and staging

1. Download ZIP to temp directory
2. Verify ZIP integrity (size, hash if available)
3. Extract to staging directory
4. Verify extracted files exist
5. Persist update path to database (for crash recovery)

### Launch temp updater

1. Copy updater executable to temp location with UUID
2. Build command line args (--updater-exe, staging path, app PID, install dir)
3. Launch temp updater as detached process
4. App exits immediately (os.\_exit(0))

### File replacement (temp updater)

1. Wait for app process to exit (timeout 30s)
2. Verify staging files exist
3. Create backups of current files
4. Replace Burndown.exe from staging
5. Replace BurndownUpdater.exe from staging (self-update!)
6. Launch new Burndown.exe
7. Clean up staging and temp files
8. Self-terminate (temp updater)

## Guardrails

- Never break the two-phase flow pattern
- Never skip file backups before replacement
- Always wait for process exit before replacement
- Always log each step (errors go to updater.log)
- Test both successful and failed update scenarios
- Verify installation type detection (portable vs installed)
- Handle both legacy (BurndownChart.exe) and new (Burndown.exe) naming

## Suggested validations

### Manual testing

1. Download update via UI
2. Trigger installation
3. Verify app restarts with new version
4. Check updater.log for errors
5. Verify both Burndown.exe and BurndownUpdater.exe were updated

### Error scenarios to test

1. Download interrupted (verify retry or cancellation)
2. Insufficient disk space (verify error message)
3. App doesn't exit in time (verify timeout handling)
4. File replacement fails (verify rollback)
5. New version fails to launch (verify error handling)

### Code checks

- Run `get_errors` on changed files
- Verify logging at each critical step
- Check exception handling covers all failure modes
- Confirm process wait logic has timeout

## Risks to mitigate

1. **Bricked installation**: If updater fails mid-replacement
   - Mitigation: Atomic operations with backups
2. **Orphaned temp updater**: If cleanup fails
   - Mitigation: App cleans up old temp updaters on startup
3. **Update loop**: If version detection broken
   - Mitigation: Version comparison logic tested thoroughly
4. **File locking**: If replace attempted while app running
   - Mitigation: Process exit wait logic with timeout

## Related artifacts

- `docs/updater_architecture.md` - Complete architecture documentation
- `.github/instructions/build-pipeline.instructions.md` - Build system rules
- `.github/skills/release-management/SKILL.md` - Release workflow
