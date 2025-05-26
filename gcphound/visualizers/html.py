"""
HTML visualization for GCPHound graphs - Dashboard style
"""

import json
import networkx as nx
from pyvis.network import Network
from typing import Dict, Any, Optional, List, Set
from collections import defaultdict
from datetime import datetime
from ..utils import get_logger, Config
from ..graph.models import NodeType, EdgeType
from ..analyzers import PathAnalyzer


logger = get_logger(__name__)


class HTMLVisualizer:
    """
    Create interactive HTML dashboard visualizations of the graph
    """
    
    # Dangerous roles that enable privilege escalation
    DANGEROUS_ROLES = {
        'roles/owner': 'Full control over all resources',
        'roles/editor': 'Can modify all resources',
        'roles/iam.securityAdmin': 'Can modify IAM policies',
        'roles/iam.serviceAccountAdmin': 'Can create and manage service accounts',
        'roles/iam.serviceAccountTokenCreator': 'Can impersonate service accounts',
        'roles/iam.serviceAccountKeyAdmin': 'Can create service account keys',
        'roles/resourcemanager.organizationAdmin': 'Full control over organization',
        'roles/resourcemanager.folderAdmin': 'Full control over folders',
        'roles/resourcemanager.projectIamAdmin': 'Can modify project IAM policies',
        'roles/compute.admin': 'Can create VMs and attach service accounts',
        'roles/cloudfunctions.admin': 'Can deploy functions with service accounts',
        'roles/run.admin': 'Can deploy Cloud Run services with service accounts',
        'roles/container.admin': 'Can manage GKE clusters and workloads',
        'roles/cloudbuild.builds.editor': 'Can trigger builds with service accounts'
    }
    
    # Attack path explanations
    ATTACK_PATH_EXPLANATIONS = {
        'service_account_impersonation': {
            'title': 'Service Account Impersonation',
            'description': 'An attacker can generate access tokens for a service account, effectively becoming that service account',
            'exploitation': 'Use gcloud or API calls to generate access tokens: gcloud auth print-access-token --impersonate-service-account=SA_EMAIL',
            'prevention': 'Limit serviceAccountTokenCreator role grants, use short-lived tokens, enable audit logging'
        },
        'service_account_key_creation': {
            'title': 'Service Account Key Creation',
            'description': 'An attacker can create long-lived keys for a service account',
            'exploitation': 'Create a key using: gcloud iam service-accounts keys create key.json --iam-account=SA_EMAIL',
            'prevention': 'Disable key creation, use workload identity, monitor key creation events'
        },
        'vm_service_account_abuse': {
            'title': 'VM Service Account Abuse',
            'description': 'An attacker can create or modify VMs to run with a privileged service account',
            'exploitation': 'Create VM with SA: gcloud compute instances create vm-name --service-account=SA_EMAIL --scopes=cloud-platform',
            'prevention': 'Restrict compute.admin role, use least-privilege service accounts for VMs'
        },
        'cloud_function_deployment': {
            'title': 'Cloud Function Deployment',
            'description': 'An attacker can deploy cloud functions that execute with a privileged service account',
            'exploitation': 'Deploy function: gcloud functions deploy func-name --service-account=SA_EMAIL --source=.',
            'prevention': 'Restrict function deployment permissions, use dedicated SAs for functions'
        },
        'cloud_run_deployment': {
            'title': 'Cloud Run Service Deployment',
            'description': 'An attacker can deploy Cloud Run services that execute with a privileged service account',
            'exploitation': 'Deploy service: gcloud run deploy --service-account=SA_EMAIL --image=malicious-image',
            'prevention': 'Restrict Cloud Run admin permissions, use least-privilege service accounts'
        }
    }
    
    def __init__(self, graph: nx.DiGraph, config: Config):
        """
        Initialize HTML visualizer
        
        Args:
            graph: NetworkX directed graph
            config: Configuration instance
        """
        self.graph = graph
        self.config = config
    
    def create_full_graph(
        self,
        output_file: str,
        risk_scores: Optional[Dict[str, Any]] = None,
        attack_paths: Optional[List[Dict[str, Any]]] = None,
        highlight_nodes: Optional[Set[str]] = None
    ):
        """
        Create full graph visualization with dashboard
        
        Args:
            output_file: Output HTML file path
            risk_scores: Optional risk scores for coloring
            attack_paths: Optional list of attack paths found
            highlight_nodes: Optional set of critical nodes to highlight
        """
        logger.info(f"Creating HTML dashboard visualization: {output_file}")
        
        # Analyze the graph if not provided
        if not attack_paths and not risk_scores:
            analyzer = PathAnalyzer(self.graph, self.config)
            analysis_results = analyzer.analyze_all_paths()
            risk_scores = analysis_results.get('risk_scores', {})
            
            # Convert attack paths to simple format
            attack_paths = []
            for category, paths in analysis_results.get('attack_paths', {}).items():
                for path in paths:
                    attack_paths.append({
                        'category': category,
                        'path': path.get_path_string() if hasattr(path, 'get_path_string') else str(path),
                        'risk_score': path.risk_score if hasattr(path, 'risk_score') else 0,
                        'length': len(path) if hasattr(path, '__len__') else 0
                    })
        
        # Create the dashboard HTML
        html_content = self._create_dashboard_html(risk_scores, attack_paths, highlight_nodes)
        
        # Save to file
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"Saved HTML dashboard visualization with {len(self.graph.nodes)} nodes")
    
    def _create_dashboard_html(
        self,
        risk_scores: Dict[str, Any],
        attack_paths: List[Dict[str, Any]],
        highlight_nodes: Optional[Set[str]]
    ) -> str:
        """Create the complete dashboard HTML"""
        
        # Create the graph visualization
        graph_html = self._create_graph_html(risk_scores, highlight_nodes)
        
        # Analyze dangerous roles in the graph
        dangerous_roles_info = self._analyze_dangerous_roles()
        
        # Get statistics
        stats = self._calculate_statistics(risk_scores, attack_paths)
        
        # Get detailed node and edge lists
        nodes_by_type = self._get_nodes_by_type()
        edges_by_type = self._get_edges_by_type()
        
        # Create the complete HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>GCPHound Security Dashboard</title>
    <meta charset="utf-8">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8f9fa;
            color: #1a1f36;
            overflow: hidden;
        }}
        
        .dashboard {{
            display: flex;
            height: 100vh;
            width: 100vw;
        }}
        
        .main-content {{
            flex: 1;
            display: flex;
            flex-direction: column;
            min-width: 0;
        }}
        
        .header {{
            background-color: #ffffff;
            padding: 15px 20px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        .header h1 {{
            margin: 0;
            color: #6b46c1;
            font-size: 24px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
        }}
        
        .stats-bar {{
            display: flex;
            gap: 20px;
        }}
        
        .stat-item {{
            background-color: #ffffff;
            padding: 8px 15px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Inter', sans-serif;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }}
        
        .stat-item:hover {{
            background-color: #f3f4f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-value {{
            font-size: 20px;
            font-weight: 600;
            color: #6b46c1;
            font-family: 'Inter', sans-serif;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 2px;
            font-weight: 400;
            font-family: 'Inter', sans-serif;
        }}
        
        .share-button {{
            background-color: #6b46c1;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-left: 20px;
        }}
        
        .share-button:hover {{
            background-color: #553c9a;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .share-button svg {{
            width: 16px;
            height: 16px;
        }}
        
        .share-modal {{
            display: none;
            position: fixed;
            z-index: 2000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}
        
        .share-modal-content {{
            background-color: #ffffff;
            margin: 10% auto;
            padding: 30px;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            width: 90%;
            max-width: 500px;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
            text-align: center;
        }}
        
        .share-modal-title {{
            font-size: 24px;
            color: #6b46c1;
            font-weight: 600;
            margin-bottom: 20px;
        }}
        
        .share-modal-description {{
            color: #6b7280;
            margin-bottom: 30px;
            line-height: 1.6;
        }}
        
        .share-modal-button {{
            background-color: #6b46c1;
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.3s;
            margin: 0 10px;
        }}
        
        .share-modal-button:hover {{
            background-color: #553c9a;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .share-modal-button.cancel {{
            background-color: #e5e7eb;
            color: #6b7280;
        }}
        
        .share-modal-button.cancel:hover {{
            background-color: #d1d5db;
        }}
        
        .share-loading {{
            display: none;
            margin-top: 20px;
            color: #6b7280;
        }}
        
        .share-success {{
            display: none;
            margin-top: 20px;
            color: #059669;
            font-weight: 500;
        }}
        
        .graph-container {{
            flex: 1;
            position: relative;
            background-color: #f3f4f6;
            overflow: hidden;
        }}
        
        #mynetwork {{
            width: 100%;
            height: 100%;
        }}
        
        .sidebar {{
            width: 400px;
            background-color: #ffffff;
            border-left: 1px solid #e5e7eb;
            display: flex;
            flex-direction: column;
            overflow: hidden;
            box-shadow: -2px 0 4px rgba(0, 0, 0, 0.05);
        }}
        
        .sidebar-tabs {{
            display: flex;
            background-color: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .tab {{
            flex: 1;
            padding: 12px;
            text-align: center;
            cursor: pointer;
            background-color: transparent;
            border: none;
            color: #6b7280;
            font-size: 14px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            transition: all 0.3s;
            border-bottom: 2px solid transparent;
        }}
        
        .tab:hover {{
            background-color: #f3f4f6;
            color: #4b5563;
        }}
        
        .tab.active {{
            background-color: #ffffff;
            color: #6b46c1;
            border-bottom: 2px solid #6b46c1;
        }}
        
        .sidebar-content {{
            flex: 1;
            overflow-y: auto;
            padding: 20px;
            font-family: 'Inter', sans-serif;
            background-color: #ffffff;
        }}
        
        .legend-section {{
            margin-bottom: 25px;
        }}
        
        .legend-title {{
            font-size: 16px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #6b46c1;
            font-family: 'Inter', sans-serif;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            color: #4b5563;
        }}
        
        .legend-color {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            border-radius: 4px;
            border: 1px solid #e5e7eb;
        }}
        
        .legend-shape {{
            width: 20px;
            height: 20px;
            margin-right: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .attack-path-item {{
            background-color: #ffffff;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 15px;
            border-left: 4px solid #dc2626;
            font-family: 'Inter', sans-serif;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
        }}
        
        .attack-path-title {{
            font-weight: 600;
            margin-bottom: 5px;
            color: #dc2626;
            font-family: 'Inter', sans-serif;
        }}
        
        .attack-path-description {{
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 8px;
            font-family: 'Inter', sans-serif;
        }}
        
        .attack-path-exploitation {{
            font-size: 12px;
            background-color: #f9fafb;
            padding: 8px;
            border-radius: 4px;
            font-family: 'Inter', monospace;
            margin-bottom: 8px;
            overflow-x: auto;
            border: 1px solid #e5e7eb;
        }}
        
        .attack-path-prevention {{
            font-size: 12px;
            color: #059669;
            font-style: italic;
            font-family: 'Inter', sans-serif;
        }}
        
        .dangerous-role-item {{
            background-color: #fef2f2;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 10px;
            border-left: 4px solid #dc2626;
            font-family: 'Inter', sans-serif;
            border: 1px solid #fee2e2;
        }}
        
        .role-name {{
            font-weight: 600;
            color: #dc2626;
            margin-bottom: 5px;
            font-family: 'Inter', sans-serif;
        }}
        
        .role-description {{
            font-size: 13px;
            color: #6b7280;
            margin-bottom: 5px;
            font-family: 'Inter', sans-serif;
        }}
        
        .role-holders {{
            font-size: 12px;
            color: #9ca3af;
            font-family: 'Inter', sans-serif;
        }}
        
        .path-list-item {{
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            font-size: 13px;
            font-family: 'Inter', sans-serif;
            border: 1px solid #e5e7eb;
        }}
        
        .path-risk {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 10px;
            font-family: 'Inter', sans-serif;
        }}
        
        .risk-critical {{ background-color: #dc2626; color: white; }}
        .risk-high {{ background-color: #f59e0b; color: white; }}
        .risk-medium {{ background-color: #eab308; color: white; }}
        .risk-low {{ background-color: #22c55e; color: white; }}
        
        .hidden {{ display: none; }}
        
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.5);
        }}
        
        .modal-content {{
            background-color: #ffffff;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #e5e7eb;
            border-radius: 12px;
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
        }}
        
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            border-bottom: 1px solid #e5e7eb;
            padding-bottom: 15px;
        }}
        
        .modal-title {{
            font-size: 20px;
            color: #6b46c1;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
        }}
        
        .close {{
            color: #9ca3af;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
            font-family: 'Inter', sans-serif;
        }}
        
        .close:hover {{
            color: #4b5563;
        }}
        
        .modal-list {{
            list-style: none;
            padding: 0;
        }}
        
        .modal-list-item {{
            background-color: #f9fafb;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 8px;
            font-size: 14px;
            font-family: 'Inter', sans-serif;
            border: 1px solid #e5e7eb;
            color: #4b5563;
        }}
        
        .modal-list-item:hover {{
            background-color: #f3f4f6;
        }}
        
        .node-type-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 10px;
            background-color: #6b46c1;
            color: white;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
        }}
        
        .edge-type-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-left: 10px;
            background-color: #8b5cf6;
            color: white;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #f3f4f6;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #d1d5db;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #9ca3af;
        }}
        
        /* Collapsible sections */
        .collapsible {{
            background-color: #f9fafb;
            color: #4b5563;
            cursor: pointer;
            padding: 12px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            margin-bottom: 5px;
            border-radius: 8px;
            transition: 0.3s;
            border: 1px solid #e5e7eb;
        }}
        
        .collapsible:hover {{
            background-color: #f3f4f6;
        }}
        
        .collapsible.active {{
            background-color: #6b46c1;
            color: white;
        }}
        
        .collapsible-content {{
            padding: 0 18px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            background-color: #ffffff;
            border-radius: 0 0 8px 8px;
            font-family: 'Inter', sans-serif;
            border: 1px solid #e5e7eb;
            border-top: none;
        }}
        
        .collapsible-content.show {{
            max-height: 500px;
            padding: 18px;
            overflow-y: auto;
        }}
    </style>
</head>
<body>
    <div class="dashboard">
        <div class="main-content">
            <div class="header">
                <h1>GCPHound Security Dashboard</h1>
                <div class="stats-bar">
                    <div class="stat-item" onclick="showModal('nodes')">
                        <div class="stat-value">{stats['total_nodes']}</div>
                        <div class="stat-label">Total Nodes</div>
                    </div>
                    <div class="stat-item" onclick="showModal('edges')">
                        <div class="stat-value">{stats['total_edges']}</div>
                        <div class="stat-label">Total Edges</div>
                    </div>
                    <div class="stat-item" onclick="showModal('paths')">
                        <div class="stat-value">{stats['attack_paths']}</div>
                        <div class="stat-label">Attack Paths</div>
                    </div>
                    <div class="stat-item" onclick="showModal('highrisk')">
                        <div class="stat-value">{stats['high_risk_nodes']}</div>
                        <div class="stat-label">High Risk Nodes</div>
                    </div>
                    <div class="stat-item" onclick="showModal('dangerous')">
                        <div class="stat-value">{stats['dangerous_roles']}</div>
                        <div class="stat-label">Dangerous Roles</div>
                    </div>
                    <button class="share-button" onclick="showShareModal()">
                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m9.032 4.026a3 3 0 10-2.684-4.026m2.684 4.026a3 3 0 00-2.684-4.026m0 0a3 3 0 00-2.684 4.026m2.684-4.026a3 3 0 10-2.684-4.026m0 8.052a3 3 0 110-8.052" />
                        </svg>
                        Share Report
                    </button>
                </div>
            </div>
            <div class="graph-container">
                {graph_html}
            </div>
        </div>
        
        <div class="sidebar">
            <div class="sidebar-tabs">
                <button class="tab active" onclick="showTab('legend')">Legend</button>
                <button class="tab" onclick="showTab('attacks')">Attack Paths</button>
                <button class="tab" onclick="showTab('roles')">Dangerous Roles</button>
                <button class="tab" onclick="showTab('paths')">Found Paths</button>
            </div>
            
            <div class="sidebar-content">
                <!-- Legend Tab -->
                <div id="legend-tab" class="tab-content">
                    <button class="collapsible active" onclick="toggleCollapsible(this)">Node Types</button>
                    <div class="collapsible-content show">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #4285F4;"></div>
                            <span>User Account</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #34A853;"></div>
                            <span>Service Account</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #FBBC04;"></div>
                            <span>Group</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #EA4335;"></div>
                            <span>Project</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #FF6D00;"></div>
                            <span>Folder</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #9C27B0;"></div>
                            <span>Organization</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #757575;"></div>
                            <span>Role</span>
                        </div>
                    </div>
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Edge Types</button>
                    <div class="collapsible-content">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #757575;"></div>
                            <span>Has Role</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #F44336;"></div>
                            <span>Can Impersonate</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #FF5722;"></div>
                            <span>Can Admin</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #9E9E9E;"></div>
                            <span>Member Of</span>
                        </div>
                    </div>
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Risk Levels</button>
                    <div class="collapsible-content">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #d32f2f;"></div>
                            <span>Critical Risk (>0.8)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #f44336;"></div>
                            <span>High Risk (>0.6)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #ff9800;"></div>
                            <span>Medium Risk (>0.4)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #ffc107;"></div>
                            <span>Low Risk (>0.2)</span>
                        </div>
                    </div>
                </div>
                
                <!-- Attack Paths Tab -->
                <div id="attacks-tab" class="tab-content hidden">
                    {self._create_attack_explanations_html()}
                </div>
                
                <!-- Dangerous Roles Tab -->
                <div id="roles-tab" class="tab-content hidden">
                    {self._create_dangerous_roles_html(dangerous_roles_info)}
                </div>
                
                <!-- Found Paths Tab -->
                <div id="paths-tab" class="tab-content hidden">
                    {self._create_found_paths_html(attack_paths)}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modals -->
    <div id="nodesModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">All Nodes</h2>
                <span class="close" onclick="closeModal('nodes')">&times;</span>
            </div>
            <ul class="modal-list">
                {self._create_nodes_list_html(nodes_by_type)}
            </ul>
        </div>
    </div>
    
    <div id="edgesModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">All Edges</h2>
                <span class="close" onclick="closeModal('edges')">&times;</span>
            </div>
            <ul class="modal-list">
                {self._create_edges_list_html(edges_by_type)}
            </ul>
        </div>
    </div>
    
    <div id="pathsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">All Attack Paths</h2>
                <span class="close" onclick="closeModal('paths')">&times;</span>
            </div>
            <div>
                {self._create_found_paths_html(attack_paths, show_all=True)}
            </div>
        </div>
    </div>
    
    <div id="highriskModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">High Risk Nodes</h2>
                <span class="close" onclick="closeModal('highrisk')">&times;</span>
            </div>
            <ul class="modal-list">
                {self._create_high_risk_nodes_html(risk_scores)}
            </ul>
        </div>
    </div>
    
    <div id="dangerousModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">Dangerous Role Assignments</h2>
                <span class="close" onclick="closeModal('dangerous')">&times;</span>
            </div>
            <div>
                {self._create_dangerous_roles_html(dangerous_roles_info, show_all=True)}
            </div>
        </div>
    </div>
    
    <!-- Share Modal -->
    <div id="shareModal" class="share-modal">
        <div class="share-modal-content">
            <h2 class="share-modal-title">Share This Report</h2>
            <p class="share-modal-description">
                Generate a standalone HTML file that contains all the data and visualizations. 
                This file can be shared with anyone and viewed without any dependencies or internet connection.
            </p>
            <div>
                <button class="share-modal-button" onclick="generateStandaloneReport()">Generate Standalone Report</button>
                <button class="share-modal-button cancel" onclick="closeShareModal()">Cancel</button>
            </div>
            <div class="share-loading" id="shareLoading">
                Generating report... This may take a few seconds.
            </div>
            <div class="share-success" id="shareSuccess">
                ✅ Report generated successfully! Check your downloads folder.
            </div>
        </div>
    </div>
    
    <script>
        // Embed the graph data for sharing
        const graphData = {json.dumps(self._serialize_graph_for_standalone(risk_scores, highlight_nodes))};
        const riskScores = {json.dumps(risk_scores) if risk_scores else '{}'};
        const attackPaths = {json.dumps(attack_paths) if attack_paths else '[]'};
        const dangerousRolesInfo = {json.dumps(dangerous_roles_info)};
        const stats = {json.dumps(stats)};
        const nodesByType = {json.dumps(nodes_by_type)};
        const edgesByType = {json.dumps(edges_by_type)};
        
        // Define all functions first
        function showTab(tabName) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.add('hidden');
            }});
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.remove('hidden');
            
            // Add active class to clicked tab
            event.target.classList.add('active');
        }}
        
        function showModal(modalType) {{
            document.getElementById(modalType + 'Modal').style.display = 'block';
        }}
        
        function closeModal(modalType) {{
            document.getElementById(modalType + 'Modal').style.display = 'none';
        }}
        
        function toggleCollapsible(element) {{
            element.classList.toggle('active');
            var content = element.nextElementSibling;
            content.classList.toggle('show');
        }}
        
        function showShareModal() {{
            document.getElementById('shareModal').style.display = 'block';
            document.getElementById('shareLoading').style.display = 'none';
            document.getElementById('shareSuccess').style.display = 'none';
        }}
        
        function closeShareModal() {{
            document.getElementById('shareModal').style.display = 'none';
        }}
        
        function generateStandaloneReport() {{
            document.getElementById('shareLoading').style.display = 'block';
            
            try {{
                // Create the standalone HTML content using the embedded data
                const standaloneHTML = createStandaloneHTML();
                
                // Create a blob and download it
                const blob = new Blob([standaloneHTML], {{ type: 'text/html' }});
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'gcphound_report_' + new Date().toISOString().slice(0, 10) + '.html';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                // Show success message
                document.getElementById('shareLoading').style.display = 'none';
                document.getElementById('shareSuccess').style.display = 'block';
                
                // Close modal after 3 seconds
                setTimeout(() => {{
                    closeShareModal();
                }}, 3000);
            }} catch (error) {{
                console.error('Failed to generate report:', error);
                document.getElementById('shareLoading').innerHTML = 'Failed to generate report. Please try again.';
            }}
        }}
        
        function createStandaloneHTML() {{
            // Build the standalone HTML using the embedded data
            // This version uses a simple table-based visualization that works everywhere
            return `<!DOCTYPE html>
<html>
<head>
    <title>GCPHound Security Report - Standalone</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
            background-color: #f8f9fa;
            color: #1a1f36;
        }}
        
        .standalone-header {{
            background-color: #ffffff;
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        .standalone-title {{
            margin: 0 0 10px 0;
            color: #6b46c1;
            font-size: 28px;
            font-weight: 600;
        }}
        
        .standalone-subtitle {{
            color: #6b7280;
            font-size: 14px;
        }}
        
        .standalone-stats {{
            display: flex;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }}
        
        .stat-box {{
            background-color: #f9fafb;
            padding: 15px 25px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }}
        
        .stat-value {{
            font-size: 24px;
            font-weight: 600;
            color: #6b46c1;
        }}
        
        .stat-label {{
            font-size: 12px;
            color: #6b7280;
            margin-top: 5px;
        }}
        
        .content-section {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .section-title {{
            font-size: 20px;
            font-weight: 600;
            color: #6b46c1;
            margin: 30px 0 15px 0;
        }}
        
        .graph-summary {{
            background-color: #f9fafb;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        
        .node-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        
        .node-table th {{
            background-color: #6b46c1;
            color: white;
            padding: 10px;
            text-align: left;
            font-weight: 600;
        }}
        
        .node-table td {{
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .node-table tr:hover {{
            background-color: #f3f4f6;
        }}
        
        .node-type {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            background-color: #e5e7eb;
            color: #4b5563;
        }}
        
        .edge-list {{
            margin-top: 15px;
            max-height: 300px;
            overflow-y: auto;
            border: 1px solid #e5e7eb;
            border-radius: 4px;
            padding: 10px;
            background-color: white;
        }}
        
        .edge-item {{
            padding: 5px 0;
            border-bottom: 1px solid #f3f4f6;
            font-size: 14px;
        }}
        
        .edge-type {{
            color: #6b46c1;
            font-weight: 500;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .info-card {{
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
        }}
        
        .info-card-title {{
            font-size: 16px;
            font-weight: 600;
            color: #6b46c1;
            margin-bottom: 15px;
        }}
        
        .risk-item {{
            background-color: #fef2f2;
            border-left: 4px solid #dc2626;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
        }}
        
        .risk-high {{ border-left-color: #dc2626; background-color: #fef2f2; }}
        .risk-medium {{ border-left-color: #f59e0b; background-color: #fef3c7; }}
        .risk-low {{ border-left-color: #22c55e; background-color: #f0fdf4; }}
        
        .footer {{
            background-color: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
            margin-top: 50px;
            border-top: 1px solid #e5e7eb;
        }}
        
        @media (max-width: 768px) {{
            .standalone-stats {{
                flex-direction: column;
                gap: 10px;
            }}
            
            .info-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="standalone-header">
        <h1 class="standalone-title">GCPHound Security Report</h1>
        <p class="standalone-subtitle">Generated on ${{new Date().toLocaleString()}} | Standalone Report</p>
        
        <div class="standalone-stats">
            <div class="stat-box">
                <div class="stat-value">${{stats.total_nodes}}</div>
                <div class="stat-label">Total Nodes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${{stats.total_edges}}</div>
                <div class="stat-label">Total Edges</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${{stats.attack_paths}}</div>
                <div class="stat-label">Attack Paths</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${{stats.high_risk_nodes}}</div>
                <div class="stat-label">High Risk Nodes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${{stats.dangerous_roles}}</div>
                <div class="stat-label">Dangerous Roles</div>
            </div>
        </div>
    </div>
    
    <div class="content-section">
        <h2 class="section-title">Interactive Graph Visualization</h2>
        <div class="graph-container">
            <div id="mynetwork"></div>
        </div>
        
        <h2 class="section-title">Key Findings</h2>
        <div class="info-grid">
            <div class="info-card">
                <h3 class="info-card-title">Critical Attack Paths</h3>
                ${{attackPaths.filter(p => p.risk_score > 0.8).slice(0, 5).map(path => 
                    `<div class="risk-item risk-high">
                        <strong>${{path.path}}</strong><br>
                        Risk Score: ${{path.risk_score.toFixed(2)}}
                    </div>`
                ).join('')}}
            </div>
            
            <div class="info-card">
                <h3 class="info-card-title">Dangerous Role Assignments</h3>
                ${{Object.entries(dangerousRolesInfo).slice(0, 5).map(([role, holders]) => 
                    `<div class="risk-item risk-medium">
                        <strong>${{role}}</strong><br>
                        Assigned to: ${{holders.length}} identities
                    </div>`
                ).join('')}}
            </div>
            
            <div class="info-card">
                <h3 class="info-card-title">Resource Summary</h3>
                ${{Object.entries(nodesByType).map(([type, nodes]) => 
                    `<div style="margin-bottom: 8px;">
                        <strong>${{type}}:</strong> ${{nodes.length}}
                    </div>`
                ).join('')}}
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>This is a standalone GCPHound report. All data is embedded in this HTML file.</p>
        <p>No external dependencies or internet connection required.</p>
    </div>
    
    <script>
        // Embed the graph data
        const graphData = ${{JSON.stringify(graphData)}};
        
        // Initialize the network
        const container = document.getElementById('mynetwork');
        const data = {{
            nodes: new vis.DataSet(graphData.nodes),
            edges: new vis.DataSet(graphData.edges)
        }};
        
        const options = {{
            physics: {{
                enabled: true,
                solver: "forceAtlas2Based",
                forceAtlas2Based: {{
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.08,
                    damping: 0.09,
                    avoidOverlap: 0.5
                }},
                stabilization: {{
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 25
                }}
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: true,
                navigationButtons: true,
                keyboard: true
            }},
            nodes: {{
                borderWidth: 2,
                borderWidthSelected: 4,
                font: {{
                    face: "Inter, sans-serif",
                    size: 14,
                    strokeWidth: 0,
                    color: "#000000"
                }}
            }},
            edges: {{
                smooth: {{
                    type: "continuous",
                    forceDirection: "none"
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.5
                    }}
                }},
                font: {{
                    face: "Inter, sans-serif",
                    size: 10,
                    strokeWidth: 0,
                    color: "#666666"
                }}
            }}
        }};
        
        const network = new vis.Network(container, data, options);
    <\\/script>
</body>
</html>`;
        }}
        
        // Close modal when clicking outside
        window.onclick = function(event) {{
            if (event.target.classList.contains('modal')) {{
                event.target.style.display = 'none';
            }}
            if (event.target.classList.contains('share-modal')) {{
                event.target.style.display = 'none';
            }}
        }}
    </script>
