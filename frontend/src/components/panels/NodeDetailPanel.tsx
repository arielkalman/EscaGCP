import { useState } from 'react';
import { 
  User, 
  Settings, 
  Shield, 
  Network, 
  Activity,
  AlertTriangle,
  ExternalLink,
  Copy,
  Share2,
  Clock,
  Tag,
  Link2
} from 'lucide-react';
import { SidePanelLayout } from '../layout/SidePanelLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Separator } from '@/components/ui/separator';
import type { GraphNode } from '../../types';
import { NodeType, getRiskLevel, getNodeTypeColor } from '../../types';
import { useGraphContext } from '../../context/GraphContext';

interface NodeDetailPanelProps {
  className?: string;
}

// Node type display information
const NODE_TYPE_INFO: Record<NodeType, {
  name: string;
  icon: React.ComponentType<any>;
  description: string;
  category: string;
}> = {
  [NodeType.USER]: {
    name: 'User Account',
    icon: User,
    description: 'A Google Cloud user account',
    category: 'Identity'
  },
  [NodeType.SERVICE_ACCOUNT]: {
    name: 'Service Account',
    icon: Settings,
    description: 'A Google Cloud service account used by applications',
    category: 'Identity'
  },
  [NodeType.GROUP]: {
    name: 'Group',
    icon: User,
    description: 'A collection of users or service accounts',
    category: 'Identity'
  },
  [NodeType.PROJECT]: {
    name: 'Project',
    icon: Tag,
    description: 'A Google Cloud project container',
    category: 'Resource'
  },
  [NodeType.FOLDER]: {
    name: 'Folder',
    icon: Tag,
    description: 'An organizational folder in the resource hierarchy',
    category: 'Resource'
  },
  [NodeType.ORGANIZATION]: {
    name: 'Organization',
    icon: Tag,
    description: 'The root organization node',
    category: 'Resource'
  },
  [NodeType.ROLE]: {
    name: 'Predefined Role',
    icon: Shield,
    description: 'A Google Cloud predefined IAM role',
    category: 'Permission'
  },
  [NodeType.CUSTOM_ROLE]: {
    name: 'Custom Role',
    icon: Shield,
    description: 'A custom IAM role created by an organization',
    category: 'Permission'
  },
  [NodeType.BUCKET]: {
    name: 'Storage Bucket',
    icon: Tag,
    description: 'A Google Cloud Storage bucket',
    category: 'Resource'
  },
  [NodeType.INSTANCE]: {
    name: 'Compute Instance',
    icon: Tag,
    description: 'A Google Compute Engine virtual machine instance',
    category: 'Resource'
  },
  [NodeType.FUNCTION]: {
    name: 'Cloud Function',
    icon: Tag,
    description: 'A Google Cloud Function',
    category: 'Resource'
  },
  [NodeType.SECRET]: {
    name: 'Secret',
    icon: Shield,
    description: 'A Google Secret Manager secret',
    category: 'Resource'
  },
  [NodeType.KMS_KEY]: {
    name: 'KMS Key',
    icon: Shield,
    description: 'A Google Cloud KMS encryption key',
    category: 'Resource'
  },
  [NodeType.DATASET]: {
    name: 'BigQuery Dataset',
    icon: Tag,
    description: 'A Google BigQuery dataset',
    category: 'Resource'
  },
  [NodeType.TOPIC]: {
    name: 'Pub/Sub Topic',
    icon: Tag,
    description: 'A Google Cloud Pub/Sub topic',
    category: 'Resource'
  },
  [NodeType.CLOUD_RUN_SERVICE]: {
    name: 'Cloud Run Service',
    icon: Tag,
    description: 'A Google Cloud Run service',
    category: 'Resource'
  },
  [NodeType.GKE_CLUSTER]: {
    name: 'GKE Cluster',
    icon: Tag,
    description: 'A Google Kubernetes Engine cluster',
    category: 'Resource'
  },
  [NodeType.CLOUD_BUILD_TRIGGER]: {
    name: 'Cloud Build Trigger',
    icon: Tag,
    description: 'A Google Cloud Build trigger',
    category: 'Resource'
  },
  [NodeType.COMPUTE_INSTANCE]: {
    name: 'Compute Instance',
    icon: Tag,
    description: 'A Google Compute Engine instance',
    category: 'Resource'
  }
};

