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
        
        # Create VM-specific mocks with config
        def create_vm_mock(vmid):
            vm_mock = Mock()
            config_mock = Mock()
            if node_name == 'pve1' and vmid == 100:
                config_mock.get.return_value = {
                    'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0',
                }
            elif node_name == 'pve1' and vmid == 101:
                config_mock.get.return_value = {
                    'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0',
                }
            else:
                config_mock.get.return_value = {}
            vm_mock.config = config_mock
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
        
        # Create container-specific mocks with config
        def create_container_mock(vmid):
            container_mock = Mock()
            config_mock = Mock()
            if node_name == 'pve1' and vmid == 200:
                config_mock.get.return_value = {
                    'ipconfig0': 'ip=192.168.1.100/24',
                }
            else:
                config_mock.get.return_value = {}
            container_mock.config = config_mock
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
            'attributes': {
                'proxmox_node': 'pve1',
                'proxmox_vmid': '100',
                'proxmox_type': 'qemu',
                'proxmox_status': 'running',
                'proxmox_running': 'true',
            }
        },
        {
            'nodename': 'test-vm2',
            'hostname': 'test-vm2.local',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,vm,qemu,pve1',
            'description': 'Proxmox VM 101 on node pve1',
            'attributes': {
                'proxmox_node': 'pve1',
                'proxmox_vmid': '101',
                'proxmox_type': 'qemu',
                'proxmox_status': 'stopped',
            }
        },
        {
            'nodename': 'test-container',
            'hostname': '192.168.1.100',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,container,lxc,pve1',
            'description': 'Proxmox Container 200 on node pve1',
            'attributes': {
                'proxmox_node': 'pve1',
                'proxmox_vmid': '200',
                'proxmox_type': 'lxc',
                'proxmox_status': 'running',
                'proxmox_running': 'true',
            }
        },
    ]

