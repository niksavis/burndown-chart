# Workflow Tools Installation

Installation guide for Spec-Kit and Beads - the core tools for our development workflow.

---

## Prerequisites

Before installing these tools, ensure you have:

- **Windows 10/11** (workflow tested on Windows)
- **PowerShell 5.1+** (included with Windows)
- **Git** (for version control)
- **VS Code** with GitHub Copilot (for agent workflows)
- **Python 3.13+** (for project development and workflow scripts)

---

## 1. Beads Installation

**Beads**: CLI issue tracker with git integration  
**Repository**: [github.com/steveyegge/beads](https://github.com/steveyegge/beads)  
**Latest Release**: [v0.47.1](https://github.com/steveyegge/beads/releases/tag/v0.47.1)

### Installation Steps (No Admin Rights Required)

1. **Download Binary**:
   - Go to [Beads Releases](https://github.com/steveyegge/beads/releases/tag/v0.47.1)
   - Under **Assets**, download the appropriate archive:
     - Windows: `beads_0.47.1_windows_amd64.zip`
     - Linux: `beads_0.47.1_linux_amd64.tar.gz`
     - macOS: `beads_0.47.1_darwin_amd64.tar.gz`

2. **Extract and Setup PATH** (Windows):
   ```powershell
   # Create tools directory and extract
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\Tools\bd"
   
   # Extract beads_0.47.1_windows_amd64.zip to $env:USERPROFILE\Tools\bd\
   # (Contains bd.exe)
   
   # Add to PATH (permanent)
   setx PATH "$env:PATH;$env:USERPROFILE\Tools\bd"
   
   # Restart PowerShell for PATH to take effect
   ```

3. **Verify Installation**:
   ```powershell
   # Restart PowerShell or reload PATH, then:
   bd --version
   # Expected output: beads version 0.47.1
   ```

### Initialize Beads in Repository

```powershell
# Navigate to repository root
cd C:\Development\burndown-chart

# Initialize Beads
bd init --quiet

# Install git hooks (auto-sync between database and JSONL)
bd hooks install

# Verify setup
bd list  # Should show existing issues or empty list
```

**Files Created by `bd init`**:
- `.beads/config.yaml` - Repository configuration
- `.beads/issues.jsonl` - Issue database (JSON Lines format)
- `.beads/interactions.jsonl` - Interaction log
- `.beads/.gitignore` - Ignore local files (db, daemon)
- `.gitattributes` - Merge strategy for issues.jsonl
- `beads.db` - SQLite cache (gitignored, local only)

---

## 2. Spec-Kit Installation

Spec-Kit is already integrated in this repository at `.specify/` and `.github/agents/`.

**Repository**: [github.com/github/spec-kit](https://github.com/github/spec-kit)  
**Latest Release**: [v0.0.90](https://github.com/github/spec-kit/releases/tag/v0.0.90)

### Option A: Installation via uv (Recommended)

**Prerequisites**: Install `uv` package manager first

```powershell
# Install uv using winget (or other package manager)
winget install astral-sh.uv

# Install spec-kit globally
uv tool install speckit

# Verify installation
speckit --version
# Expected output: speckit 0.0.90
```

### Option B: Manual Installation from Release

1. **Download Release Assets**:
   - Go to [Spec-Kit v0.0.90 Release](https://github.com/github/spec-kit/releases/tag/v0.0.90)
   - Under **Assets**, download the appropriate archive:
     - Windows: `speckit-v0.0.90-windows-x86_64.zip`
     - Linux: `speckit-v0.0.90-linux-x86_64.tar.gz`
     - macOS: `speckit-v0.0.90-darwin-x86_64.tar.gz`

2. **Extract and Setup PATH**:
   ```powershell
   # Create tools directory and extract
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\Tools\speckit"
   
   # Extract speckit-v0.0.90-windows-x86_64.zip to $env:USERPROFILE\Tools\speckit\
   # (Contains speckit.exe)
   
   # Add to PATH (permanent)
   setx PATH "$env:PATH;$env:USERPROFILE\Tools\speckit"
   
   # Restart PowerShell for PATH to take effect
   ```

3. **Verify Installation**:
   ```powershell
   # Restart PowerShell or reload PATH, then:
   speckit --version
   # Expected output: speckit 0.0.90
   ```

### Using Spec-Kit Agents in VS Code

**Prerequisites**: GitHub Copilot extension installed in VS Code

1. Open VS Code in repository with `.github/agents/` directory
2. Open Chat panel (`Ctrl+Alt+I` or `Cmd+Alt+I`)
3. Type `@` to see available agents
4. Use spec-kit agents:
   - `@speckit.plan <description>` - Run planning workflow (creates research.md, plan.md, etc.)
   - `@speckit.tasks` - Generate task breakdown (creates tasks.md)
   - `@speckit.implement` - Start implementation in phases
   - `@speckit.analyze` - Run consistency analysis

**Verify Agents Available**:
```powershell
# Check agent files exist
Get-ChildItem .github\agents\*.agent.md
# Should show: speckit.plan.agent.md, speckit.tasks.agent.md, etc.

# Test in VS Code Chat:
# 1. Open Chat (Ctrl+Alt+I)
# 2. Type @ and look for speckit.plan, speckit.tasks, etc.
```

### Configure Merge Strategy for Beads

**Already configured** in repository via `.gitattributes`:
```
.beads/issues.jsonl merge=union
```

If missing, add manually:
```powershell
echo ".beads/issues.jsonl merge=union" >> .gitattributes
git add .gitattributes
git commit -m "chore: configure Beads merge strategy"
```

---

## 3. Workflow Script Setup

### Install Conversion Script

Already included in repository at `workflow/tasks_to_beads.py`.

**Verify**:
```powershell
.\.venv\Scripts\activate; python workflow/tasks_to_beads.py --help
```

**Test**:
```powershell
.\.venv\Scripts\activate; python workflow/tasks_to_beads.py specs/016-standalone-packaging/tasks.md test_output.jsonl
```

---

## 4. Verification Checklist

Run these commands to verify complete setup:

```powershell
# Python
python --version  # Should show 3.13+

# Pip packages
pip list | Select-String "dash|plotly|pandas"  # Core dependencies

# Beads
bd --version  # Should show beads version
bd list       # Should show issues (or empty)

# Spec-Kit
.\.specify\scripts\powershell\check-prerequisites.ps1  # Should output JSON

# Git
git --version  # Should show git version
git config user.name  # Should show your name

# VS Code
code --version  # Should show VS Code version
code --list-extensions | Select-String "copilot"  # Should show GitHub.copilot
```

**Expected Results**:
```
Python 3.13.1
dash 3.1.1
beads version 0.47.1
Git 2.43.0
VS Code 1.85.0
GitHub.copilot
GitHub.copilot-chat
```

---

## 5. Troubleshooting

### Beads Not Found

**Error**: `bd : The term 'bd' is not recognized`

**Fix**:
1. Verify beads.exe exists in your tools folder
2. Check PATH variable:
   ```powershell
   $env:Path -split ';' | Select-String "beads"
   ```
3. If missing, add to PATH:
   ```powershell
   $toolsDir = "$env:USERPROFILE\Tools\beads"
   [Environment]::SetEnvironmentVariable("Path", 
       [Environment]::GetEnvironmentVariable("Path", "User") + ";$toolsDir", "User")
   ```
4. Restart PowerShell (or reload: `$env:Path = [Environment]::GetEnvironmentVariable("Path", "User")`)

### Spec-Kit Command Not Found

**Error**: `bd : The term 'bd' is not recognized`

**Fix**:
1. Verify `bd.exe` exists in your tools folder:
   ```powershell
   Test-Path "$env:USERPROFILE\Tools\bd\bd.exe"
   ```

2. Check if folder is in PATH:
   ```powershell
   $env:Path -split ';' | Select-String "bd"
   ```

3. If missing, add to PATH:
   ```powershell
   setx PATH "$env:PATH;$env:USERPROFILE\Tools\bd"
   # Restart PowerShell
   $env:Path = [Environment]::GetEnvironmentVariable("Path", "User")
   ```

### Spec-Kit Command Not Found

**Error**: `speckit : The term 'speckit' is not recognized`

**Fix (if installed via uv)**:
```powershell
# Check uv tool path
uv tool list

# Ensure uv tools are in PATH
$uvToolsPath = "$env:USERPROFILE\.local\bin"
[Environment]::SetEnvironmentVariable("Path", 
    [Environment]::GetEnvironmentVariable("Path", "User") + ";$uvToolsPath", "User")
```

**Fix (if manual installation)**:
```powershell
# Verify speckit.exe location
Test-Path "$env:USERPROFILE\Tools\speckit\speckit.exe"

# Add to PATH
setx PATH "$env:PATH;$env:USERPROFILE\Tools\speckit"
# Restart PowerShell
```

### GitHub Copilot Agents Not Showing

**Error**: Agents not appearing in VS Code chat panel

**Fix**:
1. Verify agent files exist:
   ```powershell
   Get-ChildItem .github\agents\*.prompt.md
   ```

2. Reload VS Code window: `Ctrl+Shift+P` → "Developer: Reload Window"

3. Ensure GitHub Copilot extension is installed and active

4. Check repository has `.github/agents/` directory at root level

### Git Merge Conflicts in Beads

**Error**: Conflicts in `.beads/issues.jsonl`

**Fix**:
```powershell
# Let Beads handle 3-way merge automatically
bd sync

# Verify issues are intact
bd list
```

---

## 6. Offline Installation

For systems without internet access:

1. **On connected machine**, download:
   - [Beads v0.47.1 release](https://github.com/steveyegge/beads/releases/tag/v0.47.1) → `beads_0.47.1_windows_amd64.zip`
   - [Spec-Kit v0.0.90 release](https://github.com/github/spec-kit/releases/tag/v0.0.90) → `speckit-v0.0.90-windows-x86_64.zip`

2. **Transfer** archives to offline machine (USB drive, network share)

3. **Install** on offline machine:
   ```powershell
   # Extract Beads
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\Tools\bd"
   # Extract beads_0.47.1_windows_amd64.zip → bd.exe to $env:USERPROFILE\Tools\bd
   
   # Extract Spec-Kit
   New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\Tools\speckit"
   # Extract speckit-v0.0.90-windows-x86_64.zip → speckit.exe to $env:USERPROFILE\Tools\speckit
   
   # Add both to PATH
   setx PATH "$env:PATH;$env:USERPROFILE\Tools\bd;$env:USERPROFILE\Tools\speckit"
   # Restart PowerShell
   ```

---

## 7. Updating Tools

### Update Beads

```powershell
# Download latest release from GitHub
# https://github.com/steveyegge/beads/releases

# Extract to same location, overwriting bd.exe
# Verify new version
bd --version
```

### Update Spec-Kit

**Via uv**:
```powershell
uv tool upgrade speckit
```

**Manual**:
```powershell
# Download latest release from GitHub
# https://github.com/github/spec-kit/releases

# Extract to same location, overwriting speckit.exe
# Verify new version
speckit --version
