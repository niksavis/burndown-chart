# Updater Architecture

**Audience**: Developers maintaining the build and release pipeline, troubleshooting update failures
**Purpose**: Understanding the self-updating mechanism and Windows executable replacement strategy

## Overview

The Burndown application uses a **two-phase update mechanism with temporary updater copy** to enable both the main application (`Burndown.exe`) and the updater itself (`BurndownUpdater.exe`) to be updated automatically. This architecture solves the Windows file locking problem where a running executable cannot replace itself.

---

## Architecture Pattern

**Inspired by**: Electron/Squirrel.Windows  
**Adapted for**: Python/PyInstaller single-file executables

### Core Concept

```
┌─────────────────────────────────────────────────────────────┐
│ UPDATE FLOW: Two-Phase with Temporary Updater Copy         │
└─────────────────────────────────────────────────────────────┘

Phase 1: APP DOWNLOADS & PREPARES
├── App checks GitHub API for new release
├── Downloads ZIP to %TEMP%\burndown_updates\
├── Extracts to staging directory
├── Copies NEW updater to %TEMP%\BurndownUpdater-temp-<uuid>.exe
└── Launches TEMP updater with --updater-exe flag

Phase 2: TEMP UPDATER REPLACES FILES
├── Waits for app to exit (os._exit(0))
├── Replaces Burndown.exe (from staging)
├── Replaces BurndownUpdater.exe (from staging) ← SELF-UPDATE
├── Launches new Burndown.exe
├── Cleans up temp files
└── Self-terminates (temp updater deleted on next app startup)
```

## Why This Works

### Problem: Windows File Locking

Windows prevents replacing an executable while it's running:
- Main app cannot replace itself (file locked by Windows)
- Original updater cannot replace itself (file locked by Windows)

### Solution: Temporary Updater Copy

```
Install Directory:
├── Burndown.exe        (LOCKED - running)
└── BurndownUpdater.exe (LOCKED - cannot self-update)

%TEMP% Directory (during update):
└── BurndownUpdater-temp-abc123.exe (UNLOCKED - can replace both!)
```

**Key Insight**: The temp updater runs from a different location, so it can replace BOTH the original app and the original updater without file locking conflicts.

## Detailed Update Flow

### 1. Update Check (Background Thread)

```python
# app.py - Background thread
VERSION_CHECK_RESULT = check_for_updates()
if VERSION_CHECK_RESULT.state == UpdateState.AVAILABLE:
    # Show notification to user
```

**Trigger**: Automatic on app startup  
**API**: GitHub Releases API (`/repos/{owner}/{repo}/releases/latest`)  
**Result**: `UpdateProgress` object with state (AVAILABLE/UP_TO_DATE/ERROR)

### 2. Download (User-Initiated)

```python
# callbacks/app_update.py
progress = download_update(progress)  # state: DOWNLOADING → READY
```

**Location**: `%TEMP%\burndown_updates\Burndown-Windows-X.Y.Z.zip`  
**Progress**: Tracked via `UpdateProgress.progress_percent` (0-100)  
**Persistence**: Download path saved to database (`app_state` table)

**Database Keys**:
- `pending_update_version`: "2.7.0"
- `pending_update_path`: "C:\Users\...\AppData\Local\Temp\burndown_updates\Burndown-Windows-2.7.0.zip"
- `pending_update_url`: Download URL (for re-download if needed)
- `pending_update_checked_at`: ISO timestamp (staleness check)

### 3. Launch Updater (Two-Phase Mechanism)

```python
# data/update_manager.py - launch_updater()

# Step 1: Extract ZIP to staging
with zipfile.ZipFile(update_path, 'r') as zip_ref:
    zip_ref.extractall(staging_dir)  # Contains NEW app + NEW updater

# Step 2: Create temp updater copy
temp_updater_name = f"BurndownUpdater-temp-{uuid.uuid4().hex[:8]}.exe"
temp_updater_path = Path(tempfile.gettempdir()) / temp_updater_name
shutil.copy2(new_updater, temp_updater_path)

# Step 3: Launch temp updater with self-update flag
args = [
    str(temp_updater_path),
    str(current_app_exe),         # Path to replace
    str(update_zip),              # Path to ZIP
    str(os.getpid()),             # PID to wait for
    "--updater-exe",              # Self-update flag
    str(current_updater_exe),     # Updater path to replace
]
subprocess.Popen(args, creationflags=DETACHED_PROCESS)

# Step 4: Exit immediately
os._exit(0)  # Force immediate exit, release file locks
```

**Critical**: `os._exit(0)` bypasses Python cleanup and releases file handles immediately.

