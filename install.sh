#!/usr/bin/env bash
# AGY Custom Statusline One-Line Installer for Linux & macOS
# Supports both local clone and remote execution (curl -fsSL ... | bash)
set -euo pipefail

TARGET_DIR="${HOME}/.config/agy-statusline"
SETTINGS_DIR="${HOME}/.gemini/antigravity-cli"
SETTINGS_FILE="${SETTINGS_DIR}/settings.json"
REPO_NAME="truongnq/agy-statusline"
BRANCH="main"

echo "=========================================="
echo "    AGY Custom Statusline Installer       "
echo "        (Linux / macOS / Unix)            "
echo "=========================================="

# 1. Check Python 3
if ! command -v python3 >/dev/null 2>&1; then
    echo "[-] Error: python3 is required but not found in PATH." >&2
    echo "    Please install Python 3 (e.g. 'sudo apt install python3' or 'brew install python3') and try again." >&2
    exit 1
fi
echo "[+] Python 3 detected: $(python3 --version)"

# 2. Locate source files (local or remote)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" 2>/dev/null && pwd || echo "")"
CLEANUP_TMP=""

if [[ -z "${SCRIPT_DIR}" || ! -f "${SCRIPT_DIR}/statusline.py" ]]; then
    echo "[+] Running via remote pipe. Fetching latest files from GitHub..."
    TMP_DIR=$(mktemp -d)
    CLEANUP_TMP="${TMP_DIR}"
    trap '[[ -n "${CLEANUP_TMP}" ]] && rm -rf "${CLEANUP_TMP}"' EXIT
    
    ARCHIVE_URL="https://github.com/${REPO_NAME}/archive/refs/heads/${BRANCH}.tar.gz"
    if command -v curl >/dev/null 2>&1; then
        curl -fsSL "${ARCHIVE_URL}" | tar -xz -C "${TMP_DIR}"
    elif command -v wget >/dev/null 2>&1; then
        wget -qO- "${ARCHIVE_URL}" | tar -xz -C "${TMP_DIR}"
    else
        echo "[-] Error: curl or wget is required for remote installation." >&2
        exit 1
    fi
    SCRIPT_DIR="${TMP_DIR}/agy-statusline-${BRANCH}"
fi

if [[ ! -f "${SCRIPT_DIR}/statusline.py" ]]; then
    echo "[-] Error: Could not locate statusline.py source." >&2
    exit 1
fi

# 3. Setup target directory
echo "[+] Installing statusline files to ${TARGET_DIR}..."
mkdir -p "${TARGET_DIR}/lib"
mkdir -p "${TARGET_DIR}/tests"

cp "${SCRIPT_DIR}/statusline.py" "${TARGET_DIR}/statusline.py"
cp "${SCRIPT_DIR}/statusline.sh" "${TARGET_DIR}/statusline.sh"
cp "${SCRIPT_DIR}/uninstall.sh" "${TARGET_DIR}/uninstall.sh"
if [[ -f "${SCRIPT_DIR}/config.json" ]]; then
    # Do not overwrite existing user config if present
    if [[ ! -f "${TARGET_DIR}/config.json" ]]; then
        cp "${SCRIPT_DIR}/config.json" "${TARGET_DIR}/config.json"
    fi
fi

cp -r "${SCRIPT_DIR}/lib/"* "${TARGET_DIR}/lib/" 2>/dev/null || true
if [[ -d "${SCRIPT_DIR}/tests" ]]; then
    cp -r "${SCRIPT_DIR}/tests/"* "${TARGET_DIR}/tests/" 2>/dev/null || true
fi

chmod +x "${TARGET_DIR}/statusline.py"
chmod +x "${TARGET_DIR}/statusline.sh"
chmod +x "${TARGET_DIR}/uninstall.sh"

# 4. Safely update ~/.gemini/antigravity-cli/settings.json
mkdir -p "${SETTINGS_DIR}"
echo "[+] Configuring AGY settings.json..."

python3 -c "
import json, os, sys, time

settings_path = '$SETTINGS_FILE'
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
    'command': cmd_path,
    'enabled': True
}

with open(settings_path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2)
print('[+] Successfully registered custom statusline in settings.json')
"

# 5. Verify installation
echo "[+] Verifying statusline rendering..."
echo "--------------------------------------------------"
python3 "${TARGET_DIR}/statusline.py" --demo
echo "--------------------------------------------------"
echo "[✓] Installation complete! Launch 'agy' to enjoy your new statusline."
