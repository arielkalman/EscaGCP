#!/usr/bin/env python3
"""
Enhanced Modals Demo for EscaGCP Dashboard

This script demonstrates the new enhanced modal functionality with:
- Rich node information display
- Advanced search and filtering
- Interactive edge visualization
- Export capabilities
"""

import json
import random
import networkx as nx
from datetime import datetime
from pathlib import Path
from gcphound.visualizers.html import HTMLVisualizer
from gcphound.utils import Config


def create_comprehensive_graph():
    """Create a comprehensive test graph with many nodes and edges"""
    graph = nx.DiGraph()
    
    # Create multiple projects
    projects = [f"project-{i}" for i in range(1, 6)]
    for project in projects:
        graph.add_node(f"project:{project}", 
                      type="project", 
                      name=project,
                      project_id=project,
                      description=f"Test project {project}")
    
    # Create users
    users = [
        ("alice", "alice@example.com", "Alice Smith"),
        ("bob", "bob@example.com", "Bob Johnson"),
        ("charlie", "charlie@example.com", "Charlie Brown"),
        ("david", "david@example.com", "David Wilson"),
        ("eve", "eve@example.com", "Eve Davis"),
        ("frank", "frank@external.com", "Frank External"),
    ]
    
    for username, email, full_name in users:
        graph.add_node(f"user:{email}",
                      type="user",
                      name=email,
                      email=email,
                      full_name=full_name)
    
    # Create service accounts
    service_accounts = []
    for project in projects[:3]:  # First 3 projects have SAs
        for sa_type in ["compute", "app", "function", "storage"]:
            sa_email = f"{sa_type}@{project}.iam.gserviceaccount.com"
            sa_id = f"sa:{sa_type}@{project}.iam"
            service_accounts.append(sa_id)
            graph.add_node(sa_id,
                          type="service_account",
                          name=f"{sa_type}@{project}.iam",
                          email=sa_email,
                          project_id=project,
                          description=f"{sa_type.title()} service account")
    
    # Create groups
    groups = [
        ("developers@example.com", "Developers Group"),
        ("admins@example.com", "Administrators Group"),
        ("security@example.com", "Security Team"),
        ("external-contractors@external.com", "External Contractors"),
    ]
    
    for email, description in groups:
        graph.add_node(f"group:{email}",
                      type="group",
                      name=email,
                      email=email,
                      description=description)
    
    # Create roles
    roles = [
        ("roles/owner", "Full control over all resources"),
        ("roles/editor", "Can modify all resources"),
        ("roles/viewer", "Read-only access"),
        ("roles/iam.serviceAccountTokenCreator", "Can impersonate service accounts"),
        ("roles/iam.serviceAccountKeyAdmin", "Can create service account keys"),
        ("roles/compute.admin", "Full control over Compute Engine"),
        ("roles/storage.admin", "Full control over Cloud Storage"),
        ("roles/cloudfunctions.admin", "Can deploy Cloud Functions"),
        ("roles/run.admin", "Can deploy Cloud Run services"),
        ("roles/container.admin", "Can manage GKE clusters"),
        ("roles/iam.securityAdmin", "Can modify IAM policies"),
        ("custom-developer-role", "Custom role for developers"),
    ]
    
    for role_name, description in roles:
        graph.add_node(f"role:{role_name}",
                      type="role",
                      name=role_name,
                      description=description)
    
    # Create folders and organization
    graph.add_node("org:example-org",
                  type="organization",
                  name="example-org",
                  description="Example Organization")
    
    folders = ["production", "development", "testing"]
    for folder in folders:
        graph.add_node(f"folder:{folder}",
                      type="folder",
                      name=folder,
                      description=f"{folder.title()} environment")
    
    # Add edges - Group memberships
    graph.add_edge("user:alice@example.com", "group:admins@example.com", type="MEMBER_OF")
    graph.add_edge("user:bob@example.com", "group:developers@example.com", type="MEMBER_OF")
    graph.add_edge("user:charlie@example.com", "group:developers@example.com", type="MEMBER_OF")
    graph.add_edge("user:david@example.com", "group:security@example.com", type="MEMBER_OF")
    graph.add_edge("user:eve@example.com", "group:admins@example.com", type="MEMBER_OF")
    graph.add_edge("user:frank@external.com", "group:external-contractors@external.com", type="MEMBER_OF")
    
    # Add edges - Role assignments
    # Admins have owner roles
    graph.add_edge("group:admins@example.com", "role:roles/owner", type="HAS_ROLE")
    graph.add_edge("user:alice@example.com", "role:roles/iam.securityAdmin", type="HAS_ROLE")
    
    # Developers have various roles
    graph.add_edge("group:developers@example.com", "role:roles/editor", type="HAS_ROLE")
    graph.add_edge("user:bob@example.com", "role:roles/iam.serviceAccountTokenCreator", type="HAS_ROLE")
    graph.add_edge("user:charlie@example.com", "role:roles/compute.admin", type="HAS_ROLE")
    
    # Security team
    graph.add_edge("group:security@example.com", "role:roles/viewer", type="HAS_ROLE")
    graph.add_edge("user:david@example.com", "role:roles/iam.securityAdmin", type="HAS_ROLE")
    
    # External contractors - limited access
    graph.add_edge("group:external-contractors@external.com", "role:custom-developer-role", type="HAS_ROLE")
    
    # Add dangerous edges - Service account impersonation
    graph.add_edge("user:bob@example.com", "sa:compute@project-1.iam", 
                  type="CAN_IMPERSONATE_SA",
                  permission="iam.serviceAccounts.getAccessToken",
                  resource_scope="project/project-1")
    
    graph.add_edge("user:alice@example.com", "sa:app@project-1.iam",
                  type="CAN_CREATE_SERVICE_ACCOUNT_KEY",
                  permission="iam.serviceAccountKeys.create",
                  resource_scope="project/project-1")
    
    # VM-based attacks
    graph.add_edge("user:charlie@example.com", "sa:compute@project-2.iam",
                  type="CAN_ACT_AS_VIA_VM",
                  permission="compute.instances.setServiceAccount + iam.serviceAccounts.actAs",
                  resource_scope="project/project-2")
    
    # Cloud Function deployment
    graph.add_edge("user:bob@example.com", "sa:function@project-1.iam",
                  type="CAN_DEPLOY_FUNCTION_AS",
                  permission="cloudfunctions.functions.create + iam.serviceAccounts.actAs",
                  resource_scope="project/project-1")
    
    # Cloud Run deployment
    graph.add_edge("group:developers@example.com", "sa:app@project-2.iam",
                  type="CAN_DEPLOY_CLOUD_RUN_AS",
                  permission="run.services.create + iam.serviceAccounts.actAs",
                  resource_scope="project/project-2")
    
    # VM login access
    graph.add_edge("user:frank@external.com", "project:project-3",
                  type="CAN_LOGIN_TO_VM",
                  permission="compute.instances.osLogin",
                  resource_scope="project/project-3")
    
    # Cloud Build triggers
    graph.add_edge("user:charlie@example.com", "sa:compute@project-3.iam",
                  type="CAN_TRIGGER_BUILD_AS",
                  permission="cloudbuild.builds.create",
                  resource_scope="project/project-3")
    
    # Add some role-to-resource relationships
    for project in projects[:3]:
        graph.add_edge("role:roles/owner", f"project:{project}", type="APPLIES_TO")
        graph.add_edge("role:roles/editor", f"project:{project}", type="APPLIES_TO")
    
    # Add folder relationships
    graph.add_edge("folder:production", "project:project-1", type="CONTAINS")
    graph.add_edge("folder:production", "project:project-2", type="CONTAINS")
    graph.add_edge("folder:development", "project:project-3", type="CONTAINS")
    graph.add_edge("folder:testing", "project:project-4", type="CONTAINS")
    graph.add_edge("folder:testing", "project:project-5", type="CONTAINS")
    
    # Add org relationships
    for folder in folders:
        graph.add_edge("org:example-org", f"folder:{folder}", type="CONTAINS")
    
    return graph