### 4. Updater Replacement (Atomic Operations)

```python
# updater/updater.py - main()

# Parse arguments (backward compatible)
current_exe = Path(sys.argv[1])      # Burndown.exe
update_zip = Path(sys.argv[2])       # ZIP path
app_pid = int(sys.argv[3])           # App process ID
updater_exe = Path(sys.argv[5]) if "--updater-exe" in sys.argv else None

# Wait for app to exit
wait_for_process_exit(app_pid, timeout=10)

# Backup current app
backup_path = current_exe.with_suffix('.bak')
shutil.copy2(current_exe, backup_path)

# Replace app executable
shutil.move(str(new_app_exe), str(current_exe))

# Replace updater executable (if --updater-exe provided)
if updater_exe:
    updater_backup = updater_exe.with_suffix('.bak')
    shutil.copy2(updater_exe, updater_backup)
    shutil.move(str(new_updater_exe), str(updater_exe))
```

**File Operations Order**:
1. Backup → Replace → Verify (for app)
2. Backup → Replace → Verify (for updater)
3. Launch new app
4. Clean up backups, staging, ZIP

**Rollback**: If any step fails, restore from `.bak` files.

### 5. Restart & Cleanup

```python
# updater/updater.py - cleanup

# Launch updated app
subprocess.Popen([str(current_exe)], creationflags=DETACHED_PROCESS)

# Clean up
backup_path.unlink()          # Remove .bak files
shutil.rmtree(staging_dir)    # Remove staging
update_zip.unlink()           # Remove ZIP

# Temp updater self-terminates (can't delete itself)
# Cleanup happens on next app startup via cleanup_orphaned_temp_updaters()
```

## Crash Recovery & Robustness

### Download State Persistence

**Problem**: User downloads 100MB update → app crashes → download lost

**Solution**: Persist download state to database

```python
# On download complete (data/update_manager.py)
backend.set_app_state('pending_update_version', '2.7.0')
backend.set_app_state('pending_update_path', download_path)

# On app startup (app.py)
restored = _restore_download_state()
if restored and Path(restored.download_path).exists():
    VERSION_CHECK_RESULT = restored  # Resume from READY state
```

### Fallback Logic for Missing Temp Files

**Problem**: Windows Disk Cleanup deletes files from `%TEMP%`

**Solution**: Graceful degradation

```python
# app.py - _restore_pending_update()
if pending_update_path_exists:
    state = UpdateState.READY  # Downloaded, ready to install
else:
    state = UpdateState.AVAILABLE  # Need to re-download
    backend.set_app_state('pending_update_path', None)  # Clear stale
```

**Behavior**: If ZIP missing → user clicks download again (no crashes, no error dialogs)

### Orphaned Temp Updater Cleanup

**Problem**: Temp updater cannot delete itself while running

**Solution**: Cleanup on next app startup

```python
# app.py - cleanup_orphaned_temp_updaters()
temp_dir = Path(tempfile.gettempdir())
cutoff_time = time.time() - (60 * 60)  # 1 hour ago

for temp_updater in temp_dir.glob("BurndownUpdater-temp-*.exe"):
    if temp_updater.stat().st_mtime < cutoff_time:
        temp_updater.unlink()  # Delete if older than 1 hour
```

**Safety**: 1-hour grace period prevents deleting active updater during update.

## Error Handling & Rollback

### Atomic Replacement Pattern

```python
def atomic_replace(source: Path, target: Path) -> None:
    backup = target.with_suffix('.bak')
    
    try:
        # Step 1: Backup
        if target.exists():
            shutil.copy2(target, backup)
        
        # Step 2: Replace
        shutil.move(str(source), str(target))
        
        # Step 3: Verify
        if not target.exists():
            raise UpdateError("Target missing after replacement")
        
        # Step 4: Cleanup
        if backup.exists():
            backup.unlink()
    except Exception:
        # Rollback: Restore from backup
        if backup.exists() and not target.exists():
            shutil.move(str(backup), str(target))
        raise
```

### Error Scenarios

| Scenario               | Detection                         | Recovery                               |
| ---------------------- | --------------------------------- | -------------------------------------- |
| **Download timeout**   | `requests.exceptions.Timeout`     | Retry download from UI                 |
| **Disk full**          | `OSError` during extract          | Cleanup staging, show error            |
| **App won't exit**     | `wait_for_process_exit()` timeout | Updater exits, user retries            |
| **Replace fails**      | Exception in `shutil.move()`      | Restore from .bak                      |
| **AV interference**    | `PermissionError`                 | Exponential backoff retry (5 attempts) |
| **Update interrupted** | Power loss, crash                 | Rollback on next updater run           |

