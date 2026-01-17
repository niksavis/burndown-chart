# Quick Test Script: Simulate Update with Flag
# This script simulates what the updater does - sets the post_update_relaunch flag

param(
    [switch]$Set,      # Set the flag (simulate updater)
    [switch]$Clear,    # Clear the flag (reset for testing)
    [switch]$Check,    # Check if flag is set
    [string]$DbPath = "profiles\burndown.db"
)

$ErrorActionPreference = "Stop"

# Colors
function Write-Info {
    param([string]$Message)
    Write-Host "[INFO] $Message" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[WARN] $Message" -ForegroundColor Yellow
}

# Check if database exists
if (-not (Test-Path $DbPath)) {
    Write-Warning "Database not found at: $DbPath"
    Write-Info "Make sure you're in the app directory and have run the app at least once"
    exit 1
}

# Execute SQLite commands using Python (more portable than sqlite3 CLI)
function Invoke-SqliteCommand {
    param([string]$Query)
    
    # Convert Windows path to forward slashes for Python
    $DbPathForPython = $DbPath -replace '\\', '/'
    
    # Escape single quotes in query for Python
    $QueryEscaped = $Query -replace "'", "''"
    
    $pythonScript = @"
import sqlite3
import sys
conn = sqlite3.connect('$DbPathForPython')
cursor = conn.cursor()
try:
    cursor.execute("$Query")
    conn.commit()
    results = cursor.fetchall()
    for row in results:
        print('|'.join(str(x) for x in row))
except Exception as e:
    print(f'Error: {e}', file=sys.stderr)
    sys.exit(1)
finally:
    conn.close()
"@
    
    $result = python -c $pythonScript 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw $result
    }
    return $result
}

# Main logic
try {
    if ($Set) {
        Write-Info "Setting post_update_relaunch flag (simulating updater)..."
        Invoke-SqliteCommand "INSERT OR REPLACE INTO app_state (key, value) VALUES ('post_update_relaunch', 'true')"
        Write-Success "Flag set successfully!"
        Write-Info ""
        Write-Info "Next steps:"
        Write-Info "1. Quit app (system tray icon -> Quit) - KEEP BROWSER TAB OPEN!"
        Write-Info "2. Restart the app (double-click BurndownChart.exe)"
        Write-Info "3. NO new browser tab should open (flag prevents auto-launch)"
        Write-Info "4. Existing browser tab stays open - app works when you interact"
        Write-Info "5. If you click during restart, overlay shows and auto-reconnects"
    }
    elseif ($Clear) {
        Write-Info "Clearing post_update_relaunch flag..."
        Invoke-SqliteCommand "DELETE FROM app_state WHERE key='post_update_relaunch'"
        Write-Success "Flag cleared successfully!"
    }
    elseif ($Check) {
        Write-Info "Checking post_update_relaunch flag..."
        $result = Invoke-SqliteCommand "SELECT * FROM app_state WHERE key='post_update_relaunch'"
        if ($result) {
            Write-Success "Flag is SET:"
            Write-Host $result
        }
        else {
            Write-Info "Flag is NOT set (normal state)"
        }
    }
    else {
        # No flags - show help
        Write-Host ""
        Write-Host "Update Flag Testing Script" -ForegroundColor Yellow
        Write-Host "=========================" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "This script simulates what the updater does when launching the app after an update."
        Write-Host ""
        Write-Host "Usage:" -ForegroundColor Cyan
        Write-Host "  .\test_update_flag.ps1 -Set     # Set the flag (simulate post-update launch)"
        Write-Host "  .\test_update_flag.ps1 -Clear   # Clear the flag (reset for testing)"
        Write-Host "  .\test_update_flag.ps1 -Check   # Check if flag is currently set"
        Write-Host ""
        Write-Host "Testing Workflow:" -ForegroundColor Cyan
        Write-Host "  1. Run app normally (browser opens)"
        Write-Host "  2. Keep browser tab OPEN (do not close it!)"
        Write-Host "  3. Quit app: Right-click system tray icon -> Quit"
        Write-Host "  4. Run: .\test_update_flag.ps1 -Set"
        Write-Host "  5. Verify flag: .\test_update_flag.ps1 -Check (should show 'true')"
        Write-Host "  6. Run app again: .\BurndownChart.exe"
        Write-Host ""
        Write-Host "Expected Results:" -ForegroundColor Cyan
        Write-Host "  - NO new browser tab opens (only ONE tab total)"
        Write-Host "  - Existing tab stays open and app works when you interact"
        Write-Host "  - If you click while server is restarting: 'Reconnecting...' overlay appears"
        Write-Host "  - Overlay polls server and auto-reloads page when server is ready"
        Write-Host "  - Flag is automatically cleared after first use"
        Write-Host ""
        Write-Host "Verify Success:" -ForegroundColor Cyan
        Write-Host "  .\test_update_flag.ps1 -Check    # Should show 'Flag is NOT set'"
        Write-Host ""
    }
}
catch {
    Write-Host "[ERROR] $_" -ForegroundColor Red
    exit 1
}
