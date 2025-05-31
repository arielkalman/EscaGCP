import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { dataService } from '../../services/dataService';
import { DataTable, ColumnDefinition } from '../../components/shared/DataTable';
import { GhostUsersToggle } from '../../components/common/GhostUsersToggle';
import { Badge } from '../../components/ui/badge';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { 
  User, 
  Settings, 
  Users, 
  FolderOpen, 
  Building, 
  Shield, 
  Database, 
  Server, 
  Zap, 
  Key, 
  Lock,
  BarChart3,
  MessageSquare,
  Cloud,
  Container,
  Hammer,
  Monitor,
  AlertTriangle,
  Eye,
  ExternalLink
} from 'lucide-react';
import { Node, NodeType, getNodeTypeColor, getRiskLevel } from '../../types';
import { useAppSettings } from '../../context/AppSettingsContext';
import { filterGhostNodes, getGhostUserStats } from '../../utils/ghostUsers';

// Icon mapping for node types
const getNodeIcon = (nodeType: NodeType) => {
  const iconMap = {
    [NodeType.USER]: User,
    [NodeType.SERVICE_ACCOUNT]: Settings,
    [NodeType.GROUP]: Users,
    [NodeType.PROJECT]: FolderOpen,
    [NodeType.FOLDER]: FolderOpen,
    [NodeType.ORGANIZATION]: Building,
    [NodeType.ROLE]: Shield,
    [NodeType.CUSTOM_ROLE]: Shield,
    [NodeType.BUCKET]: Database,
    [NodeType.INSTANCE]: Server,
    [NodeType.FUNCTION]: Zap,
    [NodeType.SECRET]: Lock,
    [NodeType.KMS_KEY]: Key,
    [NodeType.DATASET]: BarChart3,
    [NodeType.TOPIC]: MessageSquare,
    [NodeType.CLOUD_RUN_SERVICE]: Cloud,
    [NodeType.GKE_CLUSTER]: Container,
    [NodeType.CLOUD_BUILD_TRIGGER]: Hammer,
    [NodeType.COMPUTE_INSTANCE]: Monitor
  };
  
  return iconMap[nodeType] || Monitor;
};

// Get risk level from properties or default
const getNodeRiskScore = (node: Node): number => {
  return node.properties?.risk_score || 0;
};

