# API Reference

This document provides a reference for using EscaGCP as a Python library.

## Installation

```python
pip install escagcp
```

## Basic Usage

```python
from escagcp import EscaGCP

# Initialize
escagcp = EscaGCP()

# Run full analysis
results = escagcp.run_lazy(projects=['my-project'])
```

## Core Classes

### EscaGCP

Main orchestrator class that coordinates all operations.

```python
class EscaGCP:
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize EscaGCP with optional configuration file.
        
        Args:
            config_file: Path to YAML configuration file
        """
        
    def run_lazy(self, 
                 projects: Optional[List[str]] = None,
                 organization: Optional[str] = None,
                 open_browser: bool = False) -> Dict[str, Any]:
        """
        Run all operations automatically.
        
        Args:
            projects: List of project IDs to scan
            organization: Organization ID to scan
            open_browser: Open visualization after completion
            
        Returns:
            Dictionary with results from all phases
        """
```

### Config

Configuration management class.

```python
class Config:
    @classmethod
    def from_yaml(cls, file_path: str) -> 'Config':
        """Load configuration from YAML file."""
        
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'Config':
        """Create configuration from dictionary."""
        
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value with dot notation."""
```

### AuthManager

Handles GCP authentication.

```python
class AuthManager:
    def __init__(self, config: Config):
        """Initialize with configuration."""
        
    def authenticate(self) -> google.auth.credentials.Credentials:
        """
        Authenticate to GCP and return credentials.
        
        Raises:
            AuthenticationError: If authentication fails
        """
        
    def get_credentials(self) -> google.auth.credentials.Credentials:
        """Get current credentials."""
```

## Data Collection

### CollectionOrchestrator

Coordinates data collection from GCP.

```python
class CollectionOrchestrator:
    def __init__(self, auth_manager: AuthManager, config: Config):
        """Initialize with auth manager and configuration."""
        
    def collect_all(self,
                   organization_id: Optional[str] = None,
                   folder_ids: Optional[List[str]] = None,
                   project_ids: Optional[List[str]] = None,
                   include_logs: bool = False) -> Dict[str, Any]:
        """
        Collect all data from specified scope.
        
        Args:
            organization_id: Organization to scan
            folder_ids: Folders to scan
            project_ids: Projects to scan
            include_logs: Include audit log collection
            
        Returns:
            Dictionary with all collected data
        """
```

### Individual Collectors

```python
# IAM Collector
class IAMCollector:
    def collect_project_iam(self, project_id: str) -> Dict[str, Any]:
        """Collect IAM policies for a project."""
        
    def collect_organization_iam(self, org_id: str) -> Dict[str, Any]:
        """Collect IAM policies for an organization."""

# Identity Collector
class IdentityCollector:
    def collect_service_accounts(self, project_id: str) -> List[Dict]:
        """Collect service accounts in a project."""
        
    def collect_groups(self, customer_id: str) -> List[Dict]:
        """Collect groups in the organization."""

# Resource Collector
class ResourceCollector:
    def collect_compute_instances(self, project_id: str) -> List[Dict]:
        """Collect compute instances."""
        
    def collect_cloud_functions(self, project_id: str) -> List[Dict]:
        """Collect cloud functions."""
        
    def collect_storage_buckets(self, project_id: str) -> List[Dict]:
        """Collect storage buckets."""
```

## Graph Building

### GraphBuilder

Builds a graph from collected data.

```python
class GraphBuilder:
    def __init__(self, config: Config):
        """Initialize with configuration."""
        
    def build_from_collected_data(self, 
                                 data: Dict[str, Any]) -> 'GCPGraph':
        """
        Build graph from collected data.
        
        Args:
            data: Dictionary with collected data
            
        Returns:
            GCPGraph object
        """
        
    def add_iam_edges(self, graph: 'GCPGraph', iam_data: Dict):
        """Add IAM relationship edges to graph."""
        
    def add_resource_edges(self, graph: 'GCPGraph', resources: Dict):
        """Add resource relationship edges to graph."""
```

### GCPGraph

Graph data structure.

```python
class GCPGraph:
    def __init__(self):
        """Initialize empty graph."""
        
    def add_node(self, node: 'Node') -> None:
        """Add a node to the graph."""
        
    def add_edge(self, edge: 'Edge') -> None:
        """Add an edge to the graph."""
        
    def get_node(self, node_id: str) -> Optional['Node']:
        """Get node by ID."""
        
    def get_neighbors(self, node_id: str, 
                     edge_type: Optional['EdgeType'] = None) -> List['Node']:
        """Get neighboring nodes."""
        
    def find_paths(self, source: str, target: str, 
                  max_length: int = 6) -> List['Path']:
        """Find paths between nodes."""
```

### Node and Edge Models

```python
class NodeType(Enum):
    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    GROUP = "group"
    PROJECT = "project"
    FOLDER = "folder"
    ORGANIZATION = "organization"
    ROLE = "role"
    RESOURCE = "resource"

class Node:
    def __init__(self, 
                 node_id: str,
                 node_type: NodeType,
                 properties: Dict[str, Any]):
        """Create a node."""
        
class EdgeType(Enum):
    HAS_ROLE = "has_role"
    CAN_IMPERSONATE_SA = "can_impersonate"
    CAN_CREATE_SERVICE_ACCOUNT_KEY = "can_create_key"
    CAN_ACT_AS_VIA_VM = "can_act_as_vm"
    MEMBER_OF = "member_of"
    # ... more edge types

class Edge:
    def __init__(self,
                 source: str,
                 target: str,
                 edge_type: EdgeType,
                 properties: Dict[str, Any]):
        """Create an edge."""
```

## Analysis

### PathAnalyzer

