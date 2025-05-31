import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dataService } from '../../services/dataService';
import { AggregatedEdgesTable } from '../../components/shared/AggregatedEdgesTable';
import { GhostUsersToggle } from '../../components/common/GhostUsersToggle';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  AlertTriangle,
  Link2,
  UserCheck,
  Shield,
  Expand,
  Minimize
} from 'lucide-react';
import { Edge, EdgeType } from '../../types';
import { useAppSettings } from '../../context/AppSettingsContext';
import { 
  aggregateEdgesBySource, 
  toggleGroupExpansion, 
  expandAllGroups, 
  collapseAllGroups 
} from '../../utils/edgeAggregation';
import { getGhostUserStats } from '../../utils/ghostUsers';

// Get edge type category and risk level
const getEdgeCategory = (edgeType: EdgeType): { category: string; risk: 'critical' | 'high' | 'medium' | 'low' } => {
  const privilegeEscalationEdges = [
    EdgeType.CAN_IMPERSONATE,
    EdgeType.CAN_IMPERSONATE_SA,
    EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY,
    EdgeType.CAN_ACT_AS_VIA_VM,
    EdgeType.CAN_DEPLOY_FUNCTION_AS,
    EdgeType.CAN_DEPLOY_CLOUD_RUN_AS,
    EdgeType.CAN_TRIGGER_BUILD_AS,
    EdgeType.CAN_DEPLOY_GKE_POD_AS,
    EdgeType.HAS_IMPERSONATED,
    EdgeType.HAS_ESCALATED_PRIVILEGE
  ];

  const adminEdges = [EdgeType.CAN_ADMIN, EdgeType.CAN_LOGIN_TO_VM];
  const accessEdges = [EdgeType.CAN_READ, EdgeType.CAN_WRITE, EdgeType.HAS_ACCESSED];
  
  if (privilegeEscalationEdges.includes(edgeType)) {
    return { category: 'Privilege Escalation', risk: 'critical' };
  } else if (adminEdges.includes(edgeType)) {
    return { category: 'Administrative', risk: 'high' };
  } else if (accessEdges.includes(edgeType)) {
    return { category: 'Access Control', risk: 'medium' };
  } else {
    return { category: 'Structural', risk: 'low' };
  }
};

