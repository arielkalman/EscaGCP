"""
HTML visualization for EscaGCP graphs - Dashboard style
"""

import json
import networkx as nx
from pyvis.network import Network
from typing import Dict, Any, Optional, List, Set
from collections import defaultdict
from datetime import datetime
from ..utils import get_logger, Config
from ..graph.models import NodeType, EdgeType, AttackPath
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
        
        # Get logo base64
        logo_base64 = self._get_logo_base64()
        
        # Create the complete HTML
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>EscaGCP Security Dashboard</title>
    <meta charset="utf-8">
    <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"></script>
    <style>
        {self._get_inter_font_css()}
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
            padding: 12px 20px;
            border-bottom: 1px solid #e5e7eb;
            display: flex;
            justify-content: space-between;
            align-items: center;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
            height: 61px;
            box-sizing: border-box;
        }}
        
        .header h1 {{
            margin: 0;
            color: #6b46c1;
            font-size: 24px;
            font-weight: 600;
            font-family: 'Inter', sans-serif;
            display: flex;
            align-items: center;
            gap: 12px;
        }}
        
        .header-logo {{
            height: 40px;
            width: auto;
        }}
        
        .stats-bar {{
            display: flex;
            gap: 20px;
        }}
        
        .stat-item {{
            background-color: #ffffff;
            padding: 6px 12px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            transition: all 0.3s;
            font-family: 'Inter', sans-serif;
            border: 1px solid #e5e7eb;
            box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
            box-sizing: border-box;
        }}
        
        .stat-item:hover {{
            background-color: #f3f4f6;
            transform: translateY(-2px);
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        
        .stat-value {{
            font-size: 18px;
            font-weight: 600;
            color: #6b46c1;
            font-family: 'Inter', sans-serif;
            line-height: 1;
        }}
        
        .stat-label {{
            font-size: 11px;
            color: #6b7280;
            margin-top: 2px;
            font-weight: 400;
            font-family: 'Inter', sans-serif;
            line-height: 1;
        }}
        
        .share-button {{
            background-color: #6b46c1;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 8px;
            font-size: 13px;
            font-weight: 500;
            font-family: 'Inter', sans-serif;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            gap: 6px;
            margin-left: 16px;
            box-sizing: border-box;
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
            min-height: 0;
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
            height: 100vh;
            position: relative;
            min-width: 300px;
            max-width: 800px;
        }}
        
        .sidebar-resizer {{
            position: absolute;
            left: 0;
            top: 0;
            width: 5px;
            height: 100%;
            cursor: col-resize;
            background-color: transparent;
            transition: background-color 0.3s;
            z-index: 100;
        }}
        
        .sidebar-resizer:hover {{
            background-color: #6b46c1;
        }}
        
        .sidebar-resizer.resizing {{
            background-color: #6b46c1;
        }}
        
        .sidebar-tabs {{
            display: flex;
            background-color: #f9fafb;
            border-bottom: 1px solid #e5e7eb;
            height: 61px;
            align-items: center;
            box-sizing: border-box;
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
        
        .attack-category-section {{
            margin-bottom: 25px;
        }}
        
        .category-header {{
            font-size: 16px;
            font-weight: 600;
            color: #6b46c1;
            margin-bottom: 15px;
            font-family: 'Inter', sans-serif;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .attack-path-card {{
            background-color: #ffffff;
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 12px;
            border: 1px solid #e5e7eb;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Inter', sans-serif;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        }}
        
        .attack-path-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(107, 70, 193, 0.15);
            border-color: #6b46c1;
        }}
        
        .path-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .path-title {{
            display: flex;
            align-items: center;
            gap: 10px;
            font-size: 14px;
            font-weight: 500;
            flex: 1;
            min-width: 0;
        }}
        
        .path-source {{
            color: #6b46c1;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 200px;
        }}
        
        .path-arrow {{
            color: #9ca3af;
            font-size: 16px;
            flex-shrink: 0;
        }}
        
        .path-target {{
            color: #dc2626;
            font-weight: 600;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            max-width: 200px;
        }}
        
        .path-risk-badge {{
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
            color: white;
            flex-shrink: 0;
        }}
        
        .path-risk-badge.risk-critical {{
            background-color: #dc2626;
        }}
        
        .path-risk-badge.risk-high {{
            background-color: #f59e0b;
        }}
        
        .path-risk-badge.risk-medium {{
            background-color: #3b82f6;
        }}
        
        .path-risk-badge.risk-low {{
            background-color: #10b981;
        }}
        
        .path-details {{
            display: flex;
            gap: 15px;
            font-size: 13px;
            color: #6b7280;
            align-items: center;
        }}
        
        .path-steps {{
            font-weight: 500;
            flex-shrink: 0;
        }}
        
        .path-description {{
            flex: 1;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}
        
        .show-more-link {{
            text-align: center;
            color: #6b46c1;
            font-size: 13px;
            margin-top: 10px;
            cursor: pointer;
            font-weight: 500;
        }}
        
        .show-more-link:hover {{
            text-decoration: underline;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 40px;
            color: #9ca3af;
        }}
        
        .empty-icon {{
            font-size: 48px;
            margin-bottom: 10px;
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
        
        .role-holders-label {{
            font-weight: 600;
            margin-bottom: 4px;
        }}
        
        .role-holders-list {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
            margin-top: 8px;
        }}
        
        .role-holder-item {{
            background: #fee2e2;
            color: #991b1b;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-family: monospace;
        }}
        
        .role-holder-item.more {{
            background: #e5e7eb;
            color: #6b7280;
        }}
        
        .path-list-item {{
            background-color: #f9fafb;
            border-radius: 8px;
            padding: 10px;
            margin-bottom: 8px;
            font-size: 13px;
            font-family: 'Inter', sans-serif;
            border: 1px solid #e5e7eb;
            transition: all 0.2s ease;
        }}
        
        .path-list-item.clickable:hover {{
            background-color: #f3f4f6;
            border-color: #6b46c1;
            transform: translateX(2px);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
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
                <h1>
                    <img src="data:image/png;base64,{logo_base64}" alt="EscaGCP Logo" class="header-logo">
                    EscaGCP Security Dashboard
                </h1>
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
            <div class="sidebar-resizer"></div>
            <div class="sidebar-tabs">
                <button class="tab active" onclick="showTab('legend', event)">Dictionary</button>
                <button class="tab" onclick="showTab('attacks', event)">Attack Paths</button>
                <button class="tab" onclick="showTab('paths', event)">Found Paths</button>
            </div>
            
            <div class="sidebar-content">
                <!-- Dictionary Tab (formerly Legend) -->
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
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Node Shapes</button>
                    <div class="collapsible-content">
                        <div class="legend-item">
                            <div class="legend-shape">●</div>
                            <span>User (Circle)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">■</div>
                            <span>Service Account (Square)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">▲</div>
                            <span>Group (Triangle)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">▬</div>
                            <span>Project/Folder (Box)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">★</div>
                            <span>Organization (Star)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">◆</div>
                            <span>Role (Diamond)</span>
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
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Risk Calculation</button>
                    <div class="collapsible-content">
                        <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
                            <p style="margin-bottom: 10px;"><strong>How Risk Scores are Calculated:</strong></p>
                            <p style="margin-bottom: 8px;">• <strong>Critical (>80%):</strong> Direct privilege escalation paths like service account impersonation or key creation</p>
                            <p style="margin-bottom: 8px;">• <strong>High (>60%):</strong> Indirect escalation via resource deployment (Cloud Functions, VMs, Cloud Run)</p>
                            <p style="margin-bottom: 8px;">• <strong>Medium (>40%):</strong> Lateral movement or limited privilege paths</p>
                            <p style="margin-bottom: 8px;">• <strong>Low (>20%):</strong> Read-only access or minimal impact paths</p>
                            <p style="margin-top: 10px;"><strong>Factors:</strong></p>
                            <p style="margin-bottom: 8px;">• Attack technique severity</p>
                            <p style="margin-bottom: 8px;">• Number of steps (multi-step = higher risk)</p>
                            <p style="margin-bottom: 8px;">• Target sensitivity (Org > Folder > Project)</p>
                            <p style="margin-bottom: 8px;">• Node centrality in the graph</p>
                        </div>
                    </div>
                </div>
                
                <!-- Attack Paths Tab -->
                <div id="attacks-tab" class="tab-content hidden">
                    {self._create_attack_explanations_html()}
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
    
    {self._create_react_modal_integration()}
    
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
        
        {self._get_dashboard_javascript()}
        
        // Initialize sidebar resizer when page loads
        document.addEventListener('DOMContentLoaded', function() {{
            initSidebarResizer();
        }});
        
        // Also try to initialize immediately in case DOM is already loaded
        if (document.readyState !== 'loading') {{
            initSidebarResizer();
        }}
        
        // Window click handler to close modals
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
    
    def _create_graph_html(self, risk_scores: Dict[str, Any], highlight_nodes: Optional[Set[str]]) -> str:
        """Create the graph visualization HTML using vis.js directly"""
        
        # Prepare nodes for vis.js
        vis_nodes = []
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get('type', 'unknown')
            
            # Determine color based on risk
            if highlight_nodes and node_id in highlight_nodes:
                color = "#FFD700"  # Gold for highlighted nodes
                border_color = "#FFA500"
            elif risk_scores and node_id in risk_scores:
                risk = risk_scores[node_id].get('total', 0) if isinstance(risk_scores[node_id], dict) else risk_scores[node_id]
                if risk > 0.8:
                    color = "#d32f2f"  # Critical
                    border_color = "#b71c1c"
                elif risk > 0.6:
                    color = "#f44336"  # High
                    border_color = "#d32f2f"
                elif risk > 0.4:
                    color = "#ff9800"  # Medium
                    border_color = "#f57c00"
                else:
                    color = self.config.visualization_html_node_colors.get(node_type, '#999999')
                    border_color = "#666666"
            else:
                color = self.config.visualization_html_node_colors.get(node_type, '#999999')
                border_color = "#666666"
            
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
            
            # Add node
            vis_nodes.append({
                'id': node_id,
                'label': label,
                'title': self._create_node_tooltip(node_id, node_data, risk_scores),
                'color': {
                    'background': color,
                    'border': border_color,
                    'highlight': {
                        'background': color,
                        'border': '#ffffff'
                    }
                },
                'size': 25 if (highlight_nodes and node_id in highlight_nodes) else 20,
                'shape': shape,
                'font': {
                    'color': '#ffffff',
                    'size': 14,
                    'face': 'Inter, sans-serif',
                    'strokeWidth': 3,
                    'strokeColor': '#000000'
                }
            })
        
        # Prepare edges for vis.js
        vis_edges = []
        for u, v, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get('type', 'unknown')
            
            # Determine edge color and width based on type
            if edge_type in ['can_impersonate', 'can_impersonate_sa', 'can_create_service_account_key']:
                color = '#ff4444'
                width = 3
            elif edge_type in ['can_deploy_function_as', 'can_deploy_cloud_run_as', 'can_act_as_via_vm']:
                color = '#ff8800'
                width = 2
            else:
                color = self.config.visualization_html_edge_colors.get(edge_type, '#666666')
                width = 1
            
            vis_edges.append({
                'from': u,
                'to': v,
                'title': self._create_edge_tooltip(edge_data),
                'color': {
                    'color': color,
                    'highlight': '#ffffff'
                },
                'width': width,
                'arrows': {
                    'to': {
                        'enabled': True,
                        'scaleFactor': 0.5
                    }
                }
            })
        
        # Create the embedded HTML with vis.js
        embedded_html = f"""
        <div id="mynetwork" style="width: 100%; height: 100%; background-color: #1a1a1a; position: relative;">
            <div class="graph-controls" style="position: absolute; top: 10px; right: 10px; z-index: 1000; display: flex; gap: 8px; background: rgba(255,255,255,0.1); padding: 8px; border-radius: 8px; backdrop-filter: blur(10px);">
                <button onclick="fitNetwork()" style="background: #6b46c1; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500; transition: all 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" onmouseover="this.style.background='#553c9a'" onmouseout="this.style.background='#6b46c1'">Fit</button>
                <button onclick="centerNetwork()" style="background: #6b46c1; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500; transition: all 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" onmouseover="this.style.background='#553c9a'" onmouseout="this.style.background='#6b46c1'">Center</button>
                <button onclick="spreadNetwork()" style="background: #6b46c1; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500; transition: all 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" onmouseover="this.style.background='#553c9a'" onmouseout="this.style.background='#6b46c1'">Spread</button>
                <button onclick="toggleLabels()" style="background: #6b46c1; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-family: 'Inter', sans-serif; font-size: 14px; font-weight: 500; transition: all 0.3s; box-shadow: 0 2px 4px rgba(0,0,0,0.2);" onmouseover="this.style.background='#553c9a'" onmouseout="this.style.background='#6b46c1'">Toggle Labels</button>
            </div>
        </div>
        <script type="text/javascript">
            // Create the network
            var container = document.getElementById('mynetwork');
            var originalNodes = {json.dumps(vis_nodes)};
            var labelsVisible = true;
            var selectedNodeId = null;
            
            // Initially hide labels for cleaner view
            var nodesWithHiddenLabels = originalNodes.map(function(node) {{
                return {{
                    ...node,
                    label: '',
                    originalLabel: node.label
                }};
            }});
            
            var data = {{
                nodes: new vis.DataSet(nodesWithHiddenLabels),
                edges: new vis.DataSet({json.dumps(vis_edges)})
            }};
            
            var options = {{
                physics: {{
                    enabled: true,
                    solver: "barnesHut",
                    barnesHut: {{
                        gravitationalConstant: -2000,
                        centralGravity: 0.3,
                        springLength: 95,
                        springConstant: 0.04,
                        damping: 0.09,
                        avoidOverlap: 0.1
                    }},
                    stabilization: {{
                        enabled: true,
                        iterations: 1000,
                        updateInterval: 100,
                        onlyDynamicEdges: false,
                        fit: true
                    }},
                    timestep: 0.5,
                    adaptiveTimestep: true
                }},
                interaction: {{
                    hover: true,
                    tooltipDelay: 200,
                    hideEdgesOnDrag: true,
                    navigationButtons: true,
                    keyboard: true,
                    zoomView: true,
                    dragView: true
                }},
                nodes: {{
                    borderWidth: 2,
                    borderWidthSelected: 4,
                    font: {{
                        color: '#ffffff',
                        size: 14,
                        face: 'Inter, sans-serif',
                        strokeWidth: 3,
                        strokeColor: '#000000'
                    }}
                }},
                edges: {{
                    smooth: {{
                        type: "continuous",
                        forceDirection: "none",
                        roundness: 0.5
                    }},
                    arrows: {{
                        to: {{
                            enabled: true,
                            scaleFactor: 0.5
                        }}
                    }},
                    font: {{
                        color: '#ffffff',
                        size: 10,
                        face: 'Inter, sans-serif',
                        strokeWidth: 3,
                        strokeColor: '#000000',
                        align: 'middle'
                    }},
                    labelHighlightBold: true
                }},
                layout: {{
                    improvedLayout: true,
                    hierarchical: false
                }}
            }};
            
            var network = new vis.Network(container, data, options);
            
            // Stop physics after stabilization to prevent dancing
            network.on("stabilizationIterationsDone", function () {{
                network.setOptions({{ physics: false }});
            }});
            
            // Click handler to show/hide labels
            network.on("click", function(params) {{
                if (params.nodes.length > 0) {{
                    var nodeId = params.nodes[0];
                    var node = data.nodes.get(nodeId);
                    
                    if (selectedNodeId && selectedNodeId !== nodeId) {{
                        // Hide the previously selected node's label
                        var prevNode = data.nodes.get(selectedNodeId);
                        if (prevNode) {{
                            data.nodes.update({{
                                id: selectedNodeId,
                                label: ''
                            }});
                        }}
                    }}
                    
                    if (selectedNodeId === nodeId) {{
                        // Toggle off if clicking the same node
                        data.nodes.update({{
                            id: nodeId,
                            label: ''
                        }});
                        selectedNodeId = null;
                    }} else {{
                        // Show this node's label
                        data.nodes.update({{
                            id: nodeId,
                            label: node.originalLabel || node.id
                        }});
                        selectedNodeId = nodeId;
                    }}
                }}
            }});
            
            // Control functions
            window.fitNetwork = function() {{
                network.fit({{
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }};
            
            window.centerNetwork = function() {{
                network.moveTo({{
                    position: {{x: 0, y: 0}},
                    scale: 1,
                    animation: {{
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }}
                }});
            }};
            
            window.spreadNetwork = function() {{
                // Temporarily increase physics to spread nodes
                network.setOptions({{
                    physics: {{
                        enabled: true,
                        solver: "barnesHut",
                        barnesHut: {{
                            gravitationalConstant: -5000,
                            centralGravity: 0.01,
                            springLength: 200,
                            springConstant: 0.02,
                            damping: 0.09,
                            avoidOverlap: 1
                        }}
                    }}
                }});
                
                // Stop physics after a short time
                setTimeout(function() {{
                    network.setOptions({{ physics: false }});
                }}, 3000);
            }};
            
            window.toggleLabels = function() {{
                labelsVisible = !labelsVisible;
                var nodes = data.nodes.get();
                nodes.forEach(function(node) {{
                    data.nodes.update({{
                        id: node.id,
                        label: labelsVisible ? (node.originalLabel || node.id) : ''
                    }});
                }});
                selectedNodeId = null;
            }};
            
            // Store network globally for other functions to access
            window.graphNetwork = network;
        </script>
        """
        
        return embedded_html
    
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
        
        # Also count nodes that have dangerous roles as high risk
        for node_id, node_data in self.graph.nodes(data=True):
            if node_id.startswith(('user:', 'sa:', 'group:')):
                # Check if this identity has any dangerous roles
                for neighbor in self.graph.neighbors(node_id):
                    if neighbor.startswith('role:'):
                        role_name = self.graph.nodes[neighbor].get('name', neighbor)
                        if role_name in self.DANGEROUS_ROLES:
                            # This is a high risk node
                            if node_id not in risk_scores or (risk_scores.get(node_id, {}).get('total', 0) if isinstance(risk_scores.get(node_id, {}), dict) else risk_scores.get(node_id, 0)) <= 0.6:
                                high_risk_count += 1
                                break
        
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
        """Create HTML for nodes list in modal with enhanced data"""
        # Prepare enhanced node data
        enhanced_nodes = {}
        
        for node_type, nodes in nodes_by_type.items():
            enhanced_list = []
            for node in nodes[:100]:  # Limit to first 100 per type
                node_id = node.get('id', '')
                node_data = self.graph.nodes.get(node_id, {})
                
                # Calculate in/out degrees
                in_degree = self.graph.in_degree(node_id) if node_id in self.graph else 0
                out_degree = self.graph.out_degree(node_id) if node_id in self.graph else 0
                
                # Extract metadata
                metadata = {}
                if 'email' in node_data:
                    metadata['email'] = node_data['email']
                if 'project_id' in node_data:
                    metadata['projectId'] = node_data['project_id']
                if 'full_name' in node_data:
                    metadata['fullName'] = node_data['full_name']
                if 'description' in node_data:
                    metadata['description'] = node_data['description']
                
                enhanced_list.append({
                    'id': node_id,
                    'name': node['name'],
                    'type': node_type,
                    'metadata': metadata,
                    'inDegree': in_degree,
                    'outDegree': out_degree,
                    'riskScore': node.get('risk_score', 0)
                })
            
            enhanced_nodes[node_type] = enhanced_list
        
        # Return JSON data for React component
        return f"""
        <div id="nodes-modal-root"></div>
        <script>
            window.nodesModalData = {json.dumps(enhanced_nodes)};
        </script>
        """
    
    def _create_edges_list_html(self, edges_by_type: Dict[str, List[Dict[str, Any]]]) -> str:
        """Create HTML for edges list in modal with enhanced data"""
        # Prepare enhanced edge data
        enhanced_edges = {}
        
        for edge_type, edges in edges_by_type.items():
            enhanced_list = []
            for edge in edges[:100]:  # Limit to first 100 per type
                source_id = edge['source']
                target_id = edge['target']
                
                # Get node names
                source_name = self.graph.nodes.get(source_id, {}).get('name', source_id)
                target_name = self.graph.nodes.get(target_id, {}).get('name', target_id)
                
                # Clean names
                source_name = self._clean_node_name(source_name)
                target_name = self._clean_node_name(target_name)
                
                # Extract edge metadata
                edge_data = {}
                for u, v, data in self.graph.edges(data=True):
                    if u == source_id and v == target_id and data.get('type') == edge_type:
                        edge_data = data
                        break
                
                # Build enhanced edge
                enhanced_edge = {
                    'id': f"{source_id}-{edge_type}-{target_id}",
                    'source': source_id,
                    'target': target_id,
                    'type': edge_type,
                    'sourceName': source_name,
                    'targetName': target_name
                }
                
                # Add permission info if available
                if 'permission' in edge_data:
                    enhanced_edge['permission'] = edge_data['permission']
                elif edge_type == 'CAN_IMPERSONATE_SA':
                    enhanced_edge['permission'] = 'iam.serviceAccounts.getAccessToken'
                elif edge_type == 'CAN_CREATE_SERVICE_ACCOUNT_KEY':
                    enhanced_edge['permission'] = 'iam.serviceAccountKeys.create'
                elif edge_type == 'CAN_ACT_AS_VIA_VM':
                    enhanced_edge['permission'] = 'compute.instances.setServiceAccount + iam.serviceAccounts.actAs'
                elif edge_type == 'CAN_DEPLOY_FUNCTION_AS':
                    enhanced_edge['permission'] = 'cloudfunctions.functions.create + iam.serviceAccounts.actAs'
                elif edge_type == 'CAN_DEPLOY_CLOUD_RUN_AS':
                    enhanced_edge['permission'] = 'run.services.create + iam.serviceAccounts.actAs'
                
                # Add resource scope if available
                if 'resource_scope' in edge_data:
                    enhanced_edge['resourceScope'] = edge_data['resource_scope']
                elif 'project' in edge_data:
                    enhanced_edge['resourceScope'] = f"project/{edge_data['project']}"
                
                # Add rationale
                if edge_type == 'CAN_IMPERSONATE_SA':
                    enhanced_edge['rationale'] = f"{source_name} has Token Creator role on {target_name}"
                elif edge_type == 'CAN_CREATE_SERVICE_ACCOUNT_KEY':
                    enhanced_edge['rationale'] = f"{source_name} can create keys for {target_name}"
                elif edge_type == 'HAS_ROLE':
                    enhanced_edge['rationale'] = f"{source_name} has been granted {target_name}"
                
                enhanced_list.append(enhanced_edge)
            
            enhanced_edges[edge_type] = enhanced_list
        
        # Return JSON data for React component
        return f"""
        <div id="edges-modal-root"></div>
        <script>
            window.edgesModalData = {json.dumps(enhanced_edges)};
        </script>
        """
    
    def _create_high_risk_nodes_html(self, risk_scores: Dict[str, Any]) -> str:
        """Create HTML for high risk nodes list"""
        html = ""
        high_risk_nodes = []
        
        # Collect nodes with high risk scores
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
        
        # Also check for nodes with dangerous roles
        for node_id, node_data in self.graph.nodes(data=True):
            if node_id.startswith(('user:', 'sa:', 'group:')):
                # Check if this identity has any dangerous roles
                has_dangerous_role = False
                for neighbor in self.graph.neighbors(node_id):
                    if neighbor.startswith('role:'):
                        role_name = self.graph.nodes[neighbor].get('name', neighbor)
                        if role_name in self.DANGEROUS_ROLES:
                            has_dangerous_role = True
                            break
                
                if has_dangerous_role:
                    # Check if not already in high_risk_nodes
                    if not any(n['id'] == node_id for n in high_risk_nodes):
                        high_risk_nodes.append({
                            'id': node_id,
                            'name': node_data.get('name', node_id),
                            'type': node_data.get('type', 'unknown'),
                            'risk': 0.7  # Default risk for dangerous role holders
                        })
        
        # Sort by risk score
        high_risk_nodes.sort(key=lambda x: x['risk'], reverse=True)
        
        if not high_risk_nodes:
            html = '<li class="modal-list-item">No high risk nodes found</li>'
        else:
            for node in high_risk_nodes[:50]:  # Limit to top 50
                risk_class = 'risk-critical' if node['risk'] > 0.8 else 'risk-high'
                html += f"""
                <li class="modal-list-item">
                    {self._clean_node_name(node['name'])}
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
                
                # Clean up holder names
                cleaned_holders = []
                for holder in holders[:5]:  # Show first 5
                    cleaned_name = self._clean_node_name(holder)
                    cleaned_holders.append(cleaned_name)
                
                html += f"""
                <div class="dangerous-role-item">
                    <div class="role-name">{role}</div>
                    <div class="role-description">{description}</div>
                    <div class="role-holders">
                        <div style="font-weight: 600; margin-bottom: 4px;">Assigned to {len(holders)} identit{'ies' if len(holders) != 1 else 'y'}:</div>
                        <div style="display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px;">
                """
                
                for holder in cleaned_holders:
                    html += f'<span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-family: monospace;">{holder}</span>'
                
                if len(holders) > 5:
                    # Create a unique ID for this role's additional holders
                    role_id = role.replace('/', '_').replace('.', '_')
                    html += f'''<span id="more-btn-{role_id}" style="background: #e5e7eb; color: #6b7280; padding: 2px 8px; border-radius: 4px; font-size: 12px; cursor: pointer;" onclick="showMoreHolders('{role_id}')">+{len(holders) - 5} more</span>
                    <div id="more-holders-{role_id}" style="display: none; margin-top: 6px;">'''
                    
                    # Add the remaining holders
                    for holder in holders[5:]:
                        cleaned_holder = self._clean_node_name(holder)
                        html += f'<span style="background: #fee2e2; color: #991b1b; padding: 2px 8px; border-radius: 4px; font-size: 12px; font-family: monospace; margin: 2px;">{cleaned_holder}</span>'
                    
                    html += '</div>'
                
                html += """
                        </div>
                    </div>
                </div>
                """
        
        if not html:
            html = "<p>No dangerous roles detected in the current graph.</p>"
        
        return html
    
    def _create_found_paths_html(self, attack_paths: List[Dict[str, Any]], show_all: bool = False) -> str:
        """Create HTML for found attack paths"""
        if not attack_paths:
            return """
            <div class="empty-state">
                <div class="empty-icon">🔍</div>
                <p>No attack paths found. Run analysis to detect paths.</p>
            </div>
            """
        
        html = ""
        # Group by category
        by_category = defaultdict(list)
        for i, path in enumerate(attack_paths):
            # Ensure each path has an index for JavaScript reference
            if isinstance(path, dict):
                path['_index'] = i
                category = path.get('category', 'other')
            else:
                # Handle AttackPath objects
                path_dict = path.to_dict() if hasattr(path, 'to_dict') else {
                    'risk_score': path.risk_score if hasattr(path, 'risk_score') else 0,
                    'description': path.description if hasattr(path, 'description') else '',
                    'length': len(path) if hasattr(path, '__len__') else 1,
                    'path': path.get_path_string() if hasattr(path, 'get_path_string') else str(path),
                    'visualization_metadata': path.visualization_metadata if hasattr(path, 'visualization_metadata') else None
                }
                path_dict['_index'] = i
                # Determine category based on path attributes
                if hasattr(path, 'risk_score') and path.risk_score > 0.9:
                    category = 'critical_multi_step'
                elif hasattr(path, 'description') and 'multi-step' in str(path.description).lower():
                    category = 'critical_multi_step'
                else:
                    category = 'privilege_escalation'
            by_category[category].append((i, path))
        
        # Sort categories by severity
        category_order = ['critical_multi_step', 'critical', 'high', 'medium', 'privilege_escalation', 'lateral_movement', 'other']
        sorted_categories = sorted(by_category.items(), key=lambda x: category_order.index(x[0]) if x[0] in category_order else 999)
        
        for category, indexed_paths in sorted_categories:
            # Sort paths within category by risk score (descending) then by length (descending)
            def sort_key(item):
                idx, path = item
                if isinstance(path, dict):
                    risk = path.get('risk_score', 0)
                    length = path.get('length', 1)
                else:
                    risk = path.risk_score if hasattr(path, 'risk_score') else 0
                    length = len(path) if hasattr(path, '__len__') else 1
                # Return negative values to sort descending
                return (-risk, -length)
            
            indexed_paths.sort(key=sort_key)
            
            # Format category name
            category_display = category.replace('_', ' ').title()
            category_icon = '🚨' if 'critical' in category else '⚠️' if 'high' in category else '📊'
            
            html += f'<div class="attack-category-section">'
            html += f'<div class="category-header">{category_icon} {category_display} ({len(indexed_paths)} paths)</div>'
            
            limit = len(indexed_paths) if show_all else 10
            for idx, path in indexed_paths[:limit]:
                if isinstance(path, dict):
                    risk = path.get('risk_score', 0)
                    path_str = path.get('path', 'Unknown path')
                    description = path.get('description', '')
                    length = path.get('length', 1)
                    
                    # Better extraction of source and target
                    if 'source' in path and 'target' in path:
                        # If we have explicit source and target
                        source_data = path['source']
                        target_data = path['target']
                        if isinstance(source_data, dict):
                            source = source_data.get('name', source_data.get('id', 'Unknown'))
                        else:
                            source = str(source_data)
                        if isinstance(target_data, dict):
                            target = target_data.get('name', target_data.get('id', 'Unknown'))
                        else:
                            target = str(target_data)
                    elif 'path_nodes' in path and len(path['path_nodes']) >= 2:
                        # Extract from path nodes
                        first_node = path['path_nodes'][0]
                        last_node = path['path_nodes'][-1]
                        if isinstance(first_node, dict):
                            source = first_node.get('name', first_node.get('id', 'Unknown'))
                        else:
                            source = str(first_node)
                        if isinstance(last_node, dict):
                            target = last_node.get('name', last_node.get('id', 'Unknown'))
                        else:
                            target = str(last_node)
                        # Fix: Number of edges is nodes - 1
                        if len(path['path_nodes']) > 1:
                            length = len(path['path_nodes']) - 1
                        else:
                            length = path.get('length', 1)
                    elif '--[' in path_str and ']-->' in path_str:
                        # Parse from path string format: node1 --[edge_type]--> node2 --[edge_type]--> node3
                        parts = path_str.split(' --[')
                        if parts:
                            source = parts[0].strip()
                            # Find the last node
                            last_part = parts[-1]
                            if ']--> ' in last_part:
                                target = last_part.split(']--> ')[-1].strip()
                            else:
                                target = 'Unknown'
                            length = len(parts) - 1
                        else:
                            source = 'Unknown'
                            target = 'Unknown'
                    elif ' -> ' in path_str:
                        # Simple arrow format
                        parts = path_str.split(' -> ')
                        source = parts[0].strip()
                        target = parts[-1].strip()
                        length = len(parts) - 1
                    else:
                        # Fallback
                        source = 'Unknown'
                        target = 'Unknown'
                    
                    # Clean up source and target names
                    source = self._clean_node_name(source)
                    target = self._clean_node_name(target)
                    
                else:
                    # Handle AttackPath objects
                    risk = path.risk_score if hasattr(path, 'risk_score') else 0
                    path_str = path.get_path_string() if hasattr(path, 'get_path_string') else str(path)
                    description = path.description if hasattr(path, 'description') else ''
                    # Fix: For AttackPath objects, check if it has path_nodes or path_edges
                    if hasattr(path, 'path_nodes') and len(path.path_nodes) > 1:
                        length = len(path.path_nodes) - 1  # Number of edges
                    elif hasattr(path, 'path_edges') and len(path.path_edges) > 0:
                        length = len(path.path_edges)  # Direct edge count
                    elif hasattr(path, '__len__'):
                        # Fallback: assume len() returns nodes, so subtract 1
                        length = max(1, len(path) - 1)
                    else:
                        length = 1
                    
                    if hasattr(path, 'source_node') and hasattr(path, 'target_node'):
                        source = path.source_node.get_display_name() if hasattr(path.source_node, 'get_display_name') else str(path.source_node)
                        target = path.target_node.get_display_name() if hasattr(path.target_node, 'get_display_name') else str(path.target_node)
                    else:
                        source = 'Unknown'
                        target = 'Unknown'
                    
                    source = self._clean_node_name(source)
                    target = self._clean_node_name(target)
                
                risk_class = 'risk-critical' if risk > 0.8 else 'risk-high' if risk > 0.6 else 'risk-medium' if risk > 0.4 else 'risk-low'
                
                # Fix the description for multi-step attacks
                if 'multi-step' in description.lower() and 'steps)' in description:
                    # Extract the actual number of steps from the description
                    import re
                    match = re.search(r'(\d+) steps?\)', description)
                    if match:
                        actual_steps = int(match.group(1))
                        if actual_steps > 0:
                            length = actual_steps
                
                html += f"""
                <div class="attack-path-card" onclick="showAttackPath({idx}, event)">
                    <div class="path-header">
                        <div class="path-title">
                            <span class="path-source">{source}</span>
                            <span class="path-arrow">→</span>
                            <span class="path-target">{target}</span>
                        </div>
                        <div class="path-risk-badge {risk_class}">
                            {risk:.0%}
                        </div>
                    </div>
                    <div class="path-details">
                        <div class="path-steps">{length} step{'s' if length != 1 else ''}</div>
                        {f'<div class="path-description">{description}</div>' if description else ''}
                    </div>
                </div>
                """
            
            if len(indexed_paths) > limit:
                # Create a unique ID for this category
                category_id = category.replace('_', '-')
                remaining = len(indexed_paths) - limit
                html += f'''<div id="show-more-{category_id}" class="show-more-link" onclick="showMorePaths('{category_id}', {limit}, {len(indexed_paths)})">... and {remaining} more</div>
                <div id="more-paths-{category_id}" style="display: none;">'''
                
                # Add all remaining paths but hidden
                for idx, path in indexed_paths[limit:]:
                    if isinstance(path, dict):
                        risk = path.get('risk_score', 0)
                        path_str = path.get('path', 'Unknown path')
                        description = path.get('description', '')
                        length = path.get('length', 1)
                        
                        # Extract source and target (same logic as above)
                        if 'path_nodes' in path and len(path['path_nodes']) >= 2:
                            first_node = path['path_nodes'][0]
                            last_node = path['path_nodes'][-1]
                            if isinstance(first_node, dict):
                                source = first_node.get('name', first_node.get('id', 'Unknown'))
                            else:
                                source = str(first_node)
                            if isinstance(last_node, dict):
                                target = last_node.get('name', last_node.get('id', 'Unknown'))
                            else:
                                target = str(last_node)
                            # Fix: Number of edges is nodes - 1
                            if len(path['path_nodes']) > 1:
                                length = len(path['path_nodes']) - 1
                            else:
                                length = path.get('length', 1)
                        else:
                            source = 'Unknown'
                            target = 'Unknown'
                        
                        source = self._clean_node_name(source)
                        target = self._clean_node_name(target)
                    else:
                        # Handle AttackPath objects
                        risk = path.risk_score if hasattr(path, 'risk_score') else 0
                        description = path.description if hasattr(path, 'description') else ''
                        # Fix: For AttackPath objects, check if it has path_nodes or path_edges
                        if hasattr(path, 'path_nodes') and len(path.path_nodes) > 1:
                            length = len(path.path_nodes) - 1  # Number of edges
                        elif hasattr(path, 'path_edges') and len(path.path_edges) > 0:
                            length = len(path.path_edges)  # Direct edge count
                        elif hasattr(path, '__len__'):
                            # Fallback: assume len() returns nodes, so subtract 1
                            length = max(1, len(path) - 1)
                        else:
                            length = 1
                        source = 'Unknown'
                        target = 'Unknown'
                    
                    risk_class = 'risk-critical' if risk > 0.8 else 'risk-high' if risk > 0.6 else 'risk-medium' if risk > 0.4 else 'risk-low'
                    
                    html += f"""
                    <div class="attack-path-card hidden-path" data-category="{category_id}" style="display: none;" onclick="showAttackPath({idx}, event)">
                        <div class="path-header">
                            <div class="path-title">
                                <span class="path-source">{source}</span>
                                <span class="path-arrow">→</span>
                                <span class="path-target">{target}</span>
                            </div>
                            <div class="path-risk-badge {risk_class}">
                                {risk:.0%}
                            </div>
                        </div>
                        <div class="path-details">
                            <div class="path-steps">{length} step{'s' if length != 1 else ''}</div>
                            {f'<div class="path-description">{description}</div>' if description else ''}
                        </div>
                    </div>
                    """
                
                html += '</div>'
            
            html += '</div>'
        
        return html
    
    def _clean_node_name(self, name: str) -> str:
        """Clean up node names for display"""
        if not name or name == 'Unknown':
            return name
            
        # Remove prefixes like 'user:', 'sa:', 'role:', etc.
        prefixes = ['user:', 'sa:', 'role:', 'project:', 'folder:', 'org:', 'group:', 'resource:']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):]
                break
        
        # Shorten service account emails
        if '@' in name and '.iam.gserviceaccount.com' in name:
            name = name.split('@')[0]
        
        # Shorten role names
        if name.startswith('roles/'):
            name = name[6:]  # Remove 'roles/' prefix
        
        # Limit length
        if len(name) > 50:
            name = name[:47] + '...'
            
        return name
    
    def _get_standalone_template(self) -> str:
        """Get the JavaScript template for generating standalone reports"""
        # This returns a template string that will be evaluated in the browser
        # It uses template literals with ${} for JavaScript variable interpolation
        return '''<!DOCTYPE html>
<html>
<head>
    <title>EscaGCP Security Report - Standalone</title>
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
        <h1 class="standalone-title">EscaGCP Security Report</h1>
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
        <p>This is a standalone EscaGCP report. All data is embedded in this HTML file.</p>
        <p>No external dependencies or internet connection required.</p>
    </div>
    
    <script>
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
            },
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: true,
                navigationButtons: true,
                keyboard: true,
                navigationButtons": true,
                keyboard": true
            }},
            configure": {{
                "enabled": false
            }},
            manipulation": {{
                "enabled": false
            }},
            nodes": {{
                "borderWidth": 2,
                "borderWidthSelected": 4,
                "font": {{
                    "face": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                    "size": 14,
                    "strokeWidth": 0,
                    "color": "#ffffff"
                }}
            }},
            edges": {{
                "smooth": {{
                    "type": "continuous",
                    "forceDirection": "none"
                }},
                "arrows": {{
                    "to": {{
                        "enabled": true,
                        "scaleFactor": 0.5
                    }}
                }},
                "font": {{
                    "face": "Inter, -apple-system, BlinkMacSystemFont, sans-serif",
                    "size": 10,
                    "strokeWidth": 0,
                    "color": "#cccccc"
                }}
            }}
        }};
        
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
                border_color = "#FFA500"
            elif risk_scores and node_id in risk_scores:
                risk = risk_scores[node_id].get('total', 0) if isinstance(risk_scores[node_id], dict) else risk_scores[node_id]
                if risk > 0.8:
                    color = "#d32f2f"  # Critical
                    border_color = "#b71c1c"
                elif risk > 0.6:
                    color = "#f44336"  # High
                    border_color = "#d32f2f"
                elif risk > 0.4:
                    color = "#ff9800"  # Medium
                    border_color = "#f57c00"
                else:
                    color = self.config.visualization_html_node_colors.get(node_type, '#999999')
                    border_color = "#666666"
            else:
                color = self.config.visualization_html_node_colors.get(node_type, '#999999')
                border_color = "#666666"
            
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
                'color': {
                    'background': color,
                    'border': border_color,
                    'highlight': {
                        'background': color,
                        'border': '#ffffff'
                    }
                },
                'shape': shape,
                'size': 25 if (highlight_nodes and node_id in highlight_nodes) else 20,
                'font': {
                    'face': 'Inter, sans-serif',
                    'size': 14,
                    'color': '#ffffff',
                    'strokeWidth': 3,
                    'strokeColor': '#000000'
                }
            })
        
        # Serialize edges
        for u, v, edge_data in self.graph.edges(data=True):
            edge_type = edge_data.get('type', 'unknown')
            
            # Determine edge color and width based on type
            if edge_type in ['can_impersonate', 'can_impersonate_sa', 'can_create_service_account_key']:
                color = '#ff4444'
                width = 3
            elif edge_type in ['can_deploy_function_as', 'can_deploy_cloud_run_as', 'can_act_as_via_vm']:
                color = '#ff8800'
                width = 2
            else:
                color = self.config.visualization_html_edge_colors.get(edge_type, '#666666')
                width = 1
            
            edges.append({
                'from': u,
                'to': v,
                'title': self._create_edge_tooltip(edge_data),
                'color': {
                    'color': color,
                    'highlight': '#ffffff'
                },
                'width': width,
                'arrows': {
                    'to': {
                        'enabled': True,
                        'scaleFactor': 0.5
                    }
                }
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
    <title>EscaGCP Security Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        {self._get_inter_font_css()}
        
        body {{
            margin: 0;
            padding: 20px;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
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
        <h1>EscaGCP Security Report</h1>
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
            <div class="sidebar-resizer"></div>
            <div class="sidebar-tabs">
                <button class="tab active" onclick="showTab('legend', event)">Dictionary</button>
                <button class="tab" onclick="showTab('attacks', event)">Attack Paths</button>
                <button class="tab" onclick="showTab('paths', event)">Found Paths</button>
            </div>
            
            <div class="sidebar-content">
                <!-- Dictionary Tab (formerly Legend) -->
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
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Node Shapes</button>
                    <div class="collapsible-content">
                        <div class="legend-item">
                            <div class="legend-shape">●</div>
                            <span>User (Circle)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">■</div>
                            <span>Service Account (Square)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">▲</div>
                            <span>Group (Triangle)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">▬</div>
                            <span>Project/Folder (Box)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">★</div>
                            <span>Organization (Star)</span>
                        </div>
                        <div class="legend-item">
                            <div class="legend-shape">◆</div>
                            <span>Role (Diamond)</span>
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
                    
                    <button class="collapsible" onclick="toggleCollapsible(this)">Risk Calculation</button>
                    <div class="collapsible-content">
                        <div style="font-size: 13px; color: #6b7280; line-height: 1.6;">
                            <p style="margin-bottom: 10px;"><strong>How Risk Scores are Calculated:</strong></p>
                            <p style="margin-bottom: 8px;">• <strong>Critical (>80%):</strong> Direct privilege escalation paths like service account impersonation or key creation</p>
                            <p style="margin-bottom: 8px;">• <strong>High (>60%):</strong> Indirect escalation via resource deployment (Cloud Functions, VMs, Cloud Run)</p>
                            <p style="margin-bottom: 8px;">• <strong>Medium (>40%):</strong> Lateral movement or limited privilege paths</p>
                            <p style="margin-bottom: 8px;">• <strong>Low (>20%):</strong> Read-only access or minimal impact paths</p>
                            <p style="margin-top: 10px;"><strong>Factors:</strong></p>
                            <p style="margin-bottom: 8px;">• Attack technique severity</p>
                            <p style="margin-bottom: 8px;">• Number of steps (multi-step = higher risk)</p>
                            <p style="margin-bottom: 8px;">• Target sensitivity (Org > Folder > Project)</p>
                            <p style="margin-bottom: 8px;">• Node centrality in the graph</p>
                        </div>
                    </div>
                </div>
                
                <!-- Attack Paths Tab -->
                <div id="attacks-tab" class="tab-content hidden">
                    {self._create_attack_explanations_html()}
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
        function showTab(tabName, event) {{
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
    
    def render_attack_path_graph(self, attack_path: AttackPath, output_file: str):
        """
        Render an interactive visualization for a single attack path
        
        Args:
            attack_path: AttackPath object with visualization metadata
            output_file: Path to save the HTML file
        """
        logger.info(f"Rendering attack path graph to {output_file}")
        
        # Get attack graph data
        graph_data = attack_path.get_attack_graph_data()
        
        if not graph_data or not graph_data.get('nodes'):
            logger.warning("No visualization data available for attack path")
            return
        
        # Create HTML with Cytoscape.js for clean, interactive visualization
        html_content = self._create_attack_path_html(attack_path, graph_data)
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"Attack path visualization saved to {output_file}")
    
    def _create_attack_path_html(self, attack_path: AttackPath, graph_data: Dict[str, Any]) -> str:
        """Create HTML for attack path visualization using Cytoscape.js"""
        
        # Convert nodes and edges to Cytoscape format
        cy_elements = []
        
        # Add nodes
        for node in graph_data['nodes']:
            cy_elements.append({
                'data': {
                    'id': node['id'],
                    'label': node['label'],
                    'type': node['type'],
                    'icon': node['icon'],
                    'risk_level': node['risk_level']
                },
                'classes': f"node-{node['type']} risk-{node['risk_level']}"
            })
        
        # Add edges
        for edge in graph_data['edges']:
            cy_elements.append({
                'data': {
                    'id': f"{edge['source']}-{edge['target']}",
                    'source': edge['source'],
                    'target': edge['target'],
                    'label': edge['label'],
                    'type': edge['type'],
                    'risk_score': edge['risk_score']
                },
                'classes': f"edge-{edge['type']}"
            })
        
        # Generate HTML
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Attack Path: {graph_data['summary']}</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.26.0/cytoscape.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dagre/0.8.5/dagre.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/cytoscape-dagre@2.5.0/cytoscape-dagre.min.js"></script>
    <style>
        {self._get_inter_font_css()}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: #f8f9fa;
            color: #202124;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
        }}
        
        .header {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #202124;
        }}
        
        .header .summary {{
            font-size: 16px;
            color: #5f6368;
            margin-bottom: 16px;
        }}
        
        .header .metadata {{
            display: flex;
            gap: 24px;
            flex-wrap: wrap;
        }}
        
        .metadata-item {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .metadata-item .label {{
            font-size: 14px;
            color: #5f6368;
        }}
        
        .metadata-item .value {{
            font-size: 14px;
            font-weight: 600;
            color: #202124;
        }}
        
        .risk-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 16px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
        }}
        
        .risk-critical {{
            background: #fce8e6;
            color: #d33b27;
        }}
        
        .risk-high {{
            background: #feefc3;
            color: #f9ab00;
        }}
        
        .risk-medium {{
            background: #e6f4ea;
            color: #137333;
        }}
        
        .graph-container {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            height: 600px;
            position: relative;
        }}
        
        #cy {{
            width: 100%;
            height: 100%;
            border: 1px solid #e8eaed;
            border-radius: 8px;
        }}
        
        .controls {{
            position: absolute;
            top: 36px;
            right: 36px;
            display: flex;
            gap: 8px;
            z-index: 10;
        }}
        
        .control-btn {{
            background: white;
            border: 1px solid #dadce0;
            border-radius: 8px;
            padding: 8px 16px;
            font-size: 14px;
            font-weight: 500;
            color: #5f6368;
            cursor: pointer;
            transition: all 0.2s;
        }}
        
        .control-btn:hover {{
            background: #f8f9fa;
            border-color: #5f6368;
            color: #202124;
        }}
        
        .techniques-container {{
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-top: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        
        .techniques-container h2 {{
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 16px;
            color: #202124;
        }}
        
        .technique-list {{
            display: flex;
            flex-direction: column;
            gap: 12px;
        }}
        
        .technique-item {{
            display: flex;
            align-items: flex-start;
            gap: 12px;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 8px;
            border: 1px solid #e8eaed;
        }}
        
        .technique-icon {{
            font-size: 24px;
            line-height: 1;
        }}
        
        .technique-details {{
            flex: 1;
        }}
        
        .technique-name {{
            font-weight: 600;
            font-size: 14px;
            color: #202124;
            margin-bottom: 4px;
        }}
        
        .technique-description {{
            font-size: 13px;
            color: #5f6368;
            margin-bottom: 4px;
        }}
        
        .technique-permission {{
            font-size: 12px;
            font-family: 'Monaco', 'Consolas', monospace;
            color: #137333;
            background: #e6f4ea;
            padding: 2px 6px;
            border-radius: 4px;
            display: inline-block;
        }}
        
        .legend {{
            position: absolute;
            bottom: 36px;
            left: 36px;
            background: white;
            border: 1px solid #e8eaed;
            border-radius: 8px;
            padding: 12px;
            font-size: 12px;
        }}
        
        .legend-title {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #202124;
        }}
        
        .legend-items {{
            display: flex;
            gap: 16px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 6px;
        }}
        
        .legend-color {{
            width: 12px;
            height: 12px;
            border-radius: 50%;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Attack Path Analysis</h1>
            <div class="summary">{graph_data['summary']}</div>
            <div class="metadata">
                <div class="metadata-item">
                    <span class="label">Path Length:</span>
                    <span class="value">{graph_data['path_length']} steps</span>
                </div>
                <div class="metadata-item">
                    <span class="label">Risk Score:</span>
                    <span class="risk-badge risk-{self._get_risk_level(graph_data['risk_score'])}">{graph_data['risk_score']:.2f}</span>
                </div>
                <div class="metadata-item">
                    <span class="label">Techniques:</span>
                    <span class="value">{len(graph_data['techniques'])}</span>
                </div>
            </div>
        </div>
        
        <div class="graph-container">
            <div class="controls">
                <button class="control-btn" onclick="cy.fit()">Fit</button>
                <button class="control-btn" onclick="cy.center()">Center</button>
                <button class="control-btn" onclick="downloadImage()">Download</button>
            </div>
            <div id="cy"></div>
            <div class="legend">
                <div class="legend-title">Node Types</div>
                <div class="legend-items">
                    <div class="legend-item">
                        <div class="legend-color" style="background: #4285F4"></div>
                        <span>User</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #34A853"></div>
                        <span>Service Account</span>
                    </div>
                    <div class="legend-item">
                        <div class="legend-color" style="background: #EA4335"></div>
                        <span>Resource</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="techniques-container">
            <h2>Attack Techniques Used</h2>
            <div class="technique-list">
                {self._create_techniques_list_html(graph_data['techniques'])}
            </div>
        </div>
    </div>
    
    <script>
        // Initialize Cytoscape
        var cy = cytoscape({{
            container: document.getElementById('cy'),
            elements: {json.dumps(cy_elements)},
            style: [
                {{
                    selector: 'node',
                    style: {{
                        'label': 'data(label)',
                        'text-valign': 'bottom',
                        'text-halign': 'center',
                        'font-family': 'Inter, sans-serif',
                        'font-size': '12px',
                        'font-weight': '500',
                        'text-margin-y': 8,
                        'width': 60,
                        'height': 60,
                        'border-width': 2,
                        'border-color': '#dadce0',
                        'background-color': '#ffffff'
                    }}
                }},
                {{
                    selector: 'node.node-user',
                    style: {{
                        'background-color': '#e8f0fe',
                        'border-color': '#4285F4'
                    }}
                }},
                {{
                    selector: 'node.node-service_account',
                    style: {{
                        'background-color': '#e6f4ea',
                        'border-color': '#34A853'
                    }}
                }},
                {{
                    selector: 'node.node-project',
                    style: {{
                        'background-color': '#fce8e6',
                        'border-color': '#EA4335'
                    }}
                }},
                {{
                    selector: 'node.node-role',
                    style: {{
                        'background-color': '#f8f9fa',
                        'border-color': '#5f6368'
                    }}
                }},
                {{
                    selector: 'node.risk-critical',
                    style: {{
                        'border-width': 3,
                        'border-color': '#d33b27'
                    }}
                }},
                {{
                    selector: 'node.risk-high',
                    style: {{
                        'border-width': 3,
                        'border-color': '#f9ab00'
                    }}
                }},
                {{
                    selector: 'edge',
                    style: {{
                        'label': 'data(label)',
                        'font-family': 'Inter, sans-serif',
                        'font-size': '11px',
                        'font-weight': '500',
                        'text-background-color': '#ffffff',
                        'text-background-opacity': 0.9,
                        'text-background-padding': '4px',
                        'text-border-width': 1,
                        'text-border-color': '#e8eaed',
                        'text-border-opacity': 1,
                        'curve-style': 'bezier',
                        'target-arrow-shape': 'triangle',
                        'target-arrow-color': '#5f6368',
                        'line-color': '#dadce0',
                        'width': 2,
                        'arrow-scale': 1.2
                    }}
                }},
                {{
                    selector: 'edge.edge-can_impersonate_sa',
                    style: {{
                        'line-color': '#d33b27',
                        'target-arrow-color': '#d33b27',
                        'width': 3
                    }}
                }},
                {{
                    selector: 'edge.edge-can_create_service_account_key',
                    style: {{
                        'line-color': '#ea4335',
                        'target-arrow-color': '#ea4335',
                        'width': 3
                    }}
                }},
                {{
                    selector: 'edge.edge-can_deploy_function_as',
                    style: {{
                        'line-color': '#f9ab00',
                        'target-arrow-color': '#f9ab00',
                        'width': 3
                    }}
                }},
                {{
                    selector: 'edge.edge-can_deploy_cloud_run_as',
                    style: {{
                        'line-color': '#f9ab00',
                        'target-arrow-color': '#f9ab00',
                        'width': 3
                    }}
                }},
                {{
                    selector: 'edge.edge-has_role',
                    style: {{
                        'line-color': '#5f6368',
                        'target-arrow-color': '#5f6368'
                    }}
                }}
            ],
            layout: {{
                name: 'dagre',
                rankDir: 'LR',
                nodeSep: 100,
                rankSep: 150,
                padding: 50
            }}
        }});
        
        // Add node icons
        cy.nodes().forEach(function(node) {{
            var icon = node.data('icon');
            if (icon) {{
                node.style('content', icon);
                node.style('text-valign', 'bottom');
                node.style('font-size', '24px');
            }}
        }});
        
        // Download function
        function downloadImage() {{
            var png = cy.png({{
                output: 'blob',
                bg: 'white',
                scale: 2
            }});
            
            var link = document.createElement('a');
            link.href = URL.createObjectURL(png);
            link.download = 'attack_path.png';
            link.click();
        }}
        
        // Add interactivity
        cy.on('tap', 'node', function(evt) {{
            var node = evt.target;
            console.log('Node clicked:', node.data());
        }});
        
        cy.on('tap', 'edge', function(evt) {{
            var edge = evt.target;
            console.log('Edge clicked:', edge.data());
        }});
    </script>
</body>
</html>"""
        
        return html
    
    def _create_techniques_list_html(self, techniques: List[Dict[str, Any]]) -> str:
        """Create HTML for techniques list"""
        html_parts = []
        
        for i, technique in enumerate(techniques, 1):
            html_parts.append(f"""
                <div class="technique-item">
                    <div class="technique-icon">{technique.get('icon', '🔐')}</div>
                    <div class="technique-details">
                        <div class="technique-name">Step {i}: {technique.get('name', 'Unknown')}</div>
                        <div class="technique-description">{technique.get('description', '')}</div>
                        <div class="technique-permission">{technique.get('permission', 'Unknown')}</div>
                    </div>
                </div>
            """)
        
        return '\n'.join(html_parts)
    
    def _get_risk_level(self, risk_score: float) -> str:
        """Get risk level based on score"""
        if risk_score >= 0.8:
            return "critical"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "medium"
        else:
            return "low"
    
    def _get_logo_base64(self) -> str:
        """Get the EscaGCP logo as base64"""
        try:
            # Try to load the logo from the static directory
            import os
            logo_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'images', 'escagcp-logo-vector-no-bg.png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    import base64
                    return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.debug(f"Could not load logo: {e}")
        
        # Return a placeholder if logo not found
        return ""
    
    def _get_inter_font_base64(self) -> str:
        """Get the Inter font as base64"""
        try:
            # Load the Inter variable font from the static directory
            import os
            font_path = os.path.join(os.path.dirname(__file__), '..', 'static', 'Fonts', 'Inter', 'Inter-VariableFont_opsz,wght.ttf')
            if os.path.exists(font_path):
                with open(font_path, 'rb') as f:
                    import base64
                    return base64.b64encode(f.read()).decode('utf-8')
        except Exception as e:
            logger.debug(f"Could not load Inter font: {e}")
        
        # Return empty string if font not found (will fall back to Google Fonts)
        return ""
    
    def _get_inter_font_css(self) -> str:
        """Get the CSS for Inter font with embedded base64 or Google Fonts fallback"""
        font_base64 = self._get_inter_font_base64()
        
        if font_base64:
            # Use embedded font
            return f"""
    @font-face {{
        font-family: 'Inter';
        font-style: normal;
        font-weight: 100 900;
        font-display: swap;
        src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype-variations');
        font-named-instance: 'Regular';
    }}
    
    @font-face {{
        font-family: 'Inter';
        font-style: italic;
        font-weight: 100 900;
        font-display: swap;
        src: url(data:font/truetype;charset=utf-8;base64,{font_base64}) format('truetype-variations');
        font-named-instance: 'Italic';
    }}"""
        else:
            # Fallback to Google Fonts
            return """
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');"""
    
    def _create_react_modal_integration(self) -> str:
        """Create the integration code for React modals"""
        return """
        <!-- React Modal Integration -->
        <script crossorigin src="https://unpkg.com/react@18/umd/react.production.min.js"></script>
        <script crossorigin src="https://unpkg.com/react-dom@18/umd/react-dom.production.min.js"></script>
        <script src="https://unpkg.com/@babel/standalone/babel.min.js"></script>
        
        <style>
            /* Tailwind-like utility classes for React components */
            .flex { display: flex; }
            .flex-col { flex-direction: column; }
            .items-center { align-items: center; }
            .justify-between { justify-content: space-between; }
            .gap-2 { gap: 0.5rem; }
            .gap-3 { gap: 0.75rem; }
            .gap-4 { gap: 1rem; }
            .p-3 { padding: 0.75rem; }
            .rounded-lg { border-radius: 0.5rem; }
            .text-sm { font-size: 0.875rem; font-family: 'Inter', sans-serif; }
            .text-xs { font-size: 0.75rem; font-family: 'Inter', sans-serif; }
            .font-medium { font-weight: 500; }
            .font-semibold { font-weight: 600; }
            .bg-opacity-10 { background-opacity: 0.1; }
            .transition-colors { transition: background-color 0.15s; }
            .cursor-pointer { cursor: pointer; }
            .hover\\:bg-gray-100:hover { background-color: #f3f4f6; }
            .dark\\:hover\\:bg-gray-800:hover { background-color: #1f2937; }
            .text-gray-500 { color: #6b7280; }
            .dark\\:text-gray-400 { color: #9ca3af; }
            .ml-2 { margin-left: 0.5rem; }
            .ml-4 { margin-left: 1rem; }
            .mt-2 { margin-top: 0.5rem; }
            .mb-4 { margin-bottom: 1rem; }
            .w-full { width: 100%; }
            .max-w-4xl { max-width: 56rem; }
            .max-w-5xl { max-width: 64rem; }
            .max-h-\\[80vh\\] { max-height: 80vh; }
            .overflow-y-auto { overflow-y: auto; }
            .space-y-4 > * + * { margin-top: 1rem; }
            
            /* Badge styles */
            .badge {
                display: inline-flex;
                align-items: center;
                padding: 0.125rem 0.5rem;
                border-radius: 0.25rem;
                font-size: 0.75rem;
                font-weight: 500;
            }
            .badge-secondary {
                background-color: #e5e7eb;
                color: #374151;
            }
            .badge-destructive {
                background-color: #fee2e2;
                color: #dc2626;
            }
            .badge-warning {
                background-color: #fef3c7;
                color: #f59e0b;
            }
            
            /* Icon colors */
            .text-blue-500 { color: #3b82f6; }
            .text-green-500 { color: #10b981; }
            .text-red-500 { color: #ef4444; }
            .text-yellow-500 { color: #f59e0b; }
            .text-orange-500 { color: #f97316; }
            .text-purple-500 { color: #8b5cf6; }
            .text-gray-500 { color: #6b7280; }
            .text-indigo-500 { color: #6366f1; }
            
            .bg-blue-500 { background-color: #3b82f6; }
            .bg-green-500 { background-color: #10b981; }
            .bg-red-500 { background-color: #ef4444; }
            .bg-yellow-500 { background-color: #f59e0b; }
            .bg-orange-500 { background-color: #f97316; }
            .bg-purple-500 { background-color: #8b5cf6; }
            .bg-gray-500 { background-color: #6b7280; }
            .bg-indigo-500 { background-color: #6366f1; }
        </style>
        
        <div id="nodes-modal-container"></div>
        <div id="edges-modal-container"></div>
        """
    
    def _get_dashboard_javascript(self) -> str:
        """Get the JavaScript code for the dashboard without double braces"""
        return """
        // Define all functions first
        function showTab(tabName, event) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.add('hidden');
            });
            
            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // Show selected tab
            document.getElementById(tabName + '-tab').classList.remove('hidden');
            
            // Add active class to clicked tab
            if (event && event.target) {
                event.target.classList.add('active');
            }
        }
        
        function showModal(modalType) {
            if (modalType === 'nodes') {
                // Show React nodes modal
                if (window.nodesModalData) {
                    showNodesModal(window.nodesModalData);
                }
            } else if (modalType === 'edges') {
                // Show React edges modal
                if (window.edgesModalData) {
                    showEdgesModal(window.edgesModalData);
                }
            } else {
                // Show regular modal
                document.getElementById(modalType + 'Modal').style.display = 'block';
            }
        }
        
        function closeModal(modalType) {
            document.getElementById(modalType + 'Modal').style.display = 'none';
        }
        
        // React modal functions
        function showNodesModal(nodesData) {
            // Simple modal implementation without full React components
            const container = document.getElementById('nodes-modal-container');
            if (!container) return;
            
            let html = '<div class="modal" style="display: block;">';
            html += '<div class="modal-content" style="max-width: 56rem; max-height: 80vh;">';
            html += '<div class="modal-header">';
            html += '<h2 class="modal-title">Total Nodes</h2>';
            html += '<span class="close" onclick="closeNodesModal()">&times;</span>';
            html += '</div>';
            html += '<div style="padding: 20px; overflow-y: auto; max-height: 70vh;">';
            
            // Add search and filters
            html += '<div class="flex gap-4" style="margin-bottom: 20px;">';
            html += '<input type="text" id="nodes-search" placeholder="Search nodes..." style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" onkeyup="filterNodes()">';
            html += '<select id="nodes-type-filter" onchange="filterNodes()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">';
            html += '<option value="all">All Types</option>';
            Object.keys(nodesData).forEach(type => {
                html += `<option value="${type}">${type}</option>`;
            });
            html += '</select>';
            html += '</div>';
            
            // Add nodes by type
            html += '<div id="nodes-list">';
            Object.entries(nodesData).forEach(([type, nodes]) => {
                html += `<div class="node-type-section" data-type="${type}">`;
                html += `<h3 style="margin: 20px 0 10px 0; font-weight: 600;">${type} (${nodes.length})</h3>`;
                nodes.forEach(node => {
                    html += `<div class="node-item" data-search="${node.name.toLowerCase()} ${node.id.toLowerCase()}" style="padding: 10px; margin: 5px 0; background: #f5f5f5; border-radius: 4px; cursor: pointer;" onclick="highlightNode('${node.id}')">`;
                    html += `<div style="font-weight: 500;">${node.name}</div>`;
                    html += `<div style="font-size: 12px; color: #666;">ID: ${node.id} | In: ${node.inDegree} | Out: ${node.outDegree}</div>`;
                    if (node.metadata && Object.keys(node.metadata).length > 0) {
                        html += '<div style="font-size: 11px; color: #888; margin-top: 4px;">';
                        Object.entries(node.metadata).forEach(([key, value]) => {
                            html += `${key}: ${value} `;
                        });
                        html += '</div>';
                    }
                    html += '</div>';
                });
                html += '</div>';
            });
            html += '</div>';
            
            html += '</div>';
            html += '</div>';
            html += '</div>';
            
            container.innerHTML = html;
        }
        
        function showEdgesModal(edgesData) {
            // Simple modal implementation without full React components
            const container = document.getElementById('edges-modal-container');
            if (!container) return;
            
            let html = '<div class="modal" style="display: block;">';
            html += '<div class="modal-content" style="max-width: 64rem; max-height: 80vh;">';
            html += '<div class="modal-header">';
            html += '<h2 class="modal-title">Total Edges</h2>';
            html += '<span class="close" onclick="closeEdgesModal()">&times;</span>';
            html += '</div>';
            html += '<div style="padding: 20px; overflow-y: auto; max-height: 70vh;">';
            
            // Add search and filters
            html += '<div class="flex gap-4" style="margin-bottom: 20px;">';
            html += '<input type="text" id="edges-search" placeholder="Search edges..." style="flex: 1; padding: 8px; border: 1px solid #ddd; border-radius: 4px;" onkeyup="filterEdges()">';
            html += '<select id="edges-type-filter" onchange="filterEdges()" style="padding: 8px; border: 1px solid #ddd; border-radius: 4px;">';
            html += '<option value="all">All Types</option>';
            Object.keys(edgesData).forEach(type => {
                html += `<option value="${type}">${type}</option>`;
            });
            html += '</select>';
            html += '</div>';
            
            // Add edges by type
            html += '<div id="edges-list">';
            Object.entries(edgesData).forEach(([type, edges]) => {
                html += `<div class="edge-type-section" data-type="${type}">`;
                html += `<h3 style="margin: 20px 0 10px 0; font-weight: 600;">${type} (${edges.length})</h3>`;
                edges.forEach(edge => {
                    const searchText = `${edge.sourceName} ${edge.targetName} ${edge.type}`.toLowerCase();
                    html += `<div class="edge-item" data-search="${searchText}" style="padding: 10px; margin: 5px 0; background: #f5f5f5; border-radius: 4px;">`;
                    html += `<div style="font-weight: 500;">${edge.sourceName} → ${edge.targetName}</div>`;
                    html += `<div style="font-size: 12px; color: #666;">Type: ${edge.type}</div>`;
                    if (edge.permission) {
                        html += `<div style="font-size: 11px; color: #888;">Permission: ${edge.permission}</div>`;
                    }
                    if (edge.rationale) {
                        html += `<div style="font-size: 11px; color: #888;">Rationale: ${edge.rationale}</div>`;
                    }
                    html += '</div>';
                });
                html += '</div>';
            });
            html += '</div>';
            
            html += '</div>';
            html += '</div>';
            html += '</div>';
            
            container.innerHTML = html;
        }
        
        function closeNodesModal() {
            const container = document.getElementById('nodes-modal-container');
            if (container) container.innerHTML = '';
        }
        
        function closeEdgesModal() {
            const container = document.getElementById('edges-modal-container');
            if (container) container.innerHTML = '';
        }
        
        function filterNodes() {
            const searchTerm = document.getElementById('nodes-search').value.toLowerCase();
            const typeFilter = document.getElementById('nodes-type-filter').value;
            
            document.querySelectorAll('.node-type-section').forEach(section => {
                const sectionType = section.getAttribute('data-type');
                if (typeFilter !== 'all' && sectionType !== typeFilter) {
                    section.style.display = 'none';
                } else {
                    section.style.display = 'block';
                    
                    let hasVisibleNodes = false;
                    section.querySelectorAll('.node-item').forEach(item => {
                        const searchData = item.getAttribute('data-search');
                        if (searchData.includes(searchTerm)) {
                            item.style.display = 'block';
                            hasVisibleNodes = true;
                        } else {
                            item.style.display = 'none';
                        }
                    });
                    
                    if (!hasVisibleNodes && searchTerm) {
                        section.style.display = 'none';
                    }
                }
            });
        }
        
        function filterEdges() {
            const searchTerm = document.getElementById('edges-search').value.toLowerCase();
            const typeFilter = document.getElementById('edges-type-filter').value;
            
            document.querySelectorAll('.edge-type-section').forEach(section => {
                const sectionType = section.getAttribute('data-type');
                if (typeFilter !== 'all' && sectionType !== typeFilter) {
                    section.style.display = 'none';
                } else {
                    section.style.display = 'block';
                    
                    let hasVisibleEdges = false;
                    section.querySelectorAll('.edge-item').forEach(item => {
                        const searchData = item.getAttribute('data-search');
                        if (searchData.includes(searchTerm)) {
                            item.style.display = 'block';
                            hasVisibleEdges = true;
                        } else {
                            item.style.display = 'none';
                        }
                    });
                    
                    if (!hasVisibleEdges && searchTerm) {
                        section.style.display = 'none';
                    }
                }
            });
        }
        
        function highlightNode(nodeId) {
            // Highlight node in the graph
            if (window.graphNetwork) {
                window.graphNetwork.selectNodes([nodeId]);
                window.graphNetwork.focus(nodeId, {
                    scale: 1.5,
                    animation: {
                        duration: 1000,
                        easingFunction: 'easeInOutQuad'
                    }
                });
            }
        }
        
        function toggleCollapsible(element) {
            element.classList.toggle('active');
            const content = element.nextElementSibling;
            if (content.classList.contains('show')) {
                content.classList.remove('show');
            } else {
                content.classList.add('show');
            }
        }
        
        function showShareModal() {
            document.getElementById('shareModal').style.display = 'block';
            document.getElementById('shareLoading').style.display = 'none';
            document.getElementById('shareSuccess').style.display = 'none';
        }
        
        function closeShareModal() {
            document.getElementById('shareModal').style.display = 'none';
        }
        
        function toggleSection(sectionId) {
            const content = document.getElementById(sectionId);
            const arrow = event.target.querySelector('.arrow') || event.target;
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                arrow.textContent = '▼';
            } else {
                content.style.display = 'none';
                arrow.textContent = '▶';
            }
        }
        
        function generateStandaloneReport() {
            document.getElementById('shareLoading').style.display = 'block';
            
            try {
                // Create the standalone HTML content using the embedded data
                const standaloneHTML = createStandaloneHTML();
                
                // Create a blob and download it
                const blob = new Blob([standaloneHTML], { type: 'text/html' });
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'escagcp_report_' + new Date().toISOString().slice(0, 10) + '.html';
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
                
                // Show success message
                document.getElementById('shareLoading').style.display = 'none';
                document.getElementById('shareSuccess').style.display = 'block';
                
                // Close modal after 3 seconds
                setTimeout(() => {
                    closeShareModal();
                }, 3000);
            } catch (error) {
                console.error('Failed to generate report:', error);
                document.getElementById('shareLoading').innerHTML = 'Failed to generate report. Please try again.';
            }
        }
        
        function createStandaloneHTML() {
            // Build the standalone HTML using the embedded data
            const html = `<!DOCTYPE html>
<html>
<head>
    <title>EscaGCP Security Report - Standalone</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js"><\/script>
    <style>
        body {
            margin: 0;
            padding: 0;
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background-color: #f8f9fa;
            color: #1a1f36;
            line-height: 1.6;
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
            height: 600px;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            margin: 20px 0;
            background-color: #222222;
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
        
        @media (max-width: 768px) {
            .standalone-stats {
                flex-direction: column;
                gap: 10px;
            }
            
            .info-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="standalone-header">
        <h1 class="standalone-title">EscaGCP Security Report</h1>
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
        <p>This is a standalone EscaGCP report. All data is embedded in this HTML file.</p>
        <p>No external dependencies or internet connection required.</p>
    </div>
    
    <script>
        // Embed the graph data
        const graphData = ${JSON.stringify(graphData)};
        
        // Initialize the network
        const container = document.getElementById('mynetwork');
        const data = {
            nodes: new vis.DataSet(graphData.nodes),
            edges: new vis.DataSet(graphData.edges)
        };
        
        const options = {
            physics: {
                enabled: true,
                solver: "barnesHut",
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.1
                },
                stabilization: {
                    enabled: true,
                    iterations: 1000,
                    updateInterval: 100,
                    onlyDynamicEdges: false,
                    fit: true
                },
                timestep: 0.5,
                adaptiveTimestep: true
            },
            interaction: {
                hover: true,
                tooltipDelay: 200,
                hideEdgesOnDrag: true,
                navigationButtons: true,
                keyboard: true,
                zoomView: true,
                dragView: true
            },
            nodes: {
                borderWidth: 2,
                borderWidthSelected: 4,
                font: {
                    color: '#ffffff',
                    size: 14,
                    face: 'Inter, sans-serif',
                    strokeWidth: 3,
                    strokeColor: '#000000'
                }
            },
            edges: {
                smooth: {
                    type: "continuous",
                    forceDirection: "none",
                    roundness: 0.5
                },
                arrows: {
                    to: {
                        enabled: true,
                        scaleFactor: 0.5
                    }
                },
                font: {
                    color: '#ffffff',
                    size: 10,
                    face: 'Inter, sans-serif',
                    strokeWidth: 3,
                    strokeColor: '#000000',
                    align: 'middle'
                },
                labelHighlightBold: true
            },
            layout: {
                improvedLayout: true,
                hierarchical: false
            }
        };
        
        const network = new vis.Network(container, data, options);
        
        // Stop physics after stabilization to prevent dancing
        network.on("stabilizationIterationsDone", function () {
            network.setOptions({ physics: false });
        });
    <\/script>
</body>
</html>`;
            return html;
        }
        
        function _clean_node_name(name) {
            // Clean node name for display
            if (name && name.includes(':')) {
                const parts = name.split(':', 2);
                if (parts.length === 2) {
                    return parts[1];
                }
            }
            return name || '';
        }
        
        function extractSourceTarget(pathStr) {
            // Extract source and target from path string
            if (!pathStr) return { source: 'Unknown', target: 'Unknown' };
            
            // Try different patterns
            // Pattern 1: "source -> target"
            let match = pathStr.match(/^([^-]+)\s*->\s*(.+)$/);
            if (match) {
                return { 
                    source: _clean_node_name(match[1].trim()), 
                    target: _clean_node_name(match[2].trim()) 
                };
            }
            
            // Pattern 2: "Attack path from source to target"
            match = pathStr.match(/from\s+([^\s]+)\s+to\s+([^\s]+)/i);
            if (match) {
                return { 
                    source: _clean_node_name(match[1]), 
                    target: _clean_node_name(match[2]) 
                };
            }
            
            // Pattern 3: Just take first and last word
            const words = pathStr.split(/\s+/);
            if (words.length >= 2) {
                return { 
                    source: _clean_node_name(words[0]), 
                    target: _clean_node_name(words[words.length - 1]) 
                };
            }
            
            return { source: 'Unknown', target: 'Unknown' };
        }
        
        function showMoreHolders(roleId) {
            const moreBtn = document.getElementById('more-btn-' + roleId);
            const moreHolders = document.getElementById('more-holders-' + roleId);
            
            if (moreHolders.style.display === 'none') {
                moreHolders.style.display = 'block';
                moreBtn.textContent = 'Show less';
            } else {
                moreHolders.style.display = 'none';
                const count = moreBtn.textContent.match(/\d+/);
                moreBtn.textContent = '+' + count + ' more';
            }
        }
        
        function showMorePaths(categoryId, currentLimit, totalPaths) {
            const morePathsContainer = document.getElementById('more-paths-' + categoryId);
            const showMoreLink = document.getElementById('show-more-' + categoryId);
            
            if (!morePathsContainer || !showMoreLink) {
                console.error('Container or link not found for category:', categoryId);
                return;
            }
            
            // Get all hidden paths in this category
            const allHiddenPaths = morePathsContainer.querySelectorAll('.attack-path-card');
            let shown = 0;
            let totalShown = currentLimit;
            
            // Count currently visible paths and show next 10
            allHiddenPaths.forEach(path => {
                if (path.style.display !== 'none' && path.style.display !== '') {
                    totalShown++;
                } else if (shown < 10) {
                    // Show this path
                    path.style.display = 'block';
                    shown++;
                    totalShown++;
                }
            });
            
            // Update or hide the show more link
            const remaining = totalPaths - totalShown;
            if (remaining > 0) {
                showMoreLink.textContent = '... and ' + remaining + ' more';
            } else {
                showMoreLink.style.display = 'none';
            }
        }
        
        function showAttackPath(pathIndex, event) {
            if (event) event.stopPropagation();
            
            console.log('showAttackPath called with index:', pathIndex);
            console.log('Attack paths array:', attackPaths);
            
            // Get the attack path data
            const path = attackPaths[pathIndex];
            if (!path) {
                console.error('Attack path not found:', pathIndex);
                return;
            }
            
            console.log('Attack path data:', path);
            
            // Always show the attack path modal, even without full visualization metadata
            showAttackPathModal(path);
        }
        
        function showAttackPathModal(pathData) {
            console.log('Attack path data:', pathData);
            
            // Create or update the attack path modal
            let modal = document.getElementById('attackPathModal');
            if (!modal) {
                // Create modal if it doesn't exist
                modal = document.createElement('div');
                modal.id = 'attackPathModal';
                modal.className = 'modal';
                modal.style.cssText = 'display: none; position: fixed; z-index: 10000; left: 0; top: 0; width: 100%; height: 100%; overflow: auto; background-color: rgba(0,0,0,0.8);';
                document.body.appendChild(modal);
            }
            
            // Extract visualization data - handle both formats
            const vizData = pathData.visualization_metadata || {};
            let nodeMetadata = vizData.node_metadata || [];
            let edgeMetadata = vizData.edge_metadata || [];
            const techniques = vizData.techniques || vizData.escalation_techniques || [];
            
            // If no visualization metadata, try to construct from path data
            if (nodeMetadata.length === 0 && pathData.path_nodes) {
                nodeMetadata = pathData.path_nodes.map((node, idx) => ({
                    id: node.id || node,
                    label: node.name || node.id || node,
                    type: node.type || 'unknown',
                    color: '#6b46c1',
                    risk_level: idx === 0 ? 'source' : idx === pathData.path_nodes.length - 1 ? 'target' : 'intermediate'
                }));
            }
            
            if (edgeMetadata.length === 0 && pathData.path_edges) {
                edgeMetadata = pathData.path_edges.map((edge, idx) => ({
                    source: edge.source_id || edge.source || pathData.path_nodes[idx].id,
                    target: edge.target_id || edge.target || pathData.path_nodes[idx + 1].id,
                    label: edge.type || 'connects to',
                    type: edge.type || 'unknown',
                    risk_score: edge.risk_score || 0.5
                }));
            }
            
            // If still no nodes, create a simple path visualization
            if (nodeMetadata.length === 0) {
                // Try to extract from path string
                if (pathData.path && pathData.path.includes('--[')) {
                    const parts = pathData.path.split(/\s*--\[|\]-->\s*/);
                    for (let i = 0; i < parts.length; i += 2) {
                        if (parts[i]) {
                            nodeMetadata.push({
                                id: `node-${i}`,
                                label: parts[i].trim(),
                                type: 'unknown',
                                color: '#6b46c1',
                                risk_level: i === 0 ? 'source' : i >= parts.length - 2 ? 'target' : 'intermediate'
                            });
                            
                            if (i < parts.length - 2 && parts[i + 1]) {
                                edgeMetadata.push({
                                    source: `node-${i}`,
                                    target: `node-${i + 2}`,
                                    label: parts[i + 1].trim(),
                                    type: parts[i + 1].trim(),
                                    risk_score: 0.7
                                });
                            }
                        }
                    }
                } else {
                    // Fallback: create minimal visualization
                    nodeMetadata = [
                        { id: 'source', label: 'Source', type: 'unknown', color: '#6b46c1', risk_level: 'source' },
                        { id: 'target', label: 'Target', type: 'unknown', color: '#dc2626', risk_level: 'target' }
                    ];
                    edgeMetadata = [
                        { source: 'source', target: 'target', label: 'Attack Path', type: 'unknown', risk_score: pathData.risk_score || 0.5 }
                    ];
                }
            }
            
            console.log('Visualization data:', vizData);
            console.log('Nodes:', nodeMetadata);
            console.log('Edges:', edgeMetadata);
            console.log('Techniques:', techniques);
            
            // Convert nodes to vis.js format
            const visNodes = nodeMetadata.map((node, index) => {
                console.log(`Processing node ${index}:`, node);
                const visNode = {
                    id: node.id,
                    label: node.label || node.id,
                    title: `<div style="padding: 10px;">
                        <strong>${node.label || node.id}</strong><br>
                        Type: ${node.type}<br>
                        Risk: ${node.risk_level || 'unknown'}
                    </div>`,
                    shape: 'box',
                    color: {
                        background: node.color || '#6b46c1',
                        border: node.risk_level === 'critical' ? '#dc2626' : 
                               node.risk_level === 'high' ? '#f59e0b' : '#6b46c1',
                        highlight: {
                            background: '#8b5cf6',
                            border: '#6b46c1'
                        }
                    },
                    borderWidth: node.risk_level === 'critical' || node.risk_level === 'high' ? 3 : 2,
                    font: {
                        color: '#ffffff',
                        face: 'Inter, sans-serif'
                    },
                    level: index  // Add level for hierarchical layout
                };
                console.log(`Created vis node:`, visNode);
                return visNode;
            });
            
            // Convert edges to vis.js format
            const visEdges = edgeMetadata.map((edge, index) => {
                console.log(`Processing edge ${index}:`, edge);
                const visEdge = {
                    from: edge.source,
                    to: edge.target,
                    label: edge.label || edge.type || '',
                    title: `<div style="padding: 10px;">
                        <strong>${edge.label || edge.type || 'Connection'}</strong><br>
                        Risk Score: ${(edge.risk_score || 0).toFixed(2)}
                    </div>`,
                    arrows: {
                        to: {
                            enabled: true,
                            scaleFactor: 1
                        }
                    },
                    color: {
                        color: edge.risk_score > 0.8 ? '#dc2626' :
                               edge.risk_score > 0.6 ? '#f59e0b' : '#6b46c1',
                        highlight: '#8b5cf6'
                    },
                    width: edge.risk_score > 0.8 ? 3 : 2,
                    font: {
                        color: '#ffffff',
                        strokeWidth: 3,
                        strokeColor: '#1a1a1a',
                        face: 'Inter, sans-serif',
                        size: 12
                    }
                };
                console.log(`Created vis edge:`, visEdge);
                return visEdge;
            });
            
            modal.innerHTML = `
                <div class="modal-content" style="background-color: #1a1a1a; margin: 2% auto; padding: 20px; width: 90%; max-width: 1200px; border-radius: 8px; position: relative;">
                    <div class="modal-header" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                        <h2 class="modal-title" style="color: #fff; margin: 0;">Attack Path Visualization</h2>
                        <span class="close" onclick="document.getElementById('attackPathModal').style.display='none'" style="color: #aaa; font-size: 28px; font-weight: bold; cursor: pointer;">&times;</span>
                    </div>
                    <div style="display: grid; grid-template-columns: 1fr 350px; gap: 20px; height: 600px;">
                        <div style="position: relative; background-color: #222; border: 1px solid #444; border-radius: 4px; min-height: 500px;">
                            <div id="attackPathNetwork" style="width: 100%; height: 100%; min-height: 500px;"></div>
                        </div>
                        <div style="background-color: #2a2a2a; border: 1px solid #444; border-radius: 4px; padding: 15px; overflow-y: auto;">
                            <h3 style="color: #fff; margin-top: 0;">Path Details</h3>
                            <div style="color: #ccc; font-size: 14px;">
                                <p><strong>Risk Score:</strong> <span style="color: ${pathData.risk_score > 0.8 ? '#dc2626' : pathData.risk_score > 0.6 ? '#f59e0b' : '#22c55e'}">${(pathData.risk_score || 0).toFixed(2)}</span></p>
                                <p><strong>Path Length:</strong> ${pathData.length || 0} steps</p>
                                ${pathData.description ? `<p><strong>Description:</strong><br>${pathData.description}</p>` : ''}
                                
                                ${techniques.length > 0 ? `
                                    <h4 style="color: #fff; margin-top: 20px;">Attack Techniques:</h4>
                                    <div style="display: flex; flex-direction: column; gap: 10px;">
                                        ${techniques.map(t => `
                                            <div style="background: #333; padding: 10px; border-radius: 4px; border-left: 3px solid #6b46c1;">
                                                <div style="font-weight: 600; margin-bottom: 4px;">${t.icon || '🔐'} ${t.name || t.technique || 'Unknown'}</div>
                                                ${t.description ? `<div style="font-size: 12px; color: #999; margin-bottom: 4px;">${t.description}</div>` : ''}
                                                ${t.permission ? `<div style="font-size: 11px; font-family: monospace; color: #22c55e;">${t.permission}</div>` : ''}
                                            </div>
                                        `).join('')}
                                    </div>
                                ` : ''}
                                
                                ${vizData.permissions_used && vizData.permissions_used.length > 0 ? `
                                    <h4 style="color: #fff; margin-top: 20px;">Permissions Used:</h4>
                                    <ul style="padding-left: 20px; font-size: 12px; font-family: monospace;">
                                        ${vizData.permissions_used.map(p => `<li style="color: #22c55e;">${p}</li>`).join('')}
                                    </ul>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            // Show modal
            modal.style.display = 'block';
            console.log('Modal displayed, style:', modal.style.display);
            console.log('Modal dimensions:', modal.offsetWidth, 'x', modal.offsetHeight);
            
            // Function to create the attack path network
            const createAttackPathNetwork = () => {
                const container = document.getElementById('attackPathNetwork');
                console.log('Container found:', !!container);
                console.log('Nodes to visualize:', visNodes.length);
                console.log('Edges to visualize:', visEdges.length);
                console.log('vis object available:', typeof vis !== 'undefined');
                console.log('vis.DataSet available:', typeof vis !== 'undefined' && typeof vis.DataSet !== 'undefined');
                console.log('vis.Network available:', typeof vis !== 'undefined' && typeof vis.Network !== 'undefined');
                
                if (!container) {
                    console.error('Container not found');
                    return;
                }
                
                if (visNodes.length === 0) {
                    console.warn('No nodes found, creating test data');
                    // Create test data to verify vis.js works
                    visNodes.push(
                        {id: 'test1', label: 'Test Node 1', color: '#6b46c1', shape: 'box'},
                        {id: 'test2', label: 'Test Node 2', color: '#34A853', shape: 'box'}
                    );
                    visEdges.push(
                        {from: 'test1', to: 'test2', label: 'Test Edge', arrows: {to: {enabled: true}}}
                    );
                }
                
                // Clear any existing network
                container.innerHTML = '';
                
                // Check if vis is available
                if (typeof vis === 'undefined') {
                    console.error('vis.js library not loaded, attempting to load dynamically');
                    
                    // Try to load vis.js dynamically
                    const script = document.createElement('script');
                    script.src = 'https://unpkg.com/vis-network@9.1.2/dist/vis-network.min.js';
                    script.onload = () => {
                        console.log('vis.js loaded dynamically');
                        // Retry creating the network after vis.js loads
                        createAttackPathNetwork();
                    };
                    script.onerror = () => {
                        console.error('Failed to load vis.js dynamically');
                        container.innerHTML = '<div style="color: #ff6b6b; text-align: center; padding: 50px;">Error: Failed to load visualization library. Please refresh the page.</div>';
                    };
                    document.head.appendChild(script);
                    return;
                }
                
                try {
                    console.log('Creating vis.DataSet with nodes:', visNodes);
                    console.log('Creating vis.DataSet with edges:', visEdges);
                    
                    const nodesDataSet = new vis.DataSet(visNodes);
                    const edgesDataSet = new vis.DataSet(visEdges);
                    
                    console.log('Nodes DataSet created:', nodesDataSet);
                    console.log('Edges DataSet created:', edgesDataSet);
                    
                    const data = {
                        nodes: nodesDataSet,
                        edges: edgesDataSet
                    };
                    
                    console.log('Data object created:', data);
                    
                    const options = {
                        physics: {
                            enabled: true,
                            solver: "barnesHut",
                            barnesHut: {
                                gravitationalConstant: -2000,
                                centralGravity: 0.3,
                                springLength: 95,
                                springConstant: 0.04,
                                damping: 0.09,
                                avoidOverlap: 0.5
                            },
                            stabilization: {
                                enabled: true,
                                iterations: 200,
                                updateInterval: 10
                            }
                        },
                        interaction: {
                            hover: true,
                            tooltipDelay: 200,
                            navigationButtons: true,
                            keyboard: true
                        },
                        layout: {
                            improvedLayout: false,
                            hierarchical: false  // Disable hierarchical layout for now
                        },
                        nodes: {
                            font: {
                                face: "Inter, sans-serif",
                                size: 14,
                                color: "#ffffff"
                            },
                            borderWidth: 2,
                            borderWidthSelected: 4
                        },
                        edges: {
                            smooth: {
                                type: "continuous",
                                roundness: 0.5
                            },
                            arrows: {
                                to: {
                                    enabled: true,
                                    scaleFactor: 1
                                }
                            },
                            font: {
                                face: "Inter, sans-serif",
                                size: 12,
                                color: "#ffffff",
                                strokeWidth: 3,
                                strokeColor: "#1a1a1a"
                            }
                        },
                        height: '100%',
                        width: '100%',
                        autoResize: true
                    };
                    
                    console.log('Creating vis.Network with container:', container);
                    console.log('Container dimensions:', container.offsetWidth, 'x', container.offsetHeight);
                    console.log('Container client dimensions:', container.clientWidth, 'x', container.clientHeight);
                    console.log('Container computed style:', window.getComputedStyle(container).width, 'x', window.getComputedStyle(container).height);
                    console.log('Options:', options);
                    
                    // Ensure container has dimensions
                    if (container.offsetWidth === 0 || container.offsetHeight === 0) {
                        console.warn('Container has zero dimensions, setting explicit size');
                        container.style.width = '800px';
                        container.style.height = '500px';
                    }
                    
                    const network = new vis.Network(container, data, options);
                    
                    console.log('Network created:', network);
                    
                    // Store network instance for debugging
                    window.attackPathNetwork = network;
                    
                    // Fit the network after stabilization
                    network.once('stabilizationIterationsDone', function () {
                        network.fit({
                            animation: {
                                duration: 500,
                                easingFunction: 'easeInOutQuad'
                            }
                        });
                    });
                    
                    // Add resize handler
                    const resizeObserver = new ResizeObserver(() => {
                        network.redraw();
                        network.fit();
                    });
                    resizeObserver.observe(container);
                    
                    // Clean up observer when modal closes
                    const modalElement = document.getElementById('attackPathModal');
                    const observer = new MutationObserver((mutations) => {
                        mutations.forEach((mutation) => {
                            if (mutation.attributeName === 'style' && modalElement.style.display === 'none') {
                                resizeObserver.disconnect();
                            }
                        });
                    });
                    observer.observe(modalElement, { attributes: true });
                    
                    console.log('Network created successfully');
                } catch (error) {
                    console.error('Error creating network:', error);
                    container.innerHTML = '<div style="color: #ff6b6b; text-align: center; padding: 50px;">Error creating visualization: ' + error.message + '</div>';
                }
            };
            
            // Call the function after a short delay to ensure DOM is ready
            setTimeout(() => {
                // Force a reflow to ensure modal is rendered
                modal.offsetHeight;
                createAttackPathNetwork();
            }, 200);
        }
        
        // Sidebar resizer functionality
        function initSidebarResizer() {
            const sidebar = document.querySelector('.sidebar');
            const resizer = document.querySelector('.sidebar-resizer');
            
            if (!sidebar || !resizer) {
                console.error('Sidebar or resizer not found');
                return;
            }
            
            let isResizing = false;
            let startX = 0;
            let startWidth = 0;
            
            resizer.addEventListener('mousedown', (e) => {
                isResizing = true;
                startX = e.clientX;
                startWidth = sidebar.offsetWidth;
                resizer.classList.add('resizing');
                document.body.style.cursor = 'col-resize';
                document.body.style.userSelect = 'none'; // Prevent text selection while dragging
                e.preventDefault();
            });
            
            document.addEventListener('mousemove', (e) => {
                if (!isResizing) return;
                
                // Calculate new width (sidebar is on the right, so we subtract)
                const width = startWidth - (e.clientX - startX);
                
                // Constrain width between min and max
                if (width >= 300 && width <= 800) {
                    sidebar.style.width = width + 'px';
                    
                    // Trigger a resize event for the graph to adjust
                    if (window.graphNetwork) {
                        window.graphNetwork.redraw();
                    }
                }
            });
            
            document.addEventListener('mouseup', () => {
                if (isResizing) {
                    isResizing = false;
                    resizer.classList.remove('resizing');
                    document.body.style.cursor = '';
                    document.body.style.userSelect = ''; // Re-enable text selection
                    
                    // Final redraw of the graph
                    if (window.graphNetwork) {
                        window.graphNetwork.fit();
                    }
                }
            });
        }
        
        """