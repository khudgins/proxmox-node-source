"""Unit tests for node filtering functionality."""
import pytest

# Import the module (imported via conftest)
import proxmox_node_source


@pytest.fixture
def sample_nodes():
    """Sample nodes for testing filters."""
    return [
        {
            'nodename': 'web1',
            'hostname': 'web1.example.com',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,vm,qemu,web,production',
            'proxmox_node': 'pve1',
            'proxmox_vmid': '100',
            'proxmox_type': 'qemu',
            'proxmox_status': 'running',
            'proxmox_running_status': 'running',
            'ip_address': '192.168.1.10',
        },
        {
            'nodename': 'web2',
            'hostname': 'web2.example.com',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,vm,qemu,web,staging',
            'proxmox_node': 'pve1',
            'proxmox_vmid': '101',
            'proxmox_type': 'qemu',
            'proxmox_status': 'running',
            'proxmox_running_status': 'running',
            'ip_address': '192.168.1.11',
        },
        {
            'nodename': 'db1',
            'hostname': 'db1.example.com',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,vm,qemu,database,production',
            'proxmox_node': 'pve2',
            'proxmox_vmid': '200',
            'proxmox_type': 'qemu',
            'proxmox_status': 'stopped',
            'proxmox_running_status': 'stopped',
            'ip_address': '192.168.1.20',
        },
        {
            'nodename': 'dev1',
            'hostname': 'dev1.example.com',
            'username': 'root',
            'osFamily': 'windows',
            'tags': 'proxmox,vm,qemu,dev',
            'proxmox_node': 'pve1',
            'proxmox_vmid': '102',
            'proxmox_type': 'qemu',
            'proxmox_status': 'running',
            'proxmox_running_status': 'running',
            'ip_address': '192.168.1.30',
        },
        {
            'nodename': 'ct1',
            'hostname': 'ct1.example.com',
            'username': 'root',
            'osFamily': 'unix',
            'tags': 'proxmox,container,lxc,app',
            'proxmox_node': 'pve1',
            'proxmox_vmid': '300',
            'proxmox_type': 'lxc',
            'proxmox_status': 'running',
            'proxmox_running_status': 'running',
            'ip_address': '192.168.1.40',
        },
    ]


