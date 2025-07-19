"""
GraphML visualization for EscaGCP graphs
"""

import networkx as nx
from typing import Dict, Any, Optional
from ..utils import get_logger, Config


logger = get_logger(__name__)


class GraphMLVisualizer:
    """
    Create GraphML visualizations with risk coloring
    """
    
    def __init__(self, graph: nx.DiGraph, config: Config):
        """
        Initialize GraphML visualizer
        
        Args:
            graph: NetworkX directed graph
            config: Configuration instance
        """
        self.graph = graph
        self.config = config
    
    def export_with_risk_coloring(
        self,
        output_file: str,
        risk_scores: Optional[Dict[str, Any]] = None
    ):
        """
        Export graph to GraphML with risk-based coloring
        
        Args:
            output_file: Output GraphML file path
            risk_scores: Optional risk scores for coloring
        """
        logger.info(f"Creating GraphML visualization: {output_file}")
        
        # Create a copy of the graph to add visual properties
        visual_graph = self.graph.copy()
        
        # Add visual properties to nodes
        for node_id in visual_graph.nodes():
            node_data = visual_graph.nodes[node_id]
            
            # Determine color based on risk
            if risk_scores and node_id in risk_scores:
                risk = risk_scores[node_id].get('total', 0)
                if risk > 0.8:
                    color = self.config.visualization_graphml_risk_colors['critical']
                elif risk > 0.6:
                    color = self.config.visualization_graphml_risk_colors['high']
                elif risk > 0.4:
                    color = self.config.visualization_graphml_risk_colors['medium']
                elif risk > 0.2:
                    color = self.config.visualization_graphml_risk_colors['low']
                else:
                    color = self.config.visualization_graphml_risk_colors['info']
            else:
                # Use default color based on node type
                node_type = node_data.get('type', 'unknown')
                color = self.config.visualization_html_node_colors.get(node_type, '#999999')
            
            # Add visual properties
            visual_graph.nodes[node_id]['viz_color'] = color
            visual_graph.nodes[node_id]['viz_size'] = 20
            if risk_scores and node_id in risk_scores:
                visual_graph.nodes[node_id]['risk_score'] = risk_scores[node_id].get('total', 0)
        
        # Add visual properties to edges
        for u, v in visual_graph.edges():
            edge_data = visual_graph.edges[u, v]
            edge_type = edge_data.get('type', 'unknown')
            
            # Determine edge color
            color = self.config.visualization_html_edge_colors.get(edge_type, '#999999')
            visual_graph.edges[u, v]['viz_color'] = color
            visual_graph.edges[u, v]['viz_width'] = 2
        
        # Export to GraphML
        nx.write_graphml(visual_graph, output_file)
        
        logger.info(f"Exported GraphML with {visual_graph.number_of_nodes()} nodes") 