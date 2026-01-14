"""Unit tests for get_vm_ip_address function."""
import pytest
from unittest.mock import Mock

# Import the module (imported via conftest)
import proxmox_node_source


class TestGetVmIpAddress:
    """Test cases for get_vm_ip_address function."""
    
    def test_lxc_ip_from_ipconfig0(self):
        """Test extracting IP from LXC container ipconfig0."""
        # Create a fresh mock for this test
        proxmox = Mock()
        config_mock = Mock()
        config_mock.get.return_value = {
            'ipconfig0': 'ip=192.168.1.100/24',
        }
        container_mock = Mock()
        container_mock.config = config_mock
        node_mock = Mock()
        node_mock.lxc.return_value = container_mock
        proxmox.nodes.return_value = node_mock
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=proxmox,
            node='pve1',
            vmid=200,
            vm_type='lxc'
        )
        
        assert result == '192.168.1.100'
        config_mock.get.assert_called_once()
    
    def test_lxc_ip_from_net_interface(self):
        """Test extracting IP from net interface."""
        proxmox = Mock()
        config_mock = Mock()
        config_mock.get.return_value = {
            'net0': 'ip=10.0.0.50/24',
        }
        container_mock = Mock()
        container_mock.config = config_mock
        node_mock = Mock()
        node_mock.lxc.return_value = container_mock
        proxmox.nodes.return_value = node_mock
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=proxmox,
            node='pve1',
            vmid=200,
            vm_type='lxc'
        )
        
        assert result == '10.0.0.50'
    
    def test_qemu_no_ip_found(self):
        """Test QEMU VM with no IP configuration."""
        proxmox = Mock()
        config_mock = Mock()
        config_mock.get.return_value = {
            'net0': 'virtio=AA:BB:CC:DD:EE:FF,bridge=vmbr0',
        }
        vm_mock = Mock()
        vm_mock.config = config_mock
        node_mock = Mock()
        node_mock.qemu.return_value = vm_mock
        proxmox.nodes.return_value = node_mock
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=proxmox,
            node='pve1',
            vmid=100,
            vm_type='qemu'
        )
        
        assert result == ''
    
    def test_empty_config(self):
        """Test with empty config."""
        proxmox = Mock()
        config_mock = Mock()
        config_mock.get.return_value = {}
        container_mock = Mock()
        container_mock.config = config_mock
        node_mock = Mock()
        node_mock.lxc.return_value = container_mock
        proxmox.nodes.return_value = node_mock
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=proxmox,
            node='pve1',
            vmid=200,
            vm_type='lxc'
        )
        
        assert result == ''
    
    def test_exception_handling(self):
        """Test that exceptions return empty string."""
        proxmox = Mock()
        config_mock = Mock()
        config_mock.get.side_effect = Exception("API Error")
        container_mock = Mock()
        container_mock.config = config_mock
        node_mock = Mock()
        node_mock.lxc.return_value = container_mock
        proxmox.nodes.return_value = node_mock
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=proxmox,
            node='pve1',
            vmid=200,
            vm_type='lxc'
        )
        
        assert result == ''
    
    def test_multiple_ipconfig_keys(self, mock_proxmox):
        """Test with multiple ipconfig keys."""
        mock_proxmox.nodes('pve1').lxc(200).config.get.return_value = {
            'ipconfig0': 'ip=192.168.1.100/24',
            'ipconfig1': 'ip=10.0.0.50/24',
        }
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=mock_proxmox,
            node='pve1',
            vmid=200,
            vm_type='lxc'
        )
        
        # Should return first IP found
        assert result == '192.168.1.100'
    
    def test_ip_without_prefix(self, mock_proxmox):
        """Test IP extraction when prefix is missing."""
        mock_proxmox.nodes('pve1').lxc(200).config.get.return_value = {
            'ipconfig0': 'ip=192.168.1.100',
        }
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=mock_proxmox,
            node='pve1',
            vmid=200,
            vm_type='lxc'
        )
        
        assert result == '192.168.1.100'
    
    def test_qemu_guest_agent_ip(self, mock_proxmox):
        """Test QEMU VM IP from guest agent."""
        # Mock config with agent enabled
        config = {'agent': 1}
        
        # Mock guest agent network response
        agent_response = {
            'result': [
                {
                    'name': 'lo',
                    'ip-addresses': [
                        {'ip-address': '127.0.0.1', 'ip-address-type': 'ipv4'}
                    ]
                },
                {
                    'name': 'eth0',
                    'ip-addresses': [
                        {'ip-address': '192.168.1.50', 'ip-address-type': 'ipv4'}
                    ]
                }
            ]
        }
        
        # Set up the agent mock chain properly
        agent_get_mock = Mock()
        agent_get_mock.get.return_value = agent_response
        agent_mock = Mock(return_value=agent_get_mock)
        vm_mock = Mock()
        vm_mock.agent = agent_mock
        node_mock = Mock()
        node_mock.qemu.return_value = vm_mock
        # nodes() should be a function that returns node_mock when called with node name
        mock_proxmox.nodes = Mock(return_value=node_mock)
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=mock_proxmox,
            node='pve1',
            vmid=100,
            vm_type='qemu',
            is_running=True,
            config=config
        )
        
        # Should return the non-loopback IP
        assert result == '192.168.1.50'
        # Verify agent was called correctly
        agent_mock.assert_called_once_with('network-get-interfaces')
        agent_get_mock.get.assert_called_once()
    
    def test_qemu_guest_agent_no_ip(self, mock_proxmox):
        """Test QEMU VM with guest agent but no valid IP."""
        config = {'agent': 1}
        
        # Mock guest agent with only loopback
        agent_response = {
            'result': [
                {
                    'name': 'lo',
                    'ip-addresses': [
                        {'ip-address': '127.0.0.1', 'ip-address-type': 'ipv4'}
                    ]
                }
            ]
        }
        
        # Set up the agent mock chain properly
        agent_get_mock = Mock()
        agent_get_mock.get.return_value = agent_response
        agent_mock = Mock(return_value=agent_get_mock)
        vm_mock = Mock()
        vm_mock.agent = agent_mock
        node_mock = Mock()
        node_mock.qemu.return_value = vm_mock
        # nodes() should be a function that returns node_mock when called with node name
        mock_proxmox.nodes = Mock(return_value=node_mock)
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=mock_proxmox,
            node='pve1',
            vmid=100,
            vm_type='qemu',
            is_running=True,
            config=config
        )
        
        # Should return empty string (no valid non-loopback IP)
        assert result == ''
    
    def test_qemu_guest_agent_not_enabled(self, mock_proxmox):
        """Test QEMU VM with agent not enabled falls back to config."""
        config = {'agent': 0, 'net0': 'ip=10.0.0.100/24'}
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=mock_proxmox,
            node='pve1',
            vmid=100,
            vm_type='qemu',
            is_running=True,
            config=config
        )
        
        # Should get IP from config
        assert result == '10.0.0.100'
    
    def test_qemu_guest_agent_exception(self, mock_proxmox):
        """Test QEMU VM with guest agent error falls back to config."""
        config = {'agent': 1, 'net0': 'ip=10.0.0.100/24'}
        
        # Set up the agent mock chain to raise exception
        agent_get_mock = Mock()
        agent_get_mock.get.side_effect = Exception("Agent error")
        agent_mock = Mock(return_value=agent_get_mock)
        vm_mock = Mock()
        vm_mock.agent = agent_mock
        node_mock = Mock()
        node_mock.qemu.return_value = vm_mock
        mock_proxmox.nodes.return_value = node_mock
        
        result = proxmox_node_source.get_vm_ip_address(
            proxmox=mock_proxmox,
            node='pve1',
            vmid=100,
            vm_type='qemu',
            is_running=True,
            config=config
        )
        
        # Should fall back to config IP
        assert result == '10.0.0.100'

