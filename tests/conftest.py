"""Pytest configuration and shared fixtures."""
import sys
import importlib.util
from pathlib import Path
from unittest.mock import Mock

import pytest

# Add the project root to the path so we can import the module
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the module using importlib since it has hyphens in the filename
module_path = project_root / "proxmox-node-source.py"
spec = importlib.util.spec_from_file_location("proxmox_node_source", module_path)
proxmox_node_source = importlib.util.module_from_spec(spec)
sys.modules["proxmox_node_source"] = proxmox_node_source
spec.loader.exec_module(proxmox_node_source)


@pytest.fixture
def mock_proxmox():
    """Create a mock ProxmoxAPI object with proper chaining support."""
    proxmox = Mock()
    
    # Mock version endpoint
    proxmox.version.get.return_value = {'version': '7.4-1'}
    
    # Mock nodes endpoint
    proxmox.nodes.get.return_value = [
        {'node': 'pve1'},
        {'node': 'pve2'},
    ]
    
    # Create mock nodes with chaining support
    def create_node_mock(node_name):
        """Create a mock node that supports chaining."""
        node_mock = Mock()
        
        # QEMU mock
        qemu_mock = Mock()
        if node_name == 'pve1':
            qemu_mock.get.return_value = [
                {'vmid': 100, 'name': 'test-vm', 'status': 'running'},
                {'vmid': 101, 'name': 'test-vm2', 'status': 'stopped'},
            ]
        else:
            qemu_mock.get.return_value = []
        
        # Create VM-specific mocks with config and status
        def create_vm_mock(vmid):
            vm_mock = Mock()
            config_mock = Mock()
            status_mock = Mock()
            current_mock = Mock()
            
            if node_name == 'pve1' and vmid == 100:
                config_mock.get.return_value = {
                    'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0',
                    'cores': 2,
                    'memory': 2048,
                    'maxmem': 2147483648,
                    'maxdisk': 10737418240,
                    'ostype': 'l26',
                    'agent': 1,
                    'template': 0,
                }
                # Running VM has status data
                current_mock.get.return_value = {
                    'uptime': 3600,
                    'cpu': 0.25,
                    'mem': 1073741824,
                    'maxmem': 2147483648,
                    'cpus': 2,
                    'maxcpu': 2.0,
                    'netin': 1000000,
                    'netout': 500000,
                    'diskread': 2000000,
                    'diskwrite': 1000000,
                    'disk': 5368709120,
                }
            elif node_name == 'pve1' and vmid == 101:
                config_mock.get.return_value = {
                    'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0',
                    'cores': 1,
                    'memory': 1024,
                    'maxmem': 1073741824,
                    'maxdisk': 5368709120,
                    'ostype': 'l26',
                    'agent': 0,
                    'template': 0,
                }
                # Stopped VM has no status data - raise exception to simulate not running
                current_mock.get.side_effect = Exception("VM not running")
            else:
                config_mock.get.return_value = {}
                current_mock.get.side_effect = Exception("VM not found")
            
            status_mock.current = current_mock
            vm_mock.config = config_mock
            vm_mock.status = status_mock
            return vm_mock
        
        qemu_mock.side_effect = create_vm_mock
        node_mock.qemu = qemu_mock
        
        # LXC mock
        lxc_mock = Mock()
        if node_name == 'pve1':
            lxc_mock.get.return_value = [
                {'vmid': 200, 'name': 'test-container', 'status': 'running'},
            ]
        else:
            lxc_mock.get.return_value = []
        
        # Create container-specific mocks with config and status
        def create_container_mock(vmid):
            container_mock = Mock()
            config_mock = Mock()
            status_mock = Mock()
            current_mock = Mock()
            
            if node_name == 'pve1' and vmid == 200:
                config_mock.get.return_value = {
                    'ipconfig0': 'ip=192.168.1.100/24',
                    'cores': 1,
                    'memory': 512,
                    'maxmem': 536870912,
                    'maxdisk': 1073741824,
                    'swap': 256,
                    'ostype': 'ubuntu',
                }
                # Running container has status data
                current_mock.get.return_value = {
                    'uptime': 7200,
                    'cpu': 0.15,
                    'mem': 268435456,
                    'maxmem': 536870912,
                    'cpus': 1,
                    'maxcpu': 1.0,
                    'netin': 500000,
                    'netout': 250000,
                    'diskread': 1000000,
                    'diskwrite': 500000,
                    'disk': 536870912,
                }
            else:
                config_mock.get.return_value = {}
                current_mock.get.side_effect = Exception("Container not found")
            
            status_mock.current = current_mock
            container_mock.config = config_mock
            container_mock.status = status_mock
            return container_mock
        
        lxc_mock.side_effect = create_container_mock
        node_mock.lxc = lxc_mock
        
        return node_mock
    
    # Make nodes() return the appropriate mock
    proxmox.nodes.side_effect = create_node_mock
    
    return proxmox