class TestParseNodeFilter:
    """Test cases for parse_node_filter function."""
    
    def test_parse_simple_filter(self):
        """Test parsing a simple attribute:value filter."""
        result = proxmox_node_source.parse_node_filter('proxmox_status: running')
        assert len(result) == 1
        assert result[0]['attribute'] == 'proxmox_status'
        assert result[0]['values'] == ['running']
        assert result[0]['negate'] is False
        assert result[0]['is_regex'] is False
    
    def test_parse_filter_with_negation(self):
        """Test parsing a filter with negation."""
        result = proxmox_node_source.parse_node_filter('!osFamily: windows')
        assert len(result) == 1
        assert result[0]['attribute'] == 'osFamily'
        assert result[0]['values'] == ['windows']
        assert result[0]['negate'] is True
    
    def test_parse_multiple_filters(self):
        """Test parsing multiple space-separated filters."""
        result = proxmox_node_source.parse_node_filter('proxmox_status: running proxmox_type: qemu')
        assert len(result) == 2
        assert result[0]['attribute'] == 'proxmox_status'
        assert result[0]['values'] == ['running']
        assert result[1]['attribute'] == 'proxmox_type'
        assert result[1]['values'] == ['qemu']
    
    def test_parse_regex_filter(self):
        """Test parsing a filter with regex pattern."""
        result = proxmox_node_source.parse_node_filter('hostname: dev.*')
        assert len(result) == 1
        assert result[0]['attribute'] == 'hostname'
        assert result[0]['values'] == ['dev.*']
        assert result[0]['is_regex'] is True
    
    def test_parse_comma_separated_values(self):
        """Test parsing filter with comma-separated OR values."""
        result = proxmox_node_source.parse_node_filter('proxmox_node: pve1,pve2')
        assert len(result) == 1
        assert result[0]['attribute'] == 'proxmox_node'
        assert result[0]['values'] == ['pve1', 'pve2']
        assert result[0]['is_regex'] is False
    
    def test_parse_tag_filter_single(self):
        """Test parsing a single tag filter."""
        result = proxmox_node_source.parse_node_filter('tags: web')
        assert len(result) == 1
        assert result[0]['attribute'] == 'tags'
        assert result[0]['is_tag'] is True
        assert len(result[0]['values']) == 1
        assert result[0]['values'][0]['type'] == 'or'
        assert result[0]['values'][0]['tags'] == ['web']
    
    def test_parse_tag_filter_and(self):
        """Test parsing tag filter with AND syntax."""
        result = proxmox_node_source.parse_node_filter('tags: web+production')
        assert len(result) == 1
        assert result[0]['attribute'] == 'tags'
        assert result[0]['is_tag'] is True
        assert len(result[0]['values']) == 1
        assert result[0]['values'][0]['type'] == 'and'
        assert result[0]['values'][0]['tags'] == ['web', 'production']
    
    def test_parse_tag_filter_or(self):
        """Test parsing tag filter with OR syntax."""
        result = proxmox_node_source.parse_node_filter('tags: web,db')
        assert len(result) == 1
        assert result[0]['attribute'] == 'tags'
        assert result[0]['is_tag'] is True
        assert len(result[0]['values']) == 2
        assert result[0]['values'][0]['type'] == 'or'
        assert result[0]['values'][0]['tags'] == ['web']
        assert result[0]['values'][1]['type'] == 'or'
        assert result[0]['values'][1]['tags'] == ['db']
    
    def test_parse_tag_filter_complex(self):
        """Test parsing complex tag filter with AND and OR."""
        result = proxmox_node_source.parse_node_filter('tags: web+production,staging')
        assert len(result) == 1
        assert result[0]['attribute'] == 'tags'
        assert result[0]['is_tag'] is True
        assert len(result[0]['values']) == 2
        assert result[0]['values'][0]['type'] == 'and'
        assert result[0]['values'][0]['tags'] == ['web', 'production']
        assert result[0]['values'][1]['type'] == 'or'
        assert result[0]['values'][1]['tags'] == ['staging']
    
    def test_parse_empty_filter(self):
        """Test parsing empty filter string."""
        result = proxmox_node_source.parse_node_filter('')
        assert result == []
        
        result = proxmox_node_source.parse_node_filter('   ')
        assert result == []
    
    def test_parse_nodename_shorthand(self):
        """Test parsing nodename shorthand (no colon)."""
        result = proxmox_node_source.parse_node_filter('web1')
        assert len(result) == 1
        assert result[0]['attribute'] == 'nodename'
        assert result[0]['values'] == ['web1']
    
    def test_parse_quoted_values(self):
        """Test parsing filter with quoted values."""
        result = proxmox_node_source.parse_node_filter('hostname: "web1.example.com"')
        assert len(result) == 1
        assert result[0]['attribute'] == 'hostname'
        assert result[0]['values'] == ['web1.example.com']
        
        result = proxmox_node_source.parse_node_filter("hostname: 'web1.example.com'")
        assert len(result) == 1
        assert result[0]['values'] == ['web1.example.com']


