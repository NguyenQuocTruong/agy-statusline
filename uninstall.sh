#!/usr/bin/env bash
# Uninstall/Rollback script for AGY Custom Statusline
set -euo pipefail

SETTINGS_FILE="${HOME}/.gemini/antigravity-cli/settings.json"

echo "=== Rolling back AGY Custom Statusline ==="

if [[ -f "$SETTINGS_FILE" ]]; then
    python3 -c "
import json
path = '$SETTINGS_FILE'
try:
    with open(path, 'r') as f:
        data = json.load(f)
    if 'statusLine' in data:
        data['statusLine'] = {
            'type': '',
            'command': '',
            'enabled': True
        }
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)
    print('Successfully reset statusLine in settings.json to built-in default.')
except Exception as e:
    print(f'Error updating settings.json: {e}')
"
fi

echo "Done! Custom statusline has been safely disabled and reverted to AGY default."
