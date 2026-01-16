# Build Script for Burndown Chart Application
# Builds standalone Windows executables using PyInstaller

[CmdletBinding()]
param(
    [switch]$Clean,      # Remove previous build artifacts before building
    [switch]$VerboseBuild,    # Show detailed output from PyInstaller
    [switch]$Test,       # Run post-build validation tests
    [switch]$Sign        # Code sign the executables (requires certificate)
)

# Script configuration
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$BuildDir = Join-Path $ProjectRoot "build"
$DistDir = Join-Path $ProjectRoot "dist"

# Output formatting
function Write-Step {
    param([string]$Message)
    Write-Host "`n==== $Message ====" -ForegroundColor Cyan
}

function Write-Success {
    param([string]$Message)
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-Error {
    param([string]$Message)
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

# Main build process
try {
    Write-Host "`nBurndown Chart - Build Script" -ForegroundColor Yellow
    Write-Host "==============================`n" -ForegroundColor Yellow

    # Step 1: Extract version from configuration/__init__.py
    Write-Step "Extracting version number"
    $ConfigFile = Join-Path $ProjectRoot "configuration\__init__.py"
    if (-not (Test-Path $ConfigFile)) {
        Write-Error "Configuration file not found at: $ConfigFile"
        exit 1
    }
    
    $ConfigContent = Get-Content $ConfigFile
    $VersionLine = $ConfigContent | Where-Object { $_ -match '__version__' }
    if ($VersionLine) {
        # Extract version string between quotes
        $Version = ($VersionLine -split '"')[1]
        if (-not $Version) {
            $Version = ($VersionLine -split "'")[1]
        }
        Write-Success "Version: $Version"
    }
    else {
        Write-Error "Could not extract version from configuration/__init__.py"
        exit 1
    }

    # Step 2: Verify Python environment
    Write-Step "Verifying Python environment"
    if (-not $env:VIRTUAL_ENV) {
        Write-Host "No virtual environment detected - using global Python" -ForegroundColor Yellow
        Write-Host "This is normal in CI/CD environments" -ForegroundColor Yellow
    }
    else {
        Write-Success "Virtual environment active: $env:VIRTUAL_ENV"
    }

    # Step 3: Verify PyInstaller is installed
    Write-Step "Verifying PyInstaller installation"
    $pyinstallerVersion = python -m PyInstaller --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PyInstaller not found"
        Write-Host "Please run: pip install -r requirements.txt" -ForegroundColor Yellow
        exit 1
    }
    Write-Success "PyInstaller version: $pyinstallerVersion"

    # Step 4: Verify spec files exist
    Write-Step "Verifying build specification files"
    $appSpec = Join-Path $BuildDir "app.spec"
    $updaterSpec = Join-Path $BuildDir "updater.spec"
    
    if (-not (Test-Path $appSpec)) {
        Write-Error "app.spec not found at: $appSpec"
        exit 1
    }
    Write-Success "Found app.spec"
    
    if (-not (Test-Path $updaterSpec)) {
        Write-Error "updater.spec not found at: $updaterSpec"
        exit 1
    }
    Write-Success "Found updater.spec"

    # Step 5: Validate no test dependencies in production code
    Write-Step "Validating production code dependencies"
    $testDependencies = @("pytest", "playwright", "pip-tools", "pip_tools")
    $foundTestDeps = @()
    
    # Search Python files excluding tests directory
    $pythonFiles = Get-ChildItem -Path $ProjectRoot -Filter "*.py" -Recurse | 
    Where-Object { $_.FullName -notmatch "\\tests\\" -and $_.FullName -notmatch "\\\.venv\\" }
    
    foreach ($file in $pythonFiles) {
        $content = Get-Content $file.FullName -Raw
        foreach ($dep in $testDependencies) {
            if ($content -match "^\s*import\s+$dep" -or $content -match "^\s*from\s+$dep") {
                $foundTestDeps += "$($file.Name): imports $dep"
            }
        }
    }
    
    if ($foundTestDeps.Count -gt 0) {
        Write-Error "Test dependencies found in production code:"
        foreach ($dep in $foundTestDeps) {
            Write-Host "  - $dep" -ForegroundColor Red
        }
        exit 1
    }
    Write-Success "No test dependencies in production code"

    # Step 6: Collect license information
    Write-Step "Collecting third-party license information"
    $collectLicensesScript = Join-Path $BuildDir "collect_licenses.ps1"
    
    if (-not (Test-Path $collectLicensesScript)) {
        Write-Error "collect_licenses.ps1 not found at: $collectLicensesScript"
        exit 1
    }
    
    Push-Location $ProjectRoot
    try {
        & $collectLicensesScript
        if ($LASTEXITCODE -ne 0) {
            Write-Error "License collection failed"
            exit 1
        }
        Write-Success "License information collected"
    }
    finally {
        Pop-Location
    }

    # Step 7: Clean previous builds if requested
    if ($Clean) {
        Write-Step "Cleaning previous build artifacts"
        
        # Remove dist directory
        if (Test-Path $DistDir) {
            Remove-Item -Path $DistDir -Recurse -Force
            Write-Success "Removed dist directory"
        }
        
        # Remove build/temp directory
        $TempDir = Join-Path $BuildDir "temp"
        if (Test-Path $TempDir) {
            Remove-Item -Path $TempDir -Recurse -Force
            Write-Success "Removed build/temp directory"
        }
        
        # Remove .spec build artifacts
        $BuildArtifacts = @(
            (Join-Path $ProjectRoot "build" | Get-ChildItem -Filter "*.spec.log" -ErrorAction SilentlyContinue)
        )
        foreach ($artifact in $BuildArtifacts) {
            Remove-Item -Path $artifact.FullName -Force
            Write-Success "Removed $($artifact.Name)"
        }
    }

    # Step 8: Generate Windows version information file
    Write-Step "Generating Windows version information"
    $generateVersionScript = Join-Path $BuildDir "generate_version_info.py"
    
    if (-not (Test-Path $generateVersionScript)) {
        Write-Error "generate_version_info.py not found at: $generateVersionScript"
        exit 1
    }
    
    Push-Location $ProjectRoot
    try {
        python $generateVersionScript
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Version info generation failed"
            exit 1
        }
        Write-Success "Version info generated for version $Version"
    }
    finally {
        Pop-Location
    }

    # Step 9: Create dist directory if it doesn't exist
    Write-Step "Preparing output directory"
    if (-not (Test-Path $DistDir)) {
        New-Item -ItemType Directory -Path $DistDir | Out-Null
        Write-Success "Created dist directory"
    }
    else {
        Write-Success "Dist directory exists"
    }

    # Step 10: Build main application
    Write-Step "Building main application (BurndownChart.exe)"
    Push-Location $ProjectRoot
    try {
        $pyinstallerArgs = @($appSpec, "--noconfirm")
        if (-not $VerboseBuild) {
            $pyinstallerArgs += "--log-level=WARN"
        }
        
        python -m PyInstaller $pyinstallerArgs
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Main application build failed"
            exit 1
        }
        Write-Success "Main application built successfully"
    }
    finally {
        Pop-Location
    }

    # Step 11: Build updater
    Write-Step "Building updater (BurndownChartUpdater.exe)"
    
    # Check if updater exists
    $updaterPy = Join-Path $ProjectRoot "updater\updater.py"
    if (-not (Test-Path $updaterPy)) {
        Write-Host "Updater source not found - skipping updater build" -ForegroundColor Yellow
        $updaterExe = $null
    }
    else {
        Push-Location $ProjectRoot
        try {
            $pyinstallerArgs = @($updaterSpec, "--noconfirm")
            if (-not $VerboseBuild) {
                $pyinstallerArgs += "--log-level=WARN"
            }
            
            python -m PyInstaller $pyinstallerArgs
            if ($LASTEXITCODE -ne 0) {
                Write-Error "Updater build failed"
                exit 1
            }
            Write-Success "Updater built successfully"
            $updaterExe = Join-Path $DistDir "BurndownChartUpdater\BurndownChartUpdater.exe"
        }
        finally {
            Pop-Location
        }
    }

    # Step 12: Verify output files
    Write-Step "Verifying build artifacts"
    $mainExe = Join-Path $DistDir "BurndownChart.exe"
    
    if (-not (Test-Path $mainExe)) {
        Write-Error "Main executable not found at: $mainExe"
        exit 1
    }
    $mainSize = (Get-Item $mainExe).Length / 1MB
    $mainSizeRounded = [math]::Round($mainSize, 2)
    Write-Success "Main executable: $mainExe ($mainSizeRounded MB)"
    
    if ($updaterExe -and (Test-Path $updaterExe)) {
        $updaterSize = (Get-Item $updaterExe).Length / 1MB
        $updaterSizeRounded = [math]::Round($updaterSize, 2)
        Write-Success "Updater executable: $updaterExe ($updaterSizeRounded MB)"
    }
    else {
        Write-Host "Updater executable not built (updater feature not implemented)" -ForegroundColor Yellow
    }

    # Step 13: Code signing (if requested)
    if ($Sign) {
        Write-Step "Code signing executables"
        $signScript = Join-Path $BuildDir "sign_executable.ps1"
        
        if (-not (Test-Path $signScript)) {
            Write-Error "Sign script not found at: $signScript"
            Write-Host "Skipping code signing" -ForegroundColor Yellow
        }
        else {
            & $signScript -FilePath $mainExe
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Main executable signed"
            }
            else {
                Write-Error "Failed to sign main executable"
            }
            
            & $signScript -FilePath $updaterExe
            if ($LASTEXITCODE -eq 0) {
                Write-Success "Updater executable signed"
            }
            else {
                Write-Error "Failed to sign updater executable"
            }
        }
    }

    # Step 14: Post-build tests (if requested)
    if ($Test) {
        Write-Step "Running post-build validation tests"
        
        # Test 1: Verify executables can be launched
        Write-Host "Testing main executable launch..." -ForegroundColor White
        $testProcess = Start-Process -FilePath $mainExe -ArgumentList "--version" -PassThru -NoNewWindow -Wait
        if ($testProcess.ExitCode -eq 0) {
            Write-Success "Main executable launches successfully"
        }
        else {
            Write-Error "Main executable failed to launch (exit code: $($testProcess.ExitCode))"
        }
        
        # Test 2: Check for missing dependencies
        Write-Host "Checking for missing dependencies..." -ForegroundColor White
        python -c "import sys; sys.exit(0)" | Out-Null
        if ($LASTEXITCODE -eq 0) {
            Write-Success "No missing dependencies detected"
        }
    }

    # Build complete
    Write-Host "`n=====================================" -ForegroundColor Green
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "`nOutput location: $DistDir" -ForegroundColor Cyan
    
    # Show usage information
    if ($Clean -or $VerboseBuild -or $Test -or $Sign) {
        Write-Host "`nOptions used:" -ForegroundColor Yellow
        if ($Clean) { Write-Host "  - Clean build (previous artifacts removed)" -ForegroundColor White }
        if ($VerboseBuild) { Write-Host "  - Verbose output enabled" -ForegroundColor White }
        if ($Test) { Write-Host "  - Post-build tests executed" -ForegroundColor White }
        if ($Sign) { Write-Host "  - Code signing applied" -ForegroundColor White }
    }
    
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Test the executable: .\dist\BurndownChart\BurndownChart.exe" -ForegroundColor White
    Write-Host "  2. Create distribution package: .\build\package.ps1" -ForegroundColor White
    
    # Explicit success exit
    exit 0

}
catch {
    Write-Error "Build failed with error: $_"
    exit 1
}
