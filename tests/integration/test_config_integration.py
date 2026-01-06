"""Integration tests for configuration handling."""
import os
import sys
import pytest
from unittest.mock import Mock, patch
from io import StringIO

# Import the module (imported via conftest)
import proxmox_node_source


class TestConfigIntegration:
    """Integration tests for configuration parsing and precedence."""
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_env_var_precedence_over_cli(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test that environment variables take precedence over CLI arguments."""
        # Set environment variables
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'env-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'env-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'env-pass')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PORT', '8443')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        # Provide CLI args that should be ignored
        test_args = [
            'proxmox-node-source.py',
            '--proxmox-host', 'cli-host',
            '--proxmox-user', 'cli-user',
            '--proxmox-password', 'cli-pass',
            '--proxmox-port', '8006',
        ]
        
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify env vars were used, not CLI args
        mock_proxmox_api.assert_called_once()
        assert mock_proxmox_api.call_args[0][0] == 'env-host'
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['user'] == 'env-user'
        assert call_kwargs['password'] == 'env-pass'
        assert call_kwargs['port'] == 8443
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_cli_args_when_env_vars_missing(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test that CLI args are used when environment variables are not set."""
        # Ensure env vars are not set
        monkeypatch.delenv('RD_CONFIG_PROXMOX_HOST', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_USER', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_PASSWORD', raising=False)
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = [
            'proxmox-node-source.py',
            '--proxmox-host', 'cli-host',
            '--proxmox-user', 'cli-user',
            '--proxmox-password', 'cli-pass',
        ]
        
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify CLI args were used
        mock_proxmox_api.assert_called_once()
        assert mock_proxmox_api.call_args[0][0] == 'cli-host'
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['user'] == 'cli-user'
        assert call_kwargs['password'] == 'cli-pass'
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_password_priority_storage_path_first(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test password priority: storage path > direct password."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD_STORAGE_PATH', 'storage-pass')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'direct-pass')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Storage path should take precedence
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['password'] == 'storage-pass'
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_boolean_flags_from_env(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test boolean flags from environment variables."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_VERIFY_SSL', 'true')
        monkeypatch.setenv('RD_CONFIG_INCLUDE_VMS', 'false')
        monkeypatch.setenv('RD_CONFIG_INCLUDE_CONTAINERS', 'true')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify verify_ssl was True
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['verify_ssl'] is True
        
        # Verify fetch_proxmox_nodes was called with correct flags
        # We need to check the actual call to fetch_proxmox_nodes
        # This is a bit indirect, but we can verify the output
        output = mock_stdout.getvalue()
        import yaml
        data = yaml.safe_load(output)
        # Should only have containers (include_vms=false)
        assert all(node['proxmox_type'] == 'lxc' for node in data)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_default_values(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test that default values are used when not specified."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        # Don't set port, username, or output_format
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify defaults
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['port'] == 8006
        assert call_kwargs['verify_ssl'] is False
        
        # Verify default username in output
        output = mock_stdout.getvalue()
        import yaml
        data = yaml.safe_load(output)
        assert all(node.get('username') == 'root' for node in data)
        
        # Verify default output format is YAML
        assert output  # YAML output should be present
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    def test_missing_host_exits(self, mock_exit, mock_proxmox_api, monkeypatch):
        """Test that missing host causes script to exit."""
        monkeypatch.delenv('RD_CONFIG_PROXMOX_HOST', raising=False)
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        mock_exit.assert_called_once_with(1)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    def test_missing_user_exits(self, mock_exit, mock_proxmox_api, monkeypatch):
        """Test that missing user causes script to exit."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.delenv('RD_CONFIG_PROXMOX_USER', raising=False)
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        mock_exit.assert_called_once_with(1)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    def test_missing_password_exits(self, mock_exit, mock_proxmox_api, monkeypatch):
        """Test that missing password causes script to exit."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.delenv('RD_CONFIG_PROXMOX_PASSWORD', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_PASSWORD_STORAGE_PATH', raising=False)
        
        test_args = ['proxmox-node-source.py']
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        mock_exit.assert_called_once_with(1)
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.stdout', new_callable=StringIO)
    def test_mixed_config_sources(self, mock_stdout, mock_proxmox_api, mock_proxmox, monkeypatch):
        """Test mixing environment variables and CLI arguments."""
        # Set some via env, some via CLI
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'env-host')
        monkeypatch.delenv('RD_CONFIG_PROXMOX_USER', raising=False)
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'env-pass')
        
        mock_proxmox_api.return_value = mock_proxmox
        
        test_args = [
            'proxmox-node-source.py',
            '--proxmox-user', 'cli-user',
        ]
        
        with patch.object(sys, 'argv', test_args):
            proxmox_node_source.main()
        
        # Verify mixed config
        mock_proxmox_api.assert_called_once()
        assert mock_proxmox_api.call_args[0][0] == 'env-host'  # From env
        call_kwargs = mock_proxmox_api.call_args[1]
        assert call_kwargs['user'] == 'cli-user'  # From CLI
        assert call_kwargs['password'] == 'env-pass'  # From env

