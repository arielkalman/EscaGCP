import React, { useRef, useEffect, useImperativeHandle, forwardRef, useState } from 'react';
import { Network, DataSet, Options } from 'vis-network/standalone';
import { AttackPath, NodeType, EdgeType } from '../../types';

interface AttackPathCanvasProps {
  attackPath: AttackPath;
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
  className?: string;
}

export interface AttackPathCanvasRef {
  fitView: () => void;
  zoomIn: () => void;
  zoomOut: () => void;
  fit: () => void;
  focusNode: (nodeId: string) => void;
  selectNode: (nodeId: string) => void;
  selectEdge: (edgeId: string) => void;
  clearSelection: () => void;
}

// Modern color scheme for different node types
const getNodeColor = (nodeType: NodeType, isSource: boolean, isTarget: boolean) => {
  if (isSource) {
    return {
      background: '#3b82f6', // Blue for source
      border: '#1e40af',
      highlight: { background: '#60a5fa', border: '#1e40af' }
    };
  }
  
  if (isTarget) {
    return {
      background: '#ef4444', // Red for target
      border: '#dc2626',
      highlight: { background: '#f87171', border: '#dc2626' }
    };
  }
  
  // Intermediate nodes with neutral modern colors
  switch (nodeType) {
    case NodeType.USER:
      return {
        background: '#8b5cf6', // Purple
        border: '#7c3aed',
        highlight: { background: '#a78bfa', border: '#7c3aed' }
      };
    case NodeType.SERVICE_ACCOUNT:
      return {
        background: '#10b981', // Emerald
        border: '#059669',
        highlight: { background: '#34d399', border: '#059669' }
      };
    case NodeType.GROUP:
      return {
        background: '#f59e0b', // Amber
        border: '#d97706',
        highlight: { background: '#fbbf24', border: '#d97706' }
      };
    case NodeType.PROJECT:
      return {
        background: '#ec4899', // Pink
        border: '#db2777',
        highlight: { background: '#f472b6', border: '#db2777' }
      };
    default:
      return {
        background: '#6b7280', // Gray
        border: '#4b5563',
        highlight: { background: '#9ca3af', border: '#4b5563' }
      };
  }
};

// Professional edge colors based on attack type
const getEdgeColor = (edgeType: EdgeType) => {
  switch (edgeType) {
    case EdgeType.CAN_IMPERSONATE_SA:
    case EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY:
      return '#dc2626'; // Critical - Red
    case EdgeType.CAN_ADMIN:
    case EdgeType.HAS_ROLE:
      return '#ea580c'; // High - Orange
    case EdgeType.MEMBER_OF:
      return '#7c3aed'; // Medium - Purple
    default:
      return '#374151'; // Default - Dark gray
  }
};

// Node shapes for different types
const getNodeShape = (nodeType: NodeType, isSource: boolean, isTarget: boolean) => {
  if (isSource) return 'dot'; // Circle for source
  if (isTarget) return 'square'; // Square for target
  
  switch (nodeType) {
    case NodeType.USER:
      return 'circle';
    case NodeType.SERVICE_ACCOUNT:
      return 'diamond';
    case NodeType.GROUP:
      return 'triangle';
    case NodeType.PROJECT:
      return 'box';
    case NodeType.ROLE:
      return 'ellipse';
    default:
      return 'dot';
  }
};

// Clean edge type display names
const formatEdgeType = (edgeType: EdgeType) => {
  const edgeNames: Record<string, string> = {
    [EdgeType.CAN_IMPERSONATE_SA]: 'Impersonate SA',
    [EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY]: 'Create SA Key',
    [EdgeType.HAS_ROLE]: 'Has Role',
    [EdgeType.MEMBER_OF]: 'Member Of',
    [EdgeType.CAN_ADMIN]: 'Admin Access',
    [EdgeType.CAN_ACT_AS_VIA_VM]: 'Deploy as VM',
    [EdgeType.CAN_DEPLOY_FUNCTION_AS]: 'Deploy Function',
    [EdgeType.CAN_DEPLOY_CLOUD_RUN_AS]: 'Deploy Cloud Run'
  };
  
  return edgeNames[edgeType] || edgeType.replace(/_/g, ' ').toLowerCase();
};