@pytest.fixture
def sample_vm_data():
    """Sample VM data from Proxmox API."""
    return [
        {'vmid': 100, 'name': 'test-vm', 'status': 'running'},
        {'vmid': 101, 'name': 'test-vm2', 'status': 'stopped'},
    ]


@pytest.fixture
def sample_container_data():
    """Sample container data from Proxmox API."""
    return [
        {'vmid': 200, 'name': 'test-container', 'status': 'running'},
    ]


@pytest.fixture
def sample_cluster_nodes():
    """Sample cluster node data."""
    return [
        {'node': 'pve1'},
        {'node': 'pve2'},
    ]


@pytest.fixture
def expected_rundeck_nodes():
    """Expected Rundeck node format."""
    return [
        {
            'nodename': 'test-vm',
            'hostname': 'test-vm.local',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,vm,qemu,pve1',
            'description': 'Proxmox VM 100 on node pve1',
            'proxmox_node': 'pve1',
            'proxmox_vmid': '100',
            'proxmox_type': 'qemu',
            'proxmox_status': 'running',
            'proxmox_running_status': 'running',
            'proxmox_cores': '2',
            'proxmox_memory_mb': '2048',
            'proxmox_maxmem_bytes': '2147483648',
            'proxmox_maxdisk_bytes': '10737418240',
            'proxmox_template': 'false',
            'proxmox_agent': 'enabled',
            'proxmox_ostype': 'l26',
            'proxmox_uptime_seconds': '3600',
            'proxmox_cpu_usage': '0.25',
            'proxmox_mem_used_bytes': '1073741824',
            'proxmox_cpus': '2',
            'proxmox_maxcpu': '2.0',
            'proxmox_netin_bytes': '1000000',
            'proxmox_netout_bytes': '500000',
            'proxmox_diskread_bytes': '2000000',
            'proxmox_diskwrite_bytes': '1000000',
            'proxmox_disk_used_bytes': '5368709120',
        },
        {
            'nodename': 'test-vm2',
            'hostname': 'test-vm2.local',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,vm,qemu,pve1',
            'description': 'Proxmox VM 101 on node pve1',
            'proxmox_node': 'pve1',
            'proxmox_vmid': '101',
            'proxmox_type': 'qemu',
            'proxmox_status': 'stopped',
            'proxmox_running_status': 'stopped',
            'proxmox_cores': '1',
            'proxmox_memory_mb': '1024',
            'proxmox_maxmem_bytes': '1073741824',
            'proxmox_maxdisk_bytes': '5368709120',
            'proxmox_template': 'false',
            'proxmox_agent': 'disabled',
            'proxmox_ostype': 'l26',
        },
        {
            'nodename': 'test-container',
            'hostname': '192.168.1.100',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,container,lxc,pve1',
            'description': 'Proxmox Container 200 on node pve1',
            'proxmox_node': 'pve1',
            'proxmox_vmid': '200',
            'proxmox_type': 'lxc',
            'proxmox_status': 'running',
            'proxmox_running_status': 'running',
            'proxmox_cores': '1',
            'proxmox_memory_mb': '512',
            'proxmox_maxmem_bytes': '536870912',
            'proxmox_maxdisk_bytes': '1073741824',
            'proxmox_swap_mb': '256',
            'proxmox_ostype': 'ubuntu',
            'proxmox_uptime_seconds': '7200',
            'proxmox_cpu_usage': '0.15',
            'proxmox_mem_used_bytes': '268435456',
            'proxmox_cpus': '1',
            'proxmox_maxcpu': '1.0',
            'proxmox_netin_bytes': '500000',
            'proxmox_netout_bytes': '250000',
            'proxmox_diskread_bytes': '1000000',
            'proxmox_diskwrite_bytes': '500000',
            'proxmox_disk_used_bytes': '536870912',
        },
    ]

