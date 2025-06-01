import { useState, useRef, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dataService } from '../../services/dataService';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { GhostUsersToggle } from '../../components/common/GhostUsersToggle';
import { GraphCanvas } from '../../components/graph/GraphCanvas';
import { GraphControls } from '../../components/graph/GraphControls';
import { GraphLegend } from '../../components/graph/GraphLegend';
import { GraphFilters } from '../../components/graph/GraphFilters';
import { GraphSearch } from '../../components/graph/GraphSearch';
import { NodeDetailPanel } from '../../components/panels/NodeDetailPanel';
import { EdgeExplanationPanel } from '../../components/panels/EdgeExplanationPanel';
import { AttackPathPanel } from '../../components/panels/AttackPathPanel';
import { GraphProvider, useGraphContext } from '../../context/GraphContext';
import { useAppSettings } from '../../context/AppSettingsContext';
import { filterGhostNodes, filterGhostEdges, getGhostUserStats } from '../../utils/ghostUsers';
import type { 
  GraphNode, 
  GraphEdge, 
  RiskLevel 
} from '../../types';
import { NodeType, EdgeType } from '../../types';
import { 
  PanelLeftOpen, 
  PanelLeftClose,
  PanelRightOpen,
  PanelRightClose,
  AlertCircle,
  RefreshCw,
  Network,
  Target,
  Zap,
  Building2
} from 'lucide-react';
import { Button } from '../../components/ui/button';
import { Card, CardContent } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';