</body>
</html>
"""
        return html
    
    def _create_graph_html(self, risk_scores: Dict[str, Any], highlight_nodes: Optional[Set[str]]) -> str:
        """Create the graph visualization HTML using pyvis"""
        # Create pyvis network
        net = Network(
            height="100%",
            width="100%",
            directed=True,
            notebook=False,
            bgcolor="#222222",
            font_color="white"
        )
        
        # Configure physics for better visualization
        net.set_options("""
        {
            "physics": {
                "enabled": true,
                "solver": "forceAtlas2Based",
                "forceAtlas2Based": {
                    "gravitationalConstant": -50,
                    "centralGravity": 0.01,
                    "springLength": 100,
                    "springConstant": 0.08,
                    "damping": 0.09,
                    "avoidOverlap": 0.5
                },
                "stabilization": {
                    "enabled": true,
                    "iterations": 1000,
                    "updateInterval": 25
                }
            },
            "interaction": {
                "hover": true,
                "tooltipDelay": 200,
                "hideEdgesOnDrag": true,
                "navigationButtons": true,
                "keyboard": true,
                "navigationButtons": true,
                "keyboard": true
            },
            "configure": {
                "enabled": false
            },
            "manipulation": {
                "enabled": false
            },
            "nodes": {
                "borderWidth": 2,
                "borderWidthSelected": 4,
                "font": {
                    "face": "Inter, sans-serif",
                    "size": 14,
                    "strokeWidth": 0,
                    "color": "#ffffff"
                }
            },
            "edges": {
                "smooth": {
                    "type": "continuous",
                    "forceDirection": "none"
                },
                "arrows": {
                    "to": {
                        "enabled": true,
                        "scaleFactor": 0.5
                    }
                },
                "font": {
                    "face": "Inter, sans-serif",
                    "size": 10,
                    "strokeWidth": 0,
                    "color": "#cccccc"
                }
            }
        }
        """)
        
        # Add nodes
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get('type', 'unknown')
            
            # Determine color based on risk
            if highlight_nodes and node_id in highlight_nodes:
                color = "#FFD700"  # Gold for highlighted nodes
            elif risk_scores and node_id in risk_scores:
                risk = risk_scores[node_id].get('total', 0) if isinstance(risk_scores[node_id], dict) else risk_scores[node_id]
                if risk > 0.8:
                    color = "#d32f2f"  # Critical
                elif risk > 0.6:
                    color = "#f44336"  # High
                elif risk > 0.4:
                    color = "#ff9800"  # Medium
                else:
                    color = self.config.visualization_html_node_colors.get(node_type, '#999999')
            else:
                color = self.config.visualization_html_node_colors.get(node_type, '#999999')
            
            # Create label
            label = node_data.get('name', node_id)
            if node_type == 'service_account':
                # Shorten service account emails
                label = label.split('@')[0] if '@' in label else label
            elif node_type == 'role':
                # Shorten role names
                label = label.replace('roles/', '')
            
            # Determine shape based on node type
            shape_map = {
                'user': 'dot',
                'service_account': 'square',
                'group': 'triangle',
                'project': 'box',
                'folder': 'box',
                'organization': 'star',
                'role': 'diamond',
                'resource': 'dot'
            }
            shape = shape_map.get(node_type, 'dot')
            
            # Add node with explicit font configuration
            net.add_node(
                node_id,
                label=label,
                title=self._create_node_tooltip(node_id, node_data, risk_scores),
                color=color,
                size=25 if (highlight_nodes and node_id in highlight_nodes) else 20,
                shape=shape,
                font={'face': 'Inter, sans-serif', 'size': 14, 'color': '#ffffff', 'strokeWidth': 0}
            )
        
        # Add edges
        for u, v, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get('type', 'unknown')
            color = self.config.visualization_html_edge_colors.get(edge_type, '#999999')
            
            # Make dangerous edges more visible
            width = 2 if edge_type in ['can_impersonate', 'can_impersonate_sa', 'can_create_service_account_key'] else 1
            
            net.add_edge(
                u,
                v,
                title=self._create_edge_tooltip(edge_data),
                color=color,
                width=width,
                arrows='to'
            )
        
        # Generate HTML and save to temporary file
        import tempfile
        import os
        
        # Create a temporary file
        temp_fd, temp_path = tempfile.mkstemp(suffix='.html')
        try:
            # Generate the HTML
            net.save_graph(temp_path)
            
            # Read the generated HTML
            with open(temp_path, 'r') as f:
                full_html = f.read()
            
            # Extract the necessary parts
            # Find the vis.js library includes
            lib_start = full_html.find('<script')
            lib_end = full_html.find('</script>')
            while lib_end != -1 and 'vis-network.min.js' not in full_html[lib_start:lib_end]:
                lib_start = full_html.find('<script', lib_end)
                lib_end = full_html.find('</script>', lib_start)
            
            # Get all script tags for vis.js
            scripts = []
            script_start = full_html.find('<script')
            while script_start != -1:
                script_end = full_html.find('</script>', script_start) + 9
                script_content = full_html[script_start:script_end]
                if 'vis-network.min' in script_content or 'nodes = new vis.DataSet' in script_content:
                    scripts.append(script_content)
                script_start = full_html.find('<script', script_end)
            
            # Create the embedded HTML
            embedded_html = f"""
            <div id="mynetwork" style="width: 100%; height: 100%; background-color: #222222;"></div>
            {' '.join(scripts)}
            """
            
            return embedded_html
            
        finally:
            # Clean up the temporary file
            os.close(temp_fd)
            os.unlink(temp_path)
    
    def _create_node_tooltip(self, node_id: str, node_data: Dict[str, Any], risk_scores: Dict[str, Any]) -> str:
        """Create tooltip text for a node"""
        lines = [
            f"ID: {node_id}",
            f"Type: {node_data.get('type', 'unknown')}",
            f"Name: {node_data.get('name', node_id)}"
        ]
        
        # Add risk score if available
        if risk_scores and node_id in risk_scores:
            risk = risk_scores[node_id].get('total', 0) if isinstance(risk_scores[node_id], dict) else risk_scores[node_id]
            lines.append(f"Risk Score: {risk:.2f}")
        
        # Add additional properties
        important_props = ['email', 'projectId', 'hasOwnerRole', 'hasTokenCreatorRole', 'permissions']
        for key, value in node_data.items():
            if key in important_props and key not in ['type', 'name', 'id']:
                # Convert value to string and truncate if too long
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                lines.append(f"{key}: {str_value}")
        
        # Return plain text with newlines
        return "\n".join(lines)
    
    def _create_edge_tooltip(self, edge_data: Dict[str, Any]) -> str:
        """Create tooltip text for an edge"""
        edge_type = edge_data.get('type', 'unknown')
        lines = [
            f"Type: {edge_type}"
        ]
        
        # Add explanation for dangerous edge types
        if edge_type == 'can_impersonate':
            lines.append("Risk: Can generate access tokens")
        elif edge_type == 'can_create_service_account_key':
            lines.append("Risk: Can create long-lived keys")
        elif edge_type == 'can_impersonate_sa':
            lines.append("Risk: Can impersonate service account")
        elif edge_type == 'can_deploy_cloud_run_as':
            lines.append("Risk: Can deploy code as service account")
        elif edge_type == 'can_deploy_function_as':
            lines.append("Risk: Can deploy function as service account")
        
        # Add additional properties
        for key, value in edge_data.items():
            if key not in ['type'] and value:
                # Convert value to string and truncate if too long
                str_value = str(value)
                if len(str_value) > 100:
                    str_value = str_value[:97] + "..."
                lines.append(f"{key}: {str_value}")
        
        # Return plain text with newlines
        return "\n".join(lines)
    
    def _analyze_dangerous_roles(self) -> Dict[str, List[str]]:
        """Analyze which identities have dangerous roles"""
        dangerous_assignments = defaultdict(list)
        
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'role':
                role_name = node_data.get('name', '')
                if role_name in self.DANGEROUS_ROLES:
                    # Find who has this role
                    for predecessor in self.graph.predecessors(node_id):
                        pred_data = self.graph.nodes[predecessor]
                        if pred_data.get('type') in ['user', 'service_account', 'group']:
                            dangerous_assignments[role_name].append(predecessor)
        
        return dangerous_assignments
    
    def _calculate_statistics(self, risk_scores: Dict[str, Any], attack_paths: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate dashboard statistics"""
        high_risk_count = 0
        if risk_scores:
            for node_id, score in risk_scores.items():
                risk = score.get('total', 0) if isinstance(score, dict) else score
                if risk > 0.6:
                    high_risk_count += 1
        
        dangerous_roles_count = 0
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('type') == 'role' and node_data.get('name') in self.DANGEROUS_ROLES:
                # Check if anyone has this role
                if any(self.graph.predecessors(node_id)):
                    dangerous_roles_count += 1
        
        return {
            'total_nodes': self.graph.number_of_nodes(),
            'total_edges': self.graph.number_of_edges(),
            'attack_paths': len(attack_paths) if attack_paths else 0,
            'high_risk_nodes': high_risk_count,
            'dangerous_roles': dangerous_roles_count
        }
    
    def _get_nodes_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get nodes grouped by type"""
        nodes_by_type = defaultdict(list)
        
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get('type', 'unknown')
            nodes_by_type[node_type].append({
                'id': node_id,
                'name': node_data.get('name', node_id),
                'data': node_data
            })
        
        return dict(nodes_by_type)
    
    def _get_edges_by_type(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get edges grouped by type"""
        edges_by_type = defaultdict(list)
        
        for u, v, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get('type', 'unknown')
            edges_by_type[edge_type].append({
                'source': u,
                'target': v,
                'data': edge_data
            })
        
        return dict(edges_by_type)
    
    def _create_nodes_list_html(self, nodes_by_type: Dict[str, List[Dict[str, Any]]]) -> str:
        """Create HTML for nodes list in modal"""
        html = ""
        for node_type, nodes in nodes_by_type.items():
            for node in nodes[:100]:  # Limit to first 100 per type
                html += f"""
                <li class="modal-list-item">
                    {node['name']}
                    <span class="node-type-badge">{node_type}</span>
                </li>
                """
        return html
    
    def _create_edges_list_html(self, edges_by_type: Dict[str, List[Dict[str, Any]]]) -> str:
        """Create HTML for edges list in modal"""
        html = ""
        for edge_type, edges in edges_by_type.items():
            for edge in edges[:100]:  # Limit to first 100 per type
                html += f"""
                <li class="modal-list-item">
                    {edge['source']} → {edge['target']}
                    <span class="edge-type-badge">{edge_type}</span>
                </li>
                """
        return html
    
    def _create_high_risk_nodes_html(self, risk_scores: Dict[str, Any]) -> str:
        """Create HTML for high risk nodes list"""
        html = ""
        high_risk_nodes = []
        
        if risk_scores:
            for node_id, score in risk_scores.items():
                risk = score.get('total', 0) if isinstance(score, dict) else score
                if risk > 0.6:
                    node_data = self.graph.nodes.get(node_id, {})
                    high_risk_nodes.append({
                        'id': node_id,
                        'name': node_data.get('name', node_id),
                        'type': node_data.get('type', 'unknown'),
                        'risk': risk
                    })
        
        # Sort by risk score
        high_risk_nodes.sort(key=lambda x: x['risk'], reverse=True)
        
        for node in high_risk_nodes[:50]:  # Limit to top 50
            risk_class = 'risk-critical' if node['risk'] > 0.8 else 'risk-high'
            html += f"""
            <li class="modal-list-item">
                {node['name']}
                <span class="node-type-badge">{node['type']}</span>
                <span class="path-risk {risk_class}">Risk: {node['risk']:.2f}</span>
            </li>
            """
        
        return html
    
    def _create_attack_explanations_html(self) -> str:
        """Create HTML for attack path explanations"""
        html = ""
        for key, info in self.ATTACK_PATH_EXPLANATIONS.items():
            html += f"""
            <div class="attack-path-item">
                <div class="attack-path-title">{info['title']}</div>
                <div class="attack-path-description">{info['description']}</div>
                <div class="attack-path-exploitation">
                    <strong>Exploitation:</strong><br>
                    {info['exploitation']}
                </div>
                <div class="attack-path-prevention">
                    <strong>Prevention:</strong> {info['prevention']}
                </div>
            </div>
            """
        return html
    
    def _create_dangerous_roles_html(self, dangerous_roles_info: Dict[str, List[str]], show_all: bool = False) -> str:
        """Create HTML for dangerous roles information"""
        html = ""
        limit = None if show_all else 10
        
        for role, holders in list(dangerous_roles_info.items())[:limit]:
            if holders:  # Only show roles that are actually assigned
                description = self.DANGEROUS_ROLES.get(role, "Privileged role")
                holders_str = ", ".join(holders[:5])  # Show first 5
                if len(holders) > 5:
                    holders_str += f" and {len(holders) - 5} more"
                
                html += f"""
                <div class="dangerous-role-item">
                    <div class="role-name">{role}</div>
                    <div class="role-description">{description}</div>
                    <div class="role-holders">Assigned to: {holders_str}</div>
                </div>
                """
        
        if not html:
            html = "<p>No dangerous roles detected in the current graph.</p>"
        
        return html
    
    def _create_found_paths_html(self, attack_paths: List[Dict[str, Any]], show_all: bool = False) -> str:
        """Create HTML for found attack paths"""
        if not attack_paths:
            return "<p>No attack paths found. Run analysis to detect paths.</p>"
        
        html = ""
        # Group by category
        by_category = defaultdict(list)
        for path in attack_paths:
            category = path.get('category', 'other') if isinstance(path, dict) else 'other'
            by_category[category].append(path)
        
        for category, paths in by_category.items():
            html += f'<div class="legend-title">{category.replace("_", " ").title()}</div>'
            limit = len(paths) if show_all else 10
            for path in paths[:limit]:
                if isinstance(path, dict):
                    risk = path.get('risk_score', 0)
                    path_str = path.get('path', 'Unknown path')
                else:
                    risk = path.risk_score if hasattr(path, 'risk_score') else 0
                    path_str = path.get_path_string() if hasattr(path, 'get_path_string') else str(path)
                
                risk_class = 'risk-critical' if risk > 0.8 else 'risk-high' if risk > 0.6 else 'risk-medium' if risk > 0.4 else 'risk-low'
                
                html += f"""
                <div class="path-list-item">
                    {path_str}
                    <span class="path-risk {risk_class}">Risk: {risk:.2f}</span>
                </div>
                """
        
        return html
    
    def _get_standalone_template(self) -> str:
        """Get the JavaScript template for generating standalone reports"""
        # This returns a template string that will be evaluated in the browser
        # It uses template literals with ${} for JavaScript variable interpolation
        return '''<!DOCTYPE html>
<html>
<head>
    <title>GCPHound Security Report - Standalone</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
            background-color: #f8f9fa;
            color: #1a1f36;
        }
        
        .standalone-header {
            background-color: #ffffff;
            padding: 20px;
            border-bottom: 1px solid #e5e7eb;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }
        
        .standalone-title {
            margin: 0 0 10px 0;
            color: #6b46c1;
            font-size: 28px;
            font-weight: 600;
        }
        
        .standalone-subtitle {
            color: #6b7280;
            font-size: 14px;
        }
        
        .standalone-stats {
            display: flex;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .stat-box {
            background-color: #f9fafb;
            padding: 15px 25px;
            border-radius: 8px;
            border: 1px solid #e5e7eb;
        }
        
        .stat-value {
            font-size: 24px;
            font-weight: 600;
            color: #6b46c1;
        }
        
        .stat-label {
            font-size: 12px;
            color: #6b7280;
            margin-top: 5px;
        }
        
        .content-section {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .section-title {
            font-size: 20px;
            font-weight: 600;
            color: #6b46c1;
            margin: 30px 0 15px 0;
        }
        
        .graph-container {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
            height: 600px;
            position: relative;
        }
        
        #mynetwork {
            width: 100%;
            height: 100%;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }
        
        .info-card {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 20px;
        }
        
        .info-card-title {
            font-size: 16px;
            font-weight: 600;
            color: #6b46c1;
            margin-bottom: 15px;
        }
        
        .risk-item {
            background-color: #fef2f2;
            border-left: 4px solid #dc2626;
            padding: 10px;
            margin-bottom: 10px;
            border-radius: 4px;
        }
        
        .risk-high { border-left-color: #dc2626; background-color: #fef2f2; }
        .risk-medium { border-left-color: #f59e0b; background-color: #fef3c7; }
        .risk-low { border-left-color: #22c55e; background-color: #f0fdf4; }
        
        .footer {
            background-color: #f9fafb;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 12px;
            margin-top: 50px;
            border-top: 1px solid #e5e7eb;
        }
    </style>
</head>
<body>
    <div class="standalone-header">
        <h1 class="standalone-title">GCPHound Security Report</h1>
        <p class="standalone-subtitle">Generated on ${new Date().toLocaleString()} | Standalone Report</p>
        
        <div class="standalone-stats">
            <div class="stat-box">
                <div class="stat-value">${stats.total_nodes}</div>
                <div class="stat-label">Total Nodes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${stats.total_edges}</div>
                <div class="stat-label">Total Edges</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${stats.attack_paths}</div>
                <div class="stat-label">Attack Paths</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${stats.high_risk_nodes}</div>
                <div class="stat-label">High Risk Nodes</div>
            </div>
            <div class="stat-box">
                <div class="stat-value">${stats.dangerous_roles}</div>
                <div class="stat-label">Dangerous Roles</div>
            </div>
        </div>
    </div>
    
    <div class="content-section">
        <h2 class="section-title">Interactive Graph Visualization</h2>
        <div class="graph-container">
            <div id="mynetwork"></div>
        </div>
        
        <h2 class="section-title">Key Findings</h2>
        <div class="info-grid">
            <div class="info-card">
                <h3 class="info-card-title">Critical Attack Paths</h3>
                ${attackPaths.filter(p => p.risk_score > 0.8).slice(0, 5).map(path => 
                    `<div class="risk-item risk-high">
                        <strong>${path.path}</strong><br>
                        Risk Score: ${path.risk_score.toFixed(2)}
                    </div>`
                ).join('')}
            </div>
            
            <div class="info-card">
                <h3 class="info-card-title">Dangerous Role Assignments</h3>
                ${Object.entries(dangerousRolesInfo).slice(0, 5).map(([role, holders]) => 
                    `<div class="risk-item risk-medium">
                        <strong>${role}</strong><br>
                        Assigned to: ${holders.length} identities
                    </div>`
                ).join('')}
            </div>
            
            <div class="info-card">
                <h3 class="info-card-title">Resource Summary</h3>
                ${Object.entries(nodesByType).map(([type, nodes]) => 
                    `<div style="margin-bottom: 8px;">
                        <strong>${type}:</strong> ${nodes.length}
                    </div>`
                ).join('')}
            </div>
        </div>
    </div>
    
    <div class="footer">
        <p>This is a standalone GCPHound report. All data is embedded in this HTML file.</p>
        <p>No external dependencies or internet connection required.</p>
    </div>
    
    <script>
        // Initialize the network
        const container = document.getElementById('mynetwork');
        const data = {
            nodes: new vis.DataSet(graphData.nodes),
            edges: new vis.DataSet(graphData.edges)
        };
        
        const options = {
            physics: {
                enabled: true,
                solver: "forceAtlas2Based",
                forceAtlas2Based: {
                    gravitationalConstant: -50,
                    centralGravity: 0.01,
                    springLength: 100,
                    springConstant: 0.08,
                    damping: 0.09,
                    avoidOverlap: 0.5
                },
                stabilization: {
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 25
                }
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: true,
                navigationButtons: true,
                keyboard: true
            },
            nodes: {
                borderWidth: 2,
                borderWidthSelected: 4,
                font: {
                    face: "Inter, sans-serif",
                    size: 14,
                    strokeWidth: 0,
                    color: "#ffffff"
                }
            },
            edges: {
                smooth: {
                    type: "continuous",
                    forceDirection: "none"
                },
                arrows: {
                    to: {
                        enabled: true,
                        scaleFactor: 0.5
                    }
                },
                font: {
                    face: "Inter, sans-serif",
                    size: 10,
                    strokeWidth: 0,
                    color: "#cccccc"
                }
            }
        };
        
        const network = new vis.Network(container, data, options);
    </script>
</body>
</html>'''
    
    def create_standalone_report(
        self,
        output_file: str,
        risk_scores: Optional[Dict[str, Any]] = None,
        attack_paths: Optional[List[Dict[str, Any]]] = None,
        highlight_nodes: Optional[Set[str]] = None
    ):
        """
        Create a completely self-contained HTML report that can be shared
        
        This generates a single HTML file with all dependencies embedded,
        including the graph data, styles, and visualization libraries.
        No external dependencies or internet connection required.
        
        Args:
            output_file: Output HTML file path
            risk_scores: Optional risk scores for coloring
            attack_paths: Optional list of attack paths found
            highlight_nodes: Optional set of critical nodes to highlight
        """
        logger.info(f"Creating standalone HTML report: {output_file}")
        
        # Analyze the graph if not provided
        if not attack_paths and not risk_scores:
            analyzer = PathAnalyzer(self.graph, self.config)
            analysis_results = analyzer.analyze_all_paths()
            risk_scores = analysis_results.get('risk_scores', {})
            
            # Convert attack paths to simple format
            attack_paths = []
            for category, paths in analysis_results.get('attack_paths', {}).items():
                for path in paths:
                    attack_paths.append({
                        'category': category,
                        'path': path.get_path_string() if hasattr(path, 'get_path_string') else str(path),
                        'risk_score': path.risk_score if hasattr(path, 'risk_score') else 0,
                        'length': len(path) if hasattr(path, '__len__') else 0
                    })
        
        # Serialize the graph data
        graph_data = self._serialize_graph_for_standalone(risk_scores, highlight_nodes)
        
        # Get all the analysis data
        dangerous_roles_info = self._analyze_dangerous_roles()
        stats = self._calculate_statistics(risk_scores, attack_paths)
        nodes_by_type = self._get_nodes_by_type()
        edges_by_type = self._get_edges_by_type()
        
        # Create the standalone HTML
        html_content = self._create_standalone_html(
            graph_data,
            risk_scores,
            attack_paths,
            highlight_nodes,
            dangerous_roles_info,
            stats,
            nodes_by_type,
            edges_by_type
        )
        
        # Save to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Get file size for logging
        import os
        file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
        logger.info(f"Created standalone report: {output_file} ({file_size:.2f} MB)")
    
    def _serialize_graph_for_standalone(self, risk_scores: Dict[str, Any], highlight_nodes: Optional[Set[str]]) -> Dict[str, Any]:
        """Serialize the graph data for embedding in HTML"""
        nodes = []
        edges = []
        
        # Serialize nodes
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get('type', 'unknown')
            
            # Determine color based on risk
            if highlight_nodes and node_id in highlight_nodes:
                color = "#FFD700"  # Gold for highlighted nodes
            elif risk_scores and node_id in risk_scores:
                risk = risk_scores[node_id].get('total', 0) if isinstance(risk_scores[node_id], dict) else risk_scores[node_id]
                if risk > 0.8:
                    color = "#d32f2f"  # Critical
                elif risk > 0.6:
                    color = "#f44336"  # High
                elif risk > 0.4:
                    color = "#ff9800"  # Medium
                else:
                    color = self.config.visualization_html_node_colors.get(node_type, '#999999')
            else:
                color = self.config.visualization_html_node_colors.get(node_type, '#999999')
            
            # Create label
            label = node_data.get('name', node_id)
            if node_type == 'service_account':
                label = label.split('@')[0] if '@' in label else label
            elif node_type == 'role':
                label = label.replace('roles/', '')
            
            # Determine shape
            shape_map = {
                'user': 'dot',
                'service_account': 'square',
                'group': 'triangle',
                'project': 'box',
                'folder': 'box',
                'organization': 'star',
                'role': 'diamond',
                'resource': 'dot'
            }
            shape = shape_map.get(node_type, 'dot')
            
            nodes.append({
                'id': node_id,
                'label': label,
                'title': self._create_node_tooltip(node_id, node_data, risk_scores),
                'color': color,
                'shape': shape,
                'size': 25 if (highlight_nodes and node_id in highlight_nodes) else 20,
                'font': {
                    'face': 'Inter, sans-serif',
                    'size': 14,
                    'color': '#000000',
                    'strokeWidth': 0
                }
            })
        
        # Serialize edges
        for u, v, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get('type', 'unknown')
            color = self.config.visualization_html_edge_colors.get(edge_type, '#999999')
            
            width = 2 if edge_type in ['can_impersonate', 'can_impersonate_sa', 'can_create_service_account_key'] else 1
            
            edges.append({
                'from': u,
                'to': v,
                'title': self._create_edge_tooltip(edge_data),
                'color': color,
                'width': width,
                'arrows': 'to'
            })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def _create_standalone_html(
        self,
        graph_data: Dict[str, Any],
        risk_scores: Dict[str, Any],
        attack_paths: List[Dict[str, Any]],
        highlight_nodes: Optional[Set[str]],
        dangerous_roles_info: Dict[str, List[str]],
        stats: Dict[str, int],
        nodes_by_type: Dict[str, List[Dict[str, Any]]],
        edges_by_type: Dict[str, List[Dict[str, Any]]]
    ) -> str:
        """Create a simple table-based HTML report that works everywhere"""
        
        # Create a simple, self-contained HTML report using only tables
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>GCPHound Security Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Inter', Roboto, sans-serif;
            background-color: #f8f9fa;
            color: #1a1f36;
            line-height: 1.6;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        h1, h2, h3 {{
            color: #6b46c1;
        }}
        
        h1 {{
            font-size: 32px;
            margin-bottom: 10px;
        }}
        
        h2 {{
            font-size: 24px;
            margin-top: 40px;
            margin-bottom: 20px;
            border-bottom: 2px solid #e5e7eb;
            padding-bottom: 10px;
        }}
        
        h3 {{
            font-size: 18px;
            margin-top: 20px;
            margin-bottom: 10px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        
        th {{
            background-color: #6b46c1;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        td {{
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        tr:last-child td {{
            border-bottom: none;
        }}
        
        tr:hover {{
            background-color: #f3f4f6;
        }}
        
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        
        .summary-card {{
            background-color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}
        
        .summary-value {{
            font-size: 36px;
            font-weight: 700;
            color: #6b46c1;
            margin-bottom: 5px;
        }}
        
        .summary-label {{
            font-size: 14px;
            color: #6b7280;
        }}
        
        .risk-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .risk-critical {{
            background-color: #fef2f2;
            color: #dc2626;
        }}
        
        .risk-high {{
            background-color: #fef3c7;
            color: #f59e0b;
        }}
        
        .risk-medium {{
            background-color: #fef3c7;
            color: #f59e0b;
        }}
        
        .risk-low {{
            background-color: #f0fdf4;
            color: #22c55e;
        }}
        
        .node-type {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            background-color: #e5e7eb;
            color: #4b5563;
        }}
        
        .footer {{
            margin-top: 60px;
            padding: 20px;
            text-align: center;
            color: #6b7280;
            font-size: 14px;
            border-top: 1px solid #e5e7eb;
        }}
        
        @media print {{
            body {{
                background-color: white;
            }}
            
            .summary-card {{
                box-shadow: none;
                border: 1px solid #e5e7eb;
            }}
            
            table {{
                box-shadow: none;
                border: 1px solid #e5e7eb;
            }}
        }}
        
        @media (max-width: 768px) {{
            .summary-grid {{
                grid-template-columns: 1fr;
            }}
            
            table {{
                font-size: 14px;
            }}
            
            th, td {{
                padding: 8px;
            }}
        }}
        
        .simple-report {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
            color: #1a1f36;
        }}
        
        .simple-report h1, .simple-report h2, .simple-report h3 {{
            color: #6b46c1;
        }}
        
        .simple-report table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }}
        
        .simple-report th {{
            background-color: #6b46c1;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        
        .simple-report td {{
            padding: 10px;
            border-bottom: 1px solid #e5e7eb;
        }}
        
        .simple-report tr:hover {{
            background-color: #f3f4f6;
        }}
        
        .risk-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        
        .risk-critical {{ background-color: #fef2f2; color: #dc2626; }}
        .risk-high {{ background-color: #fef3c7; color: #f59e0b; }}
        .risk-medium {{ background-color: #fef3c7; color: #f59e0b; }}
        .risk-low {{ background-color: #f0fdf4; color: #22c55e; }}
        
        .path-list-item {{
            background-color: #3d3d3d;
            border-radius: 5px;
            padding: 10px;
            margin-bottom: 8px;
            font-size: 13px;
        }}
        
        .path-risk {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 600;
            margin-left: 10px;
        }}
        
        .risk-critical {{ background-color: #d32f2f; color: white; }}
        .risk-high {{ background-color: #f44336; color: white; }}
        .risk-medium {{ background-color: #ff9800; color: white; }}
        .risk-low {{ background-color: #ffc107; color: black; }}
        
        .hidden {{ display: none; }}
        
        /* Modal styles */
        .modal {{
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0,0,0,0.8);
        }}
        
        .modal-content {{
            background-color: #2d2d2d;
            margin: 5% auto;
            padding: 20px;
            border: 1px solid #444;
            border-radius: 8px;
            width: 80%;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
        }}
        
        .modal-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }}
        
        .modal-title {{
            font-size: 20px;
            color: #4285f4;
            font-weight: 600;
        }}
        
        .close {{
            color: #aaa;
            font-size: 28px;
            font-weight: bold;
            cursor: pointer;
        }}
        
        .close:hover {{
            color: #fff;
        }}
        
        .modal-list {{
            list-style: none;
            padding: 0;
        }}
        
        .modal-list-item {{
            background-color: #3d3d3d;
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 5px;
            font-size: 14px;
        }}
        
        .modal-list-item:hover {{
            background-color: #4d4d4d;
        }}
        
        .node-type-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 10px;
            background-color: #555;
            color: white;
            font-weight: 500;
        }}
        
        .edge-type-badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            margin-left: 10px;
            background-color: #666;
            color: white;
            font-weight: 500;
        }}
        
        /* Collapsible sections */
        .collapsible {{
            background-color: #3d3d3d;
            color: white;
            cursor: pointer;
            padding: 12px;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 15px;
            font-weight: 500;
            margin-bottom: 5px;
            border-radius: 5px;
            transition: 0.3s;
        }}
        
        .collapsible:hover {{
            background-color: #4d4d4d;
        }}
        
        .collapsible.active {{
            background-color: #4285f4;
        }}
        
        .collapsible-content {{
            padding: 0 18px;
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
            background-color: #2d2d2d;
            border-radius: 0 0 5px 5px;
        }}
        
        .collapsible-content.show {{
            max-height: 500px;
            padding: 18px;
            overflow-y: auto;
        }}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
            height: 8px;
        }}
        
        ::-webkit-scrollbar-track {{
            background: #1a1a1a;
        }}
        
        ::-webkit-scrollbar-thumb {{
            background: #555;
            border-radius: 4px;
        }}
        
        ::-webkit-scrollbar-thumb:hover {{
            background: #666;
        }}
        
        /* Standalone notice */
        .standalone-notice {{
            position: absolute;
            bottom: 10px;
            right: 10px;
            background-color: #4285f4;
            color: white;
            padding: 5px 10px;
            border-radius: 3px;
            font-size: 11px;
            opacity: 0.8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>GCPHound Security Report</h1>
        <p style="color: #6b7280;">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="summary-grid">
            <div class="summary-card">
                <div class="summary-value">{stats['total_nodes']}</div>
                <div class="summary-label">Total Nodes</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{stats['total_edges']}</div>
                <div class="summary-label">Total Edges</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{stats['attack_paths']}</div>
                <div class="summary-label">Attack Paths</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{stats['high_risk_nodes']}</div>
                <div class="summary-label">High Risk Nodes</div>
            </div>
            <div class="summary-card">
                <div class="summary-value">{stats['dangerous_roles']}</div>
                <div class="summary-label">Dangerous Roles</div>
            </div>
        </div>
        
        <div class="sidebar">
            <div class="sidebar-tabs">
                <button class="tab active" onclick="showTab('legend')">Legend</button>
                <button class="tab" onclick="showTab('attacks')">Attack Paths</button>
                <button class="tab" onclick="showTab('roles')">Dangerous Roles</button>
                <button class="tab" onclick="showTab('paths')">Found Paths</button>
            </div>
            
            <div class="sidebar-content">
                <!-- Legend Tab -->
                <div id="legend-tab" class="tab-content">
                    <button class="collapsible active" onclick="toggleCollapsible(this)">Node Types</button>
                    <div class="collapsible-content show">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #4285F4;"></div>
                            <span>User Account</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #34A853;"></div>
                            <span>Service Account</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #FBBC04;"></div>
                            <span>Group</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #EA4335;"></div>
                            <span>Project</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #FF6D00;"></div>
                            <span>Folder</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #9C27B0;"></div>
                            <span>Organization</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #757575;"></div>
                            <span>Role</span>
                        </div>
                    </div>
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Edge Types</button>
                    <div class="collapsible-content">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #757575;"></div>
                            <span>Has Role</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #F44336;"></div>
                            <span>Can Impersonate</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #FF5722;"></div>
                            <span>Can Admin</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #9E9E9E;"></div>
                            <span>Member Of</span>
                        </div>
                    </div>
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Risk Levels</button>
                    <div class="collapsible-content">
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #d32f2f;"></div>
                            <span>Critical Risk (>0.8)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #f44336;"></div>
                            <span>High Risk (>0.6)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #ff9800;"></div>
                            <span>Medium Risk (>0.4)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-color" style="background-color: #ffc107;"></div>
                            <span>Low Risk (>0.2)</span>
                        </div>
                    </div>
                </div>
                
                <!-- Attack Paths Tab -->
                <div id="attacks-tab" class="tab-content hidden">
                    {self._create_attack_explanations_html()}
                </div>
                
                <!-- Dangerous Roles Tab -->
                <div id="roles-tab" class="tab-content hidden">
                    {self._create_dangerous_roles_html(dangerous_roles_info)}
                </div>
                
                <!-- Found Paths Tab -->
                <div id="paths-tab" class="tab-content hidden">
                    {self._create_found_paths_html(attack_paths)}
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modals -->
    <div id="nodesModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">All Nodes</h2>
                <span class="close" onclick="closeModal('nodes')">&times;</span>
            </div>
            <ul class="modal-list">
                {self._create_nodes_list_html(nodes_by_type)}
            </ul>
        </div>
    </div>
    
    <div id="edgesModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">All Edges</h2>
                <span class="close" onclick="closeModal('edges')">&times;</span>
            </div>
            <ul class="modal-list">
                {self._create_edges_list_html(edges_by_type)}
            </ul>
        </div>
    </div>
    
    <div id="pathsModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">All Attack Paths</h2>
                <span class="close" onclick="closeModal('paths')">&times;</span>
            </div>
            <div>
                {self._create_found_paths_html(attack_paths, show_all=True)}
            </div>
        </div>
    </div>
    
    <div id="highriskModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">High Risk Nodes</h2>
                <span class="close" onclick="closeModal('highrisk')">&times;</span>
            </div>
            <ul class="modal-list">
                {self._create_high_risk_nodes_html(risk_scores)}
            </ul>
        </div>
    </div>
    
    <div id="dangerousModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h2 class="modal-title">Dangerous Role Assignments</h2>
                <span class="close" onclick="closeModal('dangerous')">&times;</span>
            </div>
            <div>
                {self._create_dangerous_roles_html(dangerous_roles_info, show_all=True)}
            </div>
        </div>
    </div>
    
    <!-- Embedded vis.js network library (minimal version) -->
    <script>
        // Embedded graph data
        const graphData = {json.dumps(graph_data)};
        
        // Simple network visualization implementation
        class SimpleNetwork {{
            constructor(container, data, options) {{
                this.container = container;
                this.nodes = data.nodes;
                this.edges = data.edges;
                this.canvas = document.createElement('canvas');
                this.ctx = this.canvas.getContext('2d');
                this.container.appendChild(this.canvas);
                
                this.positions = {{}};
                this.dragging = null;
                this.zoom = 1;
                this.offsetX = 0;
                this.offsetY = 0;
                
                this.init();
            }}
            
            init() {{
                this.resize();
                this.layoutNodes();
                this.setupEvents();
                this.render();
                
                window.addEventListener('resize', () => {{
                    this.resize();
                    this.render();
                }});
            }}
            
            resize() {{
                this.canvas.width = this.container.clientWidth;
                this.canvas.height = this.container.clientHeight;
            }}
            
            layoutNodes() {{
                const centerX = this.canvas.width / 2;
                const centerY = this.canvas.height / 2;
                const radius = Math.min(centerX, centerY) * 0.8;
                
                // Simple circular layout
                this.nodes.forEach((node, i) => {{
                    const angle = (i / this.nodes.length) * 2 * Math.PI;
                    this.positions[node.id] = {{
                        x: centerX + radius * Math.cos(angle),
                        y: centerY + radius * Math.sin(angle)
                    }};
                }});
                
                // Apply force-directed adjustments
                for (let iter = 0; iter < 50; iter++) {{
                    this.applyForces();
                }}
            }}
            
            applyForces() {{
                const k = 100; // Spring constant
                const c = 10000; // Repulsion constant
                
                // Calculate forces
                const forces = {{}};
                this.nodes.forEach(node => {{
                    forces[node.id] = {{ x: 0, y: 0 }};
                }});
                
                // Repulsion between nodes
                for (let i = 0; i < this.nodes.length; i++) {{
                    for (let j = i + 1; j < this.nodes.length; j++) {{
                        const n1 = this.nodes[i];
                        const n2 = this.nodes[j];
                        const p1 = this.positions[n1.id];
                        const p2 = this.positions[n2.id];
                        
                        const dx = p2.x - p1.x;
                        const dy = p2.y - p1.y;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        
                        if (dist > 0) {{
                            const force = c / (dist * dist);
                            const fx = (dx / dist) * force;
                            const fy = (dy / dist) * force;
                            
                            forces[n1.id].x -= fx;
                            forces[n1.id].y -= fy;
                            forces[n2.id].x += fx;
                            forces[n2.id].y += fy;
                        }}
                    }}
                }}
                
                // Attraction along edges
                this.edges.forEach(edge => {{
                    const p1 = this.positions[edge.from];
                    const p2 = this.positions[edge.to];
                    
                    if (p1 && p2) {{
                        const dx = p2.x - p1.x;
                        const dy = p2.y - p1.y;
                        const dist = Math.sqrt(dx * dx + dy * dy);
                        
                        if (dist > 0) {{
                            const force = k * (dist - 150) / dist;
                            const fx = dx * force;
                            const fy = dy * force;
                            
                            forces[edge.from].x += fx * 0.1;
                            forces[edge.from].y += fy * 0.1;
                            forces[edge.to].x -= fx * 0.1;
                            forces[edge.to].y -= fy * 0.1;
                        }}
                    }}
                }});
                
                // Apply forces
                this.nodes.forEach(node => {{
                    const force = forces[node.id];
                    const pos = this.positions[node.id];
                    pos.x += force.x * 0.01;
                    pos.y += force.y * 0.01;
                }});
            }}
            
            setupEvents() {{
                let lastX = 0, lastY = 0;
                let isPanning = false;
                
                this.canvas.addEventListener('mousedown', (e) => {{
                    const rect = this.canvas.getBoundingClientRect();
                    const x = (e.clientX - rect.left - this.offsetX) / this.zoom;
                    const y = (e.clientY - rect.top - this.offsetY) / this.zoom;
                    
                    // Check if clicking on a node
                    this.dragging = null;
                    this.nodes.forEach(node => {{
                        const pos = this.positions[node.id];
                        const dist = Math.sqrt((x - pos.x) ** 2 + (y - pos.y) ** 2);
                        if (dist < 20) {{
                            this.dragging = node.id;
                        }}
                    }});
                    
                    if (!this.dragging) {{
                        isPanning = true;
                        lastX = e.clientX;
                        lastY = e.clientY;
                    }}
                }});
                
                this.canvas.addEventListener('mousemove', (e) => {{
                    if (this.dragging) {{
                        const rect = this.canvas.getBoundingClientRect();
                        const x = (e.clientX - rect.left - this.offsetX) / this.zoom;
                        const y = (e.clientY - rect.top - this.offsetY) / this.zoom;
                        this.positions[this.dragging] = {{ x, y }};
                        this.render();
                    }} else if (isPanning) {{
                        this.offsetX += e.clientX - lastX;
                        this.offsetY += e.clientY - lastY;
                        lastX = e.clientX;
                        lastY = e.clientY;
                        this.render();
                    }}
                }});
                
                this.canvas.addEventListener('mouseup', () => {{
                    this.dragging = null;
                    isPanning = false;
                }});
                
                this.canvas.addEventListener('wheel', (e) => {{
                    e.preventDefault();
                    const delta = e.deltaY > 0 ? 0.9 : 1.1;
                    this.zoom *= delta;
                    this.zoom = Math.max(0.1, Math.min(5, this.zoom));
                    this.render();
                }});
            }}
            
            render() {{
                this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);
                this.ctx.save();
                this.ctx.translate(this.offsetX, this.offsetY);
                this.ctx.scale(this.zoom, this.zoom);
                
                // Draw edges
                this.ctx.strokeStyle = '#666';
                this.ctx.lineWidth = 1;
                this.edges.forEach(edge => {{
                    const p1 = this.positions[edge.from];
                    const p2 = this.positions[edge.to];
                    
                    if (p1 && p2) {{
                        this.ctx.beginPath();
                        this.ctx.moveTo(p1.x, p1.y);
                        this.ctx.lineTo(p2.x, p2.y);
                        this.ctx.strokeStyle = edge.color || '#666';
                        this.ctx.lineWidth = edge.width || 1;
                        this.ctx.stroke();
                        
                        // Draw arrow
                        if (edge.arrows === 'to') {{
                            const angle = Math.atan2(p2.y - p1.y, p2.x - p1.x);
                            const arrowLength = 10;
                            const arrowAngle = Math.PI / 6;
                            
                            this.ctx.beginPath();
                            this.ctx.moveTo(p2.x, p2.y);
                            this.ctx.lineTo(
                                p2.x - arrowLength * Math.cos(angle - arrowAngle),
                                p2.y - arrowLength * Math.sin(angle - arrowAngle)
                            );
                            this.ctx.moveTo(p2.x, p2.y);
                            this.ctx.lineTo(
                                p2.x - arrowLength * Math.cos(angle + arrowAngle),
                                p2.y - arrowLength * Math.sin(angle + arrowAngle)
                            );
                            this.ctx.stroke();
                        }}
                    }}
                }});
                
                // Draw nodes
                this.nodes.forEach(node => {{
                    const pos = this.positions[node.id];
                    if (pos) {{
                        // Draw node shape
                        this.ctx.fillStyle = node.color || '#4285F4';
                        this.ctx.beginPath();
                        
                        const size = node.size || 20;
                        if (node.shape === 'square') {{
                            this.ctx.rect(pos.x - size/2, pos.y - size/2, size, size);
                        }} else if (node.shape === 'triangle') {{
                            this.ctx.moveTo(pos.x, pos.y - size/2);
                            this.ctx.lineTo(pos.x - size/2, pos.y + size/2);
                            this.ctx.lineTo(pos.x + size/2, pos.y + size/2);
                            this.ctx.closePath();
                        }} else if (node.shape === 'diamond') {{
                            this.ctx.moveTo(pos.x, pos.y - size/2);
                            this.ctx.lineTo(pos.x + size/2, pos.y);
                            this.ctx.lineTo(pos.x, pos.y + size/2);
                            this.ctx.lineTo(pos.x - size/2, pos.y);
                            this.ctx.closePath();
                        }} else if (node.shape === 'star') {{
                            for (let i = 0; i < 5; i++) {{
                                const angle = (i * 2 * Math.PI) / 5 - Math.PI / 2;
                                const x = pos.x + size/2 * Math.cos(angle);
                                const y = pos.y + size/2 * Math.sin(angle);
                                if (i === 0) {{
                                    this.ctx.moveTo(x, y);
                                }} else {{
                                    this.ctx.lineTo(x, y);
                                }}
                            }}
                            this.ctx.closePath();
                        }} else if (node.shape === 'box') {{
                            this.ctx.rect(pos.x - size, pos.y - size/2, size * 2, size);
                        }} else {{
                            this.ctx.arc(pos.x, pos.y, size/2, 0, 2 * Math.PI);
                        }}
                        
                        this.ctx.fill();
                        this.ctx.strokeStyle = '#fff';
                        this.ctx.lineWidth = 2;
                        this.ctx.stroke();
                        
                        // Draw label
                        this.ctx.fillStyle = '#fff';
                        this.ctx.font = '12px -apple-system, BlinkMacSystemFont, "Segoe UI", "Inter", Roboto, sans-serif';
                        this.ctx.textAlign = 'center';
                        this.ctx.textBaseline = 'middle';
                        this.ctx.fillText(node.label || node.id, pos.x, pos.y + size + 10);
                    }}
                }});
                
                this.ctx.restore();
            }}
        }}
        
        // Initialize the network
        const container = document.getElementById('mynetwork');
        const network = new SimpleNetwork(container, graphData, {{}});
        
        // UI Functions
        function showTab(tabName) {{
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.classList.add('hidden');
            }});
            
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});
            
            document.getElementById(tabName + '-tab').classList.remove('hidden');
            event.target.classList.add('active');
        }}
        
        function showModal(modalType) {{
            document.getElementById(modalType + 'Modal').style.display = 'block';
        }}
        
        function closeModal(modalType) {{
            document.getElementById(modalType + 'Modal').style.display = 'none';
        }}
        
        function toggleCollapsible(element) {{
            element.classList.toggle('active');
            var content = element.nextElementSibling;
            content.classList.toggle('show');
        }}
        
        window.onclick = function(event) {{
            if (event.target.classList.contains('modal')) {{
                event.target.style.display = 'none';
            }}
        }}
    </script>
</body>
</html>
"""
        return html 