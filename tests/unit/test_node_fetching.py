"""Unit tests for fetch_proxmox_nodes function."""
import pytest
from unittest.mock import Mock, patch
from proxmoxer.core import ResourceException

# Import the module (imported via conftest)
import proxmox_node_source


class TestFetchProxmoxNodes:
    """Test cases for fetch_proxmox_nodes function."""
    
    def test_fetch_vms_only(self, mock_proxmox):
        """Test fetching only VMs."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=False
        )
        
        # Should have 2 VMs from pve1
        assert len(result) == 2
        assert all(node['proxmox_type'] == 'qemu' for node in result)
        assert all('proxmox,vm,qemu' in node['tags'] for node in result)
    
    def test_fetch_containers_only(self, mock_proxmox):
        """Test fetching only containers."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=False,
            include_containers=True
        )
        
        # Should have 1 container from pve1
        assert len(result) == 1
        assert result[0]['proxmox_type'] == 'lxc'
        assert 'proxmox,container,lxc' in result[0]['tags']
    
    def test_fetch_both_vms_and_containers(self, mock_proxmox):
        """Test fetching both VMs and containers."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=True
        )
        
        # Should have 2 VMs + 1 container = 3 nodes
        assert len(result) == 3
        vm_count = sum(1 for node in result if node['proxmox_type'] == 'qemu')
        container_count = sum(1 for node in result if node['proxmox_type'] == 'lxc')
        assert vm_count == 2
        assert container_count == 1
    
    def test_fetch_none(self, mock_proxmox):
        """Test fetching neither VMs nor containers."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=False,
            include_containers=False
        )
        
        assert len(result) == 0
    
    def test_node_structure(self, mock_proxmox):
        """Test that nodes have correct structure."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=False
        )
        
        assert len(result) > 0
        for node in result:
            assert 'nodename' in node
            assert 'hostname' in node
            assert 'username' in node
            assert 'osFamily' in node
            assert 'tags' in node
            assert 'description' in node
            # Attributes are now at top level (not nested)
            assert 'proxmox_node' in node
            assert 'proxmox_vmid' in node
            assert 'proxmox_type' in node
            assert 'proxmox_status' in node
            assert 'proxmox_running_status' in node
    
    def test_running_vm_has_running_status(self, mock_proxmox):
        """Test that running VMs have proxmox_running_status attribute."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=False
        )
        
        # Find the running VM (vmid 100)
        running_vm = next((node for node in result if node['proxmox_vmid'] == '100'), None)
        assert running_vm is not None
        assert running_vm.get('proxmox_running_status') == 'running'
        # Running VM should have status metrics
        assert 'proxmox_uptime_seconds' in running_vm
        assert 'proxmox_cpu_usage' in running_vm
        
        # Find the stopped VM (vmid 101)
        stopped_vm = next((node for node in result if node['proxmox_vmid'] == '101'), None)
        assert stopped_vm is not None
        assert stopped_vm.get('proxmox_running_status') == 'stopped'
        # Stopped VM should not have status metrics
        assert 'proxmox_uptime_seconds' not in stopped_vm
        assert 'proxmox_cpu_usage' not in stopped_vm
    
    def test_container_with_ip(self, mock_proxmox):
        """Test that container IP is extracted correctly."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=False,
            include_containers=True
        )
        
        container = result[0]
        # Container should have IP from ipconfig0
        assert container['hostname'] == '192.168.1.100'
    
    def test_vm_without_ip_uses_fallback(self, mock_proxmox):
        """Test that VM without IP uses name.local as hostname."""
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=False
        )
        
        # VMs without IP should use name.local
        for node in result:
            if node['proxmox_type'] == 'qemu':
                assert node['hostname'].endswith('.local') or node['hostname'] == node['nodename'] + '.local'
    
    @patch('sys.exit')
    def test_api_error_exits(self, mock_exit, mock_proxmox):
        """Test that API errors cause script to exit."""
        mock_proxmox.nodes.get.side_effect = Exception("API Error")
        
        proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=True
        )
        
        mock_exit.assert_called_once_with(1)
    
    def test_resource_exception_handled_gracefully(self, mock_proxmox):
        """Test that ResourceException is handled gracefully."""
        # Make one node fail but others succeed
        # ResourceException requires status_message and content
        mock_proxmox.nodes('pve2').qemu.get.side_effect = ResourceException(
            "Permission denied", "Permission denied", {}
        )
        
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=True
        )
        
        # Should still return nodes from pve1
        assert len(result) > 0
    
    def test_multiple_cluster_nodes(self, mock_proxmox):
        """Test fetching from multiple cluster nodes."""
        # pve1 has VMs, pve2 is empty
        result = proxmox_node_source.fetch_proxmox_nodes(
            proxmox=mock_proxmox,
            include_vms=True,
            include_containers=True
        )
        
        # Should get nodes from both nodes
        assert len(result) == 3  # 2 VMs + 1 container from pve1
        # Verify nodes attribute contains correct node name
        assert all(node['proxmox_node'] in ['pve1', 'pve2'] for node in result)