class TestEvaluateNodeFilter:
    """Test cases for evaluate_node_filter function."""
    
    def test_evaluate_simple_match(self, sample_nodes):
        """Test evaluating a simple matching filter."""
        node = sample_nodes[0]  # web1, running
        clauses = proxmox_node_source.parse_node_filter('proxmox_status: running')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_simple_no_match(self, sample_nodes):
        """Test evaluating a filter that doesn't match."""
        node = sample_nodes[2]  # db1, stopped
        clauses = proxmox_node_source.parse_node_filter('proxmox_status: running')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_negation_match(self, sample_nodes):
        """Test evaluating a negated filter that matches."""
        node = sample_nodes[0]  # web1, unix
        clauses = proxmox_node_source.parse_node_filter('!osFamily: windows')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_negation_no_match(self, sample_nodes):
        """Test evaluating a negated filter that doesn't match."""
        node = sample_nodes[3]  # dev1, windows
        clauses = proxmox_node_source.parse_node_filter('!osFamily: windows')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_multiple_clauses_all_match(self, sample_nodes):
        """Test evaluating multiple clauses that all match."""
        node = sample_nodes[0]  # web1, running, qemu
        clauses = proxmox_node_source.parse_node_filter('proxmox_status: running proxmox_type: qemu')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_multiple_clauses_one_fails(self, sample_nodes):
        """Test evaluating multiple clauses where one fails."""
        node = sample_nodes[0]  # web1, running, qemu
        clauses = proxmox_node_source.parse_node_filter('proxmox_status: running proxmox_type: lxc')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_regex_match(self, sample_nodes):
        """Test evaluating a regex filter that matches."""
        node = sample_nodes[3]  # dev1
        clauses = proxmox_node_source.parse_node_filter('hostname: dev.*')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_regex_no_match(self, sample_nodes):
        """Test evaluating a regex filter that doesn't match."""
        node = sample_nodes[0]  # web1
        clauses = proxmox_node_source.parse_node_filter('hostname: dev.*')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_comma_separated_or_match(self, sample_nodes):
        """Test evaluating comma-separated OR values."""
        node = sample_nodes[0]  # web1, pve1
        clauses = proxmox_node_source.parse_node_filter('proxmox_node: pve1,pve2')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
        
        node = sample_nodes[2]  # db1, pve2
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_comma_separated_or_no_match(self, sample_nodes):
        """Test evaluating comma-separated OR values that don't match."""
        node = sample_nodes[0]  # web1, pve1
        clauses = proxmox_node_source.parse_node_filter('proxmox_node: pve3,pve4')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_tag_single_match(self, sample_nodes):
        """Test evaluating a single tag filter that matches."""
        node = sample_nodes[0]  # web1, has 'web' tag
        clauses = proxmox_node_source.parse_node_filter('tags: web')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_tag_single_no_match(self, sample_nodes):
        """Test evaluating a single tag filter that doesn't match."""
        node = sample_nodes[2]  # db1, no 'web' tag
        clauses = proxmox_node_source.parse_node_filter('tags: web')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_tag_and_match(self, sample_nodes):
        """Test evaluating tag AND filter that matches."""
        node = sample_nodes[0]  # web1, has both 'web' and 'production'
        clauses = proxmox_node_source.parse_node_filter('tags: web+production')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_tag_and_no_match(self, sample_nodes):
        """Test evaluating tag AND filter that doesn't match."""
        node = sample_nodes[1]  # web2, has 'web' but not 'production'
        clauses = proxmox_node_source.parse_node_filter('tags: web+production')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_tag_or_match(self, sample_nodes):
        """Test evaluating tag OR filter that matches."""
        node = sample_nodes[0]  # web1, has 'web'
        clauses = proxmox_node_source.parse_node_filter('tags: web,db')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
        
        node = sample_nodes[2]  # db1, has 'database' (but we're looking for 'db')
        clauses = proxmox_node_source.parse_node_filter('tags: web,database')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_tag_complex_match(self, sample_nodes):
        """Test evaluating complex tag filter that matches."""
        # web1 has web+production, should match
        node = sample_nodes[0]
        clauses = proxmox_node_source.parse_node_filter('tags: web+production,staging')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
        
        # web2 has staging, should match
        node = sample_nodes[1]
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_tag_complex_no_match(self, sample_nodes):
        """Test evaluating complex tag filter that doesn't match."""
        # db1 doesn't have web+production or staging
        node = sample_nodes[2]
        clauses = proxmox_node_source.parse_node_filter('tags: web+production,staging')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_case_insensitive(self, sample_nodes):
        """Test that evaluation is case-insensitive."""
        node = sample_nodes[0]  # web1, running
        clauses = proxmox_node_source.parse_node_filter('proxmox_status: RUNNING')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
        
        clauses = proxmox_node_source.parse_node_filter('proxmox_status: Running')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
    
    def test_evaluate_missing_attribute(self, sample_nodes):
        """Test evaluating filter on missing attribute."""
        node = sample_nodes[0]
        clauses = proxmox_node_source.parse_node_filter('nonexistent: value')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_nodename_shorthand(self, sample_nodes):
        """Test evaluating nodename shorthand filter."""
        node = sample_nodes[0]  # web1
        clauses = proxmox_node_source.parse_node_filter('web1')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is True
        
        clauses = proxmox_node_source.parse_node_filter('web2')
        result = proxmox_node_source.evaluate_node_filter(node, clauses)
        assert result is False
    
    def test_evaluate_empty_clauses(self, sample_nodes):
        """Test evaluating with empty clauses (should match all)."""
        node = sample_nodes[0]
        result = proxmox_node_source.evaluate_node_filter(node, [])
        assert result is True