Analyzes graph for attack paths.

```python
class PathAnalyzer:
    def __init__(self, graph: GCPGraph, config: Config):
        """Initialize with graph and configuration."""
        
    def analyze_all_paths(self) -> Dict[str, Any]:
        """
        Analyze all attack paths in the graph.
        
        Returns:
            Dictionary with categorized attack paths
        """
        
    def find_privilege_escalation_paths(self,
                                      source: Optional[str] = None,
                                      target: Optional[str] = None) -> List['AttackPath']:
        """Find privilege escalation paths."""
        
    def find_lateral_movement_paths(self) -> List['AttackPath']:
        """Find lateral movement paths."""
        
    def calculate_risk_scores(self) -> Dict[str, float]:
        """Calculate risk scores for all nodes."""
```

### AttackPath

Represents an attack path.

```python
class AttackPath:
    def __init__(self, 
                 nodes: List[Node],
                 edges: List[Edge],
                 technique: str):
        """Create an attack path."""
        
    @property
    def risk_score(self) -> float:
        """Calculate risk score for this path."""
        
    def get_path_string(self) -> str:
        """Get human-readable path description."""
        
    def get_remediation(self) -> List[str]:
        """Get remediation recommendations."""
```

## Visualization

### HTMLVisualizer

Creates HTML visualizations.

```python
class HTMLVisualizer:
    def __init__(self, graph: GCPGraph, config: Config):
        """Initialize with graph and configuration."""
        
    def create_dashboard(self,
                        output_file: str,
                        analysis_results: Dict[str, Any],
                        title: str = "EscaGCP Dashboard"):
        """Create interactive dashboard."""
        
    def create_attack_path_visualization(self,
                                       output_file: str,
                                       attack_paths: List[AttackPath]):
        """Create attack path focused visualization."""
```

### GraphMLExporter

Exports to GraphML format.

```python
class GraphMLExporter:
    def export(self, 
              graph: GCPGraph,
              output_file: str,
              include_properties: bool = True):
        """Export graph to GraphML format."""
```

## Utilities

### Query Engine

```python
class QueryEngine:
    def __init__(self, graph: GCPGraph):
        """Initialize with graph."""
        
    def query_permissions(self, 
                         identity: str,
                         resource: Optional[str] = None) -> List[str]:
        """Query what permissions an identity has."""
        
    def query_access(self, identity: str) -> List[str]:
        """Query what resources an identity can access."""
        
    def query_who_has_permission(self,
                                permission: str,
                                resource: str) -> List[str]:
        """Query who has a specific permission."""
```

### Simulator

```python
class Simulator:
    def __init__(self, graph: GCPGraph):
        """Initialize with graph."""
        
    def simulate_add_binding(self,
                           member: str,
                           role: str,
                           resource: str) -> Dict[str, Any]:
        """Simulate adding an IAM binding."""
        
    def simulate_remove_binding(self,
                              member: str,
                              role: str,
                              resource: str) -> Dict[str, Any]:
        """Simulate removing an IAM binding."""
        
    def get_impact_analysis(self) -> Dict[str, Any]:
        """Get impact analysis of simulated changes."""
```

## Error Handling

```python
# Custom exceptions
class EscaGCPError(Exception):
    """Base exception for EscaGCP."""

class AuthenticationError(EscaGCPError):
    """Authentication failed."""

class CollectionError(EscaGCPError):
    """Data collection failed."""

class GraphBuildError(EscaGCPError):
    """Graph building failed."""

class AnalysisError(EscaGCPError):
    """Analysis failed."""
```

## Example: Complete Analysis

```python
from escagcp import (
    EscaGCP, Config, AuthManager, CollectionOrchestrator,
    GraphBuilder, PathAnalyzer, HTMLVisualizer
)

# Configure
config = Config.from_yaml('config.yaml')

# Authenticate
auth = AuthManager(config)
auth.authenticate()

# Collect data
collector = CollectionOrchestrator(auth, config)
data = collector.collect_all(
    organization_id='123456789',
    include_logs=True
)

# Build graph
builder = GraphBuilder(config)
graph = builder.build_from_collected_data(data)

# Analyze
analyzer = PathAnalyzer(graph, config)
results = analyzer.analyze_all_paths()

# Find specific user's escalation paths
user_paths = analyzer.find_privilege_escalation_paths(
    source='user:risky@example.com'
)

# Create visualization
visualizer = HTMLVisualizer(graph, config)
visualizer.create_dashboard(
    'security-dashboard.html',
    analysis_results=results,
    title='Security Analysis Report'
)

# Export for further analysis
from escagcp.graph import GraphMLExporter
exporter = GraphMLExporter()
exporter.export(graph, 'escagcp-graph.graphml')
```

## Extending EscaGCP

### Custom Collectors

```python
from escagcp.collectors import BaseCollector

class CustomCollector(BaseCollector):
    def collect(self, project_id: str) -> Dict[str, Any]:
        """Implement custom collection logic."""
        # Your collection code here
        return collected_data
```

### Custom Analyzers

```python
from escagcp.analyzers import BaseAnalyzer

class CustomAnalyzer(BaseAnalyzer):
    def analyze(self, graph: GCPGraph) -> List[AttackPath]:
        """Implement custom analysis logic."""
        # Your analysis code here
        return attack_paths
```

### Custom Edge Types

```python
from escagcp.graph import EdgeType

# Add custom edge type
EdgeType.CUSTOM_RELATIONSHIP = "custom_relationship"

# Use in graph building
edge = Edge(
    source="node1",
    target="node2",
    edge_type=EdgeType.CUSTOM_RELATIONSHIP,
    properties={"custom_property": "value"}
)
``` 