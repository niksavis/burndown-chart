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
$BuildDir = Join-Path $ProjectRoot "build"

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
    $mainExe = Join-Path $DistDir "BurndownChart.exe"
    $updaterExe = Join-Path $DistDir "BurndownChartUpdater.exe"
    
    if (-not (Test-Path $mainExe)) {
        Write-Error "Main application not found at: $mainExe"
        Write-Host "Please run: .\build\build.ps1" -ForegroundColor Yellow
        exit 1
    }
    $mainSize = (Get-Item $mainExe).Length / 1MB
    Write-Success "Found main application ($([math]::Round($mainSize, 2)) MB)"
    
    if (-not (Test-Path $updaterExe)) {
        Write-Host "[WARN] Updater not found at: $updaterExe" -ForegroundColor Yellow
        Write-Host "[WARN] Proceeding without updater" -ForegroundColor Yellow
        $updaterExe = $null
    }
    else {
        $updaterSize = (Get-Item $updaterExe).Length / 1MB
        Write-Success "Found updater ($([math]::Round($updaterSize, 2)) MB)"
    }

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
    Copy-Item -Path $mainExe -Destination $stagingDir
    Write-Success "Copied main application"
    
    # Copy updater if exists
    if ($updaterExe) {
        Copy-Item -Path $updaterExe -Destination $stagingDir
        Write-Success "Copied updater"
    }
    
    # Copy THIRD_PARTY_LICENSES.txt (bundled in executable, also in ZIP for transparency)
    # Note: Detailed licenses/ folder is bundled in executable and accessible via About dialog
    $thirdPartyLicenses = Join-Path $ProjectRoot "licenses\THIRD_PARTY_LICENSES.txt"
    if (Test-Path $thirdPartyLicenses) {
        Copy-Item -Path $thirdPartyLicenses -Destination $stagingDir
        Write-Success "Copied THIRD_PARTY_LICENSES.txt"
    }
    else {
        Write-Host "[WARN] THIRD_PARTY_LICENSES.txt not found, skipping" -ForegroundColor Yellow
    }
    
    # Copy README if exists
    $readmeSource = Join-Path $ProjectRoot "readme.md"
    if (Test-Path $readmeSource) {
        Copy-Item -Path $readmeSource -Destination (Join-Path $stagingDir "README.md")
        Write-Success "Copied README"
    }
    
    # Copy README.txt (Windows quick start guide) if exists
    $readmeTxtSource = Join-Path $BuildDir "README.txt"
    if (Test-Path $readmeTxtSource) {
        Copy-Item -Path $readmeTxtSource -Destination $stagingDir
        Write-Success "Copied README.txt (quick start guide)"
    }
    
    # Copy LICENSE as LICENSE.txt (Windows convention, matches app extraction)
    $licenseSource = Join-Path $ProjectRoot "LICENSE"
    if (Test-Path $licenseSource) {
        Copy-Item -Path $licenseSource -Destination (Join-Path $stagingDir "LICENSE.txt")
        Write-Success "Copied LICENSE as LICENSE.txt"
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
    
    # Explicit success exit
    exit 0

}
catch {
    Write-Error "Packaging failed with error: $_"
    exit 1
}
