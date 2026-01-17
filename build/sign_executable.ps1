# Code Signing Script for Burndown Chart Executables
# Signs Windows executables with a code signing certificate

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath,              # Path to the executable to sign
    
    [string]$CertificateThumbprint, # Certificate thumbprint (optional, will search if not provided)
    [string]$CertificatePath,       # Path to .pfx certificate file (alternative to thumbprint)
    [Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSAvoidUsingPlainTextForPassword', '')]
    [SecureString]$CertificatePassword,   # Password for .pfx certificate (SecureString)
    [string]$TimestampServer = "http://timestamp.digicert.com"  # Timestamp server URL
)

$ErrorActionPreference = "Stop"

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

try {
    Write-Host "`nCode Signing Script" -ForegroundColor Yellow
    Write-Host "==================`n" -ForegroundColor Yellow

    # Step 1: Verify signtool.exe is available
    Write-Step "Verifying signtool.exe availability"
    
    $signTool = $null
    $possiblePaths = @(
        "${env:ProgramFiles(x86)}\Windows Kits\10\bin\*\x64\signtool.exe",
        "${env:ProgramFiles(x86)}\Windows Kits\8.1\bin\x64\signtool.exe",
        "${env:ProgramFiles}\Windows Kits\10\bin\*\x64\signtool.exe"
    )
    
    foreach ($path in $possiblePaths) {
        $found = Get-ChildItem -Path $path -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($found) {
            $signTool = $found.FullName
            break
        }
    }
    
    if (-not $signTool) {
        Write-Error "signtool.exe not found. Please install Windows SDK."
        Write-Host "Download from: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/" -ForegroundColor Yellow
        exit 1
    }
    
    Write-Success "Found signtool.exe at: $signTool"

    # Step 2: Verify target file exists
    Write-Step "Verifying target executable"
    
    if (-not (Test-Path $FilePath)) {
        Write-Error "File not found: $FilePath"
        exit 1
    }
    
    $fileInfo = Get-Item $FilePath
    Write-Success "Target: $($fileInfo.Name) ($([math]::Round($fileInfo.Length / 1MB, 2)) MB)"

    # Step 3: Determine certificate to use
    Write-Step "Locating code signing certificate"
    
    $certToUse = $null
    
    if ($CertificatePath) {
        # Using .pfx certificate file
        if (-not (Test-Path $CertificatePath)) {
            Write-Error "Certificate file not found: $CertificatePath"
            exit 1
        }
        
        if (-not $CertificatePassword) {
            Write-Error "Certificate password is required when using .pfx file"
            exit 1
        }
        
        Write-Success "Using certificate file: $CertificatePath"
        
        # Convert SecureString to plain text for signtool (required by signtool.exe)
        $BSTR = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($CertificatePassword)
        $plainPassword = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto($BSTR)
        [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($BSTR)
        
        # Build signtool arguments for .pfx certificate
        $signArgs = @(
            "sign",
            "/f", $CertificatePath,
            "/p", $plainPassword,
            "/tr", $TimestampServer,
            "/td", "SHA256",
            "/fd", "SHA256",
            "/v",
            $FilePath
        )
        
        # Clear password from memory
        $plainPassword = $null
    }
    elseif ($CertificateThumbprint) {
        # Using certificate from certificate store by thumbprint
        $cert = Get-ChildItem -Path Cert:\CurrentUser\My -Recurse | Where-Object { $_.Thumbprint -eq $CertificateThumbprint }
        
        if (-not $cert) {
            $cert = Get-ChildItem -Path Cert:\LocalMachine\My -Recurse | Where-Object { $_.Thumbprint -eq $CertificateThumbprint }
        }
        
        if (-not $cert) {
            Write-Error "Certificate with thumbprint $CertificateThumbprint not found in certificate store"
            exit 1
        }
        
        Write-Success "Using certificate: $($cert.Subject)"
        
        # Build signtool arguments for certificate store
        $signArgs = @(
            "sign",
            "/sha1", $CertificateThumbprint,
            "/tr", $TimestampServer,
            "/td", "SHA256",
            "/fd", "SHA256",
            "/v",
            $FilePath
        )
    }
    else {
        # Search for code signing certificate in stores
        Write-Host "Searching for code signing certificates..." -ForegroundColor White
        
        $certs = @()
        $certs += Get-ChildItem -Path Cert:\CurrentUser\My -CodeSigningCert -ErrorAction SilentlyContinue
        $certs += Get-ChildItem -Path Cert:\LocalMachine\My -CodeSigningCert -ErrorAction SilentlyContinue
        
        $certs = $certs | Where-Object { $_.NotAfter -gt (Get-Date) } | Sort-Object NotAfter -Descending
        
        if ($certs.Count -eq 0) {
            Write-Error "No valid code signing certificates found in certificate store"
            Write-Host "Please provide a certificate using -CertificateThumbprint or -CertificatePath" -ForegroundColor Yellow
            exit 1
        }
        
        $certToUse = $certs[0]
        Write-Success "Using certificate: $($certToUse.Subject) (expires: $($certToUse.NotAfter.ToString('yyyy-MM-dd')))"
        
        # Build signtool arguments for auto-detected certificate
        $signArgs = @(
            "sign",
            "/sha1", $certToUse.Thumbprint,
            "/tr", $TimestampServer,
            "/td", "SHA256",
            "/fd", "SHA256",
            "/v",
            $FilePath
        )
    }

    # Step 4: Sign the executable
    Write-Step "Signing executable"
    
    Write-Host "Running: signtool.exe $($signArgs -join ' ')" -ForegroundColor Gray
    
    & $signTool $signArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Code signing failed with exit code: $LASTEXITCODE"
        exit $LASTEXITCODE
    }

    # Step 5: Verify signature
    Write-Step "Verifying signature"
    
    # Verify with signtool
    $verifyArgs = @("verify", "/pa", "/v", $FilePath)
    & $signTool $verifyArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Signature verification failed"
        exit $LASTEXITCODE
    }
    
    # Additional verification with PowerShell
    $authSig = Get-AuthenticodeSignature -FilePath $FilePath
    if ($authSig.Status -ne 'Valid') {
        Write-Host "Warning: Authenticode signature status: $($authSig.Status)" -ForegroundColor Yellow
        Write-Host "Signer: $($authSig.SignerCertificate.Subject)" -ForegroundColor Gray
    }
    else {
        Write-Success "Authenticode signature valid: $($authSig.SignerCertificate.Subject)"
    }

    # Success
    Write-Host "`n=====================================" -ForegroundColor Green
    Write-Host "Code signing completed successfully!" -ForegroundColor Green
    Write-Host "=====================================" -ForegroundColor Green
    Write-Host "`nSigned file: $FilePath" -ForegroundColor Cyan

}
catch {
    Write-Error "Code signing failed with error: $_"
    exit 1
}