def generate_risk_scores(graph):
    """Generate risk scores for nodes"""
    risk_scores = {}
    
    # High risk for users with dangerous permissions
    dangerous_edge_types = [
        "CAN_IMPERSONATE_SA", 
        "CAN_CREATE_SERVICE_ACCOUNT_KEY",
        "CAN_ACT_AS_VIA_VM",
        "CAN_DEPLOY_FUNCTION_AS",
        "CAN_DEPLOY_CLOUD_RUN_AS"
    ]
    
    for node in graph.nodes():
        risk = 0.0
        
        # Check outgoing edges
        for _, _, edge_data in graph.out_edges(node, data=True):
            if edge_data.get('type') in dangerous_edge_types:
                risk = max(risk, 0.8)
        
        # Check if has dangerous roles
        for _, target in graph.out_edges(node):
            if target in ["role:roles/owner", "role:roles/iam.securityAdmin"]:
                risk = max(risk, 0.9)
            elif target in ["role:roles/editor", "role:roles/iam.serviceAccountTokenCreator"]:
                risk = max(risk, 0.7)
        
        if risk > 0:
            risk_scores[node] = risk
    
    return risk_scores


def generate_attack_paths(graph):
    """Generate sample attack paths"""
    attack_paths = [
        {
            "path": "user:bob@example.com -> sa:compute@project-1.iam -> project:project-1",
            "risk_score": 0.85,
            "description": "User can impersonate compute service account to gain project access",
            "category": "privilege_escalation",
            "length": 2,
            "path_nodes": [
                {"id": "user:bob@example.com", "name": "bob@example.com"},
                {"id": "sa:compute@project-1.iam", "name": "compute@project-1.iam"},
                {"id": "project:project-1", "name": "project-1"}
            ],
            "path_edges": [
                {"type": "CAN_IMPERSONATE_SA", "permission": "iam.serviceAccounts.getAccessToken"},
                {"type": "HAS_ACCESS_TO", "permission": "compute.*"}
            ]
        },
        {
            "path": "user:alice@example.com -> sa:app@project-1.iam -> project:project-1",
            "risk_score": 0.9,
            "description": "Admin can create service account keys for persistent access",
            "category": "critical",
            "length": 2,
            "path_nodes": [
                {"id": "user:alice@example.com", "name": "alice@example.com"},
                {"id": "sa:app@project-1.iam", "name": "app@project-1.iam"},
                {"id": "project:project-1", "name": "project-1"}
            ]
        },
        {
            "path": "user:charlie@example.com -> sa:compute@project-2.iam -> project:project-2",
            "risk_score": 0.75,
            "description": "User can deploy VMs with service account attached",
            "category": "privilege_escalation",
            "length": 2,
            "path_nodes": [
                {"id": "user:charlie@example.com", "name": "charlie@example.com"},
                {"id": "sa:compute@project-2.iam", "name": "compute@project-2.iam"},
                {"id": "project:project-2", "name": "project-2"}
            ]
        },
        {
            "path": "group:developers@example.com -> sa:app@project-2.iam -> project:project-2",
            "risk_score": 0.7,
            "description": "Developer group can deploy Cloud Run services as service account",
            "category": "lateral_movement",
            "length": 2,
            "path_nodes": [
                {"id": "group:developers@example.com", "name": "developers@example.com"},
                {"id": "sa:app@project-2.iam", "name": "app@project-2.iam"},
                {"id": "project:project-2", "name": "project-2"}
            ]
        }
    ]
    
    return attack_paths