export function EdgesPage() {
  const [expandedGroups, setExpandedGroups] = useState<Set<string>>(new Set());
  const { settings } = useAppSettings();

  const {
    data: graphData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['graph'],
    queryFn: () => dataService.loadGraphData(),
  });

  // Original unfiltered data
  const allEdges = graphData?.edges || [];
  const allNodes = graphData?.nodes || [];
  
  // Calculate ghost user statistics
  const ghostUserStats = useMemo(() => {
    return getGhostUserStats(allNodes, allEdges);
  }, [allNodes, allEdges]);
  
  // Memoize aggregated data based on underlying data, expansion state, and ghost user setting
  const aggregatedData = useMemo(() => {
    if (allEdges.length === 0) return aggregateEdgesBySource([], [], new Set(), settings.showGhostUsers);
    return aggregateEdgesBySource(allEdges, allNodes, expandedGroups, settings.showGhostUsers);
  }, [allEdges, allNodes, expandedGroups, settings.showGhostUsers]);

  const handleViewEdgeDetails = (edge: Edge) => {
    // TODO: Implement edge details modal or navigation
    alert(`View details for edge: ${edge.source} -> ${edge.target} (${edge.type})`);
  };

  const handleExportEdges = (selectedEdges: Edge[]) => {
    const dataToExport = selectedEdges.map(edge => ({
      source: edge.source,
      target: edge.target,
      type: edge.type,
      properties: edge.properties,
      category: getEdgeCategory(edge.type).category,
      risk_level: getEdgeCategory(edge.type).risk
    }));
    
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `edges_export_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleToggleGroup = useCallback((sourceNodeId: string) => {
    setExpandedGroups(prev => {
      const newSet = new Set(prev);
      if (newSet.has(sourceNodeId)) {
        newSet.delete(sourceNodeId);
      } else {
        newSet.add(sourceNodeId);
      }
      return newSet;
    });
  }, []);

  const handleExpandAll = useCallback(() => {
    const allSourceIds = new Set(aggregatedData.groups.map(g => g.sourceNodeId));
    setExpandedGroups(allSourceIds);
  }, [aggregatedData.groups]);

  const handleCollapseAll = useCallback(() => {
    setExpandedGroups(new Set());
  }, []);

  if (error) {
    return (
      <div className="p-6">
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Failed to load edges data: {error.message}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Use current displayed data for statistics (filtered or unfiltered)
  const displayedEdges = aggregatedData.groups.flatMap(g => g.edges);
  const totalEdges = displayedEdges.length;
  const totalOriginalEdges = allEdges.length;
  
  // Calculate statistics from displayed edges
  const edgeTypeStats = displayedEdges.reduce((acc, edge) => {
    acc[edge.type] = (acc[edge.type] || 0) + 1;
    return acc;
  }, {} as Record<EdgeType, number>);

  const categoryStats = displayedEdges.reduce((acc, edge) => {
    const { category } = getEdgeCategory(edge.type);
    acc[category] = (acc[category] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const riskStats = displayedEdges.reduce((acc, edge) => {
    const { risk } = getEdgeCategory(edge.type);
    acc[risk] = (acc[risk] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/20 to-purple-50/20">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Edges</h1>
              <p className="text-muted-foreground">
                Explore relationships and connections in your GCP environment - grouped by source entity
                {totalOriginalEdges !== totalEdges && (
                  <span className="ml-2 text-sm">
                    (Showing {totalEdges} of {totalOriginalEdges} edges)
                  </span>
                )}
              </p>
            </div>
            
            {/* Ghost Users Toggle */}
            <GhostUsersToggle 
              ghostUserStats={ghostUserStats}
              size="md"
              showLabel={true}
              showStats={true}
            />
          </div>

          {/* Statistics Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <Link2 className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Edges</p>
                    <p className="text-2xl font-bold">{totalEdges}</p>
                    {totalOriginalEdges !== totalEdges && (
                      <p className="text-xs text-muted-foreground">
                        of {totalOriginalEdges}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Critical Risk</p>
                    <p className="text-2xl font-bold">
                      {riskStats.critical || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <UserCheck className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Privilege Escalation</p>
                    <p className="text-2xl font-bold">
                      {categoryStats['Privilege Escalation'] || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <Shield className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Source Entities</p>
                    <p className="text-2xl font-bold">
                      {aggregatedData.totalGroups}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Aggregated View Controls */}
          <div className="flex items-center justify-between p-4 bg-white rounded-lg border">
            <div className="flex items-center space-x-4">
              <h3 className="font-medium text-foreground">Group Controls</h3>
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExpandAll}
                  className="flex items-center space-x-2"
                >
                  <Expand className="h-4 w-4" />
                  <span>Expand All</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleCollapseAll}
                  className="flex items-center space-x-2"
                >
                  <Minimize className="h-4 w-4" />
                  <span>Collapse All</span>
                </Button>
              </div>
            </div>
            
            <div className="text-sm text-muted-foreground">
              {aggregatedData.totalGroups} source entities with {aggregatedData.totalEdges} total relationships
            </div>
          </div>
        </div>

        {/* Edges Table */}
        <AggregatedEdgesTable
          aggregatedData={aggregatedData}
          nodes={allNodes}
          title="Relationships (Grouped by Source Entity)"
          searchable={true}
          filterable={true}
          selectable={true}
          pagination={true}
          pageSize={20}
          exportable={true}
          onExport={handleExportEdges}
          onEdgeClick={(edge) => {
            // TODO: Navigate to graph focused on this edge
            console.log('Edge clicked:', edge);
          }}
          onViewEdgeDetails={handleViewEdgeDetails}
          loading={isLoading}
          emptyMessage="No relationships found in your GCP environment"
          onToggleGroup={handleToggleGroup}
        />
      </div>
    </div>
  );
} 