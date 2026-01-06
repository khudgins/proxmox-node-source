# Proxmox Node Source Plugin for Rundeck

A Python-based Rundeck node source plugin that dynamically imports virtual machines and containers from a Proxmox cluster.

## Features

- Discovers all VMs (QEMU) and containers (LXC) from a Proxmox cluster
- Automatically extracts IP addresses when available
- Tags nodes with Proxmox metadata (node name, VM ID, type, status)
- Supports filtering by VM type (VMs only, containers only, or both)
- Configurable authentication and connection settings

## Prerequisites

- Python 3.6 or higher
- Rundeck 3.x or higher
- Access to a Proxmox cluster with API access

## Caveats

Currently, the plugin will only report host address correctly (for Linux VMs, anyway) when QEMU-guest-agent is installed on the VM, or for statically assigned IPs.

## Installation

### As a Rundeck Plugin (Recommended)

The easiest way to use this is as a proper Rundeck plugin. See [INSTALL.md](INSTALL.md) for detailed installation instructions.

Quick start:
1. Build the plugin: `./build-plugin.sh`
2. Copy `proxmox-node-source.zip` to your Rundeck `libext` directory
3. Install Python dependencies on Rundeck server: `pip3 install proxmoxer requests pyyaml`
4. Restart Rundeck
5. Configure the plugin in your Rundeck project settings

### Using uv (For Local Development/Testing)

1. Install dependencies using uv:
   ```bash
   uv sync
   ```

2. Make the script executable:
   ```bash
   chmod +x proxmox-node-source.py
   ```

3. Run the script using uv:
   ```bash
   uv run ./proxmox-node-source.py --help
   ```

### Using pip

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Make the script executable:
   ```bash
   chmod +x proxmox-node-source.py
   ```

### Manual Script Deployment

If you prefer to use it as a script-based resource model source without the plugin wrapper:

1. Copy the script to your Rundeck server
2. Install Python dependencies: `pip3 install proxmoxer requests pyyaml`
3. Configure as a Script-based Resource Model Source in Rundeck

## Configuration in Rundeck

### Option 1: Script-based Resource Model Source

1. In Rundeck, go to your Project Settings
2. Navigate to "Resource Model Sources"
3. Add a new "Script" resource model source
4. Configure the following:

   **Script File**: `/path/to/proxmox-node-source.py`
   
   **Script Arguments**:
   ```
   --proxmox-host your-proxmox-host.example.com
   --proxmox-user root@pam
   --proxmox-password your-password
   --proxmox-port 8006
   --default-username root
   --output-format yaml
   ```

   **Additional Options**:
   - `--output-format {json,yaml,xml}`: Output format (default: yaml)
   - `--verify-ssl`: Enable SSL certificate verification
   - `--no-vms`: Exclude VMs, only include containers
   - `--no-containers`: Exclude containers, only include VMs

### Option 2: Using Environment Variables

You can also use environment variables for sensitive data:

```bash
export PROXMOX_HOST=your-proxmox-host.example.com
export PROXMOX_USER=root@pam
export PROXMOX_PASSWORD=your-password
```

Then modify the script to read from environment variables if arguments are not provided.

## Authentication

### Password Authentication
Use your Proxmox username and password:
```
--proxmox-user root@pam
--proxmox-password your-password
```

### API Token Authentication
Proxmox also supports API tokens. You can use them by setting:
```
--proxmox-user your-token-id
--proxmox-password your-token-secret
```

## Node Attributes

Each node imported from Proxmox includes the following attributes:

### Basic Attributes (All VMs/Containers)
- `proxmox_node`: The Proxmox node name where the VM/container is hosted
- `proxmox_vmid`: The VM/container ID
- `proxmox_type`: Either 'qemu' or 'lxc'
- `proxmox_status`: Current status (running, stopped, etc.)
- `proxmox_running_status`: Running status ('running' or 'stopped')

### Configuration Attributes (When Available)
- `proxmox_cores`: Number of CPU cores allocated
- `proxmox_sockets`: Number of CPU sockets (VMs only)
- `proxmox_memory_mb`: Allocated memory in megabytes
- `proxmox_maxmem_bytes`: Maximum memory in bytes
- `proxmox_maxdisk_bytes`: Maximum disk space in bytes
- `proxmox_template`: Whether this is a template ('true' or 'false')
- `proxmox_agent`: QEMU agent status ('enabled' or 'disabled', VMs only)
- `proxmox_ostype`: Operating system type (e.g., 'l26' for Linux, 'ubuntu' for containers)
- `proxmox_description`: VM/container description/notes from Proxmox
- `proxmox_swap_mb`: Swap space in megabytes (containers only)
- `proxmox_hostname`: Container hostname (containers only)

### OS Detection Attributes (When Available)

The plugin attempts to detect the operating system for each VM/container:

**For QEMU VMs (with QEMU Guest Agent enabled and running):**
- `os_name`: OS name (e.g., "Ubuntu", "CentOS")
- `os_version`: OS version (e.g., "22.04", "7")
- `os_version_id`: OS version ID
- `os_pretty_name`: Full OS name (e.g., "Ubuntu 22.04.3 LTS")
- `os_id`: OS identifier (e.g., "ubuntu", "centos")
- `os_kernel`: Kernel release (e.g., "5.15.0-72-generic")
- `os_kernel_version`: Full kernel version

