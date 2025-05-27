"""Unit tests for enhanced modal functionality in HTML visualizer"""

import pytest
import json
import networkx as nx
from gcphound.visualizers.html import HTMLVisualizer
from gcphound.utils import Config


class TestEnhancedModals:
    """Test suite for enhanced modal functionality"""
    
    @pytest.fixture
    def sample_graph(self):
        """Create a sample graph for testing"""
        graph = nx.DiGraph()
        
        # Add nodes with metadata
        graph.add_node("user:test@example.com", 
                      type="user", 
                      name="test@example.com",
                      email="test@example.com")
        
        graph.add_node("sa:service@project.iam",
                      type="service_account",
                      name="service@project.iam",
                      email="service@project.iam.gserviceaccount.com",
                      project_id="test-project")
        
        graph.add_node("role:roles/editor",
                      type="role",
                      name="roles/editor",
                      description="Editor role")
        
        graph.add_node("project:test-project",
                      type="project",
                      name="test-project",
                      project_id="test-project")
        
        # Add edges with metadata
        graph.add_edge("user:test@example.com", "role:roles/editor", 
                      type="HAS_ROLE")
        
        graph.add_edge("user:test@example.com", "sa:service@project.iam",
                      type="CAN_IMPERSONATE_SA",
                      permission="iam.serviceAccounts.getAccessToken")
        
        return graph
    
    @pytest.fixture
    def visualizer(self, sample_graph):
        """Create a visualizer instance"""
        config = Config()
        return HTMLVisualizer(sample_graph, config)
    
    def test_nodes_list_html_generation(self, visualizer):
        """Test that nodes list HTML includes enhanced data"""
        nodes_by_type = visualizer._get_nodes_by_type()
        html = visualizer._create_nodes_list_html(nodes_by_type)
        
        # Check that the HTML contains the modal container
        assert 'id="nodes-modal-root"' in html
        
        # Check that the JavaScript data is embedded
        assert 'window.nodesModalData' in html
        
        # Parse the embedded data
        import re
        match = re.search(r'window\.nodesModalData = ({.*?});', html, re.DOTALL)
        assert match is not None
        
        nodes_data = json.loads(match.group(1))
        
        # Verify node data structure
        assert 'user' in nodes_data
        assert 'service_account' in nodes_data
        assert 'role' in nodes_data
        assert 'project' in nodes_data
        
        # Check user node
        user_nodes = nodes_data['user']
        assert len(user_nodes) == 1
        user_node = user_nodes[0]
        assert user_node['id'] == 'user:test@example.com'
        assert user_node['name'] == 'test@example.com'
        assert user_node['type'] == 'user'
        assert 'inDegree' in user_node
        assert 'outDegree' in user_node
        assert 'metadata' in user_node
        assert user_node['metadata']['email'] == 'test@example.com'
        
        # Check service account node
        sa_nodes = nodes_data['service_account']
        assert len(sa_nodes) == 1
        sa_node = sa_nodes[0]
        assert sa_node['metadata']['projectId'] == 'test-project'
    
    def test_edges_list_html_generation(self, visualizer):
        """Test that edges list HTML includes enhanced data"""
        edges_by_type = visualizer._get_edges_by_type()
        html = visualizer._create_edges_list_html(edges_by_type)
        
        # Check that the HTML contains the modal container
        assert 'id="edges-modal-root"' in html
        
        # Check that the JavaScript data is embedded
        assert 'window.edgesModalData' in html
        
        # Parse the embedded data
        import re
        match = re.search(r'window\.edgesModalData = ({.*?});', html, re.DOTALL)
        assert match is not None
        
        edges_data = json.loads(match.group(1))
        
        # Verify edge data structure
        assert 'HAS_ROLE' in edges_data
        assert 'CAN_IMPERSONATE_SA' in edges_data
        
        # Check impersonation edge
        impersonate_edges = edges_data['CAN_IMPERSONATE_SA']
        assert len(impersonate_edges) == 1
        edge = impersonate_edges[0]
        assert edge['source'] == 'user:test@example.com'
        assert edge['target'] == 'sa:service@project.iam'
        assert edge['type'] == 'CAN_IMPERSONATE_SA'
        assert edge['sourceName'] == 'test@example.com'
        assert edge['targetName'] == 'service@project.iam'
        assert edge['permission'] == 'iam.serviceAccounts.getAccessToken'
        assert 'rationale' in edge
    
    def test_node_degree_calculation(self, visualizer):
        """Test that node degrees are calculated correctly"""
        nodes_by_type = visualizer._get_nodes_by_type()
        html = visualizer._create_nodes_list_html(nodes_by_type)
        
        import re
        match = re.search(r'window\.nodesModalData = ({.*?});', html, re.DOTALL)
        nodes_data = json.loads(match.group(1))
        
        # Check degrees for user node (1 in, 2 out)
        user_node = nodes_data['user'][0]
        assert user_node['inDegree'] == 0  # No incoming edges
        assert user_node['outDegree'] == 2  # Two outgoing edges
        
        # Check degrees for service account (1 in, 0 out)
        sa_node = nodes_data['service_account'][0]
        assert sa_node['inDegree'] == 1  # One incoming edge
        assert sa_node['outDegree'] == 0  # No outgoing edges
    
    def test_edge_metadata_extraction(self, visualizer):
        """Test that edge metadata is properly extracted"""
        edges_by_type = visualizer._get_edges_by_type()
        html = visualizer._create_edges_list_html(edges_by_type)
        
        import re
        match = re.search(r'window\.edgesModalData = ({.*?});', html, re.DOTALL)
        edges_data = json.loads(match.group(1))
        
        # Check that permissions are included
        edge = edges_data['CAN_IMPERSONATE_SA'][0]
        assert edge['permission'] == 'iam.serviceAccounts.getAccessToken'
        
        # Check that rationale is generated
        assert 'has Token Creator role on' in edge['rationale']
    
    def test_react_modal_integration(self, visualizer):
        """Test that React modal integration is included"""
        html = visualizer._create_react_modal_integration()
        
        # Check for React CDN links
        assert 'unpkg.com/react@18' in html
        assert 'unpkg.com/react-dom@18' in html
        
        # Check for modal containers
        assert 'id="nodes-modal-container"' in html
        assert 'id="edges-modal-container"' in html
        
        # Check for Tailwind-like CSS classes
        assert '.flex' in html
        assert '.gap-4' in html
        assert '.rounded-lg' in html
        assert '.badge' in html
    
    def test_dashboard_javascript_modal_functions(self, visualizer):
        """Test that dashboard JavaScript includes modal functions"""
        js = visualizer._get_dashboard_javascript()
        
        # Check for modal functions
        assert 'function showModal' in js
        assert 'function showNodesModal' in js
        assert 'function showEdgesModal' in js
        assert 'function filterNodes' in js
        assert 'function filterEdges' in js
        assert 'function highlightNode' in js
        
        # Check for React modal handling
        assert "if (modalType === 'nodes')" in js
        assert "if (modalType === 'edges')" in js
        assert 'window.nodesModalData' in js
        assert 'window.edgesModalData' in js
    
    def test_full_dashboard_generation(self, visualizer):
        """Test that the full dashboard includes all enhanced modal components"""
        risk_scores = {"user:test@example.com": 0.8}
        attack_paths = []
        
        html = visualizer._create_dashboard_html(risk_scores, attack_paths, None)
        
        # Check that React modal integration is included
        assert 'nodes-modal-container' in html
        assert 'edges-modal-container' in html
        
        # Check that modal data is embedded
        assert 'window.nodesModalData' in html
        assert 'window.edgesModalData' in html
        
        # Check that the stats bar still works
        assert 'onclick="showModal(\'nodes\')"' in html
        assert 'onclick="showModal(\'edges\')"' in html
    
    def test_clean_node_name(self, visualizer):
        """Test the _clean_node_name method"""
        # Test various node name formats
        assert visualizer._clean_node_name("user:alice@example.com") == "alice@example.com"
        assert visualizer._clean_node_name("sa:compute@project.iam.gserviceaccount.com") == "compute"
        assert visualizer._clean_node_name("roles/editor") == "editor"
        assert visualizer._clean_node_name("project:my-project") == "my-project"
        assert visualizer._clean_node_name("Unknown") == "Unknown"
        assert visualizer._clean_node_name("") == "" 