# install.ps1 — Conductor installer for Windows
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
