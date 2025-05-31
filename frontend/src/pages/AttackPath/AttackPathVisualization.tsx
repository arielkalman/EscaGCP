import React, { useState, useRef, useEffect, useMemo } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { 
  ArrowLeft, 
  ZoomIn, 
  ZoomOut, 
  RotateCcw, 
  Maximize, 
  Info,
  AlertTriangle,
  Clock,
  Target,
  User,
  Shield
} from 'lucide-react';
import { AttackPath, AttackPathDetailsProps, getRiskLevel } from '../../types';
import { AttackPathCanvas, AttackPathCanvasRef } from '../../components/graph/AttackPathCanvas';
import { GhostUsersToggle } from '../../components/common/GhostUsersToggle';
import { Button } from '../../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { useAppSettings } from '../../context/AppSettingsContext';

export function AttackPathVisualization() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const canvasRef = useRef<AttackPathCanvasRef>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('overview');

  const { settings } = useAppSettings();

  // Get attack path data from URL params
  const attackPathDataParam = searchParams.get('data');
  const attackPath: AttackPath | null = attackPathDataParam 
    ? JSON.parse(decodeURIComponent(attackPathDataParam))
    : null;

  // Check if the attack path involves ghost users
  const ghostUserInfo = useMemo(() => {
    if (!attackPath) return { hasGhostUsers: false, ghostNodes: [] };

    // Helper function to check if a node might be a ghost user
    const isNodeGhost = (node: any) => {
      if (!node) return false;
      const id = node.id || '';
      const name = node.name || '';
      return id.startsWith('deleted:') || name.startsWith('deleted:') || 
             name.includes('deleted') || id.includes('deleted') ||
             (node.properties?.deleted === true) ||
             (node.properties?.state === 'DELETED');
    };

    const ghostNodes = [];
    
    // Check source and target
    if (isNodeGhost(attackPath.source)) {
      ghostNodes.push({ ...attackPath.source, role: 'source' });
    }
    if (isNodeGhost(attackPath.target)) {
      ghostNodes.push({ ...attackPath.target, role: 'target' });
    }
    
    // Check intermediate nodes
    attackPath.path_nodes?.forEach((node, index) => {
      if (isNodeGhost(node)) {
        ghostNodes.push({ ...node, role: `step ${index + 1}` });
      }
    });

    return {
      hasGhostUsers: ghostNodes.length > 0,
      ghostNodes
    };
  }, [attackPath]);

  useEffect(() => {
    if (!attackPath) {
      // If no attack path data, redirect back to findings
      navigate('/findings');
    }
  }, [attackPath, navigate]);

  if (!attackPath) {
    return (
      <div className="p-6 text-center">
        <AlertTriangle className="h-16 w-16 text-red-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold mb-2">Attack Path Not Found</h2>
        <p className="text-muted-foreground mb-4">
          The requested attack path could not be loaded.
        </p>
        <Button onClick={() => navigate('/findings')}>
          Return to Findings
        </Button>
      </div>
    );
  }

  const riskLevel = getRiskLevel(attackPath.risk_score);
  
  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-600 text-white border-red-600';
      case 'high': return 'bg-orange-600 text-white border-orange-600';
      case 'medium': return 'bg-yellow-600 text-white border-yellow-600';
      case 'low': return 'bg-blue-600 text-white border-blue-600';
      default: return 'bg-gray-600 text-white border-gray-600';
    }
  };

  const handleNodeClick = (nodeId: string) => {
    setSelectedNode(nodeId);
    setSelectedEdge(null);
    // Don't change the tab when clicking nodes, let users see the details in current context
  };

  const handleEdgeClick = (edgeId: string) => {
    setSelectedEdge(edgeId);
    setSelectedNode(null);
    // Don't change the tab when clicking edges, let users see the details in current context
  };

  const getSelectedNodeData = () => {
    if (!selectedNode) return null;
    return attackPath.path_nodes.find(node => node.id === selectedNode);
  };

  const getSelectedEdgeData = () => {
    if (!selectedEdge) return null;
    return attackPath.path_edges.find(edge => edge.id === selectedEdge);
  };

  const formatCategoryName = (category: string) => {
    return category
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const formatEdgeType = (edgeType: string) => {
    return edgeType
      .replace(/_/g, ' ')
      .toLowerCase()
      .split(' ')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getEdgeDescription = (edgeType: string) => {
    const descriptions: Record<string, string> = {
      'can_impersonate_sa': 'Can generate access tokens for the service account',
      'can_create_service_account_key': 'Can create downloadable keys for the service account',
      'has_role': 'Has the specified IAM role with associated permissions',
      'member_of': 'Is a member of the specified group',
      'can_admin': 'Has administrative privileges over the resource',
      'can_act_as_via_vm': 'Can deploy VMs using the service account',
      'can_deploy_function_as': 'Can deploy Cloud Functions using the service account',
      'can_deploy_cloud_run_as': 'Can deploy Cloud Run services using the service account',
      'can_read': 'Has read access to the resource',
      'can_write': 'Has write access to the resource'
    };
    return descriptions[edgeType] || 'Represents a security relationship between resources';
  };

  const getEscalationTechniques = () => {
    return attackPath.visualization_metadata?.escalation_techniques || [];
  };

  return (
    <div className="p-6 space-y-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button 
            variant="outline" 
            size="sm"
            onClick={() => navigate('/findings')}
            className="flex items-center space-x-2"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to Findings</span>
          </Button>
          
          <div>
            <div className="flex items-center space-x-2 mb-1">
              <Badge className={getRiskBadgeColor(riskLevel)}>
                {riskLevel.toUpperCase()}
              </Badge>
              <Badge variant="outline">
                {formatCategoryName(attackPath.category)}
              </Badge>
              <Badge variant="outline">
                {attackPath.length} step{attackPath.length !== 1 ? 's' : ''}
              </Badge>
              {ghostUserInfo.hasGhostUsers && (
                <Badge variant="secondary" className="bg-gray-100 text-gray-700">
                  {ghostUserInfo.ghostNodes.length} ghost user{ghostUserInfo.ghostNodes.length !== 1 ? 's' : ''}
                </Badge>
              )}
            </div>
            <h1 className="text-2xl font-bold text-foreground">
              Attack Path: {attackPath.source.name} → {attackPath.target.name}
            </h1>
            <p className="text-muted-foreground">
              Risk Score: {Math.round(attackPath.risk_score * 100)}%
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {/* Ghost Users Toggle */}
          <GhostUsersToggle 
            ghostUserStats={{
              totalGhostNodes: ghostUserInfo.ghostNodes.length,
              ghostUsers: ghostUserInfo.ghostNodes.filter(n => n.type === 'user').length,
              ghostServiceAccounts: ghostUserInfo.ghostNodes.filter(n => n.type === 'service_account').length,
              edgesWithGhostUsers: 0
            }}
            size="sm"
            showLabel={false}
            showStats={false}
          />
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigate(`/graph?highlight=${encodeURIComponent(JSON.stringify({
              nodeIds: attackPath.path_nodes.map(n => n.id),
              edgeIds: attackPath.path_edges.map(e => e.id)
            }))}`)}
          >
            <Maximize className="h-4 w-4 mr-2" />
            View in Full Graph
          </Button>
        </div>
      </div>

      {/* Ghost Users Warning */}
      {ghostUserInfo.hasGhostUsers && !settings.showGhostUsers && (
        <Card className="border-l-4 border-l-yellow-400 bg-yellow-50/50">
          <CardContent className="p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-yellow-600 mt-0.5" />
              <div>
                <h3 className="font-semibold text-yellow-900">Ghost Users in Attack Path</h3>
                <p className="text-sm text-yellow-800 mt-1">
                  This attack path involves {ghostUserInfo.ghostNodes.length} ghost user{ghostUserInfo.ghostNodes.length !== 1 ? 's' : ''} (deleted or inactive accounts). 
                  While these pose lower immediate risk, they may indicate cleanup needed.
                </p>
                <div className="mt-2 space-y-1">
                  {ghostUserInfo.ghostNodes.map((node, index) => (
                    <div key={index} className="text-xs text-yellow-700">
                      • {node.name} ({node.role})
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6" style={{ height: 'calc(100vh - 8rem)' }}>
        {/* Graph Visualization */}
        <div className="lg:col-span-4 flex flex-col min-h-0">
          {/* Graph Controls */}
          <Card className="flex-shrink-0 mb-4">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold">Graph Controls</h3>
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => canvasRef.current?.zoomIn()}
                  >
                    <ZoomIn className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => canvasRef.current?.zoomOut()}
                  >
                    <ZoomOut className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => canvasRef.current?.fitView()}
                  >
                    <RotateCcw className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Attack Path Canvas */}
          <Card className="flex-1 min-h-0">
            <CardContent className="p-0 h-full">
              <AttackPathCanvas
                ref={canvasRef}
                attackPath={attackPath}
                onNodeClick={handleNodeClick}
                onEdgeClick={handleEdgeClick}
                className="h-full w-full"
              />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar with Details */}
        <div className="lg:col-span-1 space-y-4 min-h-0">
          <Card className="h-full overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center space-x-2">
                <Info className="h-5 w-5" />
                <span>Details</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 overflow-y-auto max-h-full">
              <Tabs value={activeTab} onValueChange={setActiveTab}>
                <TabsList className="grid w-full grid-cols-3">
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="path">Path</TabsTrigger>
                  <TabsTrigger value="techniques">Techniques</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <User className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">Source</div>
                        <div className="text-xs text-muted-foreground">
                          {attackPath.source.name}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Target className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">Target</div>
                        <div className="text-xs text-muted-foreground">
                          {attackPath.target.name}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Clock className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">Path Length</div>
                        <div className="text-xs text-muted-foreground">
                          {attackPath.length} step{attackPath.length !== 1 ? 's' : ''}
                        </div>
                      </div>
                    </div>
                    
                    <div className="flex items-center space-x-2">
                      <Shield className="h-4 w-4 text-muted-foreground" />
                      <div>
                        <div className="text-sm font-medium">Risk Score</div>
                        <div className="text-xs text-muted-foreground">
                          {Math.round(attackPath.risk_score * 100)}%
                        </div>
                      </div>
                    </div>

                    {ghostUserInfo.hasGhostUsers && (
                      <div className="p-2 bg-gray-50 rounded border-l-4 border-l-gray-400">
                        <div className="text-sm font-medium text-gray-900">Ghost Users</div>
                        <div className="text-xs text-gray-600 mt-1">
                          {ghostUserInfo.ghostNodes.length} deleted/inactive account{ghostUserInfo.ghostNodes.length !== 1 ? 's' : ''} in path
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <div className="pt-4 border-t">
                    <div className="text-sm font-medium mb-2">Description</div>
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {attackPath.description}
                    </p>
                  </div>
                </TabsContent>

                <TabsContent value="path" className="space-y-4">
                  <div className="space-y-3">
                    <div className="text-sm font-medium">Attack Sequence</div>
                    {attackPath.path_nodes.map((node, index) => (
                      <div key={node.id} className="space-y-2">
                        <div 
                          className={`p-2 rounded border cursor-pointer transition-colors ${
                            selectedNode === node.id ? 'bg-primary/10 border-primary' : 'hover:bg-muted'
                          }`}
                          onClick={() => handleNodeClick(node.id)}
                        >
                          <div className="text-xs font-medium">
                            Step {index + 1}: {node.type}
                            {ghostUserInfo.ghostNodes.some(gn => gn.id === node.id) && (
                              <Badge variant="secondary" className="ml-2 text-xs">ghost</Badge>
                            )}
                          </div>
                          <div className="text-xs text-muted-foreground truncate">
                            {node.name}
                          </div>
                        </div>
                        
                        {index < attackPath.path_edges.length && (
                          <div 
                            className={`ml-4 p-2 rounded border-l-2 border-muted cursor-pointer transition-colors ${
                              selectedEdge === attackPath.path_edges[index].id ? 'bg-primary/10' : 'hover:bg-muted'
                            }`}
                            onClick={() => handleEdgeClick(attackPath.path_edges[index].id)}
                          >
                            <div className="text-xs text-muted-foreground">
                              via {formatEdgeType(attackPath.path_edges[index].type)}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </TabsContent>

                <TabsContent value="techniques" className="space-y-4">
                  <div className="space-y-3">
                    <div className="text-sm font-medium">Escalation Techniques</div>
                    {getEscalationTechniques().map((technique, index) => (
                      <div key={index} className="p-2 rounded border">
                        <div className="text-xs font-medium">{technique.name}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          {technique.description}
                        </div>
                        {technique.impact && (
                          <Badge variant="outline" className="mt-2 text-xs">
                            Impact: {technique.impact}
                          </Badge>
                        )}
                      </div>
                    ))}
                    
                    {getEscalationTechniques().length === 0 && (
                      <div className="text-xs text-muted-foreground">
                        No escalation techniques identified for this path.
                      </div>
                    )}
                  </div>
                </TabsContent>
              </Tabs>

              {/* Selected Node/Edge Details */}
              {selectedNode && (
                <div className="pt-4 border-t">
                  <div className="text-sm font-medium mb-3 flex items-center space-x-2">
                    <User className="h-4 w-4 text-blue-600" />
                    <span>Selected Node Details</span>
                  </div>
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 space-y-2">
                    <div className="text-sm">
                      <span className="font-semibold text-blue-800">Name:</span> 
                      <span className="ml-2 text-blue-700">{getSelectedNodeData()?.name}</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-semibold text-blue-800">Type:</span> 
                      <span className="ml-2 text-blue-700">{formatEdgeType(getSelectedNodeData()?.type || '')}</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-semibold text-blue-800">Role in Attack:</span> 
                      <span className="ml-2 text-blue-700">
                        {selectedNode === attackPath.source.id ? 'Starting Point (Source)' : 
                         selectedNode === attackPath.target.id ? 'Target (End Goal)' : 
                         'Intermediate Step'}
                      </span>
                    </div>
                    {ghostUserInfo.ghostNodes.some(gn => gn.id === selectedNode) && (
                      <div className="text-sm p-2 bg-gray-100 rounded">
                        <span className="font-semibold text-gray-800">⚠️ Ghost User:</span> 
                        <span className="ml-2 text-gray-700 text-xs">This account appears to be deleted or inactive</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {selectedEdge && (
                <div className="pt-4 border-t">
                  <div className="text-sm font-medium mb-3 flex items-center space-x-2">
                    <Target className="h-4 w-4 text-green-600" />
                    <span>Selected Attack Step Details</span>
                  </div>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3 space-y-3">
                    <div className="text-sm">
                      <span className="font-semibold text-green-800">Attack Technique:</span> 
                      <span className="ml-2 text-green-700">{formatEdgeType(getSelectedEdgeData()?.type || '')}</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-semibold text-green-800">Description:</span> 
                      <p className="mt-1 text-green-700 text-xs leading-relaxed">
                        {getEdgeDescription(getSelectedEdgeData()?.type || '')}
                      </p>
                    </div>
                    <div className="text-sm">
                      <span className="font-semibold text-green-800">From:</span> 
                      <span className="ml-2 text-green-700 text-xs">{getSelectedEdgeData()?.source}</span>
                    </div>
                    <div className="text-sm">
                      <span className="font-semibold text-green-800">To:</span> 
                      <span className="ml-2 text-green-700 text-xs">{getSelectedEdgeData()?.target}</span>
                    </div>
                    <div className="mt-2 p-2 bg-green-100 rounded border border-green-300">
                      <div className="text-xs font-semibold text-green-800 mb-1">💡 Security Impact</div>
                      <div className="text-xs text-green-700">
                        This step allows the attacker to move from one resource to another, potentially gaining additional privileges or access to sensitive data.
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {!selectedNode && !selectedEdge && (
                <div className="pt-4 border-t">
                  <div className="text-center text-muted-foreground">
                    <Target className="h-8 w-8 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Click on nodes or edges in the graph above to see detailed information here.</p>
                    <p className="text-xs mt-1">You can also click on items in the "Path" tab to select them.</p>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
} 