# AGY Custom Statusline One-Line Installer for Windows (PowerShell)
# Usage: irm https://raw.githubusercontent.com/NguyenQuocTruong/agy-statusline/main/install.ps1 | iex
$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "    AGY Custom Statusline Installer       " -ForegroundColor Cyan
Write-Host "             (Windows)                    " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Check Python
$pythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $pythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $pythonCmd = "py -3"
} elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
    $pythonCmd = "python3"
}

if (-not $pythonCmd) {
    Write-Error "[-] Error: Python is required but not found in PATH. Please install Python from https://python.org or Microsoft Store."
    exit 1
}

$pyVersion = & $pythonCmd --version
Write-Host "[+] Python detected: $pyVersion" -ForegroundColor Green

# 2. Setup paths
$targetDir = Join-Path $env:USERPROFILE ".config\agy-statusline"
$settingsDir = Join-Path $env:USERPROFILE ".gemini\antigravity-cli"
$settingsFile = Join-Path $settingsDir "settings.json"

# 3. Download and extract repository
Write-Host "[+] Downloading latest release from GitHub..." -ForegroundColor Yellow
$tempZip = Join-Path $env:TEMP "agy-statusline-main.zip"
$tempExtract = Join-Path $env:TEMP "agy-statusline-temp"

if (Test-Path $tempExtract) { Remove-Item -Recurse -Force $tempExtract }
New-Item -ItemType Directory -Force -Path $tempExtract | Out-Null

$zipUrl = "https://github.com/NguyenQuocTruong/agy-statusline/archive/refs/heads/main.zip"
Invoke-WebRequest -Uri $zipUrl -OutFile $tempZip -UseBasicParsing

Expand-Archive -Path $tempZip -DestinationPath $tempExtract -Force
$sourceDir = Join-Path $tempExtract "agy-statusline-main"

# 4. Copy files to target directory
Write-Host "[+] Installing files to $targetDir..." -ForegroundColor Yellow
if (-not (Test-Path $targetDir)) { New-Item -ItemType Directory -Force -Path $targetDir | Out-Null }
if (-not (Test-Path (Join-Path $targetDir "lib"))) { New-Item -ItemType Directory -Force -Path (Join-Path $targetDir "lib") | Out-Null }
if (-not (Test-Path (Join-Path $targetDir "tests"))) { New-Item -ItemType Directory -Force -Path (Join-Path $targetDir "tests") | Out-Null }

Copy-Item (Join-Path $sourceDir "statusline.py") (Join-Path $targetDir "statusline.py") -Force
Copy-Item (Join-Path $sourceDir "uninstall.sh") (Join-Path $targetDir "uninstall.sh") -Force
Copy-Item (Join-Path $sourceDir "lib\*") (Join-Path $targetDir "lib") -Recurse -Force
Copy-Item (Join-Path $sourceDir "tests\*") (Join-Path $targetDir "tests") -Recurse -Force

$userConfig = Join-Path $targetDir "config.json"
if (-not (Test-Path $userConfig)) {
    Copy-Item (Join-Path $sourceDir "config.json") $userConfig -Force
}

# Cleanup temp files
Remove-Item -Force $tempZip -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force $tempExtract -ErrorAction SilentlyContinue

# 5. Configure AGY settings.json
Write-Host "[+] Configuring AGY settings.json..." -ForegroundColor Yellow
if (-not (Test-Path $settingsDir)) { New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null }

$scriptPath = (Join-Path $targetDir "statusline.py") -replace '\\', '/'

$pyConfigScript = @"
import json, os, sys, time

settings_path = os.path.expanduser('~/.gemini/antigravity-cli/settings.json')
cmd_path = os.path.expanduser('~/.config/agy-statusline/statusline.py')

if os.path.isfile(settings_path):
    try:
        backup_path = f'{settings_path}.backup.{int(time.time())}'
        with open(settings_path, 'r', encoding='utf-8') as f:
            content = f.read()
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'[+] Backed up existing settings to {backup_path}')
        data = json.loads(content)
    except Exception as e:
        print(f'[-] Warning parsing settings: {e}')
        data = {}
else:
    data = {}

data['statusLine'] = {
    'type': 'command',
    'command': f'python \"{cmd_path}\"',
    'enabled': True
}

with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print('[+] Successfully registered custom statusline in settings.json')
"@

& $pythonCmd -c $pyConfigScript

# 6. Verify installation
Write-Host "[+] Verifying statusline rendering..." -ForegroundColor Green
Write-Host "--------------------------------------------------"
& $pythonCmd (Join-Path $targetDir "statusline.py") --demo
Write-Host "--------------------------------------------------"
Write-Host "[✓] Installation complete! Launch 'agy' to enjoy your new statusline." -ForegroundColor Green
