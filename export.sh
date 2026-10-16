#!/usr/bin/env bash
# Script to export AGY Custom Statusline for offline transfer
set -euo pipefail

SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OUTPUT_DIR="${1:-${HOME}}"
ARCHIVE="${OUTPUT_DIR}/agy-statusline-bundle.tar.gz"
STANDALONE="${OUTPUT_DIR}/agy-statusline-installer.sh"

echo "=== Exporting AGY Custom Statusline ==="

# Clean pycache
find "${SOURCE_DIR}" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "${SOURCE_DIR}" -type f -name "*.pyc" -delete 2>/dev/null || true

# 1. Create tar.gz bundle
rm -f "${ARCHIVE}"
tar --exclude="*.tar.gz" --exclude="*.log" -czf "${ARCHIVE}" -C "$(dirname "${SOURCE_DIR}")" "agy-statusline"
echo "[+] Created offline bundle: ${ARCHIVE} ($(du -h "${ARCHIVE}" | cut -f1))"

# 2. Create standalone self-installing shell script (base64 embedded)
B64_DATA=$(base64 -w 0 "${ARCHIVE}")

cat << 'EOF' > "${STANDALONE}"
#!/usr/bin/env bash
# Self-extracting offline installer for AGY Custom Statusline
set -euo pipefail

TMP_DIR=$(mktemp -d)
trap 'rm -rf "${TMP_DIR}"' EXIT

echo "=========================================="
echo "  AGY Statusline Standalone Installer    "
echo "=========================================="

echo "[+] Unpacking files..."
base64 -d << 'DATA_EOF' > "${TMP_DIR}/bundle.tar.gz"
EOF

echo "${B64_DATA}" >> "${STANDALONE}"

cat << 'EOF' >> "${STANDALONE}"
DATA_EOF

tar -xzf "${TMP_DIR}/bundle.tar.gz" -C "${TMP_DIR}"
bash "${TMP_DIR}/agy-statusline/install.sh"
EOF

chmod +x "${STANDALONE}"
echo "[+] Created standalone installer: ${STANDALONE} ($(du -h "${STANDALONE}" | cut -f1))"
echo "=== Export Complete! ==="
