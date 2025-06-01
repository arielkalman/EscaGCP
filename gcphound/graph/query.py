"""
Graph query module for finding paths and analyzing relationships
"""

import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
from collections import deque, defaultdict
from copy import deepcopy
from .models import Node, Edge, NodeType, EdgeType, AttackPath
from ..utils import get_logger, Config


logger = get_logger(__name__)


class GraphQuery:
    """
    Query engine for the GCP graph with advanced simulation capabilities
    """
    
    def __init__(self, graph: nx.DiGraph, nodes: Dict[str, Node], config: Config):
        """
        Initialize query engine
        
        Args:
            graph: NetworkX graph
            nodes: Dictionary of nodes
            config: Configuration instance
        """
        self.graph = graph
        self.nodes = nodes
        self.config = config
    
    def find_shortest_path(self, source_id: str, target_id: str) -> Optional[AttackPath]:
        """
        Find shortest path between two nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            
        Returns:
            AttackPath or None if no path exists
        """
        try:
            path_nodes = nx.shortest_path(self.graph, source_id, target_id)
            
            if len(path_nodes) < 2:
                return None
            
            # Build edges
            path_edges = []
            for i in range(len(path_nodes) - 1):
                edge_data = self.graph.get_edge_data(path_nodes[i], path_nodes[i + 1])
                edge = Edge(
                    source_id=path_nodes[i],
                    target_id=path_nodes[i + 1],
                    type=EdgeType(edge_data.get('type', 'has_role')),
                    properties=edge_data
                )
                path_edges.append(edge)
            
            # Create attack path
            return AttackPath(
                source_node=self.nodes[source_id],
                target_node=self.nodes[target_id],
                path_nodes=[self.nodes[n] for n in path_nodes],
                path_edges=path_edges,
                risk_score=self._calculate_path_risk(path_edges),
                description=f"Path from {source_id} to {target_id}"
            )
            
        except nx.NetworkXNoPath:
            return None
    
    def find_all_paths(
        self,
        source_id: str,
        target_id: str,
        max_length: Optional[int] = None
    ) -> List[AttackPath]:
        """
        Find all paths between two nodes
        
        Args:
            source_id: Source node ID
            target_id: Target node ID
            max_length: Maximum path length
            
        Returns:
            List of attack paths
        """
        if max_length is None:
            max_length = self.config.analysis_max_path_length
        
        paths = []
        try:
            for path_nodes in nx.all_simple_paths(
                self.graph,
                source_id,
                target_id,
                cutoff=max_length
            ):
                attack_path = self._build_attack_path(path_nodes)
                if attack_path:
                    paths.append(attack_path)
        except nx.NetworkXNoPath:
            pass
        
        # Sort by risk score
        paths.sort(key=lambda p: p.risk_score, reverse=True)
        return paths
    
    def find_paths_to_role(
        self,
        source_id: str,
        role_name: str,
        max_length: Optional[int] = None
    ) -> List[AttackPath]:
        """
        Find all paths from a node to a specific role
        
        Args:
            source_id: Source node ID
            role_name: Target role name (e.g., 'roles/owner')
            max_length: Maximum path length
            
        Returns:
            List of attack paths
        """
        role_id = f"role:{role_name}"
        if role_id not in self.nodes:
            logger.warning(f"Role not found: {role_name}")
            return []
        
        return self.find_all_paths(source_id, role_id, max_length)
    
    def find_paths_to_resource(
        self,
        source_id: str,
        resource_id: str,
        access_level: Optional[str] = None
    ) -> List[AttackPath]:
        """
        Find paths to access a resource
        
        Args:
            source_id: Source node ID
            resource_id: Target resource ID
            access_level: Required access level ('read', 'write', 'admin')
            
        Returns:
            List of attack paths
        """
        paths = []
        
        # Find all nodes that have access to the resource
        accessor_nodes = []
        for predecessor in self.graph.predecessors(resource_id):
            edge_data = self.graph.get_edge_data(predecessor, resource_id)
            edge_type = EdgeType(edge_data.get('type', ''))
            
            # Check if access level matches
            if access_level:
                if access_level == 'admin' and edge_type != EdgeType.CAN_ADMIN:
                    continue
                elif access_level == 'write' and edge_type not in [EdgeType.CAN_WRITE, EdgeType.CAN_ADMIN]:
                    continue
                elif access_level == 'read' and edge_type not in [EdgeType.CAN_READ, EdgeType.CAN_WRITE, EdgeType.CAN_ADMIN]:
                    continue
            
            accessor_nodes.append(predecessor)
        
        # Find paths to each accessor
        for accessor in accessor_nodes:
            if accessor == source_id:
                # Direct access
                path = self._build_attack_path([source_id, resource_id])
                if path:
                    paths.append(path)
            else:
                # Indirect access through accessor
                accessor_paths = self.find_all_paths(source_id, accessor)
                for accessor_path in accessor_paths:
                    # Extend path to include resource
                    extended_nodes = accessor_path.path_nodes + [self.nodes[resource_id]]
                    extended_path = self._build_attack_path([n.id for n in extended_nodes])
                    if extended_path:
                        paths.append(extended_path)
        
        return paths
    
    def find_privilege_escalation_paths(
        self,
        source_id: str,
        target_roles: Optional[List[str]] = None
    ) -> List[AttackPath]:
        """
        Find privilege escalation paths from a node
        
        Args:
            source_id: Source node ID
            target_roles: List of target roles (uses dangerous roles if None)
            
        Returns:
            List of attack paths
        """
        if target_roles is None:
            target_roles = self.config.analysis_dangerous_roles
        
        paths = []
        for role in target_roles:
            role_paths = self.find_paths_to_role(source_id, role)
            paths.extend(role_paths)
        
        # Also find impersonation paths
        impersonation_paths = self.find_impersonation_paths(source_id)
        paths.extend(impersonation_paths)
        
        # Sort by risk score
        paths.sort(key=lambda p: p.risk_score, reverse=True)
        return paths
    
    def find_impersonation_paths(self, source_id: str) -> List[AttackPath]:
        """
        Find service account impersonation paths
        
        Args:
            source_id: Source node ID
            
        Returns:
            List of attack paths
        """
        paths = []
        
        # Find all service accounts that can be impersonated
        for node_id, node in self.nodes.items():
            if node.type != NodeType.SERVICE_ACCOUNT:
                continue
            
            # Check if there's an impersonation path
            try:
                path_nodes = nx.shortest_path(self.graph, source_id, node_id)
                
                # Verify path contains impersonation edge
                has_impersonation = False
                for i in range(len(path_nodes) - 1):
                    edge_data = self.graph.get_edge_data(path_nodes[i], path_nodes[i + 1])
                    if edge_data and EdgeType(edge_data.get('type', '')) == EdgeType.CAN_IMPERSONATE:
                        has_impersonation = True
                        break
                
                if has_impersonation:
                    attack_path = self._build_attack_path(path_nodes)
                    if attack_path:
                        attack_path.description = f"Can impersonate service account: {node.name}"
                        paths.append(attack_path)
                        
            except nx.NetworkXNoPath:
                continue
        
        return paths
    
    def find_lateral_movement_paths(
        self,
        source_id: str,
        target_project: Optional[str] = None
    ) -> List[AttackPath]:
        """
        Find lateral movement paths between projects
        
        Args:
            source_id: Source node ID
            target_project: Target project ID (finds all if None)
            
        Returns:
            List of attack paths
        """
        paths = []
        source_node = self.nodes.get(source_id)
        if not source_node:
            return paths
        
        # Determine source project
        source_project = source_node.properties.get('projectId')
        if not source_project and source_node.type == NodeType.PROJECT:
            source_project = source_node.name.split('/')[-1]
        
        # Find paths to other projects
        for node_id, node in self.nodes.items():
            if node.type != NodeType.PROJECT:
                continue
            
            project_id = node.name.split('/')[-1]
            
            # Skip same project
            if project_id == source_project:
                continue
            
            # Skip if specific target requested and doesn't match
            if target_project and project_id != target_project:
                continue
            
            # Find paths to project resources
            project_paths = self.find_all_paths(source_id, node_id)
            for path in project_paths:
                path.description = f"Lateral movement to project: {project_id}"
            paths.extend(project_paths)
        
        return paths
    
    def get_node_permissions(self, node_id: str) -> Dict[str, List[str]]:
        """
        Get all permissions for a node
        
        Args:
            node_id: Node ID
            
        Returns:
            Dictionary mapping resource to list of permissions
        """
        permissions = {}
        
        # Find all roles the node has
        for successor in self.graph.successors(node_id):
            successor_node = self.nodes.get(successor)
            if not successor_node or successor_node.type != NodeType.ROLE:
                continue
            
            edge_data = self.graph.get_edge_data(node_id, successor)
            if edge_data and EdgeType(edge_data.get('type', '')) == EdgeType.HAS_ROLE:
                resource = edge_data.get('resource', 'unknown')
                role_permissions = successor_node.properties.get('permissions', [])
                
                if resource not in permissions:
                    permissions[resource] = []
                permissions[resource].extend(role_permissions)
        
        return permissions
    
    def can_access_resource(
        self,
        source_id: str,
        resource_id: str,
        required_permission: Optional[str] = None
    ) -> bool:
        """
        Check if a node can access a resource
        
        Args:
            source_id: Source node ID
            resource_id: Target resource ID
            required_permission: Specific permission required
            
        Returns:
            True if access is possible
        """
        # Check direct access
        if self.graph.has_edge(source_id, resource_id):
            if not required_permission:
                return True
            
            # Check if node has required permission
            permissions = self.get_node_permissions(source_id)
            for resource_perms in permissions.values():
                if required_permission in resource_perms:
                    return True
        
        # Check indirect access through impersonation
        paths = self.find_paths_to_resource(source_id, resource_id)
        return len(paths) > 0
    
    def simulate_binding_addition(
        self,
        member: str,
        role: str,
        resource: str
    ) -> Dict[str, Any]:
        """
        Simulate adding an IAM binding and analyze impact
        
        Args:
            member: Member identity (e.g., 'user:alice@example.com')
            role: Role name (e.g., 'roles/editor')
            resource: Resource name (e.g., 'projects/my-project')
            
        Returns:
            Comprehensive analysis results
        """
        # Create temporary graph copy
        temp_graph = self.graph.copy()
        
        # Add the binding
        member_id = self._get_node_id_from_identity(member)
        role_id = f"role:{role}"
        resource_id = self._get_node_id_from_resource(resource)
        
        if not all([member_id, role_id, resource_id]):
            return {
                'error': 'Invalid member, role, or resource',
                'member_id': member_id,
                'role_id': role_id,
                'resource_id': resource_id
            }
        
        # Add edges
        temp_graph.add_edge(
            member_id, role_id,
            type=EdgeType.HAS_ROLE.value,
            resource=resource,
            role=role
        )
        
        # Determine access type based on role
        access_type = self._get_access_type_from_role(role)
        temp_graph.add_edge(
            member_id, resource_id,
            type=access_type.value,
            role=role
        )
        
        # Analyze changes
        results = {
            'binding': {
                'member': member,
                'role': role,
                'resource': resource
            },
            'new_paths': [],
            'new_permissions': [],
            'affected_resources': [],
            'risk_analysis': {
                'risk_increase': 0.0,
                'new_attack_vectors': [],
                'critical_paths_created': 0
            },
            'recommendations': []
        }
        
        # Create temporary query engine
        temp_query = GraphQuery(temp_graph, self.nodes, self.config)
        
        # Find new privilege escalation paths
        if member_id:
            new_paths = temp_query.find_privilege_escalation_paths(member_id)
            existing_paths = self.find_privilege_escalation_paths(member_id)
            
            existing_path_keys = {self._get_path_key(p) for p in existing_paths}
            
            for path in new_paths:
                if self._get_path_key(path) not in existing_path_keys:
                    results['new_paths'].append({
                        'path': path.get_path_string(),
                        'risk_score': path.risk_score,
                        'length': len(path)
                    })
                    results['risk_analysis']['risk_increase'] += path.risk_score
                    
                    if path.risk_score > 0.7:
                        results['risk_analysis']['critical_paths_created'] += 1
            
            # Analyze new permissions
            new_perms = temp_query.get_node_permissions(member_id)
            existing_perms = self.get_node_permissions(member_id)
            
            for resource, perms in new_perms.items():
                existing = set(existing_perms.get(resource, []))
                new = set(perms) - existing
                if new:
                    results['new_permissions'].append({
                        'resource': resource,
                        'permissions': list(new)
                    })
            
            # Find newly accessible resources
            results['affected_resources'] = self._find_newly_accessible_resources(
                member_id, temp_graph
            )
            
            # Identify new attack vectors
            if role in ['roles/iam.serviceAccountTokenCreator', 'roles/iam.serviceAccountKeyAdmin']:
                results['risk_analysis']['new_attack_vectors'].append(
                    'Service account impersonation capability'
                )
            
            if role in ['roles/cloudfunctions.admin', 'roles/run.admin']:
                results['risk_analysis']['new_attack_vectors'].append(
                    'Code execution through serverless deployment'
                )
            
            if role in ['roles/compute.admin', 'roles/compute.instanceAdmin']:
                results['risk_analysis']['new_attack_vectors'].append(
                    'VM-based privilege escalation'
                )
        
        # Generate recommendations
        results['recommendations'] = self._generate_binding_recommendations(results)
        
        return results
    
    def simulate_binding_removal(
        self,
        member: str,
        role: str,
        resource: str
    ) -> Dict[str, Any]:
        """
        Simulate removing an IAM binding and analyze impact
        
        Args:
            member: Member identity
            role: Role name
            resource: Resource name
            
        Returns:
            Analysis results including broken paths and lost access
        """
        # Create temporary graph copy
        temp_graph = self.graph.copy()
        
        # Get node IDs
        member_id = self._get_node_id_from_identity(member)
        role_id = f"role:{role}"
        resource_id = self._get_node_id_from_resource(resource)
        
        if not all([member_id, role_id, resource_id]):
            return {'error': 'Invalid member, role, or resource'}
        
        # Remove edges
        edges_to_remove = []
        
        # Remove role edge
        if temp_graph.has_edge(member_id, role_id):
            edge_data = temp_graph.get_edge_data(member_id, role_id)
            if edge_data.get('resource') == resource:
                edges_to_remove.append((member_id, role_id))
        
        # Remove resource access edge
        if temp_graph.has_edge(member_id, resource_id):
            edge_data = temp_graph.get_edge_data(member_id, resource_id)
            if edge_data.get('role') == role:
                edges_to_remove.append((member_id, resource_id))
        
        for edge in edges_to_remove:
            temp_graph.remove_edge(*edge)
        
        # Analyze impact
        results = {
            'binding': {
                'member': member,
                'role': role,
                'resource': resource
            },
            'broken_paths': [],
            'lost_permissions': [],
            'affected_resources': [],
            'security_improvements': {
                'risk_reduction': 0.0,
                'attack_vectors_removed': [],
                'critical_paths_broken': 0
            }
        }
        
        # Find broken attack paths
        existing_paths = self.find_privilege_escalation_paths(member_id)
        temp_query = GraphQuery(temp_graph, self.nodes, self.config)
        remaining_paths = temp_query.find_privilege_escalation_paths(member_id)
        
        remaining_path_keys = {self._get_path_key(p) for p in remaining_paths}
        
        for path in existing_paths:
            if self._get_path_key(path) not in remaining_path_keys:
                results['broken_paths'].append({
                    'path': path.get_path_string(),
                    'risk_score': path.risk_score
                })
                results['security_improvements']['risk_reduction'] += path.risk_score
                
                if path.risk_score > 0.7:
                    results['security_improvements']['critical_paths_broken'] += 1
        
        # Analyze lost permissions
        existing_perms = self.get_node_permissions(member_id)
        remaining_perms = temp_query.get_node_permissions(member_id)
        
        for resource, perms in existing_perms.items():
            remaining = set(remaining_perms.get(resource, []))
            lost = set(perms) - remaining
            if lost:
                results['lost_permissions'].append({
                    'resource': resource,
                    'permissions': list(lost)
                })
        
        # Identify removed attack vectors
        if role in ['roles/iam.serviceAccountTokenCreator', 'roles/iam.serviceAccountKeyAdmin']:
            results['security_improvements']['attack_vectors_removed'].append(
                'Service account impersonation capability'
            )
        
        return results
    
    def simulate_role_change(
        self,
        member: str,
        old_role: str,
        new_role: str,
        resource: str
    ) -> Dict[str, Any]:
        """
        Simulate changing a role assignment
        
        Args:
            member: Member identity
            old_role: Current role
            new_role: New role
            resource: Resource name
            
        Returns:
            Analysis of the role change impact
        """
        # First simulate removal
        removal_impact = self.simulate_binding_removal(member, old_role, resource)
        
        # Then simulate addition
        addition_impact = self.simulate_binding_addition(member, new_role, resource)
        
        # Combine results
        results = {
            'change': {
                'member': member,
                'old_role': old_role,
                'new_role': new_role,
                'resource': resource
            },
            'net_risk_change': (
                addition_impact.get('risk_analysis', {}).get('risk_increase', 0) -
                removal_impact.get('security_improvements', {}).get('risk_reduction', 0)
            ),
            'permission_changes': {
                'gained': addition_impact.get('new_permissions', []),
                'lost': removal_impact.get('lost_permissions', [])
            },
            'path_changes': {
                'new_paths': addition_impact.get('new_paths', []),
                'broken_paths': removal_impact.get('broken_paths', [])
            },
            'recommendations': []
        }
        
        # Generate recommendations
        if results['net_risk_change'] > 0.5:
            results['recommendations'].append(
                'High risk increase detected. Consider using a less privileged role.'
            )
        
        if new_role in ['roles/owner', 'roles/editor']:
            results['recommendations'].append(
                'Consider using more specific predefined roles instead of primitive roles.'
            )
        
        return results
    
    def find_minimal_permissions(
        self,
        source_id: str,
        target_id: str,
        required_action: str
    ) -> Dict[str, Any]:
        """
        Find minimal permissions needed for an action
        
        Args:
            source_id: Source identity
            target_id: Target resource
            required_action: Action to perform
            
        Returns:
            Minimal permission set and recommended roles
        """
        results = {
            'required_permissions': [],
            'recommended_roles': [],
            'current_excess_permissions': []
        }
        
        # Map actions to permissions
        action_permissions = {
            'read': ['*.get', '*.list', '*.view'],
            'write': ['*.create', '*.update', '*.patch'],
            'delete': ['*.delete'],
            'admin': ['*.setIamPolicy', '*.admin']
        }
        
        required_perms = action_permissions.get(required_action, [])
        
        # Find roles that grant these permissions
        for role_id, role_node in self.nodes.items():
            if role_node.type != NodeType.ROLE:
                continue
            
            role_perms = set(role_node.properties.get('permissions', []))
            
            # Check if role grants required permissions
            if any(self._permission_matches(rp, role_perms) for rp in required_perms):
                results['recommended_roles'].append({
                    'role': role_node.name,
                    'title': role_node.properties.get('title', ''),
                    'permission_count': len(role_perms)
                })
        
        # Sort by least privilege
        results['recommended_roles'].sort(key=lambda r: r['permission_count'])
        
        # Check current permissions
        current_perms = self.get_node_permissions(source_id)
        all_current_perms = set()
        for perms in current_perms.values():
            all_current_perms.update(perms)
        
        # Find excess permissions
        if all_current_perms:
            min_required = set()
            for rp in required_perms:
                min_required.update([p for p in all_current_perms if self._permission_matches(rp, [p])])
            
            excess = all_current_perms - min_required
            if excess:
                results['current_excess_permissions'] = list(excess)
        
        return results
    
    def _find_newly_accessible_resources(
        self,
        member_id: str,
        new_graph: nx.DiGraph
    ) -> List[Dict[str, Any]]:
        """Find resources that become newly accessible"""
        newly_accessible = []
        
        # Get current accessible resources
        current_resources = set()
        for successor in self.graph.successors(member_id):
            node = self.nodes.get(successor)
            if node and node.type in [
                NodeType.PROJECT, NodeType.BUCKET, NodeType.DATASET,
                NodeType.SECRET, NodeType.KMS_KEY
            ]:
                current_resources.add(successor)
        
        # Get new accessible resources
        new_resources = set()
        for successor in new_graph.successors(member_id):
            node = self.nodes.get(successor)
            if node and node.type in [
                NodeType.PROJECT, NodeType.BUCKET, NodeType.DATASET,
                NodeType.SECRET, NodeType.KMS_KEY
            ]:
                new_resources.add(successor)
        
        # Find difference
        for resource_id in new_resources - current_resources:
            resource_node = self.nodes[resource_id]
            newly_accessible.append({
                'resource_id': resource_id,
                'resource_type': resource_node.type.value,
                'resource_name': resource_node.name
            })
        
        return newly_accessible
    
    def _generate_binding_recommendations(self, analysis_results: Dict[str, Any]) -> List[str]:
        """Generate security recommendations based on analysis"""
        recommendations = []
        
        risk_increase = analysis_results['risk_analysis']['risk_increase']
        
        if risk_increase > 0.7:
            recommendations.append(
                'CRITICAL: This binding creates high-risk attack paths. Consider using a less privileged role.'
            )
        
        if analysis_results['risk_analysis']['critical_paths_created'] > 0:
            recommendations.append(
                f"WARNING: {analysis_results['risk_analysis']['critical_paths_created']} critical attack paths would be created."
            )
        
        # Check for dangerous permissions
        for perm_set in analysis_results['new_permissions']:
            perms = perm_set['permissions']
            if any('setIamPolicy' in p for p in perms):
                recommendations.append(
                    'DANGER: This grants IAM policy modification permissions, enabling privilege escalation.'
                )
            if any('actAs' in p for p in perms):
                recommendations.append(
                    'WARNING: This grants service account impersonation, creating lateral movement paths.'
                )
        
        # Suggest alternatives
        role = analysis_results['binding']['role']
        if role in ['roles/owner', 'roles/editor']:
            recommendations.append(
                'RECOMMENDATION: Use predefined roles with minimal required permissions instead of primitive roles.'
            )
        
        return recommendations
    
    def _get_access_type_from_role(self, role: str) -> EdgeType:
        """Determine access edge type from role"""
        if 'owner' in role or 'admin' in role.lower():
            return EdgeType.CAN_ADMIN
        elif 'editor' in role or 'write' in role.lower():
            return EdgeType.CAN_WRITE
        elif 'viewer' in role or 'read' in role.lower():
            return EdgeType.CAN_READ
        else:
            return EdgeType.HAS_ACCESS_TO
    
    def _permission_matches(self, pattern: str, permissions: List[str]) -> bool:
        """Check if a permission pattern matches any permission in the list"""
        import fnmatch
        return any(fnmatch.fnmatch(perm, pattern) for perm in permissions)
    
    def _build_attack_path(self, node_ids: List[str]) -> Optional[AttackPath]:
        """
        Build an AttackPath from a list of node IDs
        
        Args:
            node_ids: List of node IDs in path order
            
        Returns:
            AttackPath or None
        """
        if len(node_ids) < 2:
            return None
        
        path_nodes = []
        path_edges = []
        total_risk = 0.0
        
        # Build nodes list
        for node_id in node_ids:
            node = self.nodes.get(node_id)
            if not node:
                return None
            path_nodes.append(node)
        
        # Build edges list
        for i in range(len(node_ids) - 1):
            source_id = node_ids[i]
            target_id = node_ids[i + 1]
            
            edge_data = self.graph.get_edge_data(source_id, target_id)
            if not edge_data:
                return None
            
            edge = Edge(
                source_id=source_id,
                target_id=target_id,
                type=EdgeType(edge_data.get('type', EdgeType.HAS_ACCESS_TO.value)),
                properties={k: v for k, v in edge_data.items() if k != 'type'}
            )
            path_edges.append(edge)
            total_risk += edge.get_risk_score()
        
        # Calculate average risk
        avg_risk = total_risk / len(path_edges) if path_edges else 0.0
        
        return AttackPath(
            source_node=path_nodes[0],
            target_node=path_nodes[-1],
            path_nodes=path_nodes,
            path_edges=path_edges,
            risk_score=avg_risk
        )
    
    def _get_node_id_from_identity(self, identity: str) -> Optional[str]:
        """Convert identity string to node ID"""
        if identity.startswith('user:'):
            return f"user:{identity[5:]}"
        elif identity.startswith('serviceAccount:'):
            return f"sa:{identity[15:]}"
        elif identity.startswith('group:'):
            return f"group:{identity[6:]}"
        elif '@' in identity:
            if identity.endswith('.gserviceaccount.com'):
                return f"sa:{identity}"
            else:
                return f"user:{identity}"
        return None
    
    def _get_node_id_from_resource(self, resource: str) -> Optional[str]:
        """Convert resource name to node ID"""
        if resource.startswith('projects/'):
            project_id = resource.split('/')[-1]
            return f"project:{project_id}"
        elif resource.startswith('folders/'):
            folder_id = resource.split('/')[-1]
            return f"folder:{folder_id}"
        elif resource.startswith('organizations/'):
            org_id = resource.split('/')[-1]
            return f"org:{org_id}"
        return None
    
    def _get_path_key(self, path: AttackPath) -> str:
        """Get unique key for a path"""
        node_ids = [n.id for n in path.path_nodes]
        return "->".join(node_ids)
    
    def _calculate_path_risk(self, edges: List[Edge]) -> float:
        """Calculate risk score for a path"""
        if not edges:
            return 0.0
        
        # Average edge risk
        total_risk = sum(edge.get_risk_score() for edge in edges)
        return min(total_risk / len(edges), 1.0) 