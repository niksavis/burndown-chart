# Package Script for Burndown Chart Application
# Creates distribution ZIP file from built executables

[CmdletBinding()]
param(
    [string]$Version = ""  # Override version (default: read from configuration/__init__.py)
)

# Script configuration
$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
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

# Main packaging process
try {
    Write-Host "`nBurndown Chart - Package Script" -ForegroundColor Yellow
    Write-Host "================================`n" -ForegroundColor Yellow

    # Step 1: Verify build artifacts exist
    Write-Step "Verifying build artifacts"
    $mainExeDir = Join-Path $DistDir "BurndownChart"
    $updaterExeDir = Join-Path $DistDir "BurndownChartUpdater"
    
    if (-not (Test-Path $mainExeDir)) {
        Write-Error "Main application not found at: $mainExeDir"
        Write-Host "Please run: .\build\build.ps1" -ForegroundColor Yellow
        exit 1
    }
    Write-Success "Found main application"
    
    if (-not (Test-Path $updaterExeDir)) {
        Write-Error "Updater not found at: $updaterExeDir"
        Write-Host "Please run: .\build\build.ps1" -ForegroundColor Yellow
        exit 1
    }
    Write-Success "Found updater"

    # Step 2: Determine version
    Write-Step "Determining version"
    if (-not $Version) {
        # Read version from configuration/__init__.py
        $configFile = Join-Path $ProjectRoot "configuration\__init__.py"
        if (Test-Path $configFile) {
            $versionLine = Select-String -Path $configFile -Pattern '__version__\s*=\s*[''"]([^''"]+)[''"]'
            if ($versionLine) {
                $Version = $versionLine.Matches.Groups[1].Value
                Write-Success "Version from configuration: $Version"
            }
            else {
                Write-Error "Could not parse version from $configFile"
                exit 1
            }
        }
        else {
            Write-Error "Configuration file not found: $configFile"
            exit 1
        }
    }
    else {
        Write-Success "Using specified version: $Version"
    }

    # Step 3: Create package staging directory
    Write-Step "Creating package staging directory"
    $stagingDir = Join-Path $DistDir "staging"
    if (Test-Path $stagingDir) {
        Remove-Item -Path $stagingDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $stagingDir | Out-Null
    Write-Success "Created staging directory"

    # Step 4: Copy files to staging
    Write-Step "Copying files to staging"
    
    # Copy main application
    $mainAppStaging = Join-Path $stagingDir "BurndownChart"
    Copy-Item -Path $mainExeDir -Destination $mainAppStaging -Recurse
    Write-Success "Copied main application"
    
    # Copy updater
    $updaterStaging = Join-Path $stagingDir "BurndownChartUpdater"
    Copy-Item -Path $updaterExeDir -Destination $updaterStaging -Recurse
    Write-Success "Copied updater"
    
    # Copy licenses directory
    $licensesSource = Join-Path $ProjectRoot "licenses"
    if (Test-Path $licensesSource) {
        $licensesStaging = Join-Path $stagingDir "licenses"
        Copy-Item -Path $licensesSource -Destination $licensesStaging -Recurse
        Write-Success "Copied licenses"
    }
    else {
        Write-Host "[WARN] Licenses directory not found, skipping" -ForegroundColor Yellow
    }
    
    # Copy README if exists
    $readmeSource = Join-Path $ProjectRoot "readme.md"
    if (Test-Path $readmeSource) {
        Copy-Item -Path $readmeSource -Destination (Join-Path $stagingDir "README.md")
        Write-Success "Copied README"
    }
    
    # Copy LICENSE if exists
    $licenseSource = Join-Path $ProjectRoot "LICENSE"
    if (Test-Path $licenseSource) {
        Copy-Item -Path $licenseSource -Destination $stagingDir
        Write-Success "Copied LICENSE"
    }

    # Step 5: Create ZIP file
    Write-Step "Creating distribution package"
    $zipName = "BurndownChart-Windows-$Version.zip"
    $zipPath = Join-Path $DistDir $zipName
    
    # Remove existing ZIP if present
    if (Test-Path $zipPath) {
        Remove-Item -Path $zipPath -Force
        Write-Success "Removed existing ZIP"
    }
    
    # Create ZIP archive
    Compress-Archive -Path "$stagingDir\*" -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Success "Created ZIP package"

    # Step 6: Verify package
    Write-Step "Verifying package"
    if (-not (Test-Path $zipPath)) {
        Write-Error "Package not created at: $zipPath"
        exit 1
    }
    
    $zipSize = (Get-Item $zipPath).Length / 1MB
    Write-Success "Package: $zipPath ($([math]::Round($zipSize, 2)) MB)"
    
    # List contents
    Write-Host "`nPackage contents:" -ForegroundColor White
    Expand-Archive -Path $zipPath -DestinationPath "$env:TEMP\burndown-verify" -Force | Out-Null
    Get-ChildItem -Path "$env:TEMP\burndown-verify" -Recurse -File | ForEach-Object {
        $relativePath = $_.FullName.Replace("$env:TEMP\burndown-verify\", "")
        Write-Host "  - $relativePath" -ForegroundColor Gray
    }
    Remove-Item -Path "$env:TEMP\burndown-verify" -Recurse -Force

    # Step 7: Cleanup staging
    Write-Step "Cleaning up staging directory"
    Remove-Item -Path $stagingDir -Recurse -Force
    Write-Success "Staging cleaned"

    # Package complete
    Write-Host "`n=====================================" -ForegroundColor Green
    Write-Host "Package created successfully!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "`nPackage location: $zipPath" -ForegroundColor Cyan
    Write-Host "Package size: $([math]::Round($zipSize, 2)) MB" -ForegroundColor Cyan
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "  1. Test the package on a clean system" -ForegroundColor White
    Write-Host "  2. Upload to release distribution server" -ForegroundColor White
    Write-Host "  3. Update version manifest for auto-update" -ForegroundColor White

}
catch {
    Write-Error "Packaging failed with error: $_"
    exit 1
}