export const AttackPathCanvas = forwardRef<AttackPathCanvasRef, AttackPathCanvasProps>((props, ref) => {
  const {
    attackPath,
    onNodeClick,
    onEdgeClick,
    className = ''
  } = props;

  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  const nodesDataSetRef = useRef<DataSet<any> | null>(null);
  const edgesDataSetRef = useRef<DataSet<any> | null>(null);
  const onNodeClickRef = useRef(onNodeClick);
  const onEdgeClickRef = useRef(onEdgeClick);
  const networkCreatedRef = useRef<string | null>(null);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [selectedEdgeId, setSelectedEdgeId] = useState<string | null>(null);

  // Update callback refs when props change
  onNodeClickRef.current = onNodeClick;
  onEdgeClickRef.current = onEdgeClick;

  // Clear selection when attack path changes
  useEffect(() => {
    setSelectedNodeId(null);
    setSelectedEdgeId(null);
  }, [attackPath]);

  // Create the network once
  useEffect(() => {
    if (!containerRef.current || !attackPath?.path_nodes?.length) return;

    // Create a unique ID for this attack path to prevent unnecessary recreations
    const attackPathId = `${attackPath.source.id}-${attackPath.target.id}-${attackPath.path_nodes.length}`;
    
    // Only create network if it doesn't exist or if the attack path changed
    if (networkCreatedRef.current === attackPathId && networkRef.current) {
      console.log('🔄 Network already exists for this attack path, skipping recreation');
      return;
    }

    console.log('🔨 Creating new network for attack path:', attackPathId);

    // Clean up existing network if it exists
    if (networkRef.current) {
      networkRef.current.destroy();
      networkRef.current = null;
    }

    // Transform nodes with modern styling
    const transformedNodes = attackPath.path_nodes.map((node, index) => {
      const isSource = node.id === attackPath.source.id;
      const isTarget = node.id === attackPath.target.id;
      const colors = getNodeColor(node.type, isSource, isTarget);
      const shape = getNodeShape(node.type, isSource, isTarget);
      
      return {
        id: node.id,
        label: node.name.length > 25 ? node.name.substring(0, 25) + '...' : node.name,
        title: `${isSource ? '🎯 START: ' : isTarget ? '🏁 TARGET: ' : '📍 STEP ' + (index + 1) + ': '}${node.type}\n${node.name}`,
        color: colors,
        shape: shape,
        size: isSource || isTarget ? 35 : 30,
        font: {
          size: 18,
          color: '#374151', // Dark grey color
          face: 'Inter, -apple-system, sans-serif',
          strokeWidth: 0,
          strokeColor: 'transparent'
        },
        borderWidth: 3,
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.2)',
          size: 8,
          x: 2,
          y: 2
        },
        physics: false,
        fixed: { x: true, y: true },
        x: 0, // Will be set below
        y: 0  // Will be set below
      };
    });

    // Transform edges
    const transformedEdges = attackPath.path_edges?.map((edge, index) => {
      const sourceId = edge.source || (edge as any).source_id || (edge as any).from;
      const targetId = edge.target || (edge as any).target_id || (edge as any).to;
      const edgeColor = getEdgeColor(edge.type);
      
      return {
        id: edge.id || `edge_${index}`,
        from: sourceId,
        to: targetId,
        label: formatEdgeType(edge.type),
        color: edgeColor,
        width: 3,
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 1.2,
            type: 'arrow'
          }
        },
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.2
        }
      };
    }) || [];

    // Create fallback edges if none exist
    if (transformedEdges.length === 0 && transformedNodes.length > 1) {
      for (let i = 0; i < transformedNodes.length - 1; i++) {
        transformedEdges.push({
          id: `step_${i}`,
          from: transformedNodes[i].id,
          to: transformedNodes[i + 1].id,
          label: `Step ${i + 1}`,
          color: '#6b7280',
          width: 3,
          arrows: {
            to: {
              enabled: true,
              scaleFactor: 1.2,
              type: 'arrow'
            }
          },
          smooth: {
            enabled: true,
            type: 'continuous',
            roundness: 0.2
          }
        });
      }
    }

    // Calculate proper spacing for horizontal layout
    const nodeSpacing = Math.max(300, Math.min(400, (containerRef.current.clientWidth - 100) / Math.max(1, transformedNodes.length - 1)));
    
    // Position nodes horizontally with proper spacing
    transformedNodes.forEach((node, index) => {
      (node as any).x = (index * nodeSpacing) - ((transformedNodes.length - 1) * nodeSpacing / 2);
      (node as any).y = 0;
    });

    // Create vis.js datasets
    nodesDataSetRef.current = new DataSet(transformedNodes);
    edgesDataSetRef.current = new DataSet(transformedEdges);

    const data = {
      nodes: nodesDataSetRef.current,
      edges: edgesDataSetRef.current
    };

    // Modern network options
    const options: Options = {
      physics: {
        enabled: false,
        stabilization: false
      },
      layout: {
        hierarchical: false
      },
      interaction: {
        hover: true,
        hoverConnectedEdges: false,
        selectConnectedEdges: false,
        zoomView: false,
        dragView: true,
        dragNodes: false,
        multiselect: false,
        tooltipDelay: 300,
        hideEdgesOnDrag: false,
        hideNodesOnDrag: false,
        keyboard: {
          enabled: false
        },
        navigationButtons: false
      },
      edges: {
        smooth: {
          enabled: true,
          type: 'continuous',
          roundness: 0.2
        },
        hoverWidth: 2,
        color: {
          highlight: '#6366f1',
          hover: '#6366f1'
        },
        font: {
          size: 14,
          color: '#374151',
          face: 'Inter, system-ui, sans-serif',
          strokeWidth: 3,
          strokeColor: '#ffffff',
          align: 'middle',
          vadjust: 0,
          background: 'rgba(255, 255, 255, 0.9)',
          multi: false
        },
        labelHighlightBold: false,
        arrows: {
          to: {
            enabled: true,
            scaleFactor: 1.2,
            type: 'arrow'
          }
        }
      },
      nodes: {
        borderWidth: 2,
        color: {
          highlight: {
            border: '#6366f1',
            background: '#eef2ff'
          }
        },
        font: {
          size: 16,
          color: '#374151',
          face: 'Inter, system-ui, sans-serif'
        },
        shadow: {
          enabled: true,
          color: 'rgba(0,0,0,0.2)',
          size: 8,
          x: 2,
          y: 2
        },
        physics: false,
        fixed: { x: true, y: true }
      },
      configure: {
        enabled: false
      }
    };

    // Create network
    networkRef.current = new Network(containerRef.current, data, options);
    networkCreatedRef.current = attackPathId; // Mark this attack path as having a network

    // Simple container setup for drag only
    if (containerRef.current) {
      containerRef.current.style.cursor = 'grab';
      containerRef.current.style.userSelect = 'none';
    }

    // Event handlers for node/edge clicks
    networkRef.current.on('click', (params) => {
      if (params.nodes.length > 0) {
        const clickedNodeId = params.nodes[0];
        console.log('🖱️ Node clicked:', clickedNodeId);
        
        setSelectedNodeId(clickedNodeId);
        setSelectedEdgeId(null);
        
        if (onNodeClickRef.current) {
          onNodeClickRef.current(clickedNodeId);
        }
      } else if (params.edges.length > 0) {
        const clickedEdgeId = params.edges[0];
        console.log('🖱️ Edge clicked:', clickedEdgeId);
        
        setSelectedEdgeId(clickedEdgeId);
        setSelectedNodeId(null);
        
        if (onEdgeClickRef.current) {
          onEdgeClickRef.current(clickedEdgeId);
        }
      } else {
        console.log('🖱️ Cleared selection');
        setSelectedNodeId(null);
        setSelectedEdgeId(null);
      }
    });

    // Cleanup
    return () => {
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
      nodesDataSetRef.current = null;
      edgesDataSetRef.current = null;
      networkCreatedRef.current = null; // Reset the tracker
    };
  }, [attackPath]);

  // Update node styling when selection changes
  useEffect(() => {
    if (!nodesDataSetRef.current || !attackPath?.path_nodes) return;

    console.log('🎯 Updating node selection:', selectedNodeId);

    // Update all nodes to reflect current selection
    const updatedNodes = attackPath.path_nodes.map((node, index) => {
      const isSource = node.id === attackPath.source.id;
      const isTarget = node.id === attackPath.target.id;
      const isSelected = selectedNodeId === node.id;
      const colors = getNodeColor(node.type, isSource, isTarget);
      const shape = getNodeShape(node.type, isSource, isTarget);

      return {
        id: node.id,
        label: node.name.length > 25 ? node.name.substring(0, 25) + '...' : node.name,
        title: `${isSource ? '🎯 START: ' : isTarget ? '🏁 TARGET: ' : '📍 STEP ' + (index + 1) + ': '}${node.type}\n${node.name}`,
        color: isSelected ? {
          background: colors.background,
          border: '#dc2626', // Red border when selected
          highlight: colors.highlight
        } : colors,
        shape: shape,
        size: isSource || isTarget ? 35 : 30,
        font: {
          size: 18,
          color: '#374151', // Dark grey color
          face: 'Inter, -apple-system, sans-serif',
          strokeWidth: 0,
          strokeColor: 'transparent'
        },
        borderWidth: isSelected ? 6 : 3,
        shadow: isSelected ? {
          enabled: true,
          color: '#dc2626',
          size: 12,
          x: 0,
          y: 0
        } : {
          enabled: true,
          color: 'rgba(0,0,0,0.2)',
          size: 8,
          x: 2,
          y: 2
        },
        physics: false,
        fixed: { x: true, y: true },
        x: (index * Math.max(300, Math.min(400, (containerRef.current?.clientWidth || 800 - 100) / Math.max(1, attackPath.path_nodes.length - 1)))) - ((attackPath.path_nodes.length - 1) * Math.max(300, Math.min(400, (containerRef.current?.clientWidth || 800 - 100) / Math.max(1, attackPath.path_nodes.length - 1))) / 2),
        y: 0
      };
    });

    nodesDataSetRef.current.update(updatedNodes);

    // Force network to redraw
    if (networkRef.current) {
      networkRef.current.redraw();
    }
  }, [selectedNodeId, attackPath]);

  // Update edge styling when selection changes
  useEffect(() => {
    if (!edgesDataSetRef.current || !attackPath?.path_nodes) return;

    console.log('🔗 Updating edge selection:', selectedEdgeId);

    let updatedEdges: any[] = [];

    // Update all edges to reflect current selection (handle both real and fallback edges)
    if (attackPath.path_edges && attackPath.path_edges.length > 0) {
      // Handle real edges
      updatedEdges = attackPath.path_edges.map((edge, index) => {
        const sourceId = edge.source || (edge as any).source_id || (edge as any).from;
        const targetId = edge.target || (edge as any).target_id || (edge as any).to;
        const edgeId = edge.id || `edge_${index}`;
        const isSelected = selectedEdgeId === edgeId;
        const edgeColor = getEdgeColor(edge.type);

        return {
          id: edgeId,
          from: sourceId,
          to: targetId,
          label: formatEdgeType(edge.type),
          color: isSelected ? '#dc2626' : edgeColor,
          width: isSelected ? 6 : 3,
          arrows: {
            to: {
              enabled: true,
              scaleFactor: 1.2,
              type: 'arrow'
            }
          },
          smooth: {
            enabled: true,
            type: 'continuous',
            roundness: 0.2
          },
          shadow: isSelected ? {
            enabled: true,
            color: '#dc2626',
            size: 8,
            x: 0,
            y: 0
          } : {
            enabled: false
          }
        };
      });
    } else {
      // Handle fallback edges (step edges)
      updatedEdges = [];
      for (let i = 0; i < attackPath.path_nodes.length - 1; i++) {
        const stepId = `step_${i}`;
        const isSelected = selectedEdgeId === stepId;

        updatedEdges.push({
          id: stepId,
          from: attackPath.path_nodes[i].id,
          to: attackPath.path_nodes[i + 1].id,
          label: `Step ${i + 1}`,
          color: isSelected ? '#dc2626' : '#6b7280',
          width: isSelected ? 6 : 3,
          arrows: {
            to: {
              enabled: true,
              scaleFactor: 1.2,
              type: 'arrow'
            }
          },
          smooth: {
            enabled: true,
            type: 'continuous',
            roundness: 0.2
          },
          shadow: isSelected ? {
            enabled: true,
            color: '#dc2626',
            size: 8,
            x: 0,
            y: 0
          } : {
            enabled: false
          }
        });
      }
    }

    edgesDataSetRef.current.update(updatedEdges);

    // Force network to redraw
    if (networkRef.current) {
      networkRef.current.redraw();
    }
  }, [selectedEdgeId, attackPath]);

  useImperativeHandle(ref, () => ({
    fitView: () => {
      if (networkRef.current) {
        networkRef.current.fit({
          animation: {
            duration: 800,
            easingFunction: 'easeInOutCubic'
          }
        });
      }
    },
    zoomIn: () => {
      const scale = networkRef.current?.getScale();
      if (scale) {
        networkRef.current?.moveTo({
          scale: Math.min(scale * 1.3, 2.0),
          animation: {
            duration: 400,
            easingFunction: 'easeInOutCubic'
          }
        });
      }
    },
    zoomOut: () => {
      const scale = networkRef.current?.getScale();
      if (scale) {
        networkRef.current?.moveTo({
          scale: Math.max(scale * 0.75, 0.2),
          animation: {
            duration: 400,
            easingFunction: 'easeInOutCubic'
          }
        });
      }
    },
    fit: () => networkRef.current?.fit(),
    focusNode: (nodeId: string) => {
      if (networkRef.current) {
        networkRef.current.focus(nodeId, {
          animation: {
            duration: 800,
            easingFunction: 'easeInOutCubic'
          },
          scale: 1.0
        });
      }
    },
    selectNode: (nodeId: string) => {
      setSelectedNodeId(nodeId);
      setSelectedEdgeId(null);
    },
    selectEdge: (edgeId: string) => {
      setSelectedEdgeId(edgeId);
      setSelectedNodeId(null);
    },
    clearSelection: () => {
      setSelectedNodeId(null);
      setSelectedEdgeId(null);
    }
  }));

  if (!attackPath?.path_nodes?.length) {
    return (
      <div className={`w-full h-full bg-gradient-to-br from-gray-50 to-white border rounded-lg flex items-center justify-center ${className}`}>
        <div className="text-center text-muted-foreground p-8">
          <div className="text-lg font-medium mb-2">No Attack Path Data</div>
          <p className="text-sm">No nodes available to visualize in this attack path.</p>
        </div>
      </div>
    );
  }

  return (
    <div 
      ref={containerRef}
      className={`w-full h-full bg-gradient-to-br from-slate-50 to-white border rounded-lg shadow-sm overflow-hidden ${className}`}
      data-testid="attack-path-canvas"
      style={{ 
        minHeight: '600px',
        minWidth: '800px',
        height: '100%',
        width: '100%'
      }}
    >
      {/* Path Info Overlay */}
      <div className="absolute top-4 right-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg border z-10">
        <div className="text-sm font-medium text-gray-700 mb-1">Attack Path</div>
        <div className="text-xs text-gray-500">
          {attackPath.length} step{attackPath.length !== 1 ? 's' : ''} • Risk: {Math.round(attackPath.risk_score * 100)}%
        </div>
      </div>

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg border z-10">
        <div className="text-sm font-medium text-gray-700 mb-2">Legend</div>
        <div className="space-y-1 text-xs">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
            <span className="text-gray-600">Source</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-red-500"></div>
            <span className="text-gray-600">Target</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 bg-gray-400 rounded-full"></div>
            <span className="text-gray-600">Intermediate</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-1 bg-red-600"></div>
            <span className="text-gray-600">Selected</span>
          </div>
        </div>
      </div>
    </div>
  );
});

AttackPathCanvas.displayName = 'AttackPathCanvas';