## Windows-Specific Considerations

### File Locking

```python
# Immediate exit releases file handles
os._exit(0)  # C-level exit, no cleanup, immediate handle release

# Alternative (NOT recommended)
sys.exit(0)  # Python-level exit, may delay handle release
```

**Why `os._exit()`**: Bypasses `atexit` handlers and Python cleanup, ensures file locks released immediately.

### Atomic Operations

```python
# shutil.move() uses MoveFileEx on Windows (atomic if same drive)
shutil.move(source, target)  # Atomic on same drive

# os.replace() also atomic
os.replace(source, target)  # Atomic, but no cross-drive support
```

**Note**: All temp operations use same drive (`C:` typically), so replacements are atomic.

### Anti-Virus Interference

**Problem**: AV temporarily locks executables during scan

**Solution**: Exponential backoff retry

```python
for attempt in range(5):
    try:
        return shutil.move(source, target)
    except PermissionError:
        wait_time = 2 ** attempt  # 1, 2, 4, 8, 16 seconds
        time.sleep(wait_time)
```

## Backward Compatibility

### Old Updater → New Mechanism

**Scenario**: User has old updater (no self-update support)

**Behavior**:
1. App launches with `--updater-exe` flag
2. Old updater doesn't recognize flag → **ignores it**
3. Old updater replaces app only (app gets updated)
4. Next update: New updater replaces itself

**Result**: Seamless upgrade path, no breaking changes

### Missing --updater-exe Flag

```python
# updater/updater.py
if len(sys.argv) >= 6 and sys.argv[4] == "--updater-exe":
    updater_exe = Path(sys.argv[5])  # Self-update enabled
else:
    updater_exe = None  # App-only update (backward compatible)
```

## Testing Strategy

### Unit Tests

```python
# tests/test_update_manager.py
def test_persist_download_state():
    progress = UpdateProgress(state=UpdateState.READY, ...)
    _persist_download_state(progress)
    assert backend.get_app_state('pending_update_version') == progress.version

def test_restore_download_state_file_missing():
    backend.set_app_state('pending_update_path', '/nonexistent/path.zip')
    restored = _restore_download_state()
    assert restored.state == UpdateState.AVAILABLE  # Fallback
```

### Integration Tests

1. **Happy Path**: Both files updated successfully
2. **App Killed During Update**: Rollback works
3. **Disk Full**: Graceful failure with cleanup
4. **AV Interference**: Retry logic works
5. **First-Time Self-Update**: Old updater → new updater transition
6. **Backward Compatibility**: Old updater can still update app

### Manual Testing Checklist

- [ ] Download update → close app → restart → verify READY state restored
- [ ] Delete ZIP from `%TEMP%` → restart → verify AVAILABLE state
- [ ] Install update → verify both executables replaced
- [ ] Kill update mid-flight → verify rollback
- [ ] Remove updater.exe from dist/ → verify build fails
- [ ] Check `%TEMP%` for orphaned updaters after 24h → should be cleaned

## Performance Metrics

| Operation               | Target | Actual                       |
| ----------------------- | ------ | ---------------------------- |
| **Update check**        | <2s    | ~1s (GitHub API)             |
| **Download 100MB**      | <60s   | ~30s (depends on connection) |
| **Extract ZIP**         | <5s    | ~2s                          |
| **Replace executables** | <1s    | ~500ms (atomic)              |
| **Total update time**   | <90s   | ~45s (typical)               |

## Security Considerations

1. **HTTPS Only**: All downloads over HTTPS (GitHub Releases)
2. **No Signature Verification**: Currently unsigned (future enhancement)
3. **Temp File Cleanup**: Removes orphaned updaters (prevents disk bloat)
4. **Path Validation**: Sanitizes paths from ZIP (prevents path traversal)
5. **Process Verification**: Waits for specific PID to exit (prevents race conditions)

## Future Enhancements

### V2 Features (Not Implemented)

- **Delta Updates**: Download only changed bytes (reduce 100MB → 5MB)
- **Signature Verification**: Code signing with certificate validation
- **Background Updates**: Download in background, install on next restart
- **Staged Rollout**: Percentage-based release (10% users first, then 100%)
- **Automatic Rollback**: Detect crashes after update, auto-rollback

## References

### External Patterns

- **Electron autoUpdater**: https://github.com/electron/electron/blob/main/docs/api/auto-updater.md
- **Squirrel.Windows**: https://github.com/Squirrel/Squirrel.Windows
- **PyInstaller Runtime**: https://pyinstaller.org/en/stable/runtime-information.html

### Internal Documentation

