"""
Graph models for nodes and edges
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List


class NodeType(Enum):
    """
    Types of nodes in the GCP graph
    """
    USER = "user"
    SERVICE_ACCOUNT = "service_account"
    GROUP = "group"
    PROJECT = "project"
    FOLDER = "folder"
    ORGANIZATION = "organization"
    ROLE = "role"
    RESOURCE = "resource"
    BUCKET = "bucket"
    INSTANCE = "instance"
    FUNCTION = "function"
    DATASET = "dataset"
    SECRET = "secret"
    KMS_KEY = "kms_key"
    TOPIC = "topic"
    CLOUD_RUN_SERVICE = "cloud_run_service"
    GKE_CLUSTER = "gke_cluster"
    GKE_WORKLOAD = "gke_workload"
    TAG = "tag"
    TAG_VALUE = "tag_value"
    CUSTOM_ROLE = "custom_role"
    WORKLOAD_IDENTITY_PROVIDER = "workload_identity_provider"
    CLOUD_BUILD_TRIGGER = "cloud_build_trigger"
    COMPUTE_INSTANCE = "compute_instance"


class EdgeType(Enum):
    """
    Types of edges (relationships) in the GCP graph
    """
    HAS_ROLE = "has_role"
    MEMBER_OF = "member_of"
    CAN_IMPERSONATE = "can_impersonate"
    OWNS = "owns"
    INHERITS = "inherits"
    HAS_PERMISSION = "has_permission"
    PARENT_OF = "parent_of"
    USES_SERVICE_ACCOUNT = "uses_service_account"
    HAS_ACCESS_TO = "has_access_to"
    CAN_INVOKE = "can_invoke"
    CAN_READ = "can_read"
    CAN_WRITE = "can_write"
    CAN_ADMIN = "can_admin"
    
    # New edge types for advanced privilege escalation
    CAN_IMPERSONATE_SA = "can_impersonate_sa"  # Direct token creation
    CAN_CREATE_SERVICE_ACCOUNT_KEY = "can_create_service_account_key"  # Key creation
    CAN_ACT_AS_VIA_VM = "can_act_as_via_vm"  # actAs + VM deploy
    CAN_DEPLOY_FUNCTION_AS = "can_deploy_function_as"  # Cloud Function deploy with SA
    CAN_DEPLOY_CLOUD_RUN_AS = "can_deploy_cloud_run_as"  # Cloud Run deploy with SA
    CAN_TRIGGER_BUILD_AS = "can_trigger_build_as"  # Cloud Build trigger
    CAN_LOGIN_TO_VM = "can_login_to_vm"  # OS Login or IAP access
    RUNS_AS = "runs_as"  # VM/Function/etc runs as SA
    CAN_SATISFY_IAM_CONDITION = "can_satisfy_iam_condition"  # Tag-based escalation
    EXTERNAL_PRINCIPAL_CAN_IMPERSONATE = "external_principal_can_impersonate"  # WIF abuse
    CAN_HIJACK_WORKLOAD_IDENTITY = "can_hijack_workload_identity"  # GKE WI abuse
    CAN_MODIFY_CUSTOM_ROLE = "can_modify_custom_role"  # Custom role escalation
    CAN_LAUNCH_AS_DEFAULT_SA = "can_launch_as_default_sa"  # Default SA abuse
    CAN_ATTACH_SERVICE_ACCOUNT = "can_attach_service_account"  # Attach SA to resource
    CAN_UPDATE_METADATA = "can_update_metadata"  # Update instance metadata
    CAN_DEPLOY_GKE_POD_AS = "can_deploy_gke_pod_as"  # Deploy pod with SA
    CAN_ASSIGN_CUSTOM_ROLE = "can_assign_custom_role"  # Assign custom role
    HAS_TAG_BINDING = "has_tag_binding"  # Resource has tag
    CAN_CREATE_TAG_BINDING = "can_create_tag_binding"  # Can bind tags
    HAS_CONDITIONAL_ROLE = "has_conditional_role"  # Role with IAM condition
    CAN_SSH_AND_IMPERSONATE = "can_ssh_and_impersonate"  # SSH + SA impersonation
    HAS_TAG_BINDING_ESCALATION = "has_tag_binding_escalation"  # Tag-based priv esc
    
    # Audit log enriched edges
    HAS_IMPERSONATED = "has_impersonated"  # Confirmed from audit logs
    HAS_ESCALATED_PRIVILEGE = "has_escalated_privilege"  # Confirmed from audit logs
    HAS_ACCESSED = "has_accessed"  # Confirmed from audit logs


@dataclass
class Node:
    """
    Represents a node in the GCP graph
    """
    id: str
    type: NodeType
    name: str
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash(self.id)
    
    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return self.id == other.id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert node to dictionary"""
        return {
            'id': self.id,
            'type': self.type.value,
            'name': self.name,
            'properties': self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Node':
        """Create node from dictionary"""
        return cls(
            id=data['id'],
            type=NodeType(data['type']),
            name=data['name'],
            properties=data.get('properties', {})
        )
    
    def get_display_name(self) -> str:
        """Get a human-readable display name"""
        if self.type == NodeType.USER:
            return self.properties.get('email', self.name)
        elif self.type == NodeType.SERVICE_ACCOUNT:
            return self.properties.get('email', self.name)
        elif self.type == NodeType.GROUP:
            return self.properties.get('displayName', self.name)
        elif self.type == NodeType.PROJECT:
            return self.properties.get('displayName', self.name)
        elif self.type == NodeType.ROLE:
            return self.properties.get('title', self.name)
        elif self.type == NodeType.CUSTOM_ROLE:
            return self.properties.get('title', self.name)
        else:
            return self.name
    
    def get_risk_score(self) -> float:
        """Calculate risk score for the node"""
        score = 0.0
        
        # High-value node types
        if self.type == NodeType.ORGANIZATION:
            score += 0.3
        elif self.type == NodeType.FOLDER:
            score += 0.25
        elif self.type == NodeType.PROJECT:
            score += 0.2
        elif self.type == NodeType.SERVICE_ACCOUNT:
            score += 0.1
            # Additional risk for high-privilege service accounts
            if self.properties.get('hasTokenCreatorRole'):
                score += 0.3
            if self.properties.get('hasOwnerRole'):
                score += 0.4
            if self.properties.get('isDefaultServiceAccount'):
                score += 0.2
            if self.properties.get('hasEditorRole'):
                score += 0.3
        
        # Dangerous roles
        if self.type == NodeType.ROLE:
            dangerous_roles = [
                'roles/owner',
                'roles/editor',
                'roles/iam.securityAdmin',
                'roles/iam.serviceAccountAdmin',
                'roles/iam.serviceAccountTokenCreator',
                'roles/iam.serviceAccountKeyAdmin',
                'roles/resourcemanager.organizationAdmin',
                'roles/resourcemanager.folderAdmin',
                'roles/resourcemanager.projectIamAdmin',
                'roles/cloudfunctions.admin',
                'roles/run.admin',
                'roles/container.admin',
                'roles/compute.admin',
                'roles/cloudbuild.builds.editor'
            ]
            if self.name in dangerous_roles:
                score += 0.5
        
        # Custom roles with dangerous permissions
        if self.type == NodeType.CUSTOM_ROLE:
            dangerous_perms = self.properties.get('dangerousPermissions', [])
            if dangerous_perms:
                score += min(0.6, len(dangerous_perms) * 0.1)
        
        # Sensitive resources
        if self.type in [NodeType.SECRET, NodeType.KMS_KEY]:
            score += 0.3
        
        # Cloud Functions and Run services (code execution)
        if self.type in [NodeType.FUNCTION, NodeType.CLOUD_RUN_SERVICE]:
            score += 0.25
            # Higher risk if using privileged SA
            if self.properties.get('serviceAccountEmail'):
                sa_email = self.properties['serviceAccountEmail']
                if 'editor' in sa_email or 'owner' in sa_email:
                    score += 0.2
        
        # GKE clusters (container escape potential)
        if self.type == NodeType.GKE_CLUSTER:
            score += 0.3
            if self.properties.get('workloadIdentityEnabled'):
                score += 0.1
        
        # Compute instances
        if self.type == NodeType.COMPUTE_INSTANCE:
            score += 0.15
            # Higher risk if using privileged SA
            if self.properties.get('serviceAccounts'):
                for sa in self.properties['serviceAccounts']:
                    if sa.get('email', '').endswith('-compute@developer.gserviceaccount.com'):
                        score += 0.2  # Default compute SA
                        break
        
        # Tags (potential for privilege escalation)
        if self.type in [NodeType.TAG, NodeType.TAG_VALUE]:
            score += 0.2
            if self.properties.get('usedInIAMConditions'):
                score += 0.3
        
        # Workload Identity Providers
        if self.type == NodeType.WORKLOAD_IDENTITY_PROVIDER:
            score += 0.25
            if self.properties.get('allowsAnyPrincipal'):
                score += 0.4
        
        # Cloud Build triggers
        if self.type == NodeType.CLOUD_BUILD_TRIGGER:
            score += 0.2
            if self.properties.get('usesPrivilegedServiceAccount'):
                score += 0.3
        
        return min(score, 1.0)


@dataclass
class Edge:
    """
    Represents an edge (relationship) in the GCP graph
    """
    source_id: str
    target_id: str
    type: EdgeType
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __hash__(self):
        return hash((self.source_id, self.target_id, self.type))
    
    def __eq__(self, other):
        if not isinstance(other, Edge):
            return False
        return (
            self.source_id == other.source_id and
            self.target_id == other.target_id and
            self.type == other.type
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert edge to dictionary"""
        return {
            'source_id': self.source_id,
            'target_id': self.target_id,
            'type': self.type.value,
            'properties': self.properties
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Edge':
        """Create edge from dictionary"""
        return cls(
            source_id=data['source_id'],
            target_id=data['target_id'],
            type=EdgeType(data['type']),
            properties=data.get('properties', {})
        )
    
    def get_risk_score(self) -> float:
        """Calculate risk score for the edge"""
        score = 0.0
        
        # Critical edges for privilege escalation
        if self.type == EdgeType.CAN_IMPERSONATE_SA:
            score += 0.9
        elif self.type == EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY:
            score += 0.85
        elif self.type == EdgeType.CAN_ACT_AS_VIA_VM:
            score += 0.8
        elif self.type == EdgeType.CAN_DEPLOY_FUNCTION_AS:
            score += 0.9
        elif self.type == EdgeType.CAN_DEPLOY_CLOUD_RUN_AS:
            score += 0.9
        elif self.type == EdgeType.CAN_TRIGGER_BUILD_AS:
            score += 0.85
        elif self.type == EdgeType.CAN_LOGIN_TO_VM:
            score += 0.6
            # Higher if combined with RUNS_AS
            if self.properties.get('vmRunsAsPrivilegedSA'):
                score += 0.2
        elif self.type == EdgeType.RUNS_AS:
            score += 0.5
            # Higher if SA is privileged
            if self.properties.get('serviceAccountPrivileged'):
                score += 0.3
        elif self.type == EdgeType.CAN_SATISFY_IAM_CONDITION:
            score += 0.75
        elif self.type == EdgeType.EXTERNAL_PRINCIPAL_CAN_IMPERSONATE:
            score += 0.95
        elif self.type == EdgeType.CAN_HIJACK_WORKLOAD_IDENTITY:
            score += 0.85
        elif self.type == EdgeType.CAN_MODIFY_CUSTOM_ROLE:
            score += 0.8
        elif self.type == EdgeType.CAN_LAUNCH_AS_DEFAULT_SA:
            score += 0.7
            if self.properties.get('defaultSAIsEditor'):
                score += 0.2
        elif self.type == EdgeType.CAN_ATTACH_SERVICE_ACCOUNT:
            score += 0.75
        elif self.type == EdgeType.CAN_UPDATE_METADATA:
            score += 0.7
        elif self.type == EdgeType.CAN_DEPLOY_GKE_POD_AS:
            score += 0.85
        elif self.type == EdgeType.CAN_ASSIGN_CUSTOM_ROLE:
            score += 0.8
        elif self.type == EdgeType.HAS_TAG_BINDING_ESCALATION:
            score += 0.75
        elif self.type == EdgeType.CAN_SSH_AND_IMPERSONATE:
            score += 0.8
        
        # Confirmed exploitation from audit logs
        elif self.type == EdgeType.HAS_IMPERSONATED:
            score += 0.95  # Very high risk - confirmed activity
        elif self.type == EdgeType.HAS_ESCALATED_PRIVILEGE:
            score += 1.0  # Maximum risk - confirmed escalation
        elif self.type == EdgeType.HAS_ACCESSED:
            score += 0.6
        
        # Standard edges
        elif self.type == EdgeType.CAN_IMPERSONATE:
            score += 0.8
        elif self.type == EdgeType.HAS_ROLE:
            # Check if it's a dangerous role
            role = self.properties.get('role', '')
            if any(r in role for r in ['owner', 'editor', 'admin', 'tokenCreator', 'keyAdmin']):
                score += 0.6
            else:
                score += 0.2
        elif self.type == EdgeType.CAN_ADMIN:
            score += 0.7
        elif self.type in [EdgeType.CAN_WRITE, EdgeType.OWNS]:
            score += 0.5
        elif self.type == EdgeType.CAN_READ:
            score += 0.3
        elif self.type == EdgeType.MEMBER_OF:
            score += 0.1
        
        # Conditional bindings reduce risk
        if self.properties.get('condition'):
            score = score * 0.7
        
        # Audit-confirmed edges increase risk
        if self.properties.get('confirmedByAudit'):
            score = min(score * 1.2, 1.0)
        
        return min(score, 1.0)
    
    def is_high_risk(self) -> bool:
        """Check if this edge represents a high-risk relationship"""
        return self.get_risk_score() >= 0.6
    
    def is_privilege_escalation(self) -> bool:
        """Check if this edge can lead to privilege escalation"""
        escalation_edges = {
            EdgeType.CAN_IMPERSONATE,
            EdgeType.CAN_IMPERSONATE_SA,
            EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY,
            EdgeType.CAN_ACT_AS_VIA_VM,
            EdgeType.CAN_DEPLOY_FUNCTION_AS,
            EdgeType.CAN_DEPLOY_CLOUD_RUN_AS,
            EdgeType.CAN_TRIGGER_BUILD_AS,
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
        return self.type in escalation_edges


@dataclass
class GraphMetadata:
    """
    Metadata about the graph
    """
    total_nodes: int = 0
    total_edges: int = 0
    node_counts: Dict[NodeType, int] = field(default_factory=dict)
    edge_counts: Dict[EdgeType, int] = field(default_factory=dict)
    collection_time: Optional[str] = None
    gcp_projects: List[str] = field(default_factory=list)
    gcp_organization: Optional[str] = None
    high_risk_paths: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary"""
        return {
            'total_nodes': self.total_nodes,
            'total_edges': self.total_edges,
            'node_counts': {k.value: v for k, v in self.node_counts.items()},
            'edge_counts': {k.value: v for k, v in self.edge_counts.items()},
            'collection_time': self.collection_time,
            'gcp_projects': self.gcp_projects,
            'gcp_organization': self.gcp_organization,
            'high_risk_paths': self.high_risk_paths
        }


@dataclass
class AttackPath:
    """
    Represents an attack path in the graph
    """
    source_node: Node
    target_node: Node
    path_nodes: List[Node]
    path_edges: List[Edge]
    risk_score: float = 0.0
    description: str = ""
    visualization_metadata: Optional[Dict[str, Any]] = None
    
    def __len__(self) -> int:
        """Get the length of the path"""
        return len(self.path_edges)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert attack path to dictionary"""
        result = {
            'source': self.source_node.to_dict(),
            'target': self.target_node.to_dict(),
            'path_nodes': [n.to_dict() for n in self.path_nodes],
            'path_edges': [e.to_dict() for e in self.path_edges],
            'risk_score': self.risk_score,
            'description': self.description,
            'length': len(self)
        }
        
        if self.visualization_metadata:
            result['visualization_metadata'] = self.visualization_metadata
            
        return result
    
    def get_path_string(self) -> str:
        """Get a string representation of the path"""
        path_parts = []
        for i, edge in enumerate(self.path_edges):
            if i == 0:
                path_parts.append(self.path_nodes[i].get_display_name())
            path_parts.append(f"--[{edge.type.value}]-->")
            path_parts.append(self.path_nodes[i + 1].get_display_name())
        return " ".join(path_parts)
    
    def get_attack_graph_data(self) -> Dict[str, Any]:
        """Get data for attack path visualization"""
        if not self.visualization_metadata:
            return {}
            
        return {
            'nodes': self.visualization_metadata.get('node_metadata', []),
            'edges': self.visualization_metadata.get('edge_metadata', []),
            'techniques': self.visualization_metadata.get('escalation_techniques', []),
            'permissions': self.visualization_metadata.get('permissions_used', []),
            'summary': self.visualization_metadata.get('attack_summary', ''),
            'risk_score': self.risk_score,
            'path_length': len(self)
        } 