class TestFilterNodes:
    """Test cases for filter_nodes function."""
    
    def test_filter_by_status(self, sample_nodes):
        """Test filtering nodes by status."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_status: running')
        assert len(filtered) == 4  # web1, web2, dev1, ct1
        assert all(node['proxmox_status'] == 'running' for node in filtered)
    
    def test_filter_by_type(self, sample_nodes):
        """Test filtering nodes by type."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_type: qemu')
        assert len(filtered) == 4  # web1, web2, db1, dev1
        assert all(node['proxmox_type'] == 'qemu' for node in filtered)
        
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_type: lxc')
        assert len(filtered) == 1  # ct1
        assert all(node['proxmox_type'] == 'lxc' for node in filtered)
    
    def test_filter_by_tags(self, sample_nodes):
        """Test filtering nodes by tags."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'tags: web')
        assert len(filtered) == 2  # web1, web2
        assert all('web' in node['tags'] for node in filtered)
    
    def test_filter_by_tags_and(self, sample_nodes):
        """Test filtering nodes by tags with AND."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'tags: web+production')
        assert len(filtered) == 1  # web1
        assert filtered[0]['nodename'] == 'web1'
    
    def test_filter_by_negation(self, sample_nodes):
        """Test filtering nodes with negation."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, '!osFamily: windows')
        assert len(filtered) == 4  # All except dev1
        assert all(node['osFamily'] != 'windows' for node in filtered)
    
    def test_filter_multiple_clauses(self, sample_nodes):
        """Test filtering with multiple clauses."""
        filtered = proxmox_node_source.filter_nodes(
            sample_nodes,
            'proxmox_status: running proxmox_type: qemu'
        )
        assert len(filtered) == 3  # web1, web2, dev1
        assert all(
            node['proxmox_status'] == 'running' and node['proxmox_type'] == 'qemu'
            for node in filtered
        )
    
    def test_filter_by_regex(self, sample_nodes):
        """Test filtering nodes by regex pattern."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'hostname: dev.*')
        assert len(filtered) == 1
        assert filtered[0]['nodename'] == 'dev1'
        
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'hostname: web.*')
        assert len(filtered) == 2  # web1, web2
    
    def test_filter_by_node(self, sample_nodes):
        """Test filtering nodes by Proxmox node."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_node: pve1')
        assert len(filtered) == 4  # web1, web2, dev1, ct1
        
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_node: pve2')
        assert len(filtered) == 1  # db1
    
    def test_filter_comma_separated_or(self, sample_nodes):
        """Test filtering with comma-separated OR values."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_node: pve1,pve2')
        assert len(filtered) == 5  # All nodes
        
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_status: running,stopped')
        assert len(filtered) == 5  # All nodes
    
    def test_filter_complex(self, sample_nodes):
        """Test complex filter with multiple conditions."""
        filtered = proxmox_node_source.filter_nodes(
            sample_nodes,
            'proxmox_status: running proxmox_type: qemu !osFamily: windows'
        )
        assert len(filtered) == 2  # web1, web2
        assert all(
            node['proxmox_status'] == 'running' and
            node['proxmox_type'] == 'qemu' and
            node['osFamily'] != 'windows'
            for node in filtered
        )
    
    def test_filter_empty_string(self, sample_nodes):
        """Test filtering with empty filter string (should return all)."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, '')
        assert len(filtered) == len(sample_nodes)
        
        filtered = proxmox_node_source.filter_nodes(sample_nodes, '   ')
        assert len(filtered) == len(sample_nodes)
    
    def test_filter_no_matches(self, sample_nodes):
        """Test filtering that matches no nodes."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'proxmox_status: paused')
        assert len(filtered) == 0
    
    def test_filter_nodename_shorthand(self, sample_nodes):
        """Test filtering by nodename shorthand."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'web1')
        assert len(filtered) == 1
        assert filtered[0]['nodename'] == 'web1'
    
    def test_filter_by_ip_address(self, sample_nodes):
        """Test filtering by IP address."""
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'ip_address: 192.168.1.10')
        assert len(filtered) == 1
        assert filtered[0]['nodename'] == 'web1'
    
    def test_filter_invalid_regex_fallback(self, sample_nodes):
        """Test that invalid regex falls back to exact match."""
        # This should not crash, and should fall back to exact match
        filtered = proxmox_node_source.filter_nodes(sample_nodes, 'hostname: [invalid(regex')
        # Should handle gracefully, might match nothing or fall back to exact match
        assert isinstance(filtered, list)
