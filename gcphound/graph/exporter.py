"""
Graph export functionality for various formats
"""

import json
import csv
from pathlib import Path
import networkx as nx
from typing import Dict, Any, Optional
from ..utils import get_logger, Config
from .models import Node, NodeType, EdgeType
from enum import Enum


logger = get_logger(__name__)


class GraphExporter:
    """
    Export graph to various formats
    """
    
    def __init__(self, graph: nx.DiGraph, nodes: Dict[str, Node], config: Config):
        """
        Initialize graph exporter
        
        Args:
            graph: NetworkX directed graph
            nodes: Dictionary of node ID to Node objects
            config: Configuration instance
        """
        self.graph = graph
        self.nodes = nodes
        self.config = config
    
    def export_json(self, output_file: str):
        """
        Export graph to JSON format
        
        Args:
            output_file: Output file path
        """
        logger.info(f"Exporting graph to JSON: {output_file}")
        
        # Prepare data
        data = {
            'nodes': [node.to_dict() for node in self.nodes.values()],
            'edges': [],
            'metadata': {
                'total_nodes': self.graph.number_of_nodes(),
                'total_edges': self.graph.number_of_edges(),
                'node_types': self._count_node_types(),
                'edge_types': self._count_edge_types()
            }
        }
        
        # Add edges
        for u, v, edge_data in self.graph.edges(data=True):
            edge_dict = {
                'source': u,
                'target': v,
                'type': edge_data.get('type', 'unknown'),
                'properties': {k: v for k, v in edge_data.items() if k != 'type'}
            }
            data['edges'].append(edge_dict)
        
        # Write to file
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        logger.info(f"Exported {len(data['nodes'])} nodes and {len(data['edges'])} edges")
    
    def export_graphml(self, output_file: str):
        """
        Export graph to GraphML format
        
        Args:
            output_file: Output file path
        """
        logger.info(f"Exporting graph to GraphML: {output_file}")
        
        # Create a copy of the graph with serializable attributes
        export_graph = nx.DiGraph()
        
        # Add nodes with serialized attributes
        for node_id, attrs in self.graph.nodes(data=True):
            serialized_attrs = {}
            for key, value in attrs.items():
                if isinstance(value, (dict, list)):
                    serialized_attrs[key] = json.dumps(value)
                elif isinstance(value, Enum):
                    serialized_attrs[key] = value.value
                else:
                    serialized_attrs[key] = str(value)
            export_graph.add_node(node_id, **serialized_attrs)
        
        # Add edges with serialized attributes
        for u, v, attrs in self.graph.edges(data=True):
            serialized_attrs = {}
            for key, value in attrs.items():
                if isinstance(value, (dict, list)):
                    serialized_attrs[key] = json.dumps(value)
                elif isinstance(value, Enum):
                    serialized_attrs[key] = value.value
                else:
                    serialized_attrs[key] = str(value)
            export_graph.add_edge(u, v, **serialized_attrs)
        
        # Write to file
        nx.write_graphml(export_graph, output_file)
        
        logger.info(f"Exported graph with {self.graph.number_of_nodes()} nodes")
    
    def export_neo4j_csv(self, output_dir: str):
        """
        Export graph to Neo4j CSV format
        
        Args:
            output_dir: Output directory for CSV files
        """
        logger.info(f"Exporting graph to Neo4j CSV format: {output_dir}")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Export nodes
        nodes_file = output_path / 'nodes.csv'
        with open(nodes_file, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['nodeId:ID', 'name', 'type:LABEL', 'properties'])
            
            # Nodes
            for node_id, node in self.nodes.items():
                writer.writerow([
                    node_id,
                    node.name,
                    node.type.value.upper(),
                    json.dumps(node.properties)
                ])
        
        # Export edges
        edges_file = output_path / 'edges.csv'
        with open(edges_file, 'w', newline='') as f:
            writer = csv.writer(f)
            # Header
            writer.writerow(['sourceId:START_ID', 'targetId:END_ID', 'type:TYPE', 'properties'])
            
            # Edges
            for u, v, edge_data in self.graph.edges(data=True):
                edge_type = edge_data.get('type', 'RELATED_TO')
                properties = {k: v for k, v in edge_data.items() if k != 'type'}
                writer.writerow([
                    u,
                    v,
                    edge_type.upper().replace('_', '_'),
                    json.dumps(properties)
                ])
        
        logger.info(f"Exported Neo4j CSV files to {output_dir}")
    
    def export_cypher(self, output_file: str):
        """
        Export graph as Cypher queries
        
        Args:
            output_file: Output file path
        """
        logger.info(f"Exporting graph to Cypher: {output_file}")
        
        with open(output_file, 'w') as f:
            # Write header
            f.write("// EscaGCP Graph Export - Cypher Queries\n")
            f.write("// Clear existing data\n")
            f.write("MATCH (n) DETACH DELETE n;\n\n")
            
            # Create nodes
            f.write("// Create nodes\n")
            for node_id, node in self.nodes.items():
                label = node.type.value.upper()
                props = {
                    'id': node_id,
                    'name': node.name,
                    **node.properties
                }
                props_str = ', '.join([f"{k}: {json.dumps(v)}" for k, v in props.items()])
                f.write(f"CREATE (:{label} {{{props_str}}});\n")
            
            f.write("\n// Create relationships\n")
            
            # Create edges
            for u, v, edge_data in self.graph.edges(data=True):
                edge_type = edge_data.get('type', 'RELATED_TO').upper()
                properties = {k: v for k, v in edge_data.items() if k != 'type'}
                
                if properties:
                    props_str = ', '.join([f"{k}: {json.dumps(v)}" for k, v in properties.items()])
                    f.write(
                        f"MATCH (a {{id: '{u}'}}), (b {{id: '{v}'}}) "
                        f"CREATE (a)-[:{edge_type} {{{props_str}}}]->(b);\n"
                    )
                else:
                    f.write(
                        f"MATCH (a {{id: '{u}'}}), (b {{id: '{v}'}}) "
                        f"CREATE (a)-[:{edge_type}]->(b);\n"
                    )
        
        logger.info(f"Exported Cypher queries to {output_file}")
    
    def _count_node_types(self) -> Dict[str, int]:
        """Count nodes by type"""
        counts = {}
        for node in self.nodes.values():
            node_type = node.type.value
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts
    
    def _count_edge_types(self) -> Dict[str, int]:
        """Count edges by type"""
        counts = {}
        for u, v, data in self.graph.edges(data=True):
            edge_type = data.get('type', 'unknown')
            counts[edge_type] = counts.get(edge_type, 0) + 1
        return counts 