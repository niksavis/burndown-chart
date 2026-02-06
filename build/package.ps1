# Package Script for Burndown Application
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

function Copy-SharedAssets {
    param([string]$TargetDir)

    # Copy THIRD_PARTY_LICENSES.txt (bundled in executable, also in ZIP for transparency)
    # Note: Detailed licenses/ folder is bundled in executable and accessible via About dialog
    $thirdPartyLicenses = Join-Path $ProjectRoot "licenses\THIRD_PARTY_LICENSES.txt"
    if (Test-Path $thirdPartyLicenses) {
        Copy-Item -Path $thirdPartyLicenses -Destination $TargetDir
        Write-Success "Copied THIRD_PARTY_LICENSES.txt"
    }
    else {
        Write-Host "[WARN] THIRD_PARTY_LICENSES.txt not found, skipping" -ForegroundColor Yellow
    }

    # Copy README.txt (Windows quick start guide)
    $readmeTxtSource = Join-Path $BuildDir "README.txt"
    if (Test-Path $readmeTxtSource) {
        Copy-Item -Path $readmeTxtSource -Destination $TargetDir
        Write-Success "Copied README.txt (quick start guide)"
    }
    else {
        Write-Host "[WARN] README.txt not found, skipping" -ForegroundColor Yellow
    }

    # Copy LICENSE as LICENSE.txt (Windows convention, matches app extraction)
    $licenseSource = Join-Path $ProjectRoot "LICENSE"
    if (Test-Path $licenseSource) {
        Copy-Item -Path $licenseSource -Destination (Join-Path $TargetDir "LICENSE.txt")
        Write-Success "Copied LICENSE as LICENSE.txt"
    }
}

function Write-Checksums {
    param(
        [string]$TargetDir,
        [string[]]$FileNames
    )

    $checksumPath = Join-Path $TargetDir "BURNDOWN_CHECKSUMS.txt"
    $lines = @()

    foreach ($name in $FileNames) {
        $filePath = Join-Path $TargetDir $name
        if (-not (Test-Path $filePath)) {
            Write-Host "[WARN] Checksum target not found: $name" -ForegroundColor Yellow
            continue
        }

        $hash = (Get-FileHash -Path $filePath -Algorithm SHA256).Hash.ToLower()
        $lines += "$hash  $name"
    }

    if ($lines.Count -eq 0) {
        Write-Host "[WARN] No checksum entries written" -ForegroundColor Yellow
        return
    }

    $lines | Set-Content -Path $checksumPath -Encoding ASCII
    Write-Success "Wrote checksums to BURNDOWN_CHECKSUMS.txt"
}