def main():
    # Create comprehensive graph
    print("Creating comprehensive test graph...")
    graph = create_comprehensive_graph()
    print(f"Created graph with {graph.number_of_nodes()} nodes and {graph.number_of_edges()} edges")
    
    # Generate risk scores
    print("\nGenerating risk scores...")
    risk_scores = generate_risk_scores(graph)
    print(f"Generated risk scores for {len(risk_scores)} nodes")
    
    # Generate attack paths
    print("\nGenerating attack paths...")
    attack_paths = generate_attack_paths(graph)
    print(f"Generated {len(attack_paths)} attack paths")
    
    # Create config
    config = Config()
    
    # Create visualizer
    print("\nCreating visualization...")
    visualizer = HTMLVisualizer(graph, config)
    
    # Create visualization
    output_file = "enhanced_modals_demo.html"
    visualizer.create_full_graph(
        output_file=output_file,
        risk_scores=risk_scores,
        attack_paths=attack_paths
    )
    
    print(f"\n✅ Visualization created: {output_file}")
    print("\n📊 Graph Statistics:")
    print(f"   - Total Nodes: {graph.number_of_nodes()}")
    print(f"   - Total Edges: {graph.number_of_edges()}")
    print(f"   - Node Types: {len(set(data.get('type', 'unknown') for _, data in graph.nodes(data=True)))}")
    print(f"   - Edge Types: {len(set(data.get('type', 'unknown') for _, _, data in graph.edges(data=True)))}")
    print(f"   - High Risk Nodes: {sum(1 for score in risk_scores.values() if score > 0.7)}")
    
    print("\n🎯 Enhanced Modal Features to Test:")
    print("1. Click 'Total Nodes' to see the enhanced nodes modal with:")
    print("   - Search by name, ID, or metadata")
    print("   - Filter by node type")
    print("   - Sort by name or degree")
    print("   - View node metadata (email, project ID, etc.)")
    print("   - See in/out degree for each node")
    print("   - Click nodes to highlight in graph")
    print("   - Export nodes data as JSON")
    
    print("\n2. Click 'Total Edges' to see the enhanced edges modal with:")
    print("   - Search by source, target, or permission")
    print("   - Filter by edge type or severity")
    print("   - View edge permissions and rationale")
    print("   - Color-coded severity levels")
    print("   - Click source/target to navigate")
    print("   - Export edges data as JSON")
    
    print("\n3. Test the interactive features:")
    print("   - Type in search boxes to filter results")
    print("   - Use dropdowns to filter by type")
    print("   - Click on nodes/edges for interactions")
    print("   - Notice the responsive design")
    
    print("\n🚀 To open the demo:")
    print(f"   open {output_file}")


if __name__ == "__main__":
    main() 