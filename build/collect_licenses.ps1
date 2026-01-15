# Collect Third-Party Licenses Script
# Generates THIRD_PARTY_LICENSES.txt from installed packages using pip-licenses

param(
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"

Write-Host "Collecting third-party licenses..." -ForegroundColor Cyan

# Ensure virtual environment is activated
if (-not $env:VIRTUAL_ENV) {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "$PSScriptRoot\..\\.venv\Scripts\Activate.ps1"
}

# Ensure licenses directory exists
$licensesDir = "$PSScriptRoot\..\\licenses"
if (-not (Test-Path $licensesDir)) {
    New-Item -ItemType Directory -Path $licensesDir -Force | Out-Null
}

# Output file path
$outputFile = "$licensesDir\THIRD_PARTY_LICENSES.txt"

Write-Host "Generating license report..." -ForegroundColor Yellow

# Run pip-licenses to generate the report
# Format: Table with columns: Name, Version, License
$pipLicensesPath = Join-Path $env:VIRTUAL_ENV "Scripts\pip-licenses.exe"
if (-not (Test-Path $pipLicensesPath)) {
    Write-Error "pip-licenses not found at $pipLicensesPath"
    exit 1
}

$licenseOutput = & $pipLicensesPath --format=plain-vertical --with-urls --with-description

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to generate license report"
    exit 1
}

# Write header to output file
$header = @"
===============================================================================
THIRD-PARTY SOFTWARE LICENSES
===============================================================================

This file contains the licenses of all third-party dependencies bundled with
the Burndown Chart application.

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

===============================================================================

"@

$header | Out-File -FilePath $outputFile -Encoding UTF8
$licenseOutput | Out-File -FilePath $outputFile -Encoding UTF8 -Append

Write-Host "License report generated successfully!" -ForegroundColor Green
Write-Host "Output: $outputFile" -ForegroundColor Cyan

# Count dependencies (plain-vertical format has 3 lines per package + blank line)
$lines = $licenseOutput | Where-Object { $_.Trim() -ne "" }
$depCount = [Math]::Floor($lines.Count / 3)
Write-Host "Total dependencies: $depCount" -ForegroundColor Cyan

# Generate NOTICE.txt for Apache 2.0 attribution
Write-Host "Generating NOTICE.txt for Apache 2.0 attribution..." -ForegroundColor Yellow
$noticeFile = "$licensesDir\NOTICE.txt"
$noticeContent = @"
NOTICE

This product includes software developed with components licensed under the Apache License 2.0.

The following dependencies require attribution under Apache License 2.0:

- coverage
- dash-bootstrap-components
- diskcache
- packaging (also BSD)
- playwright
- requests

For full license texts of all dependencies, see THIRD_PARTY_LICENSES.txt

Apache License 2.0: https://www.apache.org/licenses/LICENSE-2.0
"@

$noticeContent | Out-File -FilePath $noticeFile -Encoding UTF8
Write-Host "NOTICE.txt generated" -ForegroundColor Green

if ($Verbose) {
    Write-Host "`nLicense summary:" -ForegroundColor Yellow
    & $pipLicensesPath --summary
}
