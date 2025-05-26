"""
Attack path analyzer for finding privilege escalation and lateral movement paths
"""

import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict
from ..graph.models import Node, Edge, NodeType, EdgeType, AttackPath
from ..utils import get_logger, Config, ProgressLogger


logger = get_logger(__name__)


class PathAnalyzer:
    """
    Analyzes the graph for attack paths and security risks
    """
    
    # Edge types that can lead to privilege escalation
    ESCALATION_EDGE_TYPES = {
        EdgeType.CAN_IMPERSONATE,
        EdgeType.CAN_IMPERSONATE_SA,
        EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY,
        EdgeType.CAN_ACT_AS_VIA_VM,
        EdgeType.CAN_DEPLOY_FUNCTION_AS,
        EdgeType.CAN_DEPLOY_CLOUD_RUN_AS,
        EdgeType.CAN_TRIGGER_BUILD_AS,
        EdgeType.CAN_LOGIN_TO_VM,
        EdgeType.CAN_SATISFY_IAM_CONDITION,
        EdgeType.EXTERNAL_PRINCIPAL_CAN_IMPERSONATE,
        EdgeType.CAN_HIJACK_WORKLOAD_IDENTITY,
        EdgeType.CAN_MODIFY_CUSTOM_ROLE,
        EdgeType.CAN_LAUNCH_AS_DEFAULT_SA,
        EdgeType.CAN_ATTACH_SERVICE_ACCOUNT,
        EdgeType.CAN_UPDATE_METADATA,
        EdgeType.CAN_DEPLOY_GKE_POD_AS,
        EdgeType.CAN_ASSIGN_CUSTOM_ROLE,
        EdgeType.HAS_TAG_BINDING_ESCALATION,
        EdgeType.CAN_SSH_AND_IMPERSONATE,
        EdgeType.HAS_ESCALATED_PRIVILEGE
    }
    
    # High-value target roles
    HIGH_VALUE_ROLES = {
        'roles/owner',
        'roles/editor',
        'roles/iam.securityAdmin',
        'roles/iam.serviceAccountAdmin',
        'roles/iam.serviceAccountTokenCreator',
        'roles/resourcemanager.organizationAdmin',
        'roles/resourcemanager.folderAdmin',
        'roles/resourcemanager.projectIamAdmin'
    }
    
    def __init__(self, graph: nx.DiGraph, config: Config):
        """
        Initialize path analyzer
        
        Args:
            graph: NetworkX directed graph
            config: Configuration instance
        """
        self.graph = graph
        self.config = config
        self._attack_paths = defaultdict(list)
        self._risk_scores = {}
        self._vulnerabilities = []
        self._critical_nodes = []
    
    def analyze_all_paths(self) -> Dict[str, Any]:
        """
        Perform comprehensive path analysis
        
        Returns:
            Analysis results dictionary
        """
        logger.info("Starting comprehensive path analysis")
        
        # Find privilege escalation paths
        self._find_privilege_escalation_paths()
        
        # Find lateral movement paths
        self._find_lateral_movement_paths()
        
        # Calculate risk scores
        self._calculate_risk_scores()
        
        # Identify critical nodes
        self._identify_critical_nodes()
        
        # Detect vulnerabilities
        self._detect_vulnerabilities()
        
        # Compile results
        results = {
            'attack_paths': dict(self._attack_paths),
            'risk_scores': self._risk_scores,
            'critical_nodes': self._critical_nodes,
            'vulnerabilities': self._vulnerabilities,
            'statistics': self._calculate_statistics()
        }
        
        logger.info(f"Analysis complete. Found {self._calculate_statistics()['total_attack_paths']} attack paths")
        
        return results
    
    def find_paths_from_identity(self, identity_id: str) -> List[AttackPath]:
        """
        Find all attack paths from a specific identity
        
        Args:
            identity_id: Identity node ID
            
        Returns:
            List of attack paths
        """
        paths = []
        
        # Find paths to service accounts (impersonation)
        for node_id in self.graph.nodes():
            if node_id.startswith('sa:') and node_id != identity_id:
                try:
                    for path in nx.all_simple_paths(
                        self.graph,
                        identity_id,
                        node_id,
                        cutoff=self.config.analysis_max_path_length
                    ):
                        attack_path = self._build_attack_path(path)
                        if attack_path:
                            paths.append(attack_path)
                except nx.NetworkXNoPath:
                    continue
        
        return paths
    
    def _find_privilege_escalation_paths(self):
        """Find paths that lead to privilege escalation"""
        logger.info("Finding privilege escalation paths")
        
        # Find all edges that represent privilege escalation
        escalation_edges = []
        for source, target, data in self.graph.edges(data=True):
            edge_type_str = data.get('type')
            if edge_type_str:
                try:
                    edge_type = EdgeType(edge_type_str)
                    if edge_type in self.ESCALATION_EDGE_TYPES:
                        escalation_edges.append((source, target, edge_type, data))
                except ValueError:
                    # Unknown edge type
                    continue
        
        logger.info(f"Found {len(escalation_edges)} privilege escalation edges")
        
        # For each escalation edge, create an attack path
        for source, target, edge_type, edge_data in escalation_edges:
            # Create a simple path from source to target
            path = [source, target]
            attack_path = self._build_attack_path(path)
            
            if attack_path:
                # Add details about the escalation
                attack_path.description = f"{edge_type.value}: {source} -> {target}"
                if 'via_role' in edge_data:
                    attack_path.description += f" (via {edge_data['via_role']})"
                
                # Categorize by severity
                if edge_type in {EdgeType.CAN_IMPERSONATE_SA, EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY}:
                    self._attack_paths['critical'].append(attack_path)
                elif edge_type in {EdgeType.CAN_DEPLOY_FUNCTION_AS, EdgeType.CAN_DEPLOY_CLOUD_RUN_AS}:
                    self._attack_paths['high'].append(attack_path)
                else:
                    self._attack_paths['medium'].append(attack_path)
        
        # Also find multi-hop paths
        identity_nodes = [n for n in self.graph.nodes() if n.startswith(('user:', 'sa:', 'group:'))]
        high_value_targets = [n for n in self.graph.nodes() if n.startswith(('org:', 'folder:', 'project:'))]
        
        for identity in identity_nodes:
            for target in high_value_targets:
                try:
                    paths = nx.all_simple_paths(
                        self.graph,
                        identity,
                        target,
                        cutoff=self.config.analysis_max_path_length
                    )
                    
                    for path in paths:
                        # Check if path contains escalation edges
                        has_escalation = False
                        for i in range(len(path) - 1):
                            edge_data = self.graph.get_edge_data(path[i], path[i + 1])
                            if edge_data:
                                edge_type_str = edge_data.get('type')
                                if edge_type_str:
                                    try:
                                        edge_type = EdgeType(edge_type_str)
                                        if edge_type in self.ESCALATION_EDGE_TYPES:
                                            has_escalation = True
                                            break
                                    except ValueError:
                                        continue
                        
                        if has_escalation:
                            attack_path = self._build_attack_path(path)
                            if attack_path:
                                self._attack_paths['privilege_escalation'].append(attack_path)
                            
                except nx.NetworkXNoPath:
                    continue
    
    def _find_lateral_movement_paths(self):
        """Find paths for lateral movement between projects"""
        logger.info("Finding lateral movement paths")
        
        # Find cross-project access paths
        project_nodes = [n for n in self.graph.nodes() if n.startswith('project:')]
        
        for i, proj1 in enumerate(project_nodes):
            for proj2 in project_nodes[i+1:]:
                # Find identities that can access both projects
                identities_proj1 = set(self.graph.predecessors(proj1))
                identities_proj2 = set(self.graph.predecessors(proj2))
                
                common_identities = identities_proj1 & identities_proj2
                
                for identity in common_identities:
                    # Create a lateral movement path
                    path = [identity, proj1, identity, proj2]
                    attack_path = self._build_attack_path(path)
                    if attack_path:
                        self._attack_paths['lateral_movement'].append(attack_path)
    
    def _calculate_risk_scores(self):
        """Calculate risk scores for all nodes"""
        logger.info("Calculating risk scores")
        
        # Node risk scores
        for node_id in self.graph.nodes():
            node_data = self.graph.nodes[node_id]
            
            # Base risk from node type
            risk = 0.0
            
            # Check if it's a high-value target
            if node_id.startswith('org:'):
                risk += 0.3
            elif node_id.startswith('folder:'):
                risk += 0.25
            elif node_id.startswith('project:'):
                risk += 0.2
            elif node_id.startswith('sa:'):
                risk += 0.15
            
            # Check for dangerous roles
            if node_id.startswith('role:'):
                if any(r in node_id for r in self.config.analysis_dangerous_roles):
                    risk += 0.5
            
            # Factor in degree centrality
            centrality = nx.degree_centrality(self.graph).get(node_id, 0)
            risk += centrality * 0.2
            
            self._risk_scores[node_id] = {
                'base': risk,
                'centrality': centrality,
                'total': min(risk, 1.0)
            }
    
    def _identify_critical_nodes(self):
        """Identify critical nodes in the graph"""
        logger.info("Identifying critical nodes")
        
        # Use betweenness centrality to find critical nodes
        betweenness = nx.betweenness_centrality(self.graph)
        
        # Sort by centrality
        sorted_nodes = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)
        
        # Take top nodes
        for node_id, centrality in sorted_nodes[:20]:
            if centrality > 0.1:  # Threshold for critical
                self._critical_nodes.append({
                    'node_id': node_id,
                    'centrality': centrality,
                    'type': self.graph.nodes[node_id].get('type', 'unknown'),
                    'risk_score': self._risk_scores.get(node_id, {}).get('total', 0)
                })
    
    def _detect_vulnerabilities(self):
        """Detect security vulnerabilities"""
        logger.info("Detecting vulnerabilities")
        
        # Check for overprivileged service accounts
        for node_id in self.graph.nodes():
            if node_id.startswith('sa:'):
                # Check if SA has dangerous roles
                roles = [n for n in self.graph.neighbors(node_id) if n.startswith('role:')]
                dangerous = [r for r in roles if any(d in r for d in self.config.analysis_dangerous_roles)]
                
                if dangerous:
                    self._vulnerabilities.append({
                        'type': 'overprivileged_service_account',
                        'severity': 'high',
                        'resource': node_id,
                        'details': f"Service account has {len(dangerous)} dangerous roles",
                        'roles': dangerous
                    })
        
        # Check for external users with high privileges
        for node_id in self.graph.nodes():
            if node_id.startswith('user:') and '@' in node_id:
                # Check if external domain
                email = node_id.split(':', 1)[1]
                if not email.endswith(('@example.com', '@yourdomain.com')):  # Replace with actual domains
                    roles = [n for n in self.graph.neighbors(node_id) if n.startswith('role:')]
                    dangerous = [r for r in roles if any(d in r for d in self.config.analysis_dangerous_roles)]
                    
                    if dangerous:
                        self._vulnerabilities.append({
                            'type': 'external_user_high_privilege',
                            'severity': 'critical',
                            'resource': node_id,
                            'details': f"External user has {len(dangerous)} dangerous roles",
                            'roles': dangerous
                        })
    
    def _build_attack_path(self, node_path: List[str]) -> Optional[AttackPath]:
        """Build an AttackPath object from a node path"""
        if len(node_path) < 2:
            return None
        
        # Build nodes
        path_nodes = []
        for node_id in node_path:
            node_data = self.graph.nodes[node_id]
            node = Node(
                id=node_id,
                type=NodeType(node_data.get('type', 'user')),
                name=node_data.get('name', node_id),
                properties={k: v for k, v in node_data.items() if k not in ['type', 'name']}
            )
            path_nodes.append(node)
        
        # Build edges
        path_edges = []
        for i in range(len(node_path) - 1):
            edge_data = self.graph.get_edge_data(node_path[i], node_path[i + 1])
            if edge_data:
                edge = Edge(
                    source_id=node_path[i],
                    target_id=node_path[i + 1],
                    type=EdgeType(edge_data.get('type', 'has_role')),
                    properties={k: v for k, v in edge_data.items() if k != 'type'}
                )
                path_edges.append(edge)
        
        # Calculate risk
        risk_score = sum(e.get_risk_score() for e in path_edges) / len(path_edges) if path_edges else 0
        
        return AttackPath(
            source_node=path_nodes[0],
            target_node=path_nodes[-1],
            path_nodes=path_nodes,
            path_edges=path_edges,
            risk_score=risk_score,
            description=f"Attack path from {path_nodes[0].name} to {path_nodes[-1].name}"
        )
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """Calculate analysis statistics"""
        total_paths = sum(len(paths) for paths in self._attack_paths.values())
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'total_attack_paths': total_paths,
            'privilege_escalation_paths': len(self._attack_paths.get('privilege_escalation', [])),
            'lateral_movement_paths': len(self._attack_paths.get('lateral_movement', [])),
            'critical_nodes': len(self._critical_nodes),
            'vulnerabilities': len(self._vulnerabilities),
            'high_risk_nodes': sum(1 for r in self._risk_scores.values() if r.get('total', 0) > 0.7)
        } 