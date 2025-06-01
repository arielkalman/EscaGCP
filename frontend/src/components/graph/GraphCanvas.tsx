import React, { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';
import { Network, DataSet, Options } from 'vis-network/standalone';
import { GraphNode, GraphEdge, NodeType, EdgeType } from '../../types';

interface GraphCanvasProps {
  nodes: GraphNode[];
  edges: GraphEdge[];
  onNodeClick?: (nodeId: string, nodeData: GraphNode) => void;
  onEdgeClick?: (edgeId: string, edgeData: GraphEdge) => void;
  highlightedNodes?: Set<string>;
  highlightedEdges?: Set<string>;
  selectedNodes?: Set<string>;
  selectedEdges?: Set<string>;
  className?: string;
}

export interface GraphCanvasRef {
  fitView: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
  fit: () => void;
  focusNode: (nodeId: string) => void;
  selectNode: (nodeId: string) => void;
  selectEdge: (edgeId: string) => void;
  clearSelection: () => void;
  getSelectedNodes: () => string[];
  getSelectedEdges: () => string[];
}

// Color mapping for different node types
const getNodeColor = (nodeType: NodeType): { background: string; border: string } => {
  switch (nodeType) {
    case NodeType.USER:
      return { background: '#4285F4', border: '#1a73e8' };
    case NodeType.SERVICE_ACCOUNT:
      return { background: '#34A853', border: '#137333' };
    case NodeType.GROUP:
      return { background: '#FBBC04', border: '#f29900' };
    case NodeType.PROJECT:
      return { background: '#EA4335', border: '#d33b2c' };
    case NodeType.FOLDER:
      return { background: '#FF6D00', border: '#e65100' };
    case NodeType.ORGANIZATION:
      return { background: '#9C27B0', border: '#7b1fa2' };
    case NodeType.ROLE:
      return { background: '#757575', border: '#424242' };
    case NodeType.CUSTOM_ROLE:
      return { background: '#616161', border: '#424242' };
    default:
      return { background: '#00ACC1', border: '#0097a7' };
  }
};

// Color mapping for different edge types
const getEdgeColor = (edgeType: EdgeType): string => {
  switch (edgeType) {
    case EdgeType.CAN_IMPERSONATE_SA:
    case EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY:
    case EdgeType.CAN_IMPERSONATE:
      return '#F44336'; // Red for dangerous privileges
    case EdgeType.CAN_ADMIN:
      return '#FF5722'; // Orange for admin access
    case EdgeType.HAS_ROLE:
      return '#757575'; // Gray for regular roles
    case EdgeType.MEMBER_OF:
      return '#9E9E9E'; // Light gray for membership
    case EdgeType.CAN_ACT_AS_VIA_VM:
    case EdgeType.CAN_DEPLOY_FUNCTION_AS:
    case EdgeType.CAN_DEPLOY_CLOUD_RUN_AS:
      return '#FF9800'; // Orange for deployment privileges
    default:
      return '#2196F3'; // Blue for other relationships
  }
};

export const GraphCanvas = forwardRef<GraphCanvasRef, GraphCanvasProps>((props, ref) => {
  const {
    nodes,
    edges,
    onNodeClick,
    onEdgeClick,
    highlightedNodes = new Set(),
    highlightedEdges = new Set(),
    selectedNodes = new Set(),
    selectedEdges = new Set(),
    className = ''
  } = props;

  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const nodesDataSetRef = useRef<DataSet<any> | null>(null);
  const edgesDataSetRef = useRef<DataSet<any> | null>(null);

  // Transform data for vis.js with improved sizing and spacing
  const transformedNodes = nodes.map(node => {
    const color = getNodeColor(node.type);
    const isHighlighted = highlightedNodes.has(node.id);
    const isSelected = selectedNodes.has(node.id);
    
    // Variable node sizes based on type for better hierarchy
    const getNodeSize = (nodeType: NodeType): number => {
      switch (nodeType) {
        case NodeType.ORGANIZATION:
          return 45; // Largest for organizations
        case NodeType.FOLDER:
          return 40; // Large for folders
        case NodeType.PROJECT:
          return 35; // Medium-large for projects
        case NodeType.USER:
        case NodeType.SERVICE_ACCOUNT:
          return 30; // Medium for identities
        case NodeType.GROUP:
          return 32; // Slightly larger for groups
        case NodeType.ROLE:
        case NodeType.CUSTOM_ROLE:
          return 25; // Smaller for roles
        default:
          return 28; // Default size for other resources
      }
    };
    
    return {
      id: node.id,
      label: node.name.length > 25 ? node.name.substring(0, 25) + '...' : node.name,
      title: `${node.type}: ${node.name}`, // Tooltip
      color: {
        background: isSelected ? '#FFD700' : (isHighlighted ? '#FFA726' : color.background),
        border: isSelected ? '#FFA000' : (isHighlighted ? '#FF6F00' : color.border)
      },
      font: {
        color: '#ffffff',
        size: 14, // Slightly larger font
        strokeWidth: 2,
        strokeColor: '#000000' // Better contrast
      },
      borderWidth: isSelected ? 5 : (isHighlighted ? 4 : 3), // Thicker borders
      size: getNodeSize(node.type),
      shape: 'dot',
      physics: true
    };
  });

  const transformedEdges = edges.map(edge => {
    const color = getEdgeColor(edge.type);
    const isHighlighted = highlightedEdges.has(edge.id);
    const isSelected = selectedEdges.has(edge.id);
    
    return {
      id: edge.id,
      from: edge.source,
      to: edge.target,
      title: `${edge.type.replace(/_/g, ' ')}: ${edge.source} → ${edge.target}`, // Tooltip only
      color: {
        color: isSelected ? '#FFD700' : (isHighlighted ? '#FFA726' : color),
        highlight: '#FFA726',
        hover: '#FFB74D',
        opacity: 0.7 // Make edges semi-transparent to reduce visual weight
      },
      width: isSelected ? 3 : (isHighlighted ? 2.5 : 1.5), // Thinner edges
      arrows: {
        to: {
          enabled: true,
          scaleFactor: 0.8, // Smaller arrows
          type: 'arrow'
        }
      },
      smooth: {
        enabled: true,
        type: 'continuous',
        roundness: 0.3 // More rounded for better spacing
      },
      physics: true,
      length: 250 // Longer default edge length for more spacing
    };
  });

  useEffect(() => {
    if (!containerRef.current) return;

    console.log('GraphCanvas: Initializing network with', nodes.length, 'nodes and', edges.length, 'edges');

    // Create data sets
    nodesDataSetRef.current = new DataSet(transformedNodes);
    edgesDataSetRef.current = new DataSet(transformedEdges);

    const data = {
      nodes: nodesDataSetRef.current,
      edges: edgesDataSetRef.current
    };

    const options: Options = {
      physics: {
        enabled: true,
        barnesHut: {
          gravitationalConstant: -2000,
          centralGravity: 0.1,
          springLength: 200,
          springConstant: 0.02,
          damping: 0.15,
          avoidOverlap: 0.8
        },
        maxVelocity: 30,
        minVelocity: 0.75,
        solver: 'barnesHut',
        timestep: 0.35,
        stabilization: {
          enabled: true,
          iterations: 2000,
          updateInterval: 50,
          onlyDynamicEdges: false,
          fit: true
        }
      },
      layout: {
        improvedLayout: true,
        hierarchical: false,
        randomSeed: 2
      },
      interaction: {
        dragNodes: true,
        dragView: true,
        zoomView: true,
        selectConnectedEdges: true,
        hover: true,
        hoverConnectedEdges: true,
        keyboard: true,
        multiselect: true,
        tooltipDelay: 200
      },
      nodes: {
        borderWidth: 3,
        borderWidthSelected: 5,
        size: 30,
        font: {
          size: 14,
          color: '#ffffff',
          strokeWidth: 2,
          strokeColor: '#000000'
        },
        shapeProperties: {
          useBorderWithImage: true
        },
        scaling: {
          min: 20,
          max: 60
        }
      },
      edges: {
        width: 1.5,
        selectionWidth: 3,
        hoverWidth: 2.5,
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 0.8,
            type: 'arrow'
          }
        },
        color: {
          inherit: false,
          opacity: 0.7
        },
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.3
        },
        length: 250,
        font: {
          size: 0
        }
      }
    };

    // Create network
    networkRef.current = new Network(containerRef.current, data, options);

    // Event handlers
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const nodeId = params.nodes[0];
        const nodeData = nodes.find(n => n.id === nodeId);
        if (nodeData && onNodeClick) {
          console.log('GraphCanvas: Node clicked:', nodeId, nodeData);
          onNodeClick(nodeId, nodeData);
          
          // Dispatch custom event for tests
          window.dispatchEvent(new CustomEvent('nodeSelected', {
            detail: {
              nodeId: nodeId,
              nodeData: nodeData
            }
          }));
        }
      } else if (params.edges.length > 0) {
        const edgeId = params.edges[0];
        const edgeData = edges.find(e => e.id === edgeId);
        if (edgeData && onEdgeClick) {
          console.log('GraphCanvas: Edge clicked:', edgeId, edgeData);
          onEdgeClick(edgeId, edgeData);
          
          // Dispatch custom event for tests
          window.dispatchEvent(new CustomEvent('edgeSelected', {
            detail: {
              edgeId: edgeId,
              edgeData: edgeData
            }
          }));
        }
      }
    });

    networkRef.current.on('stabilized', () => {
      console.log('GraphCanvas: Network stabilized');
    });

    // Add custom event listeners
    const handleFocusGraphNode = (event: CustomEvent) => {
      const { nodeId } = event.detail;
      if (networkRef.current && nodeId) {
        console.log('GraphCanvas: Focusing on node:', nodeId);
        networkRef.current.focus(nodeId, { 
          animation: { duration: 1000, easingFunction: 'easeInOutCubic' },
          scale: 1.5
        });
        networkRef.current.selectNodes([nodeId]);
      }
    };

    const handleHighlightAttackPath = (event: CustomEvent) => {
      const { nodeIds, edgeIds, attackPath } = event.detail;
      if (networkRef.current && nodeIds && nodeIds.length > 0) {
        console.log('GraphCanvas: Highlighting attack path:', { nodeIds, edgeIds });
        
        // Highlight nodes and edges
        if (nodesDataSetRef.current && edgesDataSetRef.current) {
          // Update nodes to highlight the path
          const updatedNodes = transformedNodes.map(node => {
            if (nodeIds.includes(node.id)) {
              return {
                ...node,
                color: {
                  background: '#FF5722', // Orange for highlighted nodes
                  border: '#D84315'
                },
                borderWidth: 4,
                size: 30
              };
            }
            return node;
          });
          
          // Update edges to highlight the path
          const updatedEdges = transformedEdges.map(edge => {
            // Check if this edge is part of the attack path
            const isPathEdge = attackPath?.path_edges?.some((pathEdge: any) => 
              edge.from === pathEdge.source && edge.to === pathEdge.target
            );
            
            if (isPathEdge) {
              return {
                ...edge,
                color: {
                  color: '#FF5722', // Orange for highlighted edges
                  highlight: '#FF5722',
                  hover: '#FF5722'
                },
                width: 5
              };
            }
            return edge;
          });
          
          nodesDataSetRef.current.update(updatedNodes);
          edgesDataSetRef.current.update(updatedEdges);
        }
        
        // Focus on the source node
        if (nodeIds[0]) {
          networkRef.current.focus(nodeIds[0], { 
            animation: { duration: 1000, easingFunction: 'easeInOutCubic' },
            scale: 1.2
          });
        }
      }
    };

    // Register event listeners
    window.addEventListener('focusGraphNode', handleFocusGraphNode as EventListener);
    window.addEventListener('highlightAttackPath', handleHighlightAttackPath as EventListener);

    return () => {
      // Clean up event listeners
      window.removeEventListener('focusGraphNode', handleFocusGraphNode as EventListener);
      window.removeEventListener('highlightAttackPath', handleHighlightAttackPath as EventListener);
      
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [nodes, edges, onNodeClick, onEdgeClick]);

  // Update network when highlight/selection changes
  useEffect(() => {
    if (nodesDataSetRef.current && edgesDataSetRef.current) {
      nodesDataSetRef.current.update(transformedNodes);
      edgesDataSetRef.current.update(transformedEdges);
    }
  }, [highlightedNodes, highlightedEdges, selectedNodes, selectedEdges]);

  useImperativeHandle(ref, () => ({
    fitView: () => {
      networkRef.current?.fit();
    },
    zoomIn: () => {
      const scale = networkRef.current?.getScale();
      if (scale) {
        networkRef.current?.moveTo({ scale: scale * 1.2 });
      }
    },
    zoomOut: () => {
      const scale = networkRef.current?.getScale();
      if (scale) {
        networkRef.current?.moveTo({ scale: scale * 0.8 });
      }
    },
    fit: () => {
      networkRef.current?.fit();
    },
    focusNode: (nodeId: string) => {
      networkRef.current?.focus(nodeId, { animation: true });
    },
    selectNode: (nodeId: string) => {
      networkRef.current?.selectNodes([nodeId]);
    },
    selectEdge: (edgeId: string) => {
      networkRef.current?.selectEdges([edgeId]);
    },
    clearSelection: () => {
      networkRef.current?.unselectAll();
    },
    getSelectedNodes: () => {
      const selected = networkRef.current?.getSelectedNodes() || [];
      return selected.map(id => String(id));
    },
    getSelectedEdges: () => {
      const selected = networkRef.current?.getSelectedEdges() || [];
      return selected.map(id => String(id));
    }
  }));

  return (
    <div 
      ref={containerRef}
      className={`w-full h-full bg-white border rounded-lg ${className}`}
      data-testid="graph-canvas"
      style={{ minHeight: '600px', minWidth: '800px', height: '100%', width: '100%' }}
    >
      {/* Network will be rendered here by vis.js */}
      {nodes.length === 0 && (
        <div className="absolute inset-0 flex items-center justify-center text-center text-muted-foreground">
          <div className="p-4">
            <p className="text-lg font-medium">No Graph Data</p>
            <p className="text-sm">
              No nodes or edges to display
            </p>
          </div>
        </div>
      )}
    </div>
  );
});

GraphCanvas.displayName = 'GraphCanvas'; 