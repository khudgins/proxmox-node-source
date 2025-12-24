"""Unit tests for configuration parsing in main function."""
import os
import sys
import pytest
from unittest.mock import Mock, patch, MagicMock

# Import the module (imported via conftest)
import proxmox_node_source


class TestConfigParsing:
    """Test cases for configuration parsing."""
    
    def test_env_vars_take_precedence(self, monkeypatch, mock_proxmox):
        """Test that environment variables take precedence over CLI args."""
        # Set environment variables
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'env-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'env-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'env-pass')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PORT', '8443')
        monkeypatch.setenv('RD_CONFIG_DEFAULT_USERNAME', 'admin')
        monkeypatch.setenv('RD_CONFIG_OUTPUT_FORMAT', 'json')
        
        # Mock ProxmoxAPI
        with patch('proxmox_node_source.ProxmoxAPI') as mock_api:
            mock_api.return_value = mock_proxmox
            
            # Mock sys.argv to simulate CLI args
            test_args = [
                'proxmox-node-source.py',
                '--proxmox-host', 'cli-host',
                '--proxmox-user', 'cli-user',
                '--proxmox-password', 'cli-pass',
                '--proxmox-port', '8006',
                '--default-username', 'root',
                '--output-format', 'yaml',
            ]
            
            with patch.object(sys, 'argv', test_args):
                with patch('proxmox_node_source.fetch_proxmox_nodes', return_value=[]):
                    with patch('proxmox_node_source.output_json', return_value='[]'):
                        proxmox_node_source.main()
            
            # Verify env vars were used, not CLI args
            mock_api.assert_called_once()
            call_kwargs = mock_api.call_args[1]
            assert call_kwargs['user'] == 'env-user'
            # Note: host is positional, so check the first arg
            assert mock_api.call_args[0][0] == 'env-host'
    
    def test_cli_args_when_no_env_vars(self, monkeypatch, mock_proxmox):
        """Test that CLI args are used when env vars are not set."""
        # Ensure env vars are not set
        monkeypatch.delenv('RD_CONFIG_PROXMOX_HOST', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_USER', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_PASSWORD', raising=False)
        
        # Mock ProxmoxAPI
        with patch('proxmox_node_source.ProxmoxAPI') as mock_api:
            mock_api.return_value = mock_proxmox
            
            test_args = [
                'proxmox-node-source.py',
                '--proxmox-host', 'cli-host',
                '--proxmox-user', 'cli-user',
                '--proxmox-password', 'cli-pass',
            ]
            
            with patch.object(sys, 'argv', test_args):
                with patch('proxmox_node_source.fetch_proxmox_nodes', return_value=[]):
                    with patch('proxmox_node_source.output_yaml', return_value='[]'):
                        proxmox_node_source.main()
            
            # Verify CLI args were used
            mock_api.assert_called_once()
            assert mock_api.call_args[0][0] == 'cli-host'
            call_kwargs = mock_api.call_args[1]
            assert call_kwargs['user'] == 'cli-user'
    
    def test_password_from_storage_path_env(self, monkeypatch, mock_proxmox):
        """Test password from storage path environment variable."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD_STORAGE_PATH', 'storage-pass')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        
        with patch('proxmox_node_source.ProxmoxAPI') as mock_api:
            mock_api.return_value = mock_proxmox
            
            test_args = ['proxmox-node-source.py']
            
            with patch.object(sys, 'argv', test_args):
                with patch('proxmox_node_source.fetch_proxmox_nodes', return_value=[]):
                    with patch('proxmox_node_source.output_yaml', return_value='[]'):
                        proxmox_node_source.main()
            
            # Verify storage path password was used
            call_kwargs = mock_api.call_args[1]
            assert call_kwargs['password'] == 'storage-pass'
    
    def test_password_priority_order(self, monkeypatch, mock_proxmox):
        """Test password priority: storage_path > direct password."""
        # Set both
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD_STORAGE_PATH', 'storage-pass')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'direct-pass')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        
        with patch('proxmox_node_source.ProxmoxAPI') as mock_api:
            mock_api.return_value = mock_proxmox
            
            test_args = ['proxmox-node-source.py']
            
            with patch.object(sys, 'argv', test_args):
                with patch('proxmox_node_source.fetch_proxmox_nodes', return_value=[]):
                    with patch('proxmox_node_source.output_yaml', return_value='[]'):
                        proxmox_node_source.main()
            
            # Storage path should take precedence
            call_kwargs = mock_api.call_args[1]
            assert call_kwargs['password'] == 'storage-pass'
    
    def test_required_fields_validation(self, monkeypatch):
        """Test that missing required fields cause error."""
        # Don't set any config
        monkeypatch.delenv('RD_CONFIG_PROXMOX_HOST', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_USER', raising=False)
        monkeypatch.delenv('RD_CONFIG_PROXMOX_PASSWORD', raising=False)
        
        test_args = ['proxmox-node-source.py']
        
        with patch.object(sys, 'argv', test_args):
            with patch('sys.exit') as mock_exit:
                proxmox_node_source.main()
                # Should exit with error
                assert mock_exit.called
    
    def test_boolean_flags_from_env(self, monkeypatch, mock_proxmox):
        """Test boolean flags from environment variables."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        monkeypatch.setenv('RD_CONFIG_VERIFY_SSL', 'true')
        monkeypatch.setenv('RD_CONFIG_INCLUDE_VMS', 'false')
        monkeypatch.setenv('RD_CONFIG_INCLUDE_CONTAINERS', 'true')
        
        with patch('proxmox_node_source.ProxmoxAPI') as mock_api:
            mock_api.return_value = mock_proxmox
            
            test_args = ['proxmox-node-source.py']
            
            with patch.object(sys, 'argv', test_args):
                with patch('proxmox_node_source.fetch_proxmox_nodes') as mock_fetch:
                    with patch('proxmox_node_source.output_yaml', return_value='[]'):
                        proxmox_node_source.main()
                
                # Verify verify_ssl was True
                call_kwargs = mock_api.call_args[1]
                assert call_kwargs['verify_ssl'] is True
                
                # Verify fetch was called with correct flags
                mock_fetch.assert_called_once()
                call_kwargs = mock_fetch.call_args[1]
                assert call_kwargs['include_vms'] is False
                assert call_kwargs['include_containers'] is True
    
    def test_default_values(self, monkeypatch, mock_proxmox):
        """Test that default values are used when not specified."""
        monkeypatch.setenv('RD_CONFIG_PROXMOX_HOST', 'test-host')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_USER', 'test-user')
        monkeypatch.setenv('RD_CONFIG_PROXMOX_PASSWORD', 'test-pass')
        
        with patch('proxmox_node_source.ProxmoxAPI') as mock_api:
            mock_api.return_value = mock_proxmox
            
            test_args = ['proxmox-node-source.py']
            
            with patch.object(sys, 'argv', test_args):
                with patch('proxmox_node_source.fetch_proxmox_nodes', return_value=[]):
                    with patch('proxmox_node_source.output_yaml', return_value='[]'):
                        proxmox_node_source.main()
            
            # Verify defaults
            call_kwargs = mock_api.call_args[1]
            assert call_kwargs['port'] == 8006
            assert call_kwargs['verify_ssl'] is False

