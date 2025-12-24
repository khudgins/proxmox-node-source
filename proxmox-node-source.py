#!/usr/bin/env python3
"""
Rundeck Node Source Plugin for Proxmox
Polls a Proxmox cluster to list VMs and containers as Rundeck nodes.

Copyright (C) 2025 Keith Hudgins

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import json
import sys
import os
import argparse
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
from proxmoxer import ProxmoxAPI
from proxmoxer.core import ResourceException

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


def get_proxmox_connection(host: str, user: str, password: str, 
                          verify_ssl: bool = False, port: int = 8006) -> ProxmoxAPI:
    """
    Create and return a Proxmox API connection.
    
    Args:
        host: Proxmox hostname or IP
        user: Proxmox username (format: user@realm, e.g., root@pam)
        password: Proxmox password or API token
        verify_ssl: Whether to verify SSL certificates
        port: Proxmox API port (default: 8006)
    
    Returns:
        ProxmoxAPI connection object
    """
    try:
        # Explicitly use the requests backend
        proxmox = ProxmoxAPI(
            host,
            user=user,
            password=password,
            verify_ssl=verify_ssl,
            port=port,
            backend='https'
        )
        # Test the connection by trying to access the version endpoint
        proxmox.version.get()
        return proxmox
    except Exception as e:
        error_msg = str(e)
        print(f"Error connecting to Proxmox: {error_msg}", file=sys.stderr)
        # Provide helpful troubleshooting hints
        if "Couldn't authenticate" in error_msg or "authentication" in error_msg.lower():
            print("\nTroubleshooting authentication issues:", file=sys.stderr)
            print("1. Verify username format includes realm (e.g., root@pam or root@pve)", file=sys.stderr)
            print("2. Check that the password is correct", file=sys.stderr)
            print("3. Ensure the user has API access enabled in Proxmox", file=sys.stderr)
            print("4. If 2FA is enabled, you may need to use an API token instead", file=sys.stderr)
            print("5. Verify the user exists and has proper permissions", file=sys.stderr)
            print("6. Test manually: curl -k -d 'username={user}&password=***' https://{host}:{port}/api2/json/access/ticket", file=sys.stderr)
            
        sys.exit(1)


def get_vm_ip_address(proxmox: ProxmoxAPI, node: str, vmid: int, vm_type: str) -> str:
    """
    Attempt to get the IP address of a VM or container.
    
    Args:
        proxmox: Proxmox API connection
        node: Proxmox node name
        vmid: VM/Container ID
        vm_type: 'qemu' or 'lxc'
    
    Returns:
        IP address string or empty string if not found
    """
    try:
        if vm_type == 'qemu':
            config = proxmox.nodes(node).qemu(vmid).config.get()
        else:
            config = proxmox.nodes(node).lxc(vmid).config.get()
        
        # Try to get IP from various sources
        if 'ipconfig0' in config:
            # LXC format: ip=192.168.1.100/24
            ipconfig = config['ipconfig0']
            if 'ip=' in ipconfig:
                ip = ipconfig.split('ip=')[1].split('/')[0]
                return ip
        
        # Check for network interfaces
        for key in config:
            if key.startswith('net') or key.startswith('ipconfig'):
                value = config[key]
                if isinstance(value, str) and '/' in value:
                    # Extract IP from format like "ip=192.168.1.100/24"
                    if 'ip=' in value:
                        ip = value.split('ip=')[1].split('/')[0]
                        return ip
        
        return ""
    except Exception:
        return ""


def fetch_proxmox_nodes(proxmox: ProxmoxAPI, include_vms: bool = True, 
                       include_containers: bool = True) -> List[Dict[str, Any]]:
    """
    Fetch all VMs and containers from Proxmox cluster and format as Rundeck nodes.
    
    Args:
        proxmox: Proxmox API connection
        include_vms: Whether to include VMs (qemu)
        include_containers: Whether to include containers (lxc)
    
    Returns:
        List of node dictionaries in Rundeck format
    """
    rundeck_nodes = []
    
    try:
        # Get all nodes in the cluster
        cluster_nodes = proxmox.nodes.get()
        
        for cluster_node in cluster_nodes:
            node_name = cluster_node['node']
            
            # Fetch VMs (QEMU)
            if include_vms:
                try:
                    vms = proxmox.nodes(node_name).qemu.get()
                    for vm in vms:
                        vmid = vm['vmid']
                        name = vm.get('name', f"vm-{vmid}")
                        status = vm.get('status', 'unknown')
                        
                        # Skip if VM is not running (optional - you may want to include all)
                        # if status != 'running':
                        #     continue
                        
                        # Get IP address
                        ip_address = get_vm_ip_address(proxmox, node_name, vmid, 'qemu')
                        
                        # Create Rundeck node entry
                        rundeck_node = {
                            'nodename': name,
                            'hostname': ip_address if ip_address else f"{name}.local",
                            'username': 'root',  # Default, can be configured
                            'osFamily': 'unix',
                            'tags': f"proxmox,vm,qemu,{node_name}",
                            'description': f"Proxmox VM {vmid} on node {node_name}",
                            'attributes': {
                                'proxmox_node': node_name,
                                'proxmox_vmid': str(vmid),
                                'proxmox_type': 'qemu',
                                'proxmox_status': status
                            }
                        }
                        
                        # Add status-specific attributes
                        if status == 'running':
                            rundeck_node['attributes']['proxmox_running'] = 'true'
                        
                        rundeck_nodes.append(rundeck_node)
                except ResourceException as e:
                    print(f"Error fetching VMs from node {node_name}: {e}", file=sys.stderr)
            
            # Fetch Containers (LXC)
            if include_containers:
                try:
                    containers = proxmox.nodes(node_name).lxc.get()
                    for container in containers:
                        vmid = container['vmid']
                        name = container.get('name', f"ct-{vmid}")
                        status = container.get('status', 'unknown')
                        
                        # Get IP address
                        ip_address = get_vm_ip_address(proxmox, node_name, vmid, 'lxc')
                        
                        # Create Rundeck node entry
                        rundeck_node = {
                            'nodename': name,
                            'hostname': ip_address if ip_address else f"{name}.local",
                            'username': 'root',  # Default, can be configured
                            'osFamily': 'unix',
                            'tags': f"proxmox,container,lxc,{node_name}",
                            'description': f"Proxmox Container {vmid} on node {node_name}",
                            'attributes': {
                                'proxmox_node': node_name,
                                'proxmox_vmid': str(vmid),
                                'proxmox_type': 'lxc',
                                'proxmox_status': status
                            }
                        }
                        
                        # Add status-specific attributes
                        if status == 'running':
                            rundeck_node['attributes']['proxmox_running'] = 'true'
                        
                        rundeck_nodes.append(rundeck_node)
                except ResourceException as e:
                    print(f"Error fetching containers from node {node_name}: {e}", file=sys.stderr)
    
    except Exception as e:
        print(f"Error fetching nodes from Proxmox: {e}", file=sys.stderr)
        sys.exit(1)
    
    return rundeck_nodes


def output_json(nodes: List[Dict[str, Any]]) -> str:
    """Output nodes in JSON format."""
    return json.dumps(nodes, indent=2)


def output_yaml(nodes: List[Dict[str, Any]]) -> str:
    """Output nodes in YAML format (Rundeck resource-yml)."""
    if not YAML_AVAILABLE:
        print("Error: PyYAML is required for YAML output. Install with: pip install pyyaml", file=sys.stderr)
        sys.exit(1)
    
    # Rundeck expects a list of nodes
    return yaml.dump(nodes, default_flow_style=False, sort_keys=False, allow_unicode=True)


def output_xml(nodes: List[Dict[str, Any]]) -> str:
    """Output nodes in XML format (Rundeck resource-xml)."""
    # Create root element
    project = ET.Element('project')
    
    for node in nodes:
        node_elem = ET.SubElement(project, 'node')
        node_elem.set('name', node.get('nodename', ''))
        node_elem.set('hostname', node.get('hostname', ''))
        node_elem.set('username', node.get('username', ''))
        node_elem.set('osFamily', node.get('osFamily', ''))
        
        # Add description if present
        if 'description' in node:
            node_elem.set('description', node['description'])
        
        # Add tags if present
        if 'tags' in node:
            node_elem.set('tags', node['tags'])
        
        # Add attributes
        if 'attributes' in node:
            for key, value in node['attributes'].items():
                attr_elem = ET.SubElement(node_elem, 'attribute')
                attr_elem.set('name', key)
                attr_elem.set('value', str(value))
    
    # Convert to string with proper formatting
    # ET.indent is only available in Python 3.9+
    if hasattr(ET, 'indent'):
        ET.indent(project, space='  ')
    
    xml_str = ET.tostring(project, encoding='unicode', xml_declaration=True)
    return xml_str


def main():
    """Main entry point for the plugin."""
    parser = argparse.ArgumentParser(
        description='Rundeck Node Source Plugin for Proxmox',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--proxmox-host',
        required=False,
        help='Proxmox hostname or IP address (or set RD_CONFIG_PROXMOX_HOST env var)'
    )
    parser.add_argument(
        '--proxmox-user',
        required=False,
        help='Proxmox username (format: user@realm, e.g., root@pam) (or set RD_CONFIG_PROXMOX_USER env var)'
    )
    parser.add_argument(
        '--proxmox-password',
        required=False,
        help='Proxmox password or API token (can be from key storage or direct input)'
    )
    parser.add_argument(
        '--proxmox-password-storage-path',
        required=False,
        help='Path to password in Rundeck Key Storage (alternative to --proxmox-password)'
    )
    parser.add_argument(
        '--proxmox-port',
        type=int,
        default=8006,
        help='Proxmox API port (default: 8006)'
    )
    parser.add_argument(
        '--verify-ssl',
        action='store_true',
        help='Verify SSL certificates (default: False)'
    )
    parser.add_argument(
        '--verify-ssl-flag',
        type=str,
        default='false',
        help='Verify SSL certificates flag from Rundeck (true/false string)'
    )
    parser.add_argument(
        '--include-vms-flag',
        type=str,
        default='true',
        help='Include VMs flag from Rundeck (true/false string)'
    )
    parser.add_argument(
        '--include-containers-flag',
        type=str,
        default='true',
        help='Include containers flag from Rundeck (true/false string)'
    )
    parser.add_argument(
        '--no-vms',
        action='store_true',
        help='Exclude VMs from the node list'
    )
    parser.add_argument(
        '--no-containers',
        action='store_true',
        help='Exclude containers from the node list'
    )
    parser.add_argument(
        '--include-vms',
        action='store_true',
        help='Include VMs in the node list (default: true)'
    )
    parser.add_argument(
        '--include-containers',
        action='store_true',
        help='Include containers in the node list (default: true)'
    )
    parser.add_argument(
        '--default-username',
        default='root',
        help='Default username for nodes (default: root)'
    )
    parser.add_argument(
        '--output-format',
        choices=['json', 'yaml', 'xml'],
        default='yaml',
        help='Output format: json, yaml, or xml (default: yaml)'
    )
    
    args = parser.parse_args()
    
    # Read configuration from environment variables (Rundeck) or command-line arguments (testing)
    # Environment variables take precedence for security (Rundeck passes sensitive data via env)
    proxmox_host = os.environ.get('RD_CONFIG_PROXMOX_HOST') or args.proxmox_host
    proxmox_user = os.environ.get('RD_CONFIG_PROXMOX_USER') or args.proxmox_user
    proxmox_password = (os.environ.get('RD_CONFIG_PROXMOX_PASSWORD_STORAGE_PATH') or 
                       os.environ.get('RD_CONFIG_PROXMOX_PASSWORD') or
                       (args.proxmox_password_storage_path.strip() if args.proxmox_password_storage_path else '') or
                       (args.proxmox_password.strip() if args.proxmox_password else ''))
    proxmox_port = int(os.environ.get('RD_CONFIG_PROXMOX_PORT') or args.proxmox_port or 8006)
    default_username = os.environ.get('RD_CONFIG_DEFAULT_USERNAME') or args.default_username or 'root'
    output_format = os.environ.get('RD_CONFIG_OUTPUT_FORMAT') or args.output_format or 'yaml'
    verify_ssl_flag = os.environ.get('RD_CONFIG_VERIFY_SSL', str(args.verify_ssl_flag))
    include_vms_flag = os.environ.get('RD_CONFIG_INCLUDE_VMS', str(args.include_vms_flag))
    include_containers_flag = os.environ.get('RD_CONFIG_INCLUDE_CONTAINERS', str(args.include_containers_flag))
    
    # Validate required fields
    if not proxmox_host:
        print("Error: Proxmox host is required.", file=sys.stderr)
        sys.exit(1)
    if not proxmox_user:
        print("Error: Proxmox user is required.", file=sys.stderr)
        sys.exit(1)
    if not proxmox_password:
        print("Error: Proxmox password is required.", file=sys.stderr)
        sys.exit(1)
    
    # Handle boolean flags - Rundeck passes booleans as strings
    # Determine if we should include VMs and containers
    include_vms = True
    include_containers = True
    
    # Check command-line flags first (for manual usage)
    if args.no_vms:
        include_vms = False
    elif args.include_vms:
        include_vms = True
    else:
        # Check Rundeck config flags (from env or args, passed as strings, handle empty strings)
        if include_vms_flag and include_vms_flag.strip():
            include_vms = include_vms_flag.lower() in ('true', '1', 'yes')
    
    if args.no_containers:
        include_containers = False
    elif args.include_containers:
        include_containers = True
    else:
        # Check Rundeck config flags (from env or args, passed as strings, handle empty strings)
        if include_containers_flag and include_containers_flag.strip():
            include_containers = include_containers_flag.lower() in ('true', '1', 'yes')
    
    # Handle verify_ssl - command-line flag takes precedence
    verify_ssl = args.verify_ssl
    if not verify_ssl:
        # Check Rundeck config flag (passed as string, handle empty strings)
        if verify_ssl_flag and verify_ssl_flag.strip():
            verify_ssl = verify_ssl_flag.lower() in ('true', '1', 'yes')
    
    # Create Proxmox connection
    proxmox = get_proxmox_connection(
        host=proxmox_host,
        user=proxmox_user,
        password=proxmox_password,
        verify_ssl=verify_ssl,
        port=proxmox_port
    )
    
    # Fetch nodes
    rundeck_nodes = fetch_proxmox_nodes(
        proxmox,
        include_vms=include_vms,
        include_containers=include_containers
    )
    
    # Update default username if specified
    if default_username != 'root':
        for node in rundeck_nodes:
            node['username'] = default_username
    
    # Output in the requested format
    if output_format == 'json':
        output = output_json(rundeck_nodes)
    elif output_format == 'yaml':
        output = output_yaml(rundeck_nodes)
    elif output_format == 'xml':
        output = output_xml(rundeck_nodes)
    else:
        output = output_json(rundeck_nodes)  # Fallback to JSON
    
    print(output)


if __name__ == '__main__':
    main()