# Main packaging process
try {
    Write-Host "`nBurndown - Package Script" -ForegroundColor Yellow
    Write-Host "================================`n" -ForegroundColor Yellow

    # Step 1: Verify build artifacts exist
    Write-Step "Verifying build artifacts"
    $mainExe = Join-Path $DistDir "Burndown.exe"
    $updaterExe = Join-Path $DistDir "BurndownUpdater.exe"
    
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

    # Step 3: Create package staging directories
    Write-Step "Creating package staging directories"
    $stagingNewDir = Join-Path $DistDir "staging_new"
    $stagingLegacyDir = Join-Path $DistDir "staging_legacy"
    foreach ($dir in @($stagingNewDir, $stagingLegacyDir)) {
        if (Test-Path $dir) {
            Remove-Item -Path $dir -Recurse -Force
        }
        New-Item -ItemType Directory -Path $dir | Out-Null
    }
    Write-Success "Created staging directories"

    # Step 4: Copy files to staging (new)
    Write-Step "Copying files to staging (new)"
    Copy-Item -Path $mainExe -Destination $stagingNewDir
    Write-Success "Copied main application"
    if ($updaterExe) {
        Copy-Item -Path $updaterExe -Destination $stagingNewDir
        Write-Success "Copied updater"
    }
    Copy-SharedAssets -TargetDir $stagingNewDir
    $checksumFilesNew = @("Burndown.exe", "LICENSE.txt", "README.txt", "THIRD_PARTY_LICENSES.txt")
    if ($updaterExe) {
        $checksumFilesNew += "BurndownUpdater.exe"
    }
    Write-Checksums -TargetDir $stagingNewDir -FileNames $checksumFilesNew

    # Step 4b: Copy files to staging (legacy)
    Write-Step "Copying files to staging (legacy)"
    Copy-Item -Path $mainExe -Destination (Join-Path $stagingLegacyDir "BurndownChart.exe")
    Write-Success "Copied legacy main executable name"
    if ($updaterExe) {
        Copy-Item -Path $updaterExe -Destination (Join-Path $stagingLegacyDir "BurndownChartUpdater.exe")
        Write-Success "Copied legacy updater executable name"
    }
    Copy-SharedAssets -TargetDir $stagingLegacyDir
    $checksumFilesLegacy = @("BurndownChart.exe", "LICENSE.txt", "README.txt", "THIRD_PARTY_LICENSES.txt")
    if ($updaterExe) {
        $checksumFilesLegacy += "BurndownChartUpdater.exe"
    }
    Write-Checksums -TargetDir $stagingLegacyDir -FileNames $checksumFilesLegacy

    # Step 5: Create ZIP files
    Write-Step "Creating distribution packages"
    $zipName = "Burndown-Windows-$Version.zip"
    $zipPath = Join-Path $DistDir $zipName
    $legacyZipName = "BurndownChart-Windows-$Version.zip"
    $legacyZipPath = Join-Path $DistDir $legacyZipName

    foreach ($path in @($zipPath, $legacyZipPath)) {
        if (Test-Path $path) {
            Remove-Item -Path $path -Force
            Write-Success "Removed existing ZIP: $path"
        }
    }

    Compress-Archive -Path "$stagingNewDir\*" -DestinationPath $zipPath -CompressionLevel Optimal
    Write-Success "Created ZIP package: $zipName"

    Compress-Archive -Path "$stagingLegacyDir\*" -DestinationPath $legacyZipPath -CompressionLevel Optimal
    Write-Success "Created ZIP package: $legacyZipName"

    # Step 6: Verify packages
    Write-Step "Verifying packages"
    foreach ($path in @($zipPath, $legacyZipPath)) {
        if (-not (Test-Path $path)) {
            Write-Error "Package not created at: $path"
            exit 1
        }
        $zipSize = (Get-Item $path).Length / 1MB
        Write-Success "Package: $path ($([math]::Round($zipSize, 2)) MB)"

        $verifyDir = Join-Path $env:TEMP ("burndown-verify-" + [IO.Path]::GetFileNameWithoutExtension($path))
        Write-Host "`nPackage contents ($path):" -ForegroundColor White
        Expand-Archive -Path $path -DestinationPath $verifyDir -Force | Out-Null
        Get-ChildItem -Path $verifyDir -Recurse -File | ForEach-Object {
            $relativePath = $_.FullName.Replace("$verifyDir\", "")
            Write-Host "  - $relativePath" -ForegroundColor Gray
        }
        Remove-Item -Path $verifyDir -Recurse -Force
    }

    # Step 7: Cleanup staging
    Write-Step "Cleaning up staging directories"
    Remove-Item -Path $stagingNewDir -Recurse -Force
    Remove-Item -Path $stagingLegacyDir -Recurse -Force
    Write-Success "Staging cleaned"

    # Package complete
    Write-Host "`n=====================================" -ForegroundColor Green
    Write-Host "Packages created successfully!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "`nPackage locations:" -ForegroundColor Cyan
    Write-Host "  - $zipPath" -ForegroundColor Cyan
    Write-Host "  - $legacyZipPath" -ForegroundColor Cyan
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
