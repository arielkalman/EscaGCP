"""
Command-line interface for EscaGCP
"""

import click
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Any
from .utils import get_logger, AuthManager, Config
from .collectors import CollectionOrchestrator, LogsCollector
from .graph import GraphBuilder, GraphQuery, GraphExporter
from .analyzers import PathAnalyzer
from .visualizers import HTMLVisualizer, GraphMLVisualizer


logger = get_logger(__name__)


@click.group()
@click.option('--config', '-c', type=click.Path(exists=True), help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """EscaGCP - Map GCP IAM relationships and discover attack paths"""
    # Load configuration
    config_path = config or 'config/default.yaml'
    ctx.obj = Config.from_yaml(config_path)
    logger.info("EscaGCP initialized")


@cli.command()
@click.option('--organization', '-o', help='Organization ID to scan')
@click.option('--folders', '-f', multiple=True, help='Folder IDs to scan')
@click.option('--projects', '-p', multiple=True, help='Project IDs to scan')
@click.option('--output', '-O', default='data/', help='Output directory')
@click.option('--include-logs', is_flag=True, help='Include audit log collection')
@click.option('--log-days', default=7, help='Days of audit logs to collect')
@click.pass_obj
def collect(config, organization, folders, projects, output, include_logs, log_days):
    """Collect data from GCP APIs"""
    try:
        # Initialize auth
        auth_manager = AuthManager(config)
        auth_manager.authenticate()
        
        # Initialize orchestrator
        orchestrator = CollectionOrchestrator(auth_manager, config)
        
        # Collect data
        logger.info("Starting data collection...")
        collected_data = orchestrator.collect_all(
            organization_id=organization,
            folder_ids=list(folders) if folders else None,
            project_ids=list(projects) if projects else None,
            output_dir=output
        )
        
        # Collect audit logs if requested
        if include_logs:
            logger.info("Collecting audit logs...")
            logs_collector = LogsCollector(auth_manager, config)
            
            # Get project list from collected data
            project_ids = list(collected_data['data']['hierarchy']['data']['projects'].keys())
            
            logs_data = logs_collector.collect(
                project_ids=project_ids,
                days_back=log_days
            )
            
            # Add to collected data
            collected_data['data']['logs'] = logs_data
            
            # Save logs separately
            logs_file = Path(output) / f"escagcp_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(logs_file, 'w') as f:
                json.dump(logs_data, f, indent=2, default=str)
        
        # Print summary
        summary = orchestrator.get_collection_summary()
        click.echo(f"\nCollection completed in {summary['duration_seconds']:.2f} seconds")
        click.echo(f"Projects collected: {summary['stats'].get('total_projects', 0)}")
        click.echo(f"Total errors: {summary['total_errors']}")
        
        if summary['total_errors'] > 0:
            click.echo("\nErrors encountered:")
            for error in collected_data['metadata']['errors'][:5]:
                click.echo(f"  - {error}")
        
    except Exception as e:
        logger.error(f"Collection failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--input', '-i', default='data/', help='Input directory with collected data')
@click.option('--output', '-o', default='graph/', help='Output directory for graph')
@click.pass_obj
def build_graph(config, input, output):
    """Build graph from collected data"""
    try:
        # Find latest collection file
        input_path = Path(input)
        collection_files = list(input_path.glob('escagcp_complete_*.json'))
        
        if not collection_files:
            click.echo("No collection data found. Run 'collect' first.")
            sys.exit(1)
        
        latest_file = max(collection_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"Loading data from: {latest_file}")
        
        # Load data
        with open(latest_file, 'r') as f:
            collected_data = json.load(f)
        
        # Extract just the data portion (not metadata)
        if 'data' in collected_data:
            data_to_build = collected_data['data']
        else:
            # Fallback for older format
            data_to_build = collected_data
        
        # Build graph
        builder = GraphBuilder(config)
        graph = builder.build_from_collected_data(data_to_build)
        
        # Export graph
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        exporter = GraphExporter(graph, builder.get_nodes(), config)
        
        # Export to multiple formats
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # GraphML
        graphml_file = output_path / f"escagcp_graph_{timestamp}.graphml"
        exporter.export_graphml(str(graphml_file))
        
        # JSON
        json_file = output_path / f"escagcp_graph_{timestamp}.json"
        exporter.export_json(str(json_file))
        
        # Metadata
        metadata = builder.get_metadata()
        click.echo(f"\nGraph built successfully:")
        click.echo(f"  Nodes: {metadata.total_nodes}")
        click.echo(f"  Edges: {metadata.total_edges}")
        click.echo(f"  Projects: {len(metadata.gcp_projects)}")
        
    except Exception as e:
        logger.error(f"Graph building failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--graph', '-g', help='Graph file path or pattern (e.g., graph/*.json)')
@click.option('--output', '-o', default='findings/', help='Output directory')
@click.option('--format', type=click.Choice(['json', 'html', 'text']), default='json')
@click.option('--visualize-attack-paths', is_flag=True, help='Generate individual visualizations for each attack path')
@click.pass_obj
def analyze(config, graph, output, format, visualize_attack_paths):
    """Analyze graph for attack paths"""
    try:
        # Handle graph file selection
        if graph:
            # If a specific file is provided
            graph_path = Path(graph)
            if graph_path.exists() and graph_path.is_file():
                graph_file = graph_path
            else:
                # Try to interpret as a pattern
                if '*' in graph:
                    # It's a pattern
                    pattern = graph
                else:
                    # Maybe it's a directory
                    pattern = str(Path(graph) / 'escagcp_graph_*.json')
                
                graph_files = list(Path('.').glob(pattern))
                if not graph_files:
                    click.echo(f"No graph files found matching pattern: {pattern}")
                    sys.exit(1)
                
                # Use the latest file
                graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
                click.echo(f"Using latest graph file: {graph_file}")
        else:
            # No graph specified, look in default location
            graph_files = list(Path('graph').glob('escagcp_graph_*.json'))
            if not graph_files:
                click.echo("No graph files found. Run 'escagcp build-graph' first.")
                sys.exit(1)
            
            # Use the latest file
            graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
            click.echo(f"Using latest graph file: {graph_file}")
        
        # Load graph
        with open(graph_file, 'r') as f:
            graph_data = json.load(f)
        
        # Rebuild graph
        builder = GraphBuilder(config)
        nx_graph = builder.graph
        
        # Load nodes and edges
        for node_data in graph_data['nodes']:
            nx_graph.add_node(node_data['id'], **node_data)
        
        for edge_data in graph_data['edges']:
            # Combine type with properties
            edge_attrs = edge_data.get('properties', {}).copy()
            edge_attrs['type'] = edge_data.get('type')
            
            nx_graph.add_edge(
                edge_data['source'],
                edge_data['target'],
                **edge_attrs
            )
        
        # Analyze
        analyzer = PathAnalyzer(nx_graph, config)
        results = analyzer.analyze_all_paths()
        
        # Save results
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'json':
            output_file = output_path / f"escagcp_analysis_{timestamp}.json"
            # Convert attack paths to dictionaries to preserve visualization metadata
            serializable_results = results.copy()
            serializable_results['attack_paths'] = {}
            for category, paths in results['attack_paths'].items():
                serializable_results['attack_paths'][category] = []
                for path in paths:
                    if hasattr(path, 'to_dict'):
                        serializable_results['attack_paths'][category].append(path.to_dict())
                    else:
                        serializable_results['attack_paths'][category].append(str(path))
            
            with open(output_file, 'w') as f:
                json.dump(serializable_results, f, indent=2, default=str)
        
        elif format == 'html':
            # Create HTML report
            output_file = output_path / f"escagcp_analysis_{timestamp}.html"
            _create_html_report(results, output_file)
        
        elif format == 'text':
            output_file = output_path / f"escagcp_analysis_{timestamp}.txt"
            _create_text_report(results, output_file)
        
        # Print summary
        stats = results['statistics']
        click.echo(f"\nAnalysis completed:")
        click.echo(f"  Total attack paths: {stats['total_attack_paths']}")
        click.echo(f"  Critical nodes: {stats['critical_nodes']}")
        click.echo(f"  Vulnerabilities: {stats['vulnerabilities']}")
        click.echo(f"  High-risk nodes: {stats['high_risk_nodes']}")
        
        # Show top paths
        critical_paths = results['attack_paths'].get('critical', [])
        if critical_paths:
            click.echo("\nTop critical attack paths:")
            for i, path in enumerate(critical_paths[:5]):
                click.echo(f"  {i+1}. {path['path']} (risk: {path['risk_score']:.2f})")
        
        # Generate individual attack path visualizations if requested
        if visualize_attack_paths and config.visualization.attack_path_graphs:
            click.echo("\nGenerating attack path visualizations...")
            from .visualizers import HTMLVisualizer
            visualizer = HTMLVisualizer(nx_graph, config)
            
            # Create attack paths directory
            attack_paths_dir = output_path / 'attack_paths'
            attack_paths_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate visualization for each attack path
            path_count = 0
            for category, paths in results['attack_paths'].items():
                for i, path_data in enumerate(paths):
                    # Convert path data to AttackPath object if needed
                    if hasattr(path_data, 'get_attack_graph_data'):
                        attack_path = path_data
                    else:
                        # Skip if not a proper AttackPath object
                        continue
                    
                    # Generate filename
                    safe_category = category.replace(' ', '_').lower()
                    output_file = attack_paths_dir / f"{safe_category}_path_{i+1}_{timestamp}.html"
                    
                    # Create visualization
                    try:
                        visualizer.render_attack_path_graph(attack_path, str(output_file))
                        path_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to visualize path {i+1} in {category}: {e}")
            
            if path_count > 0:
                click.echo(f"  Generated {path_count} attack path visualizations in {attack_paths_dir}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--graph', '-g', help='Graph file path or pattern (e.g., graph/*.json)')
@click.option('--output', '-o', default='visualizations/', help='Output directory')
@click.option('--type', 'viz_type', type=click.Choice(['full', 'attack-paths', 'risk']), default='full')
@click.option('--format', type=click.Choice(['html', 'graphml']), default='html')
@click.pass_obj
def visualize(config, graph, output, viz_type, format):
    """Create graph visualizations"""
    try:
        # Handle graph file selection
        if graph:
            # If a specific file is provided
            graph_path = Path(graph)
            if graph_path.exists() and graph_path.is_file():
                graph_file = graph_path
            else:
                # Try to interpret as a pattern
                if '*' in graph:
                    # It's a pattern
                    pattern = graph
                else:
                    # Maybe it's a directory
                    pattern = str(Path(graph) / 'escagcp_graph_*.json')
                
                graph_files = list(Path('.').glob(pattern))
                if not graph_files:
                    click.echo(f"No graph files found matching pattern: {pattern}")
                    sys.exit(1)
                
                # Use the latest file
                graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
                click.echo(f"Using latest graph file: {graph_file}")
        else:
            # No graph specified, look in default location
            graph_files = list(Path('graph').glob('escagcp_graph_*.json'))
            if not graph_files:
                click.echo("No graph files found. Run 'escagcp build-graph' first.")
                sys.exit(1)
            
            # Use the latest file
            graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
            click.echo(f"Using latest graph file: {graph_file}")
        
        # Load graph and analysis
        with open(graph_file, 'r') as f:
            graph_data = json.load(f)
        
        # Rebuild graph
        builder = GraphBuilder(config)
        nx_graph = builder.graph
        
        for node_data in graph_data['nodes']:
            nx_graph.add_node(node_data['id'], **node_data)
        
        for edge_data in graph_data['edges']:
            # Combine type with properties
            edge_attrs = edge_data.get('properties', {}).copy()
            edge_attrs['type'] = edge_data.get('type')
            
            nx_graph.add_edge(
                edge_data['source'],
                edge_data['target'],
                **edge_attrs
            )
        
        # Create output directory
        output_path = Path(output)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if format == 'html':
            visualizer = HTMLVisualizer(nx_graph, config)
            
            if viz_type == 'full':
                output_file = output_path / f"escagcp_graph_{timestamp}.html"
                visualizer.create_full_graph(str(output_file))
            
            elif viz_type == 'attack-paths':
                # Try to load existing analysis results first
                findings_files = list(Path('findings').glob('escagcp_analysis_*.json'))
                attack_paths = []
                risk_scores = {}
                critical_nodes = []
                
                if findings_files:
                    # Use the latest findings file
                    latest_findings = max(findings_files, key=lambda f: f.stat().st_mtime)
                    click.echo(f"Loading analysis from: {latest_findings}")
                    
                    with open(latest_findings, 'r') as f:
                        findings_data = json.load(f)
                    
                    # Extract attack paths with visualization metadata
                    for category, paths in findings_data.get('attack_paths', {}).items():
                        for path in paths:
                            if isinstance(path, dict):
                                # Generate path string from nodes if not present
                                path_str = path.get('path', '')
                                if not path_str and 'path_nodes' in path:
                                    # Build path string from nodes
                                    nodes = path['path_nodes']
                                    edges = path.get('path_edges', [])
                                    path_parts = []
                                    for i in range(len(nodes)):
                                        path_parts.append(nodes[i].get('name', nodes[i].get('id', 'Unknown')))
                                        if i < len(edges):
                                            edge_type = edges[i].get('type', 'connects to')
                                            path_parts.append(f"--[{edge_type}]-->")
                                    path_str = " ".join(path_parts)
                                
                                path_dict = {
                                    'category': category,
                                    'path': path_str or 'Unknown path',
                                    'risk_score': path.get('risk_score', 0),
                                    'length': path.get('length', 0),
                                    'description': path.get('description', '')
                                }
                                # Preserve visualization metadata
                                if 'visualization_metadata' in path:
                                    path_dict['visualization_metadata'] = path['visualization_metadata']
                                attack_paths.append(path_dict)
                    
                    risk_scores = findings_data.get('risk_scores', {})
                    critical_nodes = findings_data.get('critical_nodes', [])
                else:
                    # No findings file, run analysis
                    click.echo("No findings file found, running analysis...")
                    analyzer = PathAnalyzer(nx_graph, config)
                    results = analyzer.analyze_all_paths()
                    
                    # Convert attack paths to format for dashboard, preserving visualization metadata
                    for category, paths in results['attack_paths'].items():
                        for path in paths:
                            path_dict = {
                                'category': category,
                                'path': path.get_path_string() if hasattr(path, 'get_path_string') else str(path),
                                'risk_score': path.risk_score if hasattr(path, 'risk_score') else 0,
                                'length': len(path) if hasattr(path, '__len__') else 0
                            }
                            # Preserve visualization metadata if available
                            if hasattr(path, 'visualization_metadata') and path.visualization_metadata:
                                path_dict['visualization_metadata'] = path.visualization_metadata
                            if hasattr(path, 'description') and path.description:
                                path_dict['description'] = path.description
                            attack_paths.append(path_dict)
                    
                    risk_scores = results['risk_scores']
                    critical_nodes = results.get('critical_nodes', [])
                
                output_file = output_path / f"escagcp_attack_paths_{timestamp}.html"
                visualizer.create_full_graph(
                    str(output_file),
                    risk_scores=risk_scores,
                    attack_paths=attack_paths,
                    highlight_nodes=set(n['node_id'] for n in critical_nodes)
                )
            
            elif viz_type == 'risk':
                # Try to load existing analysis results first
                findings_files = list(Path('findings').glob('escagcp_analysis_*.json'))
                attack_paths = []
                risk_scores = {}
                critical_nodes = []
                
                if findings_files:
                    # Use the latest findings file
                    latest_findings = max(findings_files, key=lambda f: f.stat().st_mtime)
                    click.echo(f"Loading analysis from: {latest_findings}")
                    
                    with open(latest_findings, 'r') as f:
                        findings_data = json.load(f)
                    
                    # Extract attack paths with visualization metadata
                    for category, paths in findings_data.get('attack_paths', {}).items():
                        for path in paths:
                            if isinstance(path, dict):
                                # Generate path string from nodes if not present
                                path_str = path.get('path', '')
                                if not path_str and 'path_nodes' in path:
                                    # Build path string from nodes
                                    nodes = path['path_nodes']
                                    edges = path.get('path_edges', [])
                                    path_parts = []
                                    for i in range(len(nodes)):
                                        path_parts.append(nodes[i].get('name', nodes[i].get('id', 'Unknown')))
                                        if i < len(edges):
                                            edge_type = edges[i].get('type', 'connects to')
                                            path_parts.append(f"--[{edge_type}]-->")
                                    path_str = " ".join(path_parts)
                                
                                path_dict = {
                                    'category': category,
                                    'path': path_str or 'Unknown path',
                                    'risk_score': path.get('risk_score', 0),
                                    'length': path.get('length', 0),
                                    'description': path.get('description', '')
                                }
                                # Preserve visualization metadata
                                if 'visualization_metadata' in path:
                                    path_dict['visualization_metadata'] = path['visualization_metadata']
                                attack_paths.append(path_dict)
                    
                    risk_scores = findings_data.get('risk_scores', {})
                    critical_nodes = findings_data.get('critical_nodes', [])
                else:
                    # No findings file, run analysis
                    click.echo("No findings file found, running analysis...")
                    analyzer = PathAnalyzer(nx_graph, config)
                    results = analyzer.analyze_all_paths()
                    
                    # Convert attack paths to format for dashboard, preserving visualization metadata
                    for category, paths in results['attack_paths'].items():
                        for path in paths:
                            path_dict = {
                                'category': category,
                                'path': path.get_path_string() if hasattr(path, 'get_path_string') else str(path),
                                'risk_score': path.risk_score if hasattr(path, 'risk_score') else 0,
                                'length': len(path) if hasattr(path, '__len__') else 0
                            }
                            # Preserve visualization metadata if available
                            if hasattr(path, 'visualization_metadata') and path.visualization_metadata:
                                path_dict['visualization_metadata'] = path.visualization_metadata
                            if hasattr(path, 'description') and path.description:
                                path_dict['description'] = path.description
                            attack_paths.append(path_dict)
                    
                    risk_scores = results['risk_scores']
                    critical_nodes = results.get('critical_nodes', [])
                
                output_file = output_path / f"escagcp_risk_graph_{timestamp}.html"
                visualizer.create_full_graph(
                    str(output_file),
                    risk_scores=risk_scores,
                    attack_paths=attack_paths,
                    highlight_nodes=set(n['node_id'] for n in critical_nodes)
                )
        
        elif format == 'graphml':
            visualizer = GraphMLVisualizer(nx_graph, config)
            
            if viz_type in ['full', 'risk']:
                # Run analysis for risk scores
                analyzer = PathAnalyzer(nx_graph, config)
                results = analyzer.analyze_all_paths()
                
                output_file = output_path / f"escagcp_risk_{timestamp}.graphml"
                visualizer.export_with_risk_coloring(
                    str(output_file),
                    risk_scores=results['risk_scores'],
                    critical_nodes=set(results['critical_nodes'])
                )
            
            elif viz_type == 'attack-paths':
                analyzer = PathAnalyzer(nx_graph, config)
                results = analyzer.analyze_all_paths()
                
                all_paths = []
                for category in results['attack_paths'].values():
                    all_paths.extend(category)
                
                output_file = output_path / f"escagcp_paths_{timestamp}.graphml"
                visualizer.export_attack_paths_only(str(output_file), all_paths)
        
        click.echo(f"Visualization created: {output_file}")
        
    except Exception as e:
        logger.error(f"Visualization failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--graph', '-g', help='Graph file path or pattern (e.g., graph/*.json)')
@click.option('--action', type=click.Choice(['add', 'remove', 'change']), required=True)
@click.option('--member', '-m', required=True, help='Member identity (e.g., user:alice@example.com)')
@click.option('--role', '-r', required=True, help='Role name (e.g., roles/editor)')
@click.option('--resource', '-R', required=True, help='Resource (e.g., projects/my-project)')
@click.option('--new-role', help='New role for change action')
@click.pass_obj
def simulate(config, graph, action, member, role, resource, new_role):
    """Simulate IAM binding changes"""
    try:
        # Handle graph file selection
        if graph:
            # If a specific file is provided
            graph_path = Path(graph)
            if graph_path.exists() and graph_path.is_file():
                graph_file = graph_path
            else:
                # Try to interpret as a pattern
                if '*' in graph:
                    # It's a pattern
                    pattern = graph
                else:
                    # Maybe it's a directory
                    pattern = str(Path(graph) / 'escagcp_graph_*.json')
                
                graph_files = list(Path('.').glob(pattern))
                if not graph_files:
                    click.echo(f"No graph files found matching pattern: {pattern}")
                    sys.exit(1)
                
                # Use the latest file
                graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
                click.echo(f"Using latest graph file: {graph_file}")
        else:
            # No graph specified, look in default location
            graph_files = list(Path('graph').glob('escagcp_graph_*.json'))
            if not graph_files:
                click.echo("No graph files found. Run 'escagcp build-graph' first.")
                sys.exit(1)
            
            # Use the latest file
            graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
            click.echo(f"Using latest graph file: {graph_file}")
        
        # Load graph
        with open(graph_file, 'r') as f:
            graph_data = json.load(f)
        
        # Rebuild graph
        builder = GraphBuilder(config)
        nx_graph = builder.graph
        nodes = {}
        
        for node_data in graph_data['nodes']:
            nx_graph.add_node(node_data['id'], **node_data)
            # Reconstruct Node objects
            from .graph.models import Node, NodeType
            nodes[node_data['id']] = Node(
                id=node_data['id'],
                type=NodeType(node_data['type']),
                name=node_data.get('name', node_data['id']),
                properties={k: v for k, v in node_data.items() if k not in ['id', 'type', 'name']}
            )
        
        for edge_data in graph_data['edges']:
            nx_graph.add_edge(
                edge_data['source'],
                edge_data['target'],
                **edge_data.get('properties', {})
            )
        
        # Create query engine
        query = GraphQuery(nx_graph, nodes, config)
        
        # Perform simulation
        if action == 'add':
            results = query.simulate_binding_addition(member, role, resource)
        elif action == 'remove':
            results = query.simulate_binding_removal(member, role, resource)
        elif action == 'change':
            if not new_role:
                click.echo("Error: --new-role required for change action")
                sys.exit(1)
            results = query.simulate_role_change(member, role, new_role, resource)
        
        # Display results
        click.echo(f"\nSimulation Results for {action} action:")
        click.echo("=" * 50)
        
        if 'error' in results:
            click.echo(f"Error: {results['error']}")
            sys.exit(1)
        
        # Risk analysis
        if 'risk_analysis' in results:
            risk = results['risk_analysis']
            click.echo(f"\nRisk Analysis:")
            click.echo(f"  Risk increase: {risk.get('risk_increase', 0):.2f}")
            click.echo(f"  Critical paths created: {risk.get('critical_paths_created', 0)}")
            
            if risk.get('new_attack_vectors'):
                click.echo(f"\n  New attack vectors:")
                for vector in risk['new_attack_vectors']:
                    click.echo(f"    - {vector}")
        
        elif 'security_improvements' in results:
            improvements = results['security_improvements']
            click.echo(f"\nSecurity Improvements:")
            click.echo(f"  Risk reduction: {improvements.get('risk_reduction', 0):.2f}")
            click.echo(f"  Critical paths broken: {improvements.get('critical_paths_broken', 0)}")
            
            if improvements.get('attack_vectors_removed'):
                click.echo(f"\n  Attack vectors removed:")
                for vector in improvements['attack_vectors_removed']:
                    click.echo(f"    - {vector}")
        
        # New paths
        if 'new_paths' in results and results['new_paths']:
            click.echo(f"\nNew attack paths created: {len(results['new_paths'])}")
            for i, path in enumerate(results['new_paths'][:5]):
                click.echo(f"  {i+1}. {path['path']} (risk: {path['risk_score']:.2f})")
        
        # Broken paths
        if 'broken_paths' in results and results['broken_paths']:
            click.echo(f"\nAttack paths broken: {len(results['broken_paths'])}")
            for i, path in enumerate(results['broken_paths'][:5]):
                click.echo(f"  {i+1}. {path['path']} (risk: {path['risk_score']:.2f})")
        
        # Recommendations
        if 'recommendations' in results and results['recommendations']:
            click.echo(f"\nRecommendations:")
            for rec in results['recommendations']:
                click.echo(f"  • {rec}")
        
    except Exception as e:
        logger.error(f"Simulation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--graph', '-g', help='Graph file path or pattern (e.g., graph/*.json)')
@click.option('--from', 'source', required=True, help='Source identity')
@click.option('--to', 'target', help='Target resource or role')
@click.option('--type', 'query_type', type=click.Choice(['paths', 'permissions', 'access']), default='paths')
@click.pass_obj
def query(config, graph, source, target, query_type):
    """Query the graph for specific information"""
    try:
        # Handle graph file selection
        if graph:
            # If a specific file is provided
            graph_path = Path(graph)
            if graph_path.exists() and graph_path.is_file():
                graph_file = graph_path
            else:
                # Try to interpret as a pattern
                if '*' in graph:
                    # It's a pattern
                    pattern = graph
                else:
                    # Maybe it's a directory
                    pattern = str(Path(graph) / 'escagcp_graph_*.json')
                
                graph_files = list(Path('.').glob(pattern))
                if not graph_files:
                    click.echo(f"No graph files found matching pattern: {pattern}")
                    sys.exit(1)
                
                # Use the latest file
                graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
                click.echo(f"Using latest graph file: {graph_file}")
        else:
            # No graph specified, look in default location
            graph_files = list(Path('graph').glob('escagcp_graph_*.json'))
            if not graph_files:
                click.echo("No graph files found. Run 'escagcp build-graph' first.")
                sys.exit(1)
            
            # Use the latest file
            graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
            click.echo(f"Using latest graph file: {graph_file}")
        
        # Load graph
        with open(graph_file, 'r') as f:
            graph_data = json.load(f)
        
        # Rebuild graph and nodes
        builder = GraphBuilder(config)
        nx_graph = builder.graph
        nodes = {}
        
        for node_data in graph_data['nodes']:
            nx_graph.add_node(node_data['id'], **node_data)
            from .graph.models import Node, NodeType
            nodes[node_data['id']] = Node(
                id=node_data['id'],
                type=NodeType(node_data['type']),
                name=node_data.get('name', node_data['id']),
                properties={k: v for k, v in node_data.items() if k not in ['id', 'type', 'name']}
            )
        
        for edge_data in graph_data['edges']:
            nx_graph.add_edge(
                edge_data['source'],
                edge_data['target'],
                **edge_data.get('properties', {})
            )
        
        # Create query engine
        query_engine = GraphQuery(nx_graph, nodes, config)
        
        # Convert source to node ID
        source_id = query_engine._get_node_id_from_identity(source)
        if not source_id or source_id not in nx_graph:
            click.echo(f"Error: Source '{source}' not found in graph")
            sys.exit(1)
        
        if query_type == 'paths':
            if not target:
                click.echo("Error: Target required for path query")
                sys.exit(1)
            
            # Convert target
            target_id = query_engine._get_node_id_from_identity(target)
            if not target_id:
                target_id = query_engine._get_node_id_from_resource(target)
            
            if not target_id or target_id not in nx_graph:
                click.echo(f"Error: Target '{target}' not found in graph")
                sys.exit(1)
            
            # Find paths
            paths = query_engine.find_all_paths(source_id, target_id)
            
            click.echo(f"\nFound {len(paths)} paths from {source} to {target}:")
            for i, path in enumerate(paths[:10]):
                click.echo(f"\n{i+1}. {path.get_path_string()}")
                click.echo(f"   Risk score: {path.risk_score:.2f}")
                click.echo(f"   Length: {len(path)}")
        
        elif query_type == 'permissions':
            # Get permissions
            permissions = query_engine.get_node_permissions(source_id)
            
            click.echo(f"\nPermissions for {source}:")
            for resource, perms in permissions.items():
                click.echo(f"\n  Resource: {resource}")
                click.echo(f"  Permissions: {len(perms)}")
                for perm in sorted(perms)[:10]:
                    click.echo(f"    - {perm}")
                if len(perms) > 10:
                    click.echo(f"    ... and {len(perms) - 10} more")
        
        elif query_type == 'access':
            # Find what the identity can access
            analyzer = PathAnalyzer(nx_graph, config)
            
            # Find all paths from this identity
            paths = analyzer.find_paths_from_identity(source_id)
            
            # Group by target type
            targets_by_type = {}
            for path in paths:
                target_type = path.target_node.type.value
                if target_type not in targets_by_type:
                    targets_by_type[target_type] = set()
                targets_by_type[target_type].add(path.target_node.name)
            
            click.echo(f"\nResources accessible by {source}:")
            for target_type, targets in targets_by_type.items():
                click.echo(f"\n  {target_type}: {len(targets)}")
                for target in sorted(targets)[:5]:
                    click.echo(f"    - {target}")
                if len(targets) > 5:
                    click.echo(f"    ... and {len(targets) - 5} more")
        
    except Exception as e:
        logger.error(f"Query failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--lazy', is_flag=True, help='Run all operations automatically: collect, build, analyze, visualize, and open in Chrome')
@click.option('--projects', '-p', multiple=True, help='Project IDs to scan (defaults to current project)')
@click.option('--open-browser', is_flag=True, default=True, help='Open visualization in browser after completion')
@click.pass_obj
def run(config, lazy, projects, open_browser):
    """Run EscaGCP operations - use --lazy for automatic execution"""
    if lazy:
        import subprocess
        import webbrowser
        import platform
        from pathlib import Path
        
        try:
            # Step 1: Collect data
            click.echo("Step 1/4: Collecting data from GCP...")
            
            # Get current project if none specified
            if not projects:
                try:
                    result = subprocess.run(
                        ['gcloud', 'config', 'get-value', 'project'],
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    current_project = result.stdout.strip()
                    if current_project:
                        projects = [current_project]
                        click.echo(f"Using current project: {current_project}")
                    else:
                        click.echo("No project specified and no current project found.")
                        sys.exit(1)
                except subprocess.CalledProcessError:
                    click.echo("Failed to get current project. Please specify with -p option.")
                    sys.exit(1)
            
            # Run collect command
            ctx = click.get_current_context()
            ctx.invoke(collect, projects=projects, output='data/')
            
            # Step 2: Build graph
            click.echo("\nStep 2/4: Building graph from collected data...")
            ctx.invoke(build_graph, input='data/', output='graph/')
            
            # Step 3: Analyze graph
            click.echo("\nStep 3/4: Analyzing graph for attack paths...")
            ctx.invoke(analyze, graph='graph/escagcp_graph_*.json', output='findings/', format='json')
            
            # Step 4: Create visualization
            click.echo("\nStep 4/4: Creating visualization...")
            ctx.invoke(visualize, graph='graph/escagcp_graph_*.json', output='visualizations/', viz_type='attack-paths', format='html')
            
            # Find the latest visualization file
            viz_files = list(Path('visualizations').glob('escagcp_*.html'))
            if viz_files:
                latest_viz = max(viz_files, key=lambda f: f.stat().st_mtime)
                click.echo(f"\n✅ All operations completed successfully!")
                click.echo(f"Visualization created: {latest_viz}")
                
                # Open in browser if requested
                if open_browser:
                    click.echo("Opening visualization in browser...")
                    
                    # Get absolute path
                    abs_path = latest_viz.absolute()
                    file_url = f"file://{abs_path}"
                    
                    # Try to open in Chrome specifically
                    system = platform.system()
                    try:
                        if system == "Darwin":  # macOS
                            subprocess.run(['open', '-a', 'Google Chrome', file_url], check=True)
                        elif system == "Linux":
                            subprocess.run(['google-chrome', file_url], check=True)
                        elif system == "Windows":
                            # Try Chrome first, fall back to default browser
                            chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
                            if Path(chrome_path).exists():
                                subprocess.run([chrome_path, file_url], check=True)
                            else:
                                webbrowser.open(file_url)
                        else:
                            # Fallback to default browser
                            webbrowser.open(file_url)
                    except Exception as e:
                        # If Chrome fails, use default browser
                        click.echo(f"Could not open Chrome specifically, using default browser...")
                        webbrowser.open(file_url)
            else:
                click.echo("Warning: No visualization file found.")
                
        except Exception as e:
            logger.error(f"Lazy execution failed: {e}")
            click.echo(f"\n❌ Error during execution: {e}")
            sys.exit(1)
    else:
        # Show help for manual execution
        click.echo("GCPHound - Run operations manually or use --lazy for automatic execution")
        click.echo("\nManual execution steps:")
        click.echo("1. gcphound collect --projects $(gcloud config get-value project)")
        click.echo("2. gcphound build-graph --input data/ --output graph/")
        click.echo("3. gcphound analyze --graph graph/escagcp_graph_*.json --output findings/")
        click.echo("4. gcphound visualize --graph graph/escagcp_graph_*.json --output visualizations/")
        click.echo("\nOr simply run: gcphound run --lazy")


@cli.command()
@click.option('--graph', '-g', help='Graph file path or pattern (e.g., graph/*.json)')
@click.option('--output', '-o', default='report.html', help='Output HTML file')
@click.option('--title', '-t', default='EscaGCP Security Report', help='Report title')
@click.pass_obj
def export(config, graph, output, title):
    """Export a standalone HTML report that can be shared"""
    try:
        # Handle graph file selection
        if graph:
            # If a specific file is provided
            graph_path = Path(graph)
            if graph_path.exists() and graph_path.is_file():
                graph_file = graph_path
            else:
                # Try to interpret as a pattern
                if '*' in graph:
                    # It's a pattern
                    pattern = graph
                else:
                    # Maybe it's a directory
                    pattern = str(Path(graph) / 'escagcp_graph_*.json')
                
                graph_files = list(Path('.').glob(pattern))
                if not graph_files:
                    click.echo(f"No graph files found matching pattern: {pattern}")
                    sys.exit(1)
                
                # Use the latest file
                graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
                click.echo(f"Using latest graph file: {graph_file}")
        else:
            # No graph specified, look in default location
            graph_files = list(Path('graph').glob('escagcp_graph_*.json'))
            if not graph_files:
                click.echo("No graph files found. Run 'escagcp build-graph' first.")
                sys.exit(1)
            
            # Use the latest file
            graph_file = max(graph_files, key=lambda f: f.stat().st_mtime)
            click.echo(f"Using latest graph file: {graph_file}")
        
        # Load graph
        with open(graph_file, 'r') as f:
            graph_data = json.load(f)
        
        # Rebuild graph
        builder = GraphBuilder(config)
        nx_graph = builder.graph
        
        for node_data in graph_data['nodes']:
            nx_graph.add_node(node_data['id'], **node_data)
        
        for edge_data in graph_data['edges']:
            # Combine type with properties
            edge_attrs = edge_data.get('properties', {}).copy()
            edge_attrs['type'] = edge_data.get('type')
            
            nx_graph.add_edge(
                edge_data['source'],
                edge_data['target'],
                **edge_attrs
            )
        
        # Create visualizer
        visualizer = HTMLVisualizer(nx_graph, config)
        
        # Generate standalone report
        click.echo("Generating standalone report...")
        visualizer.create_standalone_report(output)
        
        # Get file size
        import os
        file_size = os.path.getsize(output) / (1024 * 1024)  # MB
        
        click.echo(f"\n✅ Standalone report created successfully!")
        click.echo(f"📄 File: {output}")
        click.echo(f"📊 Size: {file_size:.2f} MB")
        click.echo(f"\nThis report is completely self-contained and can be:")
        click.echo("  • Opened on any computer without internet")
        click.echo("  • Shared via email or file transfer")
        click.echo("  • Viewed in any modern web browser")
        click.echo("\nThe report includes:")
        click.echo("  • Interactive graph visualization")
        click.echo("  • All nodes and edges data")
        click.echo("  • Attack path analysis")
        click.echo("  • Risk scoring")
        click.echo("  • Dangerous roles information")
        
    except Exception as e:
        logger.error(f"Export failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--graph', '-g', type=click.Path(exists=True), help='Path to graph JSON file (supports wildcards)')
@click.option('--output', '-o', type=click.Path(), default='escagcp_simple_report.html', help='Output HTML file')
def simple_export(graph, output):
    """Export a simple HTML report with no external dependencies"""
    import json
    import os
    from datetime import datetime
    
    # Handle wildcard patterns
    if graph and '*' in graph:
        import glob
        files = glob.glob(graph)
        if not files:
            click.echo(f"No files matching pattern: {graph}", err=True)
            return
        # Use the most recent file
        graph = max(files, key=os.path.getmtime)
        click.echo(f"Using graph file: {graph}")
    
    # Load graph data
    if not graph:
        # Find the latest graph file
        graph_files = glob.glob('graph/escagcp_graph_*.json')
        if not graph_files:
            click.echo("No graph files found. Run 'escagcp collect' first.", err=True)
            return
        graph = max(graph_files, key=os.path.getmtime)
    
    click.echo(f"Loading graph from: {graph}")
    with open(graph, 'r') as f:
        graph_data = json.load(f)
    
    # Extract data
    nodes = graph_data.get('nodes', [])
    edges = graph_data.get('edges', [])
    metadata = graph_data.get('metadata', {})
    
    # Count statistics
    node_types = {}
    for node in nodes:
        node_type = node.get('type', 'unknown')
        node_types[node_type] = node_types.get(node_type, 0) + 1
    
    edge_types = {}
    for edge in edges:
        edge_type = edge.get('type', 'unknown')
        edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
    
    # Count attack paths
    attack_edges = [e for e in edges if e.get('type', '').startswith('CAN_')]
    
    # Generate simple HTML
    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>EscaGCP Report</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        h1, h2 {{ color: #6b46c1; }}
        h1 {{ border-bottom: 3px solid #6b46c1; padding-bottom: 10px; }}
        h2 {{ margin-top: 30px; border-bottom: 1px solid #ddd; padding-bottom: 5px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            background: white;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background-color: #6b46c1;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            padding: 10px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{ background-color: #f5f5f5; }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .summary-value {{
            font-size: 36px;
            font-weight: bold;
            color: #6b46c1;
        }}
        .summary-label {{
            color: #666;
            margin-top: 5px;
        }}
        .attack-edge {{ color: #dc2626; font-weight: bold; }}
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <h1>EscaGCP Security Report</h1>
    <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    
    <div class="summary">
        <div class="summary-card">
            <div class="summary-value">{len(nodes)}</div>
            <div class="summary-label">Total Nodes</div>
        </div>
        <div class="summary-card">
            <div class="summary-value">{len(edges)}</div>
            <div class="summary-label">Total Edges</div>
        </div>
        <div class="summary-card">
            <div class="summary-value">{len(attack_edges)}</div>
            <div class="summary-label">Attack Paths</div>
        </div>
        <div class="summary-card">
            <div class="summary-value">{metadata.get('projects_analyzed', 0)}</div>
            <div class="summary-label">Projects Analyzed</div>
        </div>
    </div>
    
    <h2>Resource Summary</h2>
    <table>
        <tr>
            <th>Resource Type</th>
            <th>Count</th>
        </tr>
        {''.join(f'<tr><td>{k.replace("_", " ").title()}</td><td>{v}</td></tr>' for k, v in sorted(node_types.items()))}
    </table>
    
    <h2>Relationship Summary</h2>
    <table>
        <tr>
            <th>Relationship Type</th>
            <th>Count</th>
        </tr>
        {''.join(f'<tr><td class="{"attack-edge" if k.startswith("CAN_") else ""}">{k}</td><td>{v}</td></tr>' for k, v in sorted(edge_types.items()))}
    </table>
    
    <h2>Attack Paths Found</h2>
    {'<p>No attack paths found.</p>' if not attack_edges else f'''
    <table>
        <tr>
            <th>From</th>
            <th>Attack Type</th>
            <th>To</th>
        </tr>
        {''.join(f'<tr><td>{e["source"]}</td><td class="attack-edge">{e["type"]}</td><td>{e["target"]}</td></tr>' for e in attack_edges[:50])}
    </table>
    {f'<p>Showing first 50 of {len(attack_edges)} attack paths.</p>' if len(attack_edges) > 50 else ''}
    '''}
    
    <h2>All Nodes</h2>
    <table>
        <tr>
            <th>ID</th>
            <th>Name</th>
            <th>Type</th>
        </tr>
        {''.join(f'<tr><td>{n["id"]}</td><td>{n.get("name", n["id"])}</td><td>{n.get("type", "unknown")}</td></tr>' for n in sorted(nodes, key=lambda x: x.get("type", ""))[:100])}
    </table>
    {f'<p>Showing first 100 of {len(nodes)} nodes.</p>' if len(nodes) > 100 else ''}
    
    <h2>All Relationships</h2>
    <table>
        <tr>
            <th>From</th>
            <th>Type</th>
            <th>To</th>
        </tr>
        {''.join(f'<tr><td>{e["source"]}</td><td>{e.get("type", "unknown")}</td><td>{e["target"]}</td></tr>' for e in edges[:100])}
    </table>
    {f'<p>Showing first 100 of {len(edges)} relationships.</p>' if len(edges) > 100 else ''}
    
    <div class="footer">
        <p>This is a standalone EscaGCP report. No external dependencies required.</p>
        <p>Generated by EscaGCP</p>
    </div>
</body>
</html>"""
    
    # Write the file
    with open(output, 'w') as f:
        f.write(html)
    
    file_size = os.path.getsize(output) / 1024  # KB
    click.echo(f"✓ Simple HTML report exported to: {output} ({file_size:.1f} KB)")


def _create_html_report(results: Dict[str, Any], output_file: Path):
    """Create HTML analysis report"""
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>EscaGCP Analysis Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1, h2, h3 {{ color: #1a73e8; }}
            .stats {{ background: #f8f9fa; padding: 15px; border-radius: 5px; }}
            .critical {{ color: #d93025; }}
            .high {{ color: #ea8600; }}
            .medium {{ color: #fbbc04; }}
            .low {{ color: #34a853; }}
            table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h1>EscaGCP Analysis Report</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        
        <div class="stats">
            <h2>Summary Statistics</h2>
            <ul>
                <li>Total Nodes: {results['statistics']['total_nodes']}</li>
                <li>Total Edges: {results['statistics']['total_edges']}</li>
                <li>Attack Paths Found: {results['statistics']['total_attack_paths']}</li>
                <li>Critical Nodes: {results['statistics']['critical_nodes']}</li>
                <li>Vulnerabilities: {results['statistics']['vulnerabilities']}</li>
            </ul>
        </div>
        
        <h2>Attack Paths by Severity</h2>
    """
    
    for severity, paths in results['attack_paths'].items():
        if paths:
            html += f"<h3 class='{severity}'>{severity.upper()} ({len(paths)} paths)</h3>"
            html += "<table><tr><th>Path</th><th>Risk Score</th><th>Length</th></tr>"
            
            for path in paths[:10]:
                html += f"""
                <tr>
                    <td>{path.get('path', 'N/A')}</td>
                    <td>{path.get('risk_score', 0):.2f}</td>
                    <td>{path.get('length', 0)}</td>
                </tr>
                """
            
            html += "</table>"
    
    html += """
        <h2>Vulnerabilities</h2>
        <table>
            <tr><th>Type</th><th>Severity</th><th>Resource</th><th>Details</th></tr>
    """
    
    for vuln in results.get('vulnerabilities', [])[:20]:
        html += f"""
        <tr>
            <td>{vuln.get('type', 'N/A')}</td>
            <td class='{vuln.get('severity', '').lower()}'>{vuln.get('severity', 'N/A')}</td>
            <td>{vuln.get('resource', 'N/A')}</td>
            <td>{vuln.get('details', 'N/A')}</td>
        </tr>
        """
    
    html += """
        </table>
    </body>
    </html>
    """
    
    with open(output_file, 'w') as f:
        f.write(html)


def _create_text_report(results: Dict[str, Any], output_file: Path):
    """Create text analysis report"""
    with open(output_file, 'w') as f:
        f.write("EscaGCP Analysis Report\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write("Summary Statistics\n")
        f.write("-" * 30 + "\n")
        for key, value in results['statistics'].items():
            f.write(f"{key}: {value}\n")
        
        f.write("\n\nAttack Paths\n")
        f.write("-" * 30 + "\n")
        
        for severity, paths in results['attack_paths'].items():
            if paths:
                f.write(f"\n{severity.upper()} ({len(paths)} paths):\n")
                for i, path in enumerate(paths[:10]):
                    f.write(f"{i+1}. {path.get('path', 'N/A')} (risk: {path.get('risk_score', 0):.2f})\n")
        
        f.write("\n\nVulnerabilities\n")
        f.write("-" * 30 + "\n")
        
        for vuln in results.get('vulnerabilities', [])[:20]:
            f.write(f"\nType: {vuln.get('type', 'N/A')}\n")
            f.write(f"Severity: {vuln.get('severity', 'N/A')}\n")
            f.write(f"Resource: {vuln.get('resource', 'N/A')}\n")
            f.write(f"Details: {vuln.get('details', 'N/A')}\n")
            f.write(f"Recommendation: {vuln.get('recommendation', 'N/A')}\n")


@cli.command()
@click.option('--force', '-f', is_flag=True, help='Skip confirmation prompt')
@click.option('--dry-run', is_flag=True, help='Show what would be deleted without actually deleting')
def cleanup(force, dry_run):
    """Clean up all generated files and collected data"""
    import shutil
    from pathlib import Path
    
    # Define directories and file patterns to clean
    cleanup_targets = {
        'data/': 'Collected GCP data',
        'graph/': 'Generated graph files',
        'findings/': 'Analysis findings',
        'visualizations/': 'Visualization files',
        'test_output/': 'Test output files',
        'temp_test_files/': 'Temporary test files',
        'htmlcov/': 'Coverage HTML reports',
        '.pytest_cache/': 'Pytest cache',
        '__pycache__/': 'Python cache files',
        '.coverage': 'Coverage data file',
        'coverage.xml': 'Coverage XML report',
        '*.html': 'Generated HTML reports (in root)',
        'escagcp_*.html': 'EscaGCP HTML reports',
        'simple_report.html': 'Simple HTML reports',
    }
    
    # Find all files and directories to delete
    to_delete = []
    root_path = Path('.')
    
    for pattern, description in cleanup_targets.items():
        if pattern.endswith('/'):
            # It's a directory
            dir_path = root_path / pattern
            if dir_path.exists() and dir_path.is_dir():
                to_delete.append((dir_path, description, 'directory'))
        else:
            # It's a file pattern
            for file_path in root_path.glob(pattern):
                if file_path.is_file():
                    to_delete.append((file_path, description, 'file'))
    
    # Also find all __pycache__ directories recursively
    for pycache in root_path.rglob('__pycache__'):
        if pycache.is_dir():
            to_delete.append((pycache, 'Python cache directory', 'directory'))
    
    if not to_delete:
        click.echo("✨ No files to clean up. The workspace is already clean.")
        return
    
    # Display what will be deleted
    click.echo("The following files and directories will be deleted:\n")
    
    # Group by type
    directories = [item for item in to_delete if item[2] == 'directory']
    files = [item for item in to_delete if item[2] == 'file']
    
    if directories:
        click.echo("📁 Directories:")
        for path, desc, _ in sorted(directories):
            click.echo(f"   - {path} ({desc})")
    
    if files:
        click.echo("\n📄 Files:")
        for path, desc, _ in sorted(files):
            click.echo(f"   - {path} ({desc})")
    
    # Calculate total size
    total_size = 0
    for path, _, _ in to_delete:
        try:
            if path.is_dir():
                total_size += sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
            else:
                total_size += path.stat().st_size
        except:
            pass
    
    size_mb = total_size / (1024 * 1024)
    click.echo(f"\n💾 Total size to be freed: {size_mb:.2f} MB")
    
    if dry_run:
        click.echo("\n🔍 DRY RUN: No files were actually deleted.")
        return
    
    # Confirmation prompt
    if not force:
        click.echo("\n" + "⚠️  " * 10)
        click.echo("⚠️  WARNING: This action cannot be undone!")
        click.echo("⚠️  All collected data, graphs, and analysis results will be permanently deleted.")
        click.echo("⚠️  " * 10)
        
        if not click.confirm("\nDo you want to proceed with the cleanup?", default=False):
            click.echo("Cleanup cancelled.")
            return
    
    # Perform deletion
    click.echo("\n🗑️  Cleaning up...")
    deleted_count = 0
    error_count = 0
    
    with click.progressbar(to_delete, label='Deleting files') as items:
        for path, desc, item_type in items:
            try:
                if item_type == 'directory':
                    shutil.rmtree(path)
                else:
                    path.unlink()
                deleted_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"Failed to delete {path}: {e}")
    
    # Summary
    click.echo(f"\n✅ Cleanup completed!")
    click.echo(f"   - Deleted: {deleted_count} items")
    if error_count > 0:
        click.echo(f"   - Errors: {error_count} items (check logs for details)")
    click.echo(f"   - Freed: {size_mb:.2f} MB")
    click.echo("\n🎉 EscaGCP is now clean and ready for a fresh start!")


@cli.command()
def list_attack_types():
    """List all attack types that EscaGCP can detect"""
    from .graph.models import EdgeType
    from .analyzers.paths import PathAnalyzer
    
    click.echo("=" * 80)
    click.echo("EscaGCP Attack Path Detection Capabilities")
    click.echo("=" * 80)
    click.echo("\nEscaGCP can detect the following types of privilege escalation attack paths:\n")
    
    # Define attack path descriptions
    attack_descriptions = {
        EdgeType.CAN_IMPERSONATE_SA: {
            "name": "Service Account Impersonation",
            "description": "Allows an identity to directly impersonate a service account using generateAccessToken API",
            "required_permission": "iam.serviceAccounts.getAccessToken",
            "example": "User with roles/iam.serviceAccountTokenCreator can generate tokens for any SA they have access to",
            "risk": "Critical"
        },
        EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY: {
            "name": "Service Account Key Creation",
            "description": "Allows creating long-lived service account keys that can be used outside GCP",
            "required_permission": "iam.serviceAccountKeys.create",
            "example": "User with roles/iam.serviceAccountKeyAdmin can create keys and use them indefinitely",
            "risk": "High"
        },
        EdgeType.CAN_ACT_AS_VIA_VM: {
            "name": "VM-based Service Account Abuse",
            "description": "Deploy or modify a VM that runs as a privileged service account",
            "required_permission": "compute.instances.setServiceAccount + iam.serviceAccounts.actAs",
            "example": "User can create a VM running as project editor SA and SSH into it",
            "risk": "High"
        },
        EdgeType.CAN_DEPLOY_FUNCTION_AS: {
            "name": "Cloud Function Deployment Abuse",
            "description": "Deploy Cloud Functions that execute with a service account's permissions",
            "required_permission": "cloudfunctions.functions.create + iam.serviceAccounts.actAs",
            "example": "Deploy a function as roles/editor SA to escalate privileges",
            "risk": "Critical"
        },
        EdgeType.CAN_DEPLOY_CLOUD_RUN_AS: {
            "name": "Cloud Run Deployment Abuse",
            "description": "Deploy Cloud Run services that execute with a service account's permissions",
            "required_permission": "run.services.create + iam.serviceAccounts.actAs",
            "example": "Deploy a Cloud Run service as roles/owner SA to gain full project access",
            "risk": "Critical"
        },
        EdgeType.CAN_TRIGGER_BUILD_AS: {
            "name": "Cloud Build Trigger Abuse",
            "description": "Create or modify Cloud Build triggers that run with elevated permissions",
            "required_permission": "cloudbuild.builds.create",
            "example": "Trigger builds that run as Cloud Build default SA with editor permissions",
            "risk": "High"
        },
        EdgeType.CAN_LOGIN_TO_VM: {
            "name": "VM Login Access",
            "description": "SSH or RDP access to VMs, potentially accessing attached service accounts",
            "required_permission": "compute.instances.osLogin or iap.tunnelInstances.accessViaIAP",
            "example": "SSH into VM and use metadata server to get SA tokens",
            "risk": "Medium"
        },
        EdgeType.CAN_SATISFY_IAM_CONDITION: {
            "name": "IAM Condition Bypass",
            "description": "Ability to satisfy IAM conditions to gain conditional roles",
            "required_permission": "Varies based on condition",
            "example": "Create resources with specific tags to satisfy tag-based IAM conditions",
            "risk": "High"
        },
        EdgeType.EXTERNAL_PRINCIPAL_CAN_IMPERSONATE: {
            "name": "Workload Identity Federation Abuse",
            "description": "External identities can impersonate service accounts via WIF",
            "required_permission": "iam.workloadIdentityPools.providers.create",
            "example": "Misconfigured WIF allows any GitHub action to impersonate privileged SA",
            "risk": "Critical"
        },
        EdgeType.CAN_HIJACK_WORKLOAD_IDENTITY: {
            "name": "GKE Workload Identity Hijacking",
            "description": "Deploy pods that can impersonate GKE workload identity service accounts",
            "required_permission": "container.pods.create",
            "example": "Deploy pod in namespace bound to privileged SA",
            "risk": "High"
        },
        EdgeType.CAN_MODIFY_CUSTOM_ROLE: {
            "name": "Custom Role Modification",
            "description": "Modify custom roles to add dangerous permissions",
            "required_permission": "iam.roles.update",
            "example": "Add iam.serviceAccounts.getAccessToken to a custom role you have",
            "risk": "High"
        },
        EdgeType.CAN_LAUNCH_AS_DEFAULT_SA: {
            "name": "Default Service Account Abuse",
            "description": "Launch resources using default service accounts with editor permissions",
            "required_permission": "Varies by service",
            "example": "Deploy App Engine app using default editor SA",
            "risk": "Medium"
        },
        EdgeType.CAN_ATTACH_SERVICE_ACCOUNT: {
            "name": "Service Account Attachment",
            "description": "Attach service accounts to resources after creation",
            "required_permission": "iam.serviceAccounts.actAs + resource update permission",
            "example": "Update existing VM to use a more privileged service account",
            "risk": "High"
        },
        EdgeType.CAN_UPDATE_METADATA: {
            "name": "Instance Metadata Manipulation",
            "description": "Update VM metadata to enable features or change configurations",
            "required_permission": "compute.instances.setMetadata",
            "example": "Enable OS Login on VM to gain SSH access",
            "risk": "Medium"
        },
        EdgeType.CAN_DEPLOY_GKE_POD_AS: {
            "name": "GKE Pod Deployment",
            "description": "Deploy pods in GKE that can access node or workload identity SAs",
            "required_permission": "container.pods.create",
            "example": "Deploy privileged pod to access node's service account",
            "risk": "High"
        },
        EdgeType.CAN_ASSIGN_CUSTOM_ROLE: {
            "name": "Custom Role Assignment",
            "description": "Assign custom roles with dangerous permissions to identities",
            "required_permission": "resourcemanager.projects.setIamPolicy",
            "example": "Grant custom role with token creation permissions",
            "risk": "High"
        },
        EdgeType.HAS_TAG_BINDING_ESCALATION: {
            "name": "Tag-based Privilege Escalation",
            "description": "Use tag bindings to satisfy IAM conditions and gain elevated roles",
            "required_permission": "resourcemanager.tagBindings.create",
            "example": "Apply tags to resources to activate conditional role bindings",
            "risk": "High"
        },
        EdgeType.CAN_SSH_AND_IMPERSONATE: {
            "name": "SSH + Impersonation Combo",
            "description": "SSH access to VMs combined with SA impersonation capabilities",
            "required_permission": "compute.instances.osLogin + iam.serviceAccounts.getAccessToken",
            "example": "SSH to VM and impersonate its attached service account",
            "risk": "High"
        },
        EdgeType.HAS_ESCALATED_PRIVILEGE: {
            "name": "Confirmed Privilege Escalation",
            "description": "Privilege escalation activity detected in audit logs",
            "required_permission": "N/A - detected from logs",
            "example": "Audit logs show user gained higher privileges through exploitation",
            "risk": "Critical"
        }
    }
    
    # Group by risk level
    risk_groups = {
        "Critical": [],
        "High": [],
        "Medium": []
    }
    
    for edge_type in PathAnalyzer.ESCALATION_EDGE_TYPES:
        if edge_type in attack_descriptions:
            info = attack_descriptions[edge_type]
            risk_groups[info["risk"]].append((edge_type, info))
    
    # Display by risk level
    for risk_level in ["Critical", "High", "Medium"]:
        attacks = risk_groups[risk_level]
        if attacks:
            click.echo(f"\n{risk_level.upper()} RISK ATTACKS ({len(attacks)} types)")
            click.echo("-" * 60)
            
            for edge_type, info in attacks:
                click.echo(f"\n{info['name']} ({edge_type.value})")
                click.echo(f"  Description: {info['description']}")
                click.echo(f"  Required: {info['required_permission']}")
                click.echo(f"  Example: {info['example']}")
    
    # Summary statistics
    click.echo("\n" + "=" * 80)
    click.echo("SUMMARY")
    click.echo("=" * 80)
    click.echo(f"Total attack types detected: {len(PathAnalyzer.ESCALATION_EDGE_TYPES)}")
    click.echo(f"  - Critical risk: {len(risk_groups['Critical'])}")
    click.echo(f"  - High risk: {len(risk_groups['High'])}")
    click.echo(f"  - Medium risk: {len(risk_groups['Medium'])}")
    
    click.echo("\nAdditional Detection Capabilities:")
    click.echo("  - Lateral movement between projects")
    click.echo("  - Overprivileged service accounts")
    click.echo("  - External users with dangerous permissions")
    click.echo("  - Default service account usage")
    click.echo("  - Audit log enrichment for confirmed attacks")
    
    click.echo("\nFor more information, see the documentation at: https://github.com/arielkalman/EscaGCP")


def main():
    """Main entry point"""
    cli()


if __name__ == '__main__':
    main() 