**For LXC Containers:**
- `os_name`: OS name derived from ostype (e.g., "Ubuntu", "Debian", "Alpine Linux")
- `os_hostname`: Container hostname (may contain OS hints)

**Fallback (when detailed OS info not available):**
- `os_family`: OS family name derived from ostype (e.g., "Linux", "Windows 10", "Windows 11")
- `proxmox_ostype`: Basic OS type identifier from Proxmox config

**Note:** For QEMU VMs, detailed OS detection requires:
1. QEMU Guest Agent installed and running inside the VM
2. Guest Agent enabled in Proxmox VM configuration (`agent: 1`)
3. VM must be running

### Performance Metrics (Running VMs/Containers Only)
- `proxmox_uptime_seconds`: Uptime in seconds since last start
- `proxmox_cpu_usage`: Current CPU usage (0.0 to 1.0)
- `proxmox_mem_used_bytes`: Current memory usage in bytes
- `proxmox_cpus`: Number of CPUs
- `proxmox_maxcpu`: Maximum CPU usage
- `proxmox_netin_bytes`: Total network bytes received
- `proxmox_netout_bytes`: Total network bytes sent
- `proxmox_diskread_bytes`: Total disk bytes read
- `proxmox_diskwrite_bytes`: Total disk bytes written
- `proxmox_disk_used_bytes`: Current disk usage in bytes

## Tags

Nodes are automatically tagged with:
- `proxmox`: All nodes from Proxmox
- `vm` or `container`: Type of resource
- `qemu` or `lxc`: Technical type
- `{node_name}`: The Proxmox node name
- Any custom tags defined in Proxmox (if the VM/container has tags configured)

## Output Formats

The plugin supports three output formats compatible with Rundeck:

- **YAML** (default): Rundeck resource-yml format
  ```bash
  --output-format yaml
  ```

- **XML**: Rundeck resource-xml format
  ```bash
  --output-format xml
  ```

- **JSON**: Rundeck resource-json format
  ```bash
  --output-format json
  ```

The default format is YAML. All formats include the same node information (name, hostname, username, tags, attributes, etc.) and are compatible with Rundeck's Resource Model Source plugins.

## Troubleshooting

### Authentication Errors

If you get "Couldn't authenticate user" errors:

1. **Username Format**: Ensure the username includes the realm:
   - For root user: `root@pam` or `root@pve`
   - For other users: `username@pam` or `username@pve`
   - The realm (`@pam` or `@pve`) is required

2. **Password Verification**: Double-check the password is correct

3. **API Access**: Ensure the user has API access enabled:
   - Log into Proxmox web UI
   - Go to Datacenter → Permissions → Users
   - Verify the user exists and has appropriate roles
   - API access is typically enabled by default for users with roles

4. **Two-Factor Authentication (2FA)**: If 2FA is enabled, password authentication may not work. Use an API token instead:
   - In Proxmox web UI: Datacenter → Permissions → API Tokens
   - Create a token for your user
   - Use format: `--proxmox-user TOKENID@REALM` and `--proxmox-password TOKEN_SECRET`

5. **Test API Access Manually**:
   ```bash
   curl -k -d "username=root@pam&password=YOUR_PASSWORD" \
     https://YOUR_PROXMOX_HOST:8006/api2/json/access/ticket
   ```
   If this fails, the issue is with Proxmox configuration, not the script.

6. **Time Synchronization**: Ensure system time is synchronized (NTP)

### Connection Issues
- Verify the Proxmox host is reachable from the Rundeck server
- Check firewall rules for port 8006
- Ensure SSL certificate issues are handled (use `--verify-ssl` if certificates are valid)
- Test network connectivity: `telnet YOUR_PROXMOX_HOST 8006`

### No Nodes Appearing
- Check that the Proxmox user has sufficient permissions to list VMs and containers
- Verify the script has execute permissions
- Check Rundeck logs for script execution errors
- Test the script manually from the command line
- Ensure the user has at least "PVEAuditor" role or higher on the datacenter

### IP Address Not Found
- The script attempts to extract IP addresses from VM/container configuration
- If IPs are not found, nodes will use `{name}.local` as hostname
- You may need to configure IP addresses manually in Rundeck or modify the script to use a different method

## Testing

Test the plugin manually using uv:

```bash
uv run ./proxmox-node-source.py \
  --proxmox-host your-proxmox-host.example.com \
  --proxmox-user root@pam \
  --proxmox-password your-password \
  --default-username root \
  --output-format yaml
```

Or if you've installed dependencies with pip and activated a virtual environment:

```bash
./proxmox-node-source.py \
  --proxmox-host your-proxmox-host.example.com \
  --proxmox-user root@pam \
  --proxmox-password your-password \
  --default-username root \
  --output-format yaml
```

This should output YAML (default) with all discovered nodes. You can also use `--output-format json` or `--output-format xml` to get different formats.

## License

This plugin is provided as-is. Feel free to modify and adapt it to your needs.