- [Release Process](release_process.md) - How to create releases
- [Logging Standards](logging_standards.md) - Log format for update operations
- [Caching System](caching_system.md) - Download state persistence

### Code Locations

- `app.py` - Startup cleanup, download state restoration
- `data/update_manager.py` - Update checking, downloading, launching
- `updater/updater.py` - Atomic file replacement, rollback
- `callbacks/app_update.py` - UI callbacks for update notifications
- `.github/workflows/release.yml` - CI/CD release pipeline
- `build/build.ps1` - Build script (updater mandatory)

---

**Questions?** See [troubleshooting section](#troubleshooting) or check logs in `logs/app.log`.

## Troubleshooting

### Update Fails Silently (No Error Message)

**Symptom**: Download succeeds, backup created (`.bak` file), but update doesn't complete

**Cause**: Updater encountered error during copy phase (e.g., permission denied, disk full, AV interference)

**Solution**:
1. Check updater log: `%TEMP%\burndown_updater.log`
2. Look for "ERROR:" or "WARNING:" messages
3. Check disk space (updater needs ~200MB free)
4. Check anti-virus (may block file replacement)
5. Check folder permissions (install directory must be writable)

**Common Errors in Log**:
- `Access is denied` (WinError 5): 
  - **Primary Cause**: Anti-virus software locking executable during/after scan (especially common with admin privileges)
  - **Secondary Cause**: App installed in protected directory requiring admin rights
  - **Solution 1**: Wait for automatic retry (updater retries 20 times over ~60 seconds)
  - **Solution 2**: Add install directory to anti-virus exclusions
  - **Solution 3**: If in protected directory (e.g., `C:\Program Files\`), move to user directory
  - **Observation**: Updates may work WITHOUT admin rights but fail WITH admin rights (AV scans elevated processes more aggressively)
- `Permission denied`: UAC issue or directory permissions - check folder security settings
- `No space left on device`: Free up disk space
- `File not found in ZIP`: Download corrupted - re-download update
- `Failed to replace executable after 20 attempts`: Persistent anti-virus lock or system issue - try disabling AV temporarily

**Log Location**: `C:\Users\[USERNAME]\AppData\Local\Temp\burndown_updater.log`

### Update Stuck at "Downloading..."

**Cause**: Network timeout, server unavailable

**Solution**:
1. Check internet connection
2. Check GitHub status: https://www.githubstatus.com/
3. Retry download from UI
4. If persists, download manually from releases page

### Update Fails with "File locked" Error

**Cause**: Windows file handles not immediately released after process exit, or anti-virus scanning executable

**Admin Rights Paradox**: Updates may work on machines WITHOUT admin rights but fail WITH admin rights because:
- Windows Defender/AV software scans elevated processes more aggressively
- Admin processes may trigger deeper security scans (10-30 second delays)
- File system caching behaves differently for elevated processes

**Fix (v2.7.2+)**: Updater now implements:
1. **3-second grace period** after process exit (allows AV to start scan)
2. **20-attempt exponential backoff** - retries up to ~60 seconds
3. **Progress messages** - informs user when AV scanning is likely cause
4. **PermissionError-specific handling** - distinguishes file locking from other issues

**Solution**:
- Update to v2.7.2+ (fix is automatic, waits for AV scan to complete)
- If fails: Add install directory to anti-virus exclusions
- Alternative: Run update when AV is idle (not during scheduled scan)

**Technical Details**:
Anti-virus software on Windows can hold file locks for 10-30 seconds after process exit due to:
- Real-time protection scanning new/modified executables
- Elevated process reputation checking
- SmartScreen verification
- Signature analysis

### Download Lost After App Crash

**Cause**: Should NOT happen (download state persisted)

**Check**:
1. Restart app → should restore READY state
2. Check `%TEMP%\burndown_updates\` for ZIP
3. If ZIP exists but app shows AVAILABLE → database issue (check logs)

### Orphaned Temp Updaters in %TEMP%

**Cause**: Normal behavior (temp updater cannot delete itself)

**Solution**: Automatic cleanup on next app startup (files >1 hour old)

**Manual Cleanup**:
```powershell
Remove-Item "$env:TEMP\BurndownUpdater-temp-*.exe"
```

### Update Interrupted (Power Loss)

**Cause**: Update in progress when power lost

**Result**: Original app/updater remain (update fails safely)

**Recovery**:
1. Restart app
2. Download update again
3. Install update

**Rollback**: If app corrupted, `.bak` files in install directory

### Build Fails: "Updater executable not found"

**Cause**: Updater is now mandatory (as of v2.7.0)

**Solution**: Verify `updater/updater.py` exists

**Reason**: Self-updating updater requires both executables in release package