function GraphContent() {
  const { selectNode, selectEdge } = useGraphContext();
  const { settings } = useAppSettings();
  
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [selectedNodeId, setSelectedNodeId] = useState<string | undefined>();
  const [highlightedNodes, setHighlightedNodes] = useState<Set<string>>(new Set());
  const [isPhysicsEnabled, setIsPhysicsEnabled] = useState(true);
  const [isHierarchicalLayout, setIsHierarchicalLayout] = useState(false);
  
  // Filter states - Updated to use selectedNodeTypes for actual filtering
  const [selectedNodeTypes, setSelectedNodeTypes] = useState<Set<string>>(new Set());
  const [selectedEdgeTypes, setSelectedEdgeTypes] = useState<Set<string>>(new Set());
  const [selectedRiskLevels, setSelectedRiskLevels] = useState<Set<RiskLevel>>(
    new Set(['critical', 'high', 'medium', 'low', 'info'])
  );
  const [minRiskScore, setMinRiskScore] = useState(0);
  const [maxRiskScore, setMaxRiskScore] = useState(1);
  
  const graphCanvasRef = useRef<any>(null);

  // Load graph data
  const { data: graphData, isLoading, error, refetch } = useQuery({
    queryKey: ['graphData'],
    queryFn: () => dataService.loadGraphData(),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });

  // Original unfiltered data
  const allNodes: GraphNode[] = graphData?.nodes || [];
  const allEdges: GraphEdge[] = graphData?.edges || [];
  
  // Calculate ghost user statistics
  const ghostUserStats = useMemo(() => {
    return getGhostUserStats(allNodes, allEdges);
  }, [allNodes, allEdges]);

  // Apply ghost user filtering first - ALWAYS call these hooks
  const ghostFilteredNodes = useMemo(() => {
    return filterGhostNodes(allNodes, settings.showGhostUsers);
  }, [allNodes, settings.showGhostUsers]);

  const ghostFilteredEdges = useMemo(() => {
    return filterGhostEdges(allEdges, allNodes, settings.showGhostUsers);
  }, [allEdges, allNodes, settings.showGhostUsers]);

  // Use ghost-filtered data for further processing
  const nodes: GraphNode[] = ghostFilteredNodes;
  const edges: GraphEdge[] = ghostFilteredEdges;

  // Get unique node and edge types - ALWAYS call these
  const availableNodeTypes = useMemo(() => {
    return Array.from(new Set(nodes.map(n => n.type))) as NodeType[];
  }, [nodes]);
  
  const availableEdgeTypes = useMemo(() => {
    return Array.from(new Set(edges.map(e => e.type))) as EdgeType[];
  }, [edges]);

  // Count nodes and edges by type - ALWAYS call these
  const nodeCounts = useMemo(() => {
    return nodes.reduce((acc, node) => {
      acc[node.type] = (acc[node.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [nodes]);

  const edgeCounts = useMemo(() => {
    return edges.reduce((acc, edge) => {
      acc[edge.type] = (acc[edge.type] || 0) + 1;
      return acc;
    }, {} as Record<string, number>);
  }, [edges]);

  // Apply filtering logic - ALWAYS define these functions
  const getNodeRiskScore = (node: GraphNode): number => {
    // Mock risk calculation - in a real app this would come from analysis data
    if (node.type === NodeType.SERVICE_ACCOUNT) return 0.7;
    if (node.name.toLowerCase().includes('admin')) return 0.8;
    if (node.name.toLowerCase().includes('owner')) return 0.9;
    if (node.type === NodeType.USER && node.name.includes('@gmail.com')) return 0.6;
    return Math.random() * 0.5; // Low risk for others
  };

  const getNodeRiskLevel = (riskScore: number): RiskLevel => {
    if (riskScore >= 0.8) return 'critical';
    if (riskScore >= 0.6) return 'high';
    if (riskScore >= 0.4) return 'medium';
    if (riskScore >= 0.2) return 'low';
    return 'info';
  };

  // Filter nodes based on current filter settings - ALWAYS calculate
  const filteredNodes = useMemo(() => {
    return nodes.filter(node => {
      // Node type filtering - if no types selected, show all
      if (selectedNodeTypes.size > 0 && !selectedNodeTypes.has(node.type)) {
        return false;
      }

      // Risk level filtering
      const riskScore = getNodeRiskScore(node);
      const riskLevel = getNodeRiskLevel(riskScore);
      
      if (!selectedRiskLevels.has(riskLevel)) {
        return false;
      }

      // Risk score range filtering
      if (riskScore < minRiskScore || riskScore > maxRiskScore) {
        return false;
      }

      return true;
    });
  }, [nodes, selectedNodeTypes, selectedRiskLevels, minRiskScore, maxRiskScore]);

  // Filter edges based on current filter settings and filtered nodes - ALWAYS calculate
  const filteredEdges = useMemo(() => {
    const filteredNodeIds = new Set(filteredNodes.map(n => n.id));
    return edges.filter(edge => {
      // Edge type filtering - if no types selected, show all
      if (selectedEdgeTypes.size > 0 && !selectedEdgeTypes.has(edge.type)) {
        return false;
      }

      // Only show edges where both source and target nodes are visible
      return filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target);
    });
  }, [edges, filteredNodes, selectedEdgeTypes]);

  // Event handlers - ALWAYS define these
  const handleNodeClick = (nodeId: string, nodeData: GraphNode) => {
    console.log('Node clicked:', nodeId, nodeData);
    setSelectedNodeId(nodeId);
    selectNode(nodeData); // Use context to select node and open panel
  };

  const handleEdgeClick = (edgeId: string, edgeData: GraphEdge) => {
    console.log('Edge clicked:', edgeId, edgeData);
    selectEdge(edgeData); // Use context to select edge and open panel
  };

  const handleNodeHover = (_nodeId: string | null) => {
    // TODO: Show hover tooltip
  };

  const handleEdgeHover = (_edgeId: string | null) => {
    // TODO: Show hover tooltip
  };

  const handleZoomIn = () => {
    graphCanvasRef.current?.zoomIn();
  };

  const handleZoomOut = () => {
    graphCanvasRef.current?.zoomOut();
  };

  const handleFit = () => {
    graphCanvasRef.current?.fit();
  };

  const handleReset = () => {
    setSelectedNodeId(undefined);
    setHighlightedNodes(new Set());
    handleFit();
  };

  const handleExport = () => {
    try {
      // First try to find vis-network canvas
      const visCanvas = document.querySelector('canvas[data-id="vis-canvas"]') ||
                       document.querySelector('.vis-network canvas') ||
                       document.querySelector('canvas');
      
      if (visCanvas) {
        const canvas = visCanvas as HTMLCanvasElement;
        
        // Create download link
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().split('T')[0];
        link.download = `gcphound-graph-${timestamp}.png`;
        
        // Convert canvas to blob and download
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob);
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
            console.log('Graph exported successfully');
          } else {
            throw new Error('Failed to create blob from canvas');
          }
        }, 'image/png');
      } else {
        // Fallback: Export graph data as JSON
        const graphData = {
          nodes: filteredNodes,
          edges: filteredEdges,
          metadata: {
            exportTime: new Date().toISOString(),
            totalNodes: filteredNodes.length,
            totalEdges: filteredEdges.length,
            filters: {
              selectedNodeTypes: Array.from(selectedNodeTypes),
              selectedEdgeTypes: Array.from(selectedEdgeTypes),
              selectedRiskLevels: Array.from(selectedRiskLevels),
              riskScoreRange: [minRiskScore, maxRiskScore],
              showGhostUsers: settings.showGhostUsers
            }
          }
        };
        
        const dataStr = JSON.stringify(graphData, null, 2);
        const dataBlob = new Blob([dataStr], { type: 'application/json' });
        const url = URL.createObjectURL(dataBlob);
        
        const link = document.createElement('a');
        const timestamp = new Date().toISOString().split('T')[0];
        link.download = `gcphound-graph-data-${timestamp}.json`;
        link.href = url;
        link.click();
        URL.revokeObjectURL(url);
        
        console.log('Graph data exported as JSON (canvas not available)');
      }
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed. Please try again or check the console for details.');
    }
  };

  const handleTogglePhysics = () => {
    setIsPhysicsEnabled(!isPhysicsEnabled);
    // TODO: Update vis-network physics settings
  };

  const handleToggleLayout = () => {
    setIsHierarchicalLayout(!isHierarchicalLayout);
    // TODO: Update vis-network layout settings
  };

  const handleSettings = () => {
    // Open a simple settings dialog
    const settingsOptions = [
      'Physics: ' + (isPhysicsEnabled ? 'Enabled' : 'Disabled'),
      'Layout: ' + (isHierarchicalLayout ? 'Hierarchical' : 'Force-directed'),
      `Nodes: ${filteredNodes.length}/${nodes.length}`,
      `Edges: ${filteredEdges.length}/${edges.length}`,
      `Ghost Users: ${settings.showGhostUsers ? 'Visible' : 'Hidden'}`,
      'Export Options: PNG, JSON'
    ].join('\n');
    
    const userChoice = confirm(
      `Graph Settings:\n\n${settingsOptions}\n\nWould you like to reset all settings to default?`
    );
    
    if (userChoice) {
      // Reset all settings
      setIsPhysicsEnabled(true);
      setIsHierarchicalLayout(false);
      handleFiltersReset();
      handleReset();
      console.log('Settings reset to default');
    }
  };

  const handleFocusHighRisk = () => {
    // Find high-risk nodes (mock risk calculation for now)
    const highRiskNodes = nodes.filter(node => {
      // Mock risk calculation - in reality this would come from analysis data
      const mockRiskScore = Math.random();
      return mockRiskScore >= 0.6 || 
             node.type === NodeType.SERVICE_ACCOUNT ||
             node.name.toLowerCase().includes('admin') ||
             node.name.toLowerCase().includes('owner');
    });
    
    if (highRiskNodes.length > 0) {
      const highRiskNodeIds = highRiskNodes.map(n => n.id);
      setHighlightedNodes(new Set(highRiskNodeIds));
      
      // Focus on the first high-risk node
      graphCanvasRef.current?.focusNode(highRiskNodes[0].id);
      
      console.log('Focused on high-risk nodes:', highRiskNodeIds);
    } else {
      alert('No high-risk nodes found in the current graph.');
    }
  };

  const handleShowAttackPaths = () => {
    // Find potential attack paths (mock implementation)
    const dangerousEdges = edges.filter(edge => 
      edge.type === EdgeType.CAN_IMPERSONATE_SA ||
      edge.type === EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY ||
      edge.type === EdgeType.CAN_ADMIN ||
      edge.type === EdgeType.CAN_IMPERSONATE
    );
    
    if (dangerousEdges.length > 0) {
      // Highlight nodes involved in dangerous relationships
      const attackPathNodes = new Set<string>();
      dangerousEdges.forEach(edge => {
        attackPathNodes.add(edge.source);
        attackPathNodes.add(edge.target);
      });
      
      setHighlightedNodes(attackPathNodes);
      
      // Focus on the first attack path node
      const firstNode = Array.from(attackPathNodes)[0];
      if (firstNode) {
        graphCanvasRef.current?.focusNode(firstNode);
      }
      
      console.log('Highlighted attack paths:', Array.from(attackPathNodes));
    } else {
      alert('No attack paths found in the current graph.');
    }
  };

  const handleCenterOrganization = () => {
    // Find organization nodes
    const orgNodes = nodes.filter(node => node.type === NodeType.ORGANIZATION);
    
    if (orgNodes.length > 0) {
      // Focus on the first organization node
      graphCanvasRef.current?.focusNode(orgNodes[0].id);
      setHighlightedNodes(new Set([orgNodes[0].id]));
      
      console.log('Centered on organization:', orgNodes[0].name);
    } else {
      // If no organization nodes, focus on the first project or folder
      const hierarchyNodes = nodes.filter(node => 
        node.type === NodeType.PROJECT || node.type === NodeType.FOLDER
      );
      
      if (hierarchyNodes.length > 0) {
        graphCanvasRef.current?.focusNode(hierarchyNodes[0].id);
        setHighlightedNodes(new Set([hierarchyNodes[0].id]));
        console.log('Centered on hierarchy node:', hierarchyNodes[0].name);
      } else {
        alert('No organization or hierarchy nodes found in the current graph.');
      }
    }
  };

  const handleNodeSearch = (nodeId: string) => {
    setSelectedNodeId(nodeId);
    graphCanvasRef.current?.focusNode(nodeId);
  };

  const handleSearchHighlight = (nodeIds: string[]) => {
    setHighlightedNodes(new Set(nodeIds));
  };

  const handleSearchClear = () => {
    setHighlightedNodes(new Set());
    setSelectedNodeId(undefined);
  };

  const handleFiltersReset = () => {
    setSelectedNodeTypes(new Set());
    setSelectedEdgeTypes(new Set());
    setSelectedRiskLevels(new Set(['critical', 'high', 'medium', 'low', 'info']));
    setMinRiskScore(0);
    setMaxRiskScore(1);
  };

  const handleNodeTypeToggle = (nodeType: string) => {
    setSelectedNodeTypes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(nodeType)) {
        newSet.delete(nodeType);
      } else {
        newSet.add(nodeType);
      }
      return newSet;
    });
  };

  const handleEdgeTypeToggle = (edgeType: string) => {
    setSelectedEdgeTypes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(edgeType)) {
        newSet.delete(edgeType);
      } else {
        newSet.add(edgeType);
      }
      return newSet;
    });
  };

  // NOW handle all conditional rendering at the very end
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error || !graphData) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="p-6">
          <CardContent className="flex flex-col items-center text-center space-y-4">
            <AlertCircle className="w-12 h-12 text-red-500" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">Error: Failed to Load Graph</h3>
              <p className="text-gray-600 mt-1">
                Could not load the graph data. Please try again.
              </p>
              {/* Show specific error message for tests */}
              <p className="text-red-600 text-sm mt-2">
                {error?.message || 'An unexpected error occurred'}
              </p>
            </div>
            <Button onClick={() => refetch()} className="flex items-center space-x-2">
              <RefreshCw className="w-4 h-4" />
              <span>Retry</span>
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Handle empty graph data
  if (nodes.length === 0 && edges.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <Card className="p-6">
          <CardContent className="flex flex-col items-center text-center space-y-4">
            <Network className="w-12 h-12 text-gray-400" />
            <div>
              <h3 className="text-lg font-semibold text-gray-900">No Data Available</h3>
              <p className="text-gray-600 mt-1">
                The graph is empty. Please ensure data has been collected and processed.
              </p>
              {/* Add empty message for tests */}
              <p className="text-gray-500 text-sm mt-2">
                No graph data found. Check your data collection configuration.
              </p>
            </div>
            <div data-testid="graph-controls" className="flex space-x-2">
              <Button onClick={() => refetch()} variant="outline" className="flex items-center space-x-2">
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Now render the main component
  return (
    <div className="h-full flex bg-gray-50 relative">
      {/* Page Header Bar - Fixed at top */}
      <div className="absolute top-0 left-0 right-0 z-40 bg-white border-b border-gray-200 shadow-sm">
        <div className="flex items-center justify-between px-4 py-2">
          {/* Left side - Title and ghost users info */}
          <div className="flex items-center space-x-3">
            <h1 className="text-lg font-semibold text-gray-900">
              Graph Visualization
            </h1>
            {ghostUserStats.totalGhostNodes > 0 && !settings.showGhostUsers && (
              <Badge variant="secondary" className="text-xs">
                {ghostUserStats.totalGhostNodes} ghost users hidden
              </Badge>
            )}
          </div>
          
          {/* Right side - Ghost Users Toggle */}
          <div className="flex items-center">
            <GhostUsersToggle 
              ghostUserStats={ghostUserStats}
              size="sm"
              showLabel={false}
              showStats={true}
            />
          </div>
        </div>
      </div>
      
      {/* Left Panel - Search & Filters */}
      <div className={`transition-all duration-300 ${leftPanelOpen ? 'w-80' : 'w-0'} 
        overflow-hidden bg-white border-r border-gray-200 z-10 mt-12`}>
        <div className="h-full flex flex-col p-4 space-y-4 overflow-y-auto">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Search & Filters</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setLeftPanelOpen(false)}
              className="w-8 h-8 p-0"
              aria-label="Close search and filters panel"
            >
              <PanelLeftClose className="w-4 h-4" />
            </Button>
          </div>

          {/* Ghost User Info */}
          {ghostUserStats.totalGhostNodes > 0 && (
            <div className="p-3 bg-gray-50 rounded-lg border-l-4 border-l-gray-400">
              <div className="text-sm">
                <p className="font-medium text-gray-900">Ghost Users</p>
                <p className="text-gray-600 text-xs mt-1">
                  {settings.showGhostUsers 
                    ? `Showing ${ghostUserStats.totalGhostNodes} ghost users`
                    : `${ghostUserStats.totalGhostNodes} ghost users hidden`
                  }
                </p>
              </div>
            </div>
          )}

          <GraphSearch
            nodes={nodes}
            onNodeSelect={handleNodeSearch}
            onNodeHighlight={handleSearchHighlight}
            onSearchClear={handleSearchClear}
            selectedNodeId={selectedNodeId}
            highlightedNodeIds={Array.from(highlightedNodes)}
          />

          <GraphFilters
            availableNodeTypes={availableNodeTypes}
            availableEdgeTypes={availableEdgeTypes}
            selectedNodeTypes={selectedNodeTypes}
            selectedEdgeTypes={selectedEdgeTypes}
            selectedRiskLevels={selectedRiskLevels}
            minRiskScore={minRiskScore}
            maxRiskScore={maxRiskScore}
            onNodeTypeChange={setSelectedNodeTypes}
            onEdgeTypeChange={setSelectedEdgeTypes}
            onRiskLevelChange={setSelectedRiskLevels}
            onRiskScoreChange={(min, max) => {
              setMinRiskScore(min);
              setMaxRiskScore(max);
            }}
            onReset={handleFiltersReset}
            nodeCounts={nodeCounts}
            edgeCounts={edgeCounts}
          />
        </div>
      </div>

      {/* Main Graph Area */}
      <div className="flex-1 flex flex-col relative mt-12">
        {/* Top Controls - Positioned below header */}
        <div className="absolute top-4 left-4 z-30 flex space-x-2">
          {!leftPanelOpen && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLeftPanelOpen(true)}
              className="bg-white shadow-sm"
              aria-label="Open search and filters panel"
            >
              <PanelLeftOpen className="w-4 h-4" />
            </Button>
          )}
        </div>

        <div className="absolute top-4 right-4 z-30 flex space-x-2">
          {!rightPanelOpen && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => setRightPanelOpen(true)}
              className="bg-white shadow-sm"
              aria-label="Open controls and legend panel"
            >
              <PanelRightOpen className="w-4 h-4" />
            </Button>
          )}
        </div>

        {/* Graph Canvas */}
        <div className="flex-1 relative">
          <GraphCanvas
            ref={graphCanvasRef}
            nodes={filteredNodes}
            edges={filteredEdges}
            selectedNodes={selectedNodeId ? new Set([selectedNodeId]) : new Set()}
            highlightedNodes={highlightedNodes}
            onNodeClick={handleNodeClick}
            onEdgeClick={handleEdgeClick}
            className="w-full h-full"
          />

          {/* Graph Statistics Overlay */}
          <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur-sm rounded-lg p-3 shadow-lg border z-20">
            <div className="text-sm space-y-1">
              <div className="font-medium text-gray-700">Graph Statistics</div>
              <div className="text-gray-600">
                Nodes: {filteredNodes.length}/{nodes.length}
              </div>
              <div className="text-gray-600">
                Edges: {filteredEdges.length}/{edges.length}
              </div>
              {ghostUserStats.totalGhostNodes > 0 && (
                <div className="text-gray-600">
                  Ghost Users: {settings.showGhostUsers ? 'Visible' : 'Hidden'}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Right Panel - Controls & Legend */}
      <div className={`transition-all duration-300 ${rightPanelOpen ? 'w-80' : 'w-0'} 
        overflow-hidden bg-white border-l border-gray-200 z-10 mt-12`}>
        <div className="h-full flex flex-col">
          {/* Panel Header */}
          <div className="flex items-center justify-between p-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Controls & Legend</h2>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setRightPanelOpen(false)}
              className="w-8 h-8 p-0"
              aria-label="Close controls and legend panel"
            >
              <PanelRightClose className="w-4 h-4" />
            </Button>
          </div>

          <div className="flex-1 p-4 space-y-6 overflow-y-auto">
            {/* Graph Controls */}
            <GraphControls
              onZoomIn={handleZoomIn}
              onZoomOut={handleZoomOut}
              onFit={handleFit}
              onReset={handleReset}
              onExport={handleExport}
              onTogglePhysics={handleTogglePhysics}
              onToggleLayout={handleToggleLayout}
              onSettings={handleSettings}
              isPhysicsEnabled={isPhysicsEnabled}
              isHierarchicalLayout={isHierarchicalLayout}
            />

            {/* Quick Actions */}
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-900">Quick Actions</h3>
              <div className="grid grid-cols-1 gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleFocusHighRisk}
                  className="justify-start text-xs"
                >
                  <Target className="w-3 h-3 mr-2" />
                  Focus High Risk
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleShowAttackPaths}
                  className="justify-start text-xs"
                >
                  <Zap className="w-3 h-3 mr-2" />
                  Show Attack Paths
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCenterOrganization}
                  className="justify-start text-xs"
                >
                  <Building2 className="w-3 h-3 mr-2" />
                  Center Organization
                </Button>
              </div>
            </div>

            {/* Graph Legend */}
            <GraphLegend
              nodeTypes={availableNodeTypes}
              edgeTypes={availableEdgeTypes}
              nodeCounts={nodeCounts}
              edgeCounts={edgeCounts}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

// Main exported component wrapped with GraphProvider
export function Graph() {
  return (
    <GraphProvider>
      <GraphContent />
    </GraphProvider>
  );
} 