export function NodeDetailPanel({ className }: NodeDetailPanelProps) {
  const { state, closeNodePanel } = useGraphContext();
  const [activeTab, setActiveTab] = useState('overview');
  
  const node = state.selectedNode;
  const isOpen = state.isNodePanelOpen && !!node;
  
  // Always render the panel but pass empty state when no node is selected
  const nodeInfo = node ? NODE_TYPE_INFO[node.type] || NODE_TYPE_INFO[NodeType.PROJECT] : NODE_TYPE_INFO[NodeType.PROJECT];
  const IconComponent = nodeInfo.icon;
  
  // Mock risk score - in real implementation this would come from analysis data
  const mockRiskScore = node ? Math.random() * 0.8 + 0.1 : 0; // 0.1-0.9
  const riskLevel = getRiskLevel(mockRiskScore);
  const nodeColor = node ? getNodeTypeColor(node.type) : '#6366f1';

  const handleCopyNodeId = () => {
    if (!node) return;
    navigator.clipboard.writeText(node.id);
    console.log('Copied node ID to clipboard');
  };

  const handleExportDetails = () => {
    if (!node) return;
    
    const exportData = {
      id: node.id,
      type: node.type,
      name: node.name,
      properties: node.properties,
      riskScore: mockRiskScore,
      riskLevel: riskLevel,
      exportedAt: new Date().toISOString()
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `node-${node.id.replace(/[^a-zA-Z0-9]/g, '_')}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('Exported node details:', exportData);
  };

  const handleNavigateToResource = () => {
    if (!node) return;
    
    // Close the panel and focus the graph on this node
    closeNodePanel();
    
    // Dispatch an event to focus the graph on this node
    window.dispatchEvent(new CustomEvent('focusGraphNode', {
      detail: { nodeId: node.id }
    }));
    
    console.log('Focusing graph on node:', node.id);
  };

  const getRiskBadgeVariant = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  // Mock data for demonstration
  const mockPermissions = [
    'storage.buckets.get',
    'storage.objects.list',
    'compute.instances.create',
    'iam.serviceAccounts.actAs'
  ];

  const mockRelationships = [
    { type: 'has_role', target: 'roles/storage.objectViewer', direction: 'outgoing' },
    { type: 'member_of', target: 'group:developers@company.com', direction: 'outgoing' },
    { type: 'can_impersonate_sa', target: 'sa-analytics@project.iam', direction: 'outgoing' }
  ];

  const mockActivities = [
    { timestamp: '2024-01-15T10:30:00Z', action: 'iam.serviceAccounts.getAccessToken', resource: 'projects/my-project/serviceAccounts/analytics-sa' },
    { timestamp: '2024-01-15T09:15:00Z', action: 'storage.objects.list', resource: 'gs://sensitive-data-bucket' },
    { timestamp: '2024-01-14T16:45:00Z', action: 'compute.instances.create', resource: 'projects/my-project/zones/us-central1-a/instances/temp-vm' }
  ];

  return (
    <SidePanelLayout
      isOpen={isOpen}
      onClose={closeNodePanel}
      title="Node Details"
      description="Detailed information about the selected node"
      width="xl"
      className={className}
    >
      <div data-testid="node-detail-panel">
        {/* Node Header */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-3">
              <div 
                className="w-10 h-10 rounded-full flex items-center justify-center text-white"
                style={{ backgroundColor: nodeColor }}
              >
                <IconComponent className="w-5 h-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center space-x-2">
                  <h2 className="font-semibold text-gray-900 truncate">{node?.name || 'No Node Selected'}</h2>
                  <Badge variant={getRiskBadgeVariant(riskLevel)}>
                    {riskLevel.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-sm text-gray-600">{nodeInfo.name}</p>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <span className="font-medium text-gray-800">Node ID:</span>
                  <div className="flex items-center space-x-2 mt-1">
                    <code className="bg-gray-100 px-2 py-1 rounded text-xs flex-1 truncate">
                      {node?.id || 'No ID Available'}
                    </code>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={handleCopyNodeId}
                      className="h-6 w-6 p-0"
                    >
                      <Copy className="w-3 h-3" />
                    </Button>
                  </div>
                </div>
                <div>
                  <span className="font-medium text-gray-800">Type:</span>
                  <p className="text-gray-600 mt-1">{nodeInfo.name}</p>
                </div>
              </div>
              
              <div>
                <span className="font-medium text-gray-800">Description:</span>
                <p className="text-gray-600 mt-1 text-sm">{nodeInfo.description}</p>
              </div>

              <div className="flex space-x-2">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleNavigateToResource}
                  className="flex items-center space-x-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  <span>Show in Graph</span>
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExportDetails}
                  className="flex items-center space-x-1"
                >
                  <Share2 className="w-3 h-3" />
                  <span>Export</span>
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Tabbed Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-4">
          <TabsList className="grid w-full grid-cols-2 lg:grid-cols-4 gap-1">
            <TabsTrigger value="overview" className="text-xs">Overview</TabsTrigger>
            <TabsTrigger value="permissions" className="text-xs">Permissions</TabsTrigger>
            <TabsTrigger value="relationships" className="text-xs">Relations</TabsTrigger>
            <TabsTrigger value="activity" className="text-xs">Activity</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Properties</CardTitle>
              </CardHeader>
              <CardContent>
                {node?.properties && Object.keys(node.properties).length > 0 ? (
                  <div className="space-y-3">
                    {Object.entries(node.properties)
                      .filter(([_, value]) => value !== null && value !== undefined && value !== '')
                      .map(([key, value]) => (
                        <div key={key} className="flex justify-between items-start">
                          <span className="font-medium text-gray-800 capitalize">
                            {key.replace(/_/g, ' ')}:
                          </span>
                          <span className="text-gray-600 text-right max-w-60 break-words text-sm">
                            {typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
                          </span>
                        </div>
                      ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-600 italic">No additional properties available</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <AlertTriangle className="w-4 h-4 text-orange-500" />
                  <span>Risk Assessment</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="font-medium text-gray-800">Risk Score:</span>
                    <div className="flex items-center space-x-2">
                      <Badge variant={getRiskBadgeVariant(riskLevel)}>
                        {riskLevel.toUpperCase()}
                      </Badge>
                      <span className="text-sm text-gray-600">
                        {(mockRiskScore * 100).toFixed(0)}%
                      </span>
                    </div>
                  </div>
                  
                  <Separator />
                  
                  <div>
                    <span className="font-medium text-gray-800 text-sm">Risk Factors:</span>
                    <ul className="mt-2 space-y-1">
                      <li className="text-sm text-gray-600 flex items-start">
                        <span className="inline-block w-1.5 h-1.5 bg-red-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                        High privilege level
                      </li>
                      <li className="text-sm text-gray-600 flex items-start">
                        <span className="inline-block w-1.5 h-1.5 bg-orange-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                        Access to sensitive resources
                      </li>
                      <li className="text-sm text-gray-600 flex items-start">
                        <span className="inline-block w-1.5 h-1.5 bg-yellow-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                        Multiple escalation paths
                      </li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="permissions" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <Shield className="w-4 h-4 text-blue-600" />
                  <span>Effective Permissions</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {mockPermissions.map((permission, index) => (
                    <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <code className="text-sm">{permission}</code>
                      <Badge variant="outline" className="text-xs">
                        ALLOW
                      </Badge>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs text-gray-600">
                    Showing {mockPermissions.length} permissions. These are computed based on all role assignments.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="relationships" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <Network className="w-4 h-4 text-green-600" />
                  <span>Connections</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockRelationships.map((rel, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex items-center space-x-3">
                        <Link2 className="w-4 h-4 text-gray-400" />
                        <div>
                          <div className="font-medium text-sm">{rel.type.replace(/_/g, ' ')}</div>
                          <code className="text-xs text-gray-600">{rel.target}</code>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2">
                        <Badge variant="outline" className="text-xs">
                          {rel.direction === 'outgoing' ? 'OUT' : 'IN'}
                        </Badge>
                        <Button variant="ghost" size="sm" className="h-6 w-6 p-0">
                          <ExternalLink className="w-3 h-3" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="activity" className="space-y-4">
            <Card>
              <CardHeader>
                <CardTitle className="text-base flex items-center space-x-2">
                  <Activity className="w-4 h-4 text-purple-600" />
                  <span>Recent Activity</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockActivities.map((activity, index) => (
                    <div key={index} className="flex items-start space-x-3 p-3 border rounded-lg">
                      <Clock className="w-4 h-4 text-gray-400 mt-0.5" />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <code className="text-sm font-medium">{activity.action}</code>
                          <Badge variant="outline" className="text-xs">
                            {new Date(activity.timestamp).toLocaleDateString()}
                          </Badge>
                        </div>
                        <p className="text-sm text-gray-600 mt-1 truncate">
                          {activity.resource}
                        </p>
                        <p className="text-xs text-gray-600 mt-1">
                          {new Date(activity.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
                <div className="mt-4 pt-4 border-t">
                  <p className="text-xs text-gray-600">
                    Activity data from audit logs. Showing last 3 events.
                  </p>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </SidePanelLayout>
  );
} 