# Installing the Proxmox Node Source Plugin for Rundeck

This guide explains how to install and configure the Proxmox Node Source plugin in Rundeck.

## Prerequisites

1. Rundeck 3.x or higher installed and running
2. Python 3.6 or higher installed on the Rundeck server
3. Access to a Proxmox cluster with API access

## Installation Steps

### 1. Install Python Dependencies

On your Rundeck server, install the required Python packages:

```bash
pip3 install proxmoxer requests pyyaml
```

Or using the requirements file:

```bash
pip3 install -r requirements.txt
```

### 2. Copy Plugin ZIP to Rundeck Server

Copy the plugin ZIP file to Rundeck's `libext` directory:

```bash
sudo cp proxmox-node-source.zip /var/lib/rundeck/libext/
```

(Adjust the path based on your Rundeck installation. Common locations:
- `/var/lib/rundeck/libext/` (Debian/Ubuntu)
- `/opt/rundeck/libext/` (RPM-based)
- Check your Rundeck configuration for the exact path)

### 3. Extract Plugin (Manual Method)

Rundeck should automatically extract ZIP files, but if it doesn't, extract manually:

**Option A: Using the extraction script (recommended)**

Copy `extract-plugin.sh` to your Rundeck server and run:

```bash
sudo ./extract-plugin.sh
```

**Option B: Manual extraction**

```bash
cd /var/lib/rundeck/libext
sudo unzip proxmox-node-source.zip
sudo chown -R rundeck:rundeck proxmox-node-source/
sudo chmod +x proxmox-node-source/proxmox-node-source.py
```

**Verify extraction:**

```bash
ls -la /var/lib/rundeck/libext/proxmox-node-source/
```

You should see `plugin.yaml` and `proxmox-node-source.py` files.

### 4. Verify Python Interpreter

Ensure that `python3` is available and points to the correct Python installation:

```bash
which python3
python3 --version
```

If your system uses `python` instead of `python3`, you may need to:
- Create a symlink: `ln -s /usr/bin/python3 /usr/bin/python3`
- Or update the `script-interpreter` in `plugin.yaml` to use `python` instead

### 5. Restart Rundeck

Restart Rundeck to load the new plugin:

```bash
# Systemd (most common)
sudo systemctl restart rundeckd

# Or using service command
sudo service rundeckd restart
```

### 6. Verify Plugin Installation

1. Log into Rundeck web interface
2. Go to **Configure** → **Plugins**
3. Look for "Proxmox Node Source" in the list of installed plugins

## Configuration in Rundeck

### Add as Resource Model Source

1. Navigate to your **Project** settings
2. Go to **Edit Nodes** → **Add a new Node Source**
3. Select **Proxmox Node Source** from the dropdown
4. Fill in the configuration:

   - **Proxmox Host**: Your Proxmox hostname or IP (e.g., `10.0.0.4`)
   - **Proxmox User**: Username with realm (e.g., `root@pam`)
   - **Proxmox Password**: Your Proxmox password or API token
   - **Proxmox Port**: API port (default: `8006`)
   - **Default Username**: Default username for nodes (default: `root`)
   - **Output Format**: Choose `yaml`, `json`, or `xml` (default: `yaml`)
   - **Verify SSL**: Check to verify SSL certificates
   - **Include VMs**: Check to include virtual machines
   - **Include Containers**: Check to include containers

5. Click **Save**

### Test the Configuration

1. Go to **Nodes** in your project
2. Click **Refresh** or wait for automatic refresh
3. You should see nodes from your Proxmox cluster appear

## Troubleshooting

### Plugin Not Appearing

- Check Rundeck logs: `/var/log/rundeck/service.log` or `rundeck.log`
- Verify plugin files are in the correct location
- Ensure file permissions are correct (script should be executable)
- Check that `plugin.yaml` syntax is correct

### Script Execution Errors

- Verify Python dependencies are installed: `pip3 list | grep -E "proxmoxer|requests|pyyaml"`
- Test the script manually:
  ```bash
  /var/lib/rundeck/libext/proxmox-node-source/proxmox-node-source.py --help
  ```
- Check Rundeck execution logs for detailed error messages

### Authentication Errors

- Verify username includes realm (e.g., `root@pam`)
- Check password is correct
- Ensure user has API access in Proxmox
- Consider using API tokens instead of passwords

### No Nodes Appearing

- Check Proxmox user has permissions to list VMs/containers
- Verify network connectivity to Proxmox host
- Test script manually with your credentials
- Check Rundeck logs for script output

## Alternative: Package as ZIP

You can also package the plugin as a ZIP file:

```bash
zip -r proxmox-node-source.zip proxmox-node-source.py plugin.yaml
```

Then copy the ZIP to Rundeck's `libext` directory:

```bash
cp proxmox-node-source.zip /var/lib/rundeck/libext/
```

Rundeck will automatically extract and load the plugin.

## Updating the Plugin

To update the plugin:

1. Stop Rundeck (optional, but recommended)
2. Replace the plugin files with new versions
3. Restart Rundeck
4. The plugin will be reloaded automatically

