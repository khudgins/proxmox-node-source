"""Integration tests for full script execution."""
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Import the module (imported via conftest)
import proxmox_node_source


class TestFullExecution:
    """Test cases for full script execution."""
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_with_env_vars(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test full execution using environment variables."""
        # Set environment variables
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_OUTPUT_FORMAT', 'json')
        
        # Mock ProxmoxAPI
        mock_proxmox_api.return_value = mock_proxmox
        
        # Mock sys.argv
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify output
        output = mock_stdout.getvalue()
        assert output
        # Should be valid JSON
        import json
        data = json.loads(output)
        assert isinstance(data, list)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_with_cli_args(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test full execution using command-line arguments."""
        # Ensure env vars are not set
        monkeypatch.delenv('RD_CONFIG_PROXMOX_HOST', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_USER', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_PASSWORD', raising=False)
        
        # Mock ProxmoxAPI
        mock_proxmox_api.return_value = mock_proxmox
        
        # Mock sys.argv with CLI args
        test_args = [
            'proxmox-node-source.py',
            '--proxmox-host', 'cli-host',
            '--proxmox-user', 'cli-user',
            '--proxmox-password', 'cli-pass',
            '--output-format', 'yaml',
        ]
        
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify output
        output = mock_stdout.getvalue()
        assert output
        # Should be valid YAML
        import yaml
        data = yaml.safe_load(output)
        assert isinstance(data, list)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_xml_output(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test full execution with XML output format."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_OUTPUT_FORMAT', 'xml')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        output = mock_stdout.getvalue()
        assert output.startswith('<?xml')
        # Should be valid XML
        import xml.etree.ElementTree as ET
        root = ET.fromstring(output)
        assert root.tag == 'project'
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    def test_full_execution_missing_required_fields(self, mock_exit, mock_proxmox_api, monkeypatch):
        """Test that missing required fields cause script to exit."""
        # Don't set any required config
        monkeypatch.delenv('RD_CONFIG_PROXMOX_HOST', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_USER', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_PASSWORD', raising=False)
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Script exits for each missing required field (host, user, password)
        assert mock_exit.called
        assert mock_exit.call_args[0][0] == 1
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    def test_full_execution_authentication_error(self, mock_exit, mock_proxmox_api, monkeypatch):
        """Test handling of authentication errors."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'wrong-pass')
        
        # Mock ProxmoxAPI to raise authentication error
        mock_proxmox = Mock()
        mock_proxmox.version.get.side_effect = Exception("Couldn't authenticate user")
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Script exits in get_proxmox_connection when authentication fails
        assert mock_exit.called
        assert mock_exit.call_args[0][0] == 1
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_with_custom_username(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test that custom default username is applied to nodes."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_DEFAULT_USERNAME', 'admin')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        output = mock_stdout.getvalue()
        import yaml
        data = yaml.safe_load(output)
        # All nodes should have username 'admin'
        assert all(node.get('username') == 'admin' for node in data)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_exclude_vms(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test excluding VMs from output."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_INCLUDE_VMS', 'false')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        output = mock_stdout.getvalue()
        import yaml
        data = yaml.safe_load(output)
        # Should only have containers, no VMs
        assert all(node['attributes']['proxmox_type'] == 'lxc' for node in data)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_exclude_containers(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test excluding containers from output."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_INCLUDE_CONTAINERS', 'false')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        output = mock_stdout.getvalue()
        import yaml
        data = yaml.safe_load(output)
        # Should only have VMs, no containers
        assert all(node['attributes']['proxmox_type'] == 'qemu' for node in data)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_verify_ssl(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test SSL verification flag."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_VERIFY_SSL', 'true')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify SSL verification was enabled
        mock_proxmox_api.assert_called_once()
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['verify_ssl'] is True
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_custom_port(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test custom Proxmox port."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PORT', '8443')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify custom port was used
        mock_proxmox_api.assert_called_once()
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['port'] == 8443
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_full_execution_password_from_storage_path(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test password from storage path environment variable."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD_STORAGE_PATH', 'storage-password')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify storage path password was used
        mock_proxmox_api.assert_called_once()
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['password'] == 'storage-password'
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    def test_full_execution_api_error(self, mock_exit, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test handling of API errors during node fetching."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        
        # Make nodes.get() raise an error
        mock_proxmox.nodes.get.side_effect = Exception("API Error")
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        mock_exit.assert_called_once_with(1)

