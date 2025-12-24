"""Unit tests for output format functions."""
import json
import xml.etree.ElementTree as ET
import pytest
from unittest.mock import patch

# Import the module (imported via conftest)
import proxmox_node_source


class TestOutputFormats:
    """Test cases for output format functions."""
    
    @pytest.fixture
    def sample_nodes(self):
        """Sample Rundeck nodes for testing."""
        return [
            {
                'nodename': 'test-vm',
                'hostname': '192.168.1.100',
                'username': 'root',
                'osFamily': 'unix',
                'tags': 'proxmox,vm',
                'description': 'Test VM',
                'attributes': {
                    'proxmox_node': 'pve1',
                    'proxmox_vmid': '100',
                }
            },
            {
                'nodename': 'test-container',
                'hostname': '192.168.1.101',
                'username': 'root',
                'osFamily': 'unix',
                'tags': 'proxmox,container',
                'description': 'Test Container',
                'attributes': {
                    'proxmox_node': 'pve1',
                    'proxmox_vmid': '200',
                }
            },
        ]
    
    def test_output_json(self, sample_nodes):
        """Test JSON output format."""
        result = proxmox_node_source.output_json(sample_nodes)
        
        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]['nodename'] == 'test-vm'
        assert parsed[1]['nodename'] == 'test-container'
    
    def test_output_json_empty_list(self):
        """Test JSON output with empty list."""
        result = proxmox_node_source.output_json([])
        parsed = json.loads(result)
        assert parsed == []
    
    def test_output_yaml(self, sample_nodes):
        """Test YAML output format."""
        result = proxmox_node_source.output_yaml(sample_nodes)
        
        # Should be valid YAML
        import yaml
        parsed = yaml.safe_load(result)
        assert isinstance(parsed, list)
        assert len(parsed) == 2
        assert parsed[0]['nodename'] == 'test-vm'
        assert parsed[1]['nodename'] == 'test-container'
    
    @patch('proxmox_node_source.YAML_AVAILABLE', False)
    @patch('sys.exit')
    def test_output_yaml_missing_library(self, mock_exit, sample_nodes):
        """Test YAML output when PyYAML is not available."""
        proxmox_node_source.output_yaml(sample_nodes)
        mock_exit.assert_called_once_with(1)
    
    def test_output_yaml_empty_list(self):
        """Test YAML output with empty list."""
        result = proxmox_node_source.output_yaml([])
        import yaml
        parsed = yaml.safe_load(result)
        assert parsed == []
    
    def test_output_xml(self, sample_nodes):
        """Test XML output format."""
        result = proxmox_node_source.output_xml(sample_nodes)
        
        # Should be valid XML
        root = ET.fromstring(result)
        assert root.tag == 'project'
        
        # Should have 2 node elements
        nodes = root.findall('node')
        assert len(nodes) == 2
        
        # Check first node attributes
        node1 = nodes[0]
        assert node1.get('name') == 'test-vm'
        assert node1.get('hostname') == '192.168.1.100'
        assert node1.get('username') == 'root'
        assert node1.get('osFamily') == 'unix'
        assert node1.get('tags') == 'proxmox,vm'
        assert node1.get('description') == 'Test VM'
        
        # Check attributes
        attrs = node1.findall('attribute')
        assert len(attrs) == 2
        attr_dict = {attr.get('name'): attr.get('value') for attr in attrs}
        assert attr_dict['proxmox_node'] == 'pve1'
        assert attr_dict['proxmox_vmid'] == '100'
    
    def test_output_xml_empty_list(self):
        """Test XML output with empty list."""
        result = proxmox_node_source.output_xml([])
        root = ET.fromstring(result)
        assert root.tag == 'project'
        assert len(root.findall('node')) == 0
    
    def test_output_xml_has_declaration(self, sample_nodes):
        """Test that XML output includes XML declaration."""
        result = proxmox_node_source.output_xml(sample_nodes)
        assert result.startswith('<?xml')
    
    def test_output_xml_all_node_fields(self, sample_nodes):
        """Test that XML includes all node fields."""
        result = proxmox_node_source.output_xml(sample_nodes)
        root = ET.fromstring(result)
        node = root.find('node')
        
        # Check all expected attributes are present
        assert node.get('name') is not None
        assert node.get('hostname') is not None
        assert node.get('username') is not None
        assert node.get('osFamily') is not None
        assert node.get('tags') is not None
        assert node.get('description') is not None

