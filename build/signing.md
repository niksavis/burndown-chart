# Code Signing Script

## Overview

`sign_executable.ps1` signs Windows executables with a code signing certificate. This is an optional step in the build process and is only used when the `-Sign` flag is provided to `build.ps1`.

## Prerequisites

- **Windows SDK** - Required for `signtool.exe`
  - Download: https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/
  - Only install "Signing Tools for Desktop Apps" component (~few MB vs several GB full install)
- **Code Signing Certificate** - Either:
  - Certificate installed in Windows certificate store (Current User or Local Machine)
  - `.pfx` certificate file with password

### Recommended: Add Version Information

For professional signed executables, include version information in the PyInstaller spec file:

```python
# Create a version.txt file with Windows version resource info
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(2, 5, 0, 0),
    prodvers=(2, 5, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x4,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(u'040904B0', [
        StringStruct(u'CompanyName', u'Your Company'),
        StringStruct(u'FileDescription', u'Burndown Application'),
        StringStruct(u'FileVersion', u'2.5.0'),
        StringStruct(u'InternalName', u'Burndown'),
        StringStruct(u'LegalCopyright', u'Copyright (c) 2026'),
        StringStruct(u'OriginalFilename', u'Burndown.exe'),
        StringStruct(u'ProductName', u'Burndown'),
        StringStruct(u'ProductVersion', u'2.5.0')
      ])
    ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)

# Then in app.spec EXE() section:
exe = EXE(
    ...
    name='Burndown',
    version='version.txt',  # Add this line
    ...
)
```

Version information is visible in Windows Explorer file properties and helps with code signing trust.

## Usage

### Auto-detect certificate from store
```powershell
.\build\sign_executable.ps1 -FilePath "dist\Burndown.exe"
```

### Specify certificate by thumbprint
```powershell
.\build\sign_executable.ps1 -FilePath "dist\Burndown.exe" -CertificateThumbprint "ABC123..."
```

### Use .pfx certificate file
```powershell
$password = Read-Host -AsSecureString -Prompt "Certificate password"
.\build\sign_executable.ps1 -FilePath "dist\Burndown.exe" -CertificatePath "path\to\cert.pfx" -CertificatePassword $password
```

### Custom timestamp server
```powershell
.\build\sign_executable.ps1 -FilePath "dist\Burndown.exe" -TimestampServer "http://timestamp.comodoca.com"
```

## Build Integration

The script is automatically called by `build.ps1` when the `-Sign` flag is used:

```powershell
.\build\build.ps1 -Clean -Sign
```

## Certificate Requirements

- **Type**: Code Signing Certificate
- **Key Usage**: Code Signing
- **Validity**: Must not be expired
- **Algorithm**: SHA256 (script uses SHA256 for both signing and timestamping)

## Timestamp Servers

Default: `http://timestamp.digicert.com`

Alternative servers:
- `http://timestamp.comodoca.com`
- `http://timestamp.sectigo.com`
- `http://timestamp.globalsign.com`

Timestamping ensures the signature remains valid even after the certificate expires.

## Troubleshooting

### signtool.exe not found
Install Windows SDK from Microsoft's website. The script searches common installation paths automatically.

### Certificate not found
- Check certificate is installed in `Cert:\CurrentUser\My` or `Cert:\LocalMachine\My`
- Verify certificate has Code Signing key usage
- Ensure certificate is not expired

### Signature verification failed
- Check certificate chain is trusted
- Verify timestamp server is accessible
- Ensure executable is not corrupted

## Security Notes

- Certificate passwords are handled as `SecureString` to prevent exposure
- Plain text passwords are only in memory temporarily during signing
- Never commit certificates or passwords to version control
- Consider using Azure Key Vault or similar for production signing
