"""Unit tests for get_proxmox_connection function."""
import sys
from unittest.mock import Mock, patch, MagicMock

import pytest

# Import the module (imported via conftest)
import proxmox_node_source


class TestGetProxmoxConnection:
    """Test cases for get_proxmox_connection function."""
    
    @patch('proxmox_node_source.ProxmoxAPI')
    def test_successful_connection(self, mock_proxmox_api_class):
        """Test successful Proxmox connection."""
        # Setup mock
        mock_proxmox = Mock()
        mock_proxmox.version.get.return_value = {'version': '7.4-1'}
        mock_proxmox_api_class.return_value = mock_proxmox
        
        # Call function
        result = proxmox_node_source.get_proxmox_connection(
            host='10.0.0.4',
            user='root@pam',
            password='testpass',
            verify_ssl=False,
            port=8006
        )
        
        # Assertions
        assert result == mock_proxmox
        mock_proxmox_api_class.assert_called_once_with(
            '10.0.0.4',
            user='root@pam',
            password='testpass',
            verify_ssl=False,
            port=8006,
            backend='https'
        )
        mock_proxmox.version.get.assert_called_once()
    
    @patch('proxmox_node_source.ProxmoxAPI')
    def test_connection_with_ssl_verification(self, mock_proxmox_api_class):
        """Test connection with SSL verification enabled."""
        mock_proxmox = Mock()
        mock_proxmox.version.get.return_value = {'version': '7.4-1'}
        mock_proxmox_api_class.return_value = mock_proxmox
        
        result = proxmox_node_source.get_proxmox_connection(
            host='10.0.0.4',
            user='root@pam',
            password='testpass',
            verify_ssl=True,
            port=8006
        )
        
        assert result == mock_proxmox
        mock_proxmox_api_class.assert_called_once_with(
            '10.0.0.4',
            user='root@pam',
            password='testpass',
            verify_ssl=True,
            port=8006,
            backend='https'
        )
    
    @patch('proxmox_node_source.ProxmoxAPI')
    def test_connection_custom_port(self, mock_proxmox_api_class):
        """Test connection with custom port."""
        mock_proxmox = Mock()
        mock_proxmox.version.get.return_value = {'version': '7.4-1'}
        mock_proxmox_api_class.return_value = mock_proxmox
        
        result = proxmox_node_source.get_proxmox_connection(
            host='10.0.0.4',
            user='root@pam',
            password='testpass',
            verify_ssl=False,
            port=8443
        )
        
        assert result == mock_proxmox
        mock_proxmox_api_class.assert_called_once_with(
            '10.0.0.4',
            user='root@pam',
            password='testpass',
            verify_ssl=False,
            port=8443,
            backend='https'
        )
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    @patch('sys.stderr')
    def test_authentication_error(self, mock_stderr, mock_exit, mock_proxmox_api_class):
        """Test handling of authentication errors."""
        # Setup mock to raise authentication error
        mock_proxmox = Mock()
        mock_proxmox.version.get.side_effect = Exception("Couldn't authenticate user")
        mock_proxmox_api_class.return_value = mock_proxmox
        
        # Call function
        proxmox_node_source.get_proxmox_connection(
            host='10.0.0.4',
            user='root@pam',
            password='wrongpass',
            verify_ssl=False,
            port=8006
        )
        
        # Should exit with error
        mock_exit.assert_called_once_with(1)
        # Check that error message was printed
        assert mock_stderr.write.called
    
    @patch('proxmox_node_source.ProxmoxAPI')
    @patch('sys.exit')
    def test_connection_error(self, mock_exit, mock_proxmox_api_class):
        """Test handling of general connection errors."""
        # Setup mock to raise connection error
        mock_proxmox_api_class.side_effect = Exception("Connection refused")
        
        # Call function
        proxmox_node_source.get_proxmox_connection(
            host='10.0.0.4',
            user='root@pam',
            password='testpass',
            verify_ssl=False,
            port=8006
        )
        
        # Should exit with error
        mock_exit.assert_called_once_with(1)

