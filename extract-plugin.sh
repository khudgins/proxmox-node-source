#!/bin/bash
# Script to manually extract the plugin on the Rundeck server

set -e

PLUGIN_NAME="proxmox-node-source"
ZIP_FILE="${PLUGIN_NAME}.zip"
LIBEXT_DIR="/var/lib/rundeck/libext"
PLUGIN_DIR="${LIBEXT_DIR}/${PLUGIN_NAME}"

echo "Extracting ${PLUGIN_NAME} plugin..."

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then 
    echo "This script should be run with sudo"
    echo "Usage: sudo ./extract-plugin.sh"
    exit 1
fi

# Check if ZIP file exists
if [ ! -f "${LIBEXT_DIR}/${ZIP_FILE}" ]; then
    echo "Error: ${LIBEXT_DIR}/${ZIP_FILE} not found"
    echo "Please copy the ZIP file to ${LIBEXT_DIR}/ first"
    exit 1
fi

# Remove existing directory if it exists
if [ -d "${PLUGIN_DIR}" ]; then
    echo "Removing existing ${PLUGIN_DIR}..."
    rm -rf "${PLUGIN_DIR}"
fi

# Extract ZIP file
echo "Extracting ${ZIP_FILE} to ${PLUGIN_DIR}..."
cd "${LIBEXT_DIR}"
unzip -q "${ZIP_FILE}"

# Set proper permissions
echo "Setting permissions..."
chown -R rundeck:rundeck "${PLUGIN_DIR}"
chmod +x "${PLUGIN_DIR}/proxmox-node-source.py"
chmod 644 "${PLUGIN_DIR}/plugin.yaml"

echo "Plugin extracted successfully!"
echo ""
echo "Directory structure:"
ls -la "${PLUGIN_DIR}"
echo ""
echo "Now restart Rundeck:"
echo "  sudo systemctl restart rundeckd"

