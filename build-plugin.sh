#!/bin/bash
# Build script for Rundeck Proxmox Node Source Plugin

set -e

PLUGIN_NAME="proxmox-node-source"
PLUGIN_DIR="rundeck-plugin"
ZIP_FILE="${PLUGIN_NAME}.zip"

echo "Building Rundeck plugin: ${PLUGIN_NAME}"

# Remove old ZIP file if it exists
if [ -f "${ZIP_FILE}" ]; then
    echo "Removing existing ${ZIP_FILE}..."
    rm -f "${ZIP_FILE}"
fi

# Create plugin directory structure
# Try both structures: files at root for libext, contents/ for UI upload
rm -rf "${PLUGIN_DIR}"
mkdir -p "${PLUGIN_DIR}/${PLUGIN_NAME}/contents"

# Copy plugin.yaml to root of plugin directory
echo "Copying plugin files..."
cp plugin.yaml "${PLUGIN_DIR}/${PLUGIN_NAME}/"

# Copy script file to both locations for compatibility
cp proxmox-node-source.py "${PLUGIN_DIR}/${PLUGIN_NAME}/"
cp proxmox-node-source.py "${PLUGIN_DIR}/${PLUGIN_NAME}/contents/"
chmod +x "${PLUGIN_DIR}/${PLUGIN_NAME}/proxmox-node-source.py"
chmod +x "${PLUGIN_DIR}/${PLUGIN_NAME}/contents/proxmox-node-source.py"

# Create ZIP file with proper directory structure
# Preserve executable permissions
echo "Creating ZIP archive..."
cd "${PLUGIN_DIR}"
zip -r "../${ZIP_FILE}" "${PLUGIN_NAME}"
cd ..

echo "Plugin built successfully: ${ZIP_FILE}"
echo ""
echo "To install:"
echo "  1. Copy ${ZIP_FILE} to your Rundeck libext directory"
echo "  2. Restart Rundeck"
echo ""
echo "Example:"
echo "  sudo cp ${ZIP_FILE} /var/lib/rundeck/libext/"
echo "  sudo systemctl restart rundeckd"