export function NodesPage() {
  const { settings } = useAppSettings();

  const {
    data: graphData,
    isLoading,
    error,
  } = useQuery({
    queryKey: ['graph'],
    queryFn: () => dataService.loadGraphData(),
  });

  const {
    data: analysisData,
  } = useQuery({
    queryKey: ['analysis'],
    queryFn: () => dataService.loadAnalysisData(),
  });

  // Original unfiltered data
  const allNodes = graphData?.nodes || [];
  const allEdges = graphData?.edges || [];
  
  // Calculate ghost user statistics
  const ghostUserStats = useMemo(() => {
    return getGhostUserStats(allNodes, allEdges);
  }, [allNodes, allEdges]);
  
  // Filter nodes based on ghost users setting
  const filteredNodes = useMemo(() => {
    return filterGhostNodes(allNodes, settings.showGhostUsers);
  }, [allNodes, settings.showGhostUsers]);

  const handleViewNodeDetails = (node: Node) => {
    // TODO: Implement node details modal or navigation
    alert(`View details for node: ${node.name}`);
  };

  const handleExportNodes = (selectedNodes: Node[]) => {
    const dataToExport = selectedNodes.map(node => ({
      id: node.id,
      type: node.type,
      name: node.name,
      risk_score: getNodeRiskScore(node),
      properties: node.properties
    }));
    
    const blob = new Blob([JSON.stringify(dataToExport, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `nodes_export_${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Define columns for the DataTable
  const columns: ColumnDefinition<Node>[] = [
    {
      key: 'type',
      header: 'Type',
      accessor: (node) => {
        const IconComponent = getNodeIcon(node.type);
        return (
          <div className="flex items-center space-x-2">
            <div 
              className="p-1 rounded"
              style={{ backgroundColor: `${getNodeTypeColor(node.type)}20` }}
            >
              <IconComponent 
                className="h-4 w-4" 
                style={{ color: getNodeTypeColor(node.type) }}
              />
            </div>
            <span className="font-medium capitalize">
              {node.type.replace(/_/g, ' ')}
            </span>
          </div>
        );
      },
      sortable: true,
      sortValue: (node) => node.type,
      filterable: true,
      filterType: 'select',
      filterOptions: Object.values(NodeType).map(type => ({
        value: type,
        label: type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
      })),
      searchableFields: ['type'],
      resizable: true,
      minWidth: 150,
      maxWidth: 300
    },
    {
      key: 'name',
      header: 'Name',
      accessor: (node) => (
        <div className="space-y-1">
          <div className="font-medium text-foreground break-words">
            {node.name}
          </div>
          <div className="text-xs text-muted-foreground break-words">
            {node.id}
          </div>
        </div>
      ),
      sortable: true,
      sortValue: (node) => node.name,
      filterable: true,
      width: 'min-w-[250px]',
      searchableFields: ['name', 'id', 'properties'],
      resizable: true,
      minWidth: 200,
      maxWidth: 500
    },
    {
      key: 'risk',
      header: 'Risk Level',
      accessor: (node) => {
        const riskScore = getNodeRiskScore(node);
        const riskLevel = getRiskLevel(riskScore);
        const riskColors = {
          critical: 'bg-red-100 text-red-800 border-red-200',
          high: 'bg-orange-100 text-orange-800 border-orange-200',
          medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
          low: 'bg-blue-100 text-blue-800 border-blue-200',
          info: 'bg-gray-100 text-gray-800 border-gray-200'
        };
        
        return (
          <div className="space-y-1">
            <Badge className={`${riskColors[riskLevel]} capitalize`}>
              {riskLevel}
            </Badge>
            <div className="text-xs text-muted-foreground">
              Score: {Math.round(riskScore * 100)}%
            </div>
          </div>
        );
      },
      sortable: true,
      sortValue: (node) => getNodeRiskScore(node),
      filterable: true,
      filterType: 'select',
      filterOptions: [
        { value: 'critical', label: 'Critical' },
        { value: 'high', label: 'High' },
        { value: 'medium', label: 'Medium' },
        { value: 'low', label: 'Low' },
        { value: 'info', label: 'Info' }
      ],
      searchableFields: [],
      resizable: true,
      minWidth: 120,
      maxWidth: 200
    },
    {
      key: 'properties',
      header: 'Key Properties',
      accessor: (node) => {
        const properties = node.properties || {};
        const keyProps = [];
        
        // Show different key properties based on node type
        if (properties.email) keyProps.push(`Email: ${properties.email}`);
        if (properties.project_id || properties.projectId) {
          keyProps.push(`Project: ${properties.project_id || properties.projectId}`);
        }
        if (properties.is_external) keyProps.push('External User');
        if (properties.is_dangerous) keyProps.push('Dangerous Role');
        if (properties.disabled) keyProps.push('Disabled');
        if (properties.state) keyProps.push(`State: ${properties.state}`);
        
        return (
          <div className="space-y-1">
            {keyProps.slice(0, 3).map((prop, index) => (
              <div key={index} className="text-xs text-muted-foreground break-words">
                {prop}
              </div>
            ))}
            {keyProps.length > 3 && (
              <div className="text-xs text-muted-foreground">
                +{keyProps.length - 3} more
              </div>
            )}
          </div>
        );
      },
      sortable: true,
      sortValue: (node) => {
        const properties = node.properties || {};
        // Sort by email if available, otherwise by project, otherwise by node ID
        return properties.email || properties.project_id || properties.projectId || node.id;
      },
      filterable: true,
      searchableFields: ['properties'],
      resizable: true,
      minWidth: 200,
      maxWidth: 450
    },
    {
      key: 'actions',
      header: 'Actions',
      accessor: (node) => (
        <div className="flex items-center space-x-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              handleViewNodeDetails(node);
            }}
          >
            <Eye className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={(e) => {
              e.stopPropagation();
              // TODO: Navigate to graph focused on this node
              alert(`Focus graph on: ${node.name}`);
            }}
          >
            <ExternalLink className="h-4 w-4" />
          </Button>
        </div>
      ),
      width: 'w-24',
      searchableFields: [],
      resizable: true,
      minWidth: 100,
      maxWidth: 150
    }
  ];

  if (error) {
    return (
      <div className="p-6">
        <Alert>
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            Failed to load nodes data: {error.message}
          </AlertDescription>
        </Alert>
      </div>
    );
  }

  // Use filtered data for display and statistics
  const totalNodes = filteredNodes.length;
  const totalOriginalNodes = allNodes.length;
  
  const nodeTypeStats = filteredNodes.reduce((acc, node) => {
    acc[node.type] = (acc[node.type] || 0) + 1;
    return acc;
  }, {} as Record<NodeType, number>);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/20 to-purple-50/20">
      <div className="p-6 space-y-6 max-w-7xl mx-auto">
        {/* Header */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-foreground">Nodes</h1>
              <p className="text-muted-foreground">
                Explore and manage all nodes in your GCP environment
                {totalOriginalNodes !== totalNodes && (
                  <span className="ml-2 text-sm">
                    (Showing {totalNodes} of {totalOriginalNodes} nodes)
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
                    <Database className="h-5 w-5 text-blue-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Total Nodes</p>
                    <p className="text-2xl font-bold">{totalNodes}</p>
                    {totalOriginalNodes !== totalNodes && (
                      <p className="text-xs text-muted-foreground">
                        of {totalOriginalNodes}
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-green-100 rounded-lg">
                    <User className="h-5 w-5 text-green-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Users</p>
                    <p className="text-2xl font-bold">
                      {nodeTypeStats[NodeType.USER] || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Settings className="h-5 w-5 text-purple-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Service Accounts</p>
                    <p className="text-2xl font-bold">
                      {nodeTypeStats[NodeType.SERVICE_ACCOUNT] || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-orange-100 rounded-lg">
                    <FolderOpen className="h-5 w-5 text-orange-600" />
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">Projects</p>
                    <p className="text-2xl font-bold">
                      {nodeTypeStats[NodeType.PROJECT] || 0}
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Nodes Table */}
        <DataTable
          data={filteredNodes}
          columns={columns}
          title="All Nodes"
          searchable={true}
          searchPlaceholder="Search nodes by name, ID, or email..."
          filterable={true}
          selectable={true}
          pagination={true}
          pageSize={20}
          exportable={true}
          onExport={handleExportNodes}
          onRowClick={handleViewNodeDetails}
          loading={isLoading}
          emptyMessage="No nodes found in your environment"
          className="bg-white/50 backdrop-blur-sm"
        />
      </div>
    </div>
  );
} 