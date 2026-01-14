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
$licenseOutput = & pip-licenses --format=plain-vertical --with-urls --with-description

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

# Count dependencies
$depCount = ($licenseOutput | Select-String "^Name:" | Measure-Object).Count
Write-Host "Total dependencies: $depCount" -ForegroundColor Cyan

if ($Verbose) {
    Write-Host "`nLicense summary:" -ForegroundColor Yellow
    & pip-licenses --summary
}
