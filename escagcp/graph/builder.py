"""
Graph builder for constructing the GCP IAM graph
"""

import networkx as nx
from typing import Dict, Any, List, Optional, Set, Tuple
from ..utils import get_logger, Config
from .models import Node, Edge, NodeType, EdgeType, GraphMetadata


logger = get_logger(__name__)


class GraphBuilder:
    """
    Builds a NetworkX graph from collected GCP data
    """
    
    def __init__(self, config: Config):
        """
        Initialize graph builder
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.graph = nx.DiGraph()
        self._nodes = {}  # id -> Node mapping
        self._metadata = GraphMetadata()
    
    def build_from_collected_data(self, collected_data: Dict[str, Any]) -> nx.DiGraph:
        """
        Build graph from collected data
        
        Args:
            collected_data: Data collected by collectors
            
        Returns:
            NetworkX directed graph
        """
        logger.info("Building graph from collected data")
        
        # Reset graph
        self.graph.clear()
        self._nodes.clear()
        self._metadata = GraphMetadata()
        
        # Build nodes and edges from each data type
        if 'hierarchy' in collected_data:
            # Handle both data structures - with and without nested 'data' key
            hierarchy_data = collected_data['hierarchy']
            if 'data' in hierarchy_data:
                hierarchy_data = hierarchy_data['data']
            self._build_hierarchy_nodes(hierarchy_data)
        
        if 'identity' in collected_data:
            # Handle both data structures
            identity_data = collected_data['identity']
            if 'data' in identity_data:
                identity_data = identity_data['data']
            self._build_identity_nodes(identity_data)
        
        if 'iam' in collected_data:
            # Handle both data structures
            iam_data = collected_data['iam']
            if 'data' in iam_data:
                iam_data = iam_data['data']
            self._build_iam_nodes_and_edges(iam_data)
            
            # Build advanced privilege escalation edges
            self._build_privilege_escalation_edges()
        
        if 'resources' in collected_data:
            # Handle both data structures
            resource_data = collected_data['resources']
            if 'data' in resource_data:
                resource_data = resource_data['data']
            self._build_resource_nodes(resource_data)
        
        # Update metadata
        self._update_metadata()
        
        logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
        
        return self.graph
    
    def _build_hierarchy_nodes(self, hierarchy_data: Dict[str, Any]):
        """Build nodes for organizations, folders, and projects"""
        # Organizations
        for org_id, org_data in hierarchy_data.get('organizations', {}).items():
            node = Node(
                id=f"org:{org_id}",
                type=NodeType.ORGANIZATION,
                name=org_data.get('name', f'organizations/{org_id}'),
                properties=org_data
            )
            self._add_node(node)
        
        # Folders
        for folder_id, folder_data in hierarchy_data.get('folders', {}).items():
            node = Node(
                id=f"folder:{folder_id}",
                type=NodeType.FOLDER,
                name=folder_data.get('name', f'folders/{folder_id}'),
                properties=folder_data
            )
            self._add_node(node)
        
        # Projects
        for project_id, project_data in hierarchy_data.get('projects', {}).items():
            node = Node(
                id=f"project:{project_id}",
                type=NodeType.PROJECT,
                name=project_data.get('name', f'projects/{project_id}'),
                properties=project_data
            )
            self._add_node(node)
        
        # Build hierarchy edges
        self._build_hierarchy_edges(hierarchy_data.get('hierarchy', {}))
    
    def _build_hierarchy_edges(self, hierarchy: Dict[str, Any]):
        """Build parent-child edges for hierarchy"""
        # Organization -> Folder/Project edges
        for org_id, org_hierarchy in hierarchy.get('organizations', {}).items():
            for folder_id in org_hierarchy.get('folders', []):
                self._add_edge(Edge(
                    source_id=f"org:{org_id}",
                    target_id=f"folder:{folder_id}",
                    type=EdgeType.PARENT_OF
                ))
            
            for project_id in org_hierarchy.get('projects', []):
                self._add_edge(Edge(
                    source_id=f"org:{org_id}",
                    target_id=f"project:{project_id}",
                    type=EdgeType.PARENT_OF
                ))
        
        # Folder -> Folder/Project edges
        for folder_id, folder_hierarchy in hierarchy.get('folders', {}).items():
            for child_folder_id in folder_hierarchy.get('folders', []):
                self._add_edge(Edge(
                    source_id=f"folder:{folder_id}",
                    target_id=f"folder:{child_folder_id}",
                    type=EdgeType.PARENT_OF
                ))
            
            for project_id in folder_hierarchy.get('projects', []):
                self._add_edge(Edge(
                    source_id=f"folder:{folder_id}",
                    target_id=f"project:{project_id}",
                    type=EdgeType.PARENT_OF
                ))
    
    def _build_identity_nodes(self, identity_data: Dict[str, Any]):
        """Build nodes for users, groups, and service accounts"""
        # Service accounts
        for sa_email, sa_data in identity_data.get('service_accounts', {}).items():
            node = Node(
                id=f"sa:{sa_email}",
                type=NodeType.SERVICE_ACCOUNT,
                name=sa_email,
                properties=sa_data
            )
            self._add_node(node)
        
        # Groups
        for group_id, group_data in identity_data.get('groups', {}).items():
            node = Node(
                id=f"group:{group_id}",
                type=NodeType.GROUP,
                name=group_id,
                properties=group_data
            )
            self._add_node(node)
        
        # Users
        for user_email, user_data in identity_data.get('users', {}).items():
            node = Node(
                id=f"user:{user_email}",
                type=NodeType.USER,
                name=user_email,
                properties=user_data
            )
            self._add_node(node)
        
        # Group memberships
        for group_id, members in identity_data.get('group_memberships', {}).items():
            for member in members:
                member_id = member.get('id')
                if member_id:
                    # Determine member type and create edge
                    if '@' in member_id and not member_id.endswith('.gserviceaccount.com'):
                        member_node_id = f"user:{member_id}"
                    else:
                        member_node_id = f"sa:{member_id}"
                    
                    self._add_edge(Edge(
                        source_id=member_node_id,
                        target_id=f"group:{group_id}",
                        type=EdgeType.MEMBER_OF
                    ))
    
    def _build_iam_nodes_and_edges(self, iam_data: Dict[str, Any]):
        """Build nodes for roles and edges for IAM bindings"""
        # Build role nodes
        for role_name, role_data in iam_data.get('roles', {}).get('predefined', {}).items():
            node = Node(
                id=f"role:{role_name}",
                type=NodeType.ROLE,
                name=role_name,
                properties=role_data
            )
            self._add_node(node)
        
        for role_name, role_data in iam_data.get('roles', {}).get('custom', {}).items():
            node = Node(
                id=f"role:{role_name}",
                type=NodeType.CUSTOM_ROLE,
                name=role_name,
                properties=role_data
            )
            self._add_node(node)
        
        # Build IAM binding edges
        policies = iam_data.get('policies', {})
        for resource_type in ['organizations', 'folders', 'projects']:
            for resource_id, policy in policies.get(resource_type, {}).items():
                for binding in policy.get('bindings', []):
                    role = binding.get('role')
                    members = binding.get('members', [])
                    
                    # Create role node if it doesn't exist
                    role_node_id = f"role:{role}"
                    if role_node_id not in self._nodes:
                        self._add_node(Node(
                            id=role_node_id,
                            type=NodeType.ROLE,
                            name=role
                        ))
                    
                    # Create edges from members to roles
                    for member in members:
                        member_node_id = self._normalize_member_to_node_id(member)
                        
                        # Create member node if it doesn't exist
                        if member_node_id not in self._nodes:
                            self._create_member_node(member)
                        
                        # Add HAS_ROLE edge
                        self._add_edge(Edge(
                            source_id=member_node_id,
                            target_id=role_node_id,
                            type=EdgeType.HAS_ROLE,
                            properties={
                                'resource': policy['resource'],
                                'role': role,
                                'condition': binding.get('condition')
                            }
                        ))
        
        # Build impersonation edges
        impersonation_data = iam_data.get('impersonation_analysis', {})
        for sa_email, impersonators in impersonation_data.get('can_impersonate', {}).items():
            sa_node_id = f"sa:{sa_email}"
            
            for impersonator_data in impersonators:
                member = impersonator_data['member']
                member_node_id = self._normalize_member_to_node_id(member)
                
                # Add CAN_IMPERSONATE edge
                self._add_edge(Edge(
                    source_id=member_node_id,
                    target_id=sa_node_id,
                    type=EdgeType.CAN_IMPERSONATE,
                    properties=impersonator_data
                ))
    
    def _build_resource_nodes(self, resource_data: Dict[str, Any]):
        """Build nodes for GCP resources"""
        resources = resource_data.get('resources', {})
        
        # Buckets
        for bucket_name, bucket_data in resources.get('buckets', {}).items():
            node = Node(
                id=f"bucket:{bucket_name}",
                type=NodeType.BUCKET,
                name=bucket_name,
                properties=bucket_data
            )
            self._add_node(node)
        
        # Compute instances
        for instance_id, instance_data in resources.get('compute_instances', {}).items():
            node = Node(
                id=f"instance:{instance_id}",
                type=NodeType.INSTANCE,
                name=instance_data.get('name', instance_id),
                properties=instance_data
            )
            self._add_node(node)
        
        # Cloud Functions
        for function_name, function_data in resources.get('functions', {}).items():
            node = Node(
                id=f"function:{function_name}",
                type=NodeType.FUNCTION,
                name=function_name,
                properties=function_data
            )
            self._add_node(node)
    
    def _normalize_member_to_node_id(self, member: str) -> str:
        """Normalize a member string to a node ID"""
        if member.startswith('user:'):
            return f"user:{member[5:]}"
        elif member.startswith('serviceAccount:'):
            return f"sa:{member[15:]}"
        elif member.startswith('group:'):
            return f"group:{member[6:]}"
        else:
            # Handle special members
            return f"special:{member}"
    
    def _create_member_node(self, member: str):
        """Create a node for a member if it doesn't exist"""
        node_id = self._normalize_member_to_node_id(member)
        
        if member.startswith('user:'):
            email = member[5:]
            node = Node(
                id=node_id,
                type=NodeType.USER,
                name=email,
                properties={'email': email}
            )
        elif member.startswith('serviceAccount:'):
            email = member[15:]
            node = Node(
                id=node_id,
                type=NodeType.SERVICE_ACCOUNT,
                name=email,
                properties={'email': email}
            )
        elif member.startswith('group:'):
            group_id = member[6:]
            node = Node(
                id=node_id,
                type=NodeType.GROUP,
                name=group_id,
                properties={'id': group_id}
            )
        else:
            # Special member (allUsers, allAuthenticatedUsers, etc.)
            node = Node(
                id=node_id,
                type=NodeType.USER,
                name=member,
                properties={'special': True}
            )
        
        self._add_node(node)
    
    def _add_node(self, node: Node):
        """Add a node to the graph"""
        # Convert node to dict for networkx attributes
        node_attrs = node.to_dict()
        # Remove 'id' from attributes since it's used as the node identifier
        node_attrs.pop('id', None)
        
        self.graph.add_node(node.id, **node_attrs)
        self._nodes[node.id] = node
    
    def _add_edge(self, edge: Edge):
        """Add an edge to the graph"""
        # Ensure both nodes exist
        if edge.source_id in self._nodes and edge.target_id in self._nodes:
            self.graph.add_edge(
                edge.source_id,
                edge.target_id,
                type=edge.type.value,
                **edge.properties
            )
    
    def _update_metadata(self):
        """Update graph metadata"""
        self._metadata.total_nodes = self.graph.number_of_nodes()
        self._metadata.total_edges = self.graph.number_of_edges()
        
        # Count node types
        for node_id, node in self._nodes.items():
            node_type = node.type
            self._metadata.node_counts[node_type] = self._metadata.node_counts.get(node_type, 0) + 1
            
            # Track GCP projects
            if node.type == NodeType.PROJECT:
                # Extract project ID from node ID (format: "project:project-id")
                project_id = node_id.split(':', 1)[1] if ':' in node_id else node_id
                if project_id not in self._metadata.gcp_projects:
                    self._metadata.gcp_projects.append(project_id)
            
            # Track organization
            elif node.type == NodeType.ORGANIZATION:
                org_id = node_id.split(':', 1)[1] if ':' in node_id else node_id
                self._metadata.gcp_organization = org_id
        
        # Count edge types
        for u, v, data in self.graph.edges(data=True):
            edge_type_str = data.get('type')
            if edge_type_str:
                edge_type = EdgeType(edge_type_str)
                self._metadata.edge_counts[edge_type] = self._metadata.edge_counts.get(edge_type, 0) + 1
    
    def get_nodes(self) -> Dict[str, Node]:
        """Get all nodes in the graph"""
        return self._nodes.copy()
    
    def get_metadata(self) -> GraphMetadata:
        """Get graph metadata"""
        return self._metadata
    
    def _build_privilege_escalation_edges(self):
        """Build advanced privilege escalation edges based on roles and permissions"""
        logger.info("Building privilege escalation edges")
        
        # Map of dangerous roles to the edges they enable
        role_to_edge_mappings = {
            'roles/iam.serviceAccountTokenCreator': EdgeType.CAN_IMPERSONATE_SA,
            'roles/iam.serviceAccountKeyAdmin': EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY,
            'roles/iam.serviceAccountAdmin': EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY,
            'roles/compute.admin': EdgeType.CAN_ACT_AS_VIA_VM,
            'roles/compute.instanceAdmin': EdgeType.CAN_ACT_AS_VIA_VM,
            'roles/cloudfunctions.admin': EdgeType.CAN_DEPLOY_FUNCTION_AS,
            'roles/cloudfunctions.developer': EdgeType.CAN_DEPLOY_FUNCTION_AS,
            'roles/run.admin': EdgeType.CAN_DEPLOY_CLOUD_RUN_AS,
            'roles/run.developer': EdgeType.CAN_DEPLOY_CLOUD_RUN_AS,
            'roles/cloudbuild.builds.editor': EdgeType.CAN_TRIGGER_BUILD_AS,
            'roles/container.admin': EdgeType.CAN_DEPLOY_GKE_POD_AS,
            'roles/container.developer': EdgeType.CAN_DEPLOY_GKE_POD_AS,
        }
        
        # Collect edges to add (to avoid modifying during iteration)
        edges_to_add = []
        
        # Find all principals with dangerous roles
        for source_id, target_id, edge_data in list(self.graph.edges(data=True)):
            if edge_data.get('type') == EdgeType.HAS_ROLE.value:
                # Check if this is a dangerous role
                if target_id in self._nodes:
                    role_node = self._nodes[target_id]
                    role_name = role_node.name
                    
                    if role_name in role_to_edge_mappings:
                        edge_type = role_to_edge_mappings[role_name]
                        
                        # Find all service accounts in the same project
                        resource = edge_data.get('resource', '')
                        if 'projects/' in resource:
                            project_id = resource.split('/')[-1]
                            
                            # Create edges to all service accounts in the project
                            for node_id, node in self._nodes.items():
                                if node.type == NodeType.SERVICE_ACCOUNT:
                                    # Check if SA is in the same project
                                    sa_email = node.name
                                    if f'@{project_id}.' in sa_email:
                                        # Don't create self-edges
                                        if source_id != node_id:
                                            edges_to_add.append(Edge(
                                                source_id=source_id,
                                                target_id=node_id,
                                                type=edge_type,
                                                properties={
                                                    'via_role': role_name,
                                                    'resource': resource
                                                }
                                            ))
        
        # Add all collected edges
        edge_count_before = self.graph.number_of_edges()
        for edge in edges_to_add:
            self._add_edge(edge)
        edge_count_after = self.graph.number_of_edges()
        
        # Build edges for service accounts that can act as other SAs
        self._build_service_account_usage_edges()
        
        logger.info(f"Built {edge_count_after - edge_count_before} privilege escalation edges")
    
    def _build_service_account_usage_edges(self):
        """Build edges for resources that use service accounts"""
        # This would be populated if we had resource data
        # For now, we'll skip this as it requires resource collection
        pass 