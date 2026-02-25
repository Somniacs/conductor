# conductor — Local orchestration for terminal sessions.
#
# Copyright (c) 2026 Max Rheiner / Somniacs AG
#
# Licensed under the MIT License. You may obtain a copy
# of the license at:
#
#     https://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND.

# Installer for Windows — sets up Python 3.10+, pipx, and conductor.
# Run: powershell -ExecutionPolicy Bypass -File install.ps1

$ErrorActionPreference = "Stop"

Write-Host "b conductor - install" -ForegroundColor Cyan
Write-Host ""

# Check Python
$pyCmd = $null
foreach ($cmd in @("py", "python3", "python")) {
    try {
        $ver = & $cmd --version 2>&1
        if ($ver -match "Python (\d+)\.(\d+)") {
            $major = [int]$Matches[1]
            $minor = [int]$Matches[2]
            if ($major -ge 3 -and $minor -ge 10) {
                $pyCmd = $cmd
                Write-Host "Python $major.$minor (via $cmd)" -NoNewline
                Write-Host " OK" -ForegroundColor Green
                break
            }
        }
    } catch {}
}

if (-not $pyCmd) {
    Write-Host "Error: Python 3.10+ is required but not found." -ForegroundColor Red
    Write-Host "Install from https://python.org (check 'Add to PATH' during install)"
    exit 1
}

# Install pipx if needed
$hasPipx = $false
try {
    & pipx --version 2>&1 | Out-Null
    $hasPipx = $true
} catch {}

if (-not $hasPipx) {
    Write-Host "Installing pipx..."
    & $pyCmd -m pip install --user pipx
    & $pyCmd -m pipx ensurepath
    # Refresh PATH for current session
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH", "User") + ";" + $env:PATH
}

Write-Host "pipx" -NoNewline
Write-Host " OK" -ForegroundColor Green

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Install conductor
Write-Host ""
Write-Host "Installing conductor..."
& pipx install -e $scriptDir --force

Write-Host ""
Write-Host "Done!" -ForegroundColor Green
Write-Host "Run 'conductor run claude research' to start."
Write-Host ""
Write-Host "If the command is not found, restart your terminal."
