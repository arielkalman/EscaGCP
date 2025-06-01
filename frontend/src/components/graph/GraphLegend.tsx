import React, { useState } from 'react';
import { 
  ChevronDown, 
  ChevronRight, 
  User, 
  Bot, 
  Users, 
  FolderOpen, 
  Building, 
  Shield,
  Database,
  Server,
  Zap,
  Key,
  Eye,
  EyeOff
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { NodeType, EdgeType } from '../../types';

interface LegendItem {
  type: string;
  label: string;
  color: string;
  icon?: React.ComponentType<any>;
  description?: string;
  count?: number;
  visible?: boolean;
}

interface GraphLegendProps {
  nodeTypes: NodeType[];
  edgeTypes: EdgeType[];
  nodeCounts?: Record<string, number>;
  edgeCounts?: Record<string, number>;
  visibleNodeTypes?: Set<string>;
  visibleEdgeTypes?: Set<string>;
  onToggleNodeType?: (nodeType: string) => void;
  onToggleEdgeType?: (edgeType: string) => void;
  onToggleSection?: (section: string) => void;
  className?: string;
}

const NODE_LEGEND_DATA: Record<NodeType, LegendItem> = {
  [NodeType.USER]: {
    type: 'user',
    label: 'Users',
    color: '#4285F4',
    icon: User,
    description: 'Human users and accounts'
  },
  [NodeType.SERVICE_ACCOUNT]: {
    type: 'service_account',
    label: 'Service Accounts',
    color: '#34A853',
    icon: Bot,
    description: 'Automated service accounts'
  },
  [NodeType.GROUP]: {
    type: 'group',
    label: 'Groups',
    color: '#FBBC04',
    icon: Users,
    description: 'User and service account groups'
  },
  [NodeType.PROJECT]: {
    type: 'project',
    label: 'Projects',
    color: '#EA4335',
    icon: FolderOpen,
    description: 'GCP projects'
  },
  [NodeType.FOLDER]: {
    type: 'folder',
    label: 'Folders',
    color: '#FF6D00',
    icon: FolderOpen,
    description: 'GCP folders'
  },
  [NodeType.ORGANIZATION]: {
    type: 'organization',
    label: 'Organizations',
    color: '#9C27B0',
    icon: Building,
    description: 'GCP organizations'
  },
  [NodeType.ROLE]: {
    type: 'role',
    label: 'Roles',
    color: '#757575',
    icon: Shield,
    description: 'IAM roles and permissions'
  },
  [NodeType.CUSTOM_ROLE]: {
    type: 'custom_role',
    label: 'Custom Roles',
    color: '#616161',
    icon: Shield,
    description: 'Custom IAM roles'
  },
  [NodeType.BUCKET]: {
    type: 'bucket',
    label: 'Storage Buckets',
    color: '#00ACC1',
    icon: Database,
    description: 'Cloud Storage buckets'
  },
  [NodeType.INSTANCE]: {
    type: 'instance',
    label: 'Compute Instances',
    color: '#FF9800',
    icon: Server,
    description: 'Virtual machine instances'
  },
  [NodeType.FUNCTION]: {
    type: 'function',
    label: 'Cloud Functions',
    color: '#9C27B0',
    icon: Zap,
    description: 'Serverless functions'
  },
  [NodeType.SECRET]: {
    type: 'secret',
    label: 'Secrets',
    color: '#F44336',
    icon: Key,
    description: 'Secret Manager secrets'
  },
  [NodeType.KMS_KEY]: {
    type: 'kms_key',
    label: 'KMS Keys',
    color: '#FFA726',
    icon: Key,
    description: 'Cloud KMS encryption keys'
  },
  [NodeType.DATASET]: {
    type: 'dataset',
    label: 'BigQuery Datasets',
    color: '#42A5F5',
    icon: Database,
    description: 'BigQuery datasets'
  },
  [NodeType.TOPIC]: {
    type: 'topic',
    label: 'Pub/Sub Topics',
    color: '#66BB6A',
    icon: Database,
    description: 'Pub/Sub topics'
  },
  [NodeType.CLOUD_RUN_SERVICE]: {
    type: 'cloud_run_service',
    label: 'Cloud Run Services',
    color: '#29B6F6',
    icon: Server,
    description: 'Cloud Run containerized services'
  },
  [NodeType.GKE_CLUSTER]: {
    type: 'gke_cluster',
    label: 'GKE Clusters',
    color: '#5C6BC0',
    icon: Server,
    description: 'Google Kubernetes Engine clusters'
  },
  [NodeType.CLOUD_BUILD_TRIGGER]: {
    type: 'cloud_build_trigger',
    label: 'Build Triggers',
    color: '#FF8A65',
    icon: Zap,
    description: 'Cloud Build triggers'
  },
  [NodeType.COMPUTE_INSTANCE]: {
    type: 'compute_instance',
    label: 'Compute Instances',
    color: '#FF7043',
    icon: Server,
    description: 'Compute Engine instances'
  }
};

const EDGE_LEGEND_DATA: Record<string, LegendItem> = {
  has_role: {
    type: 'has_role',
    label: 'Has Role',
    color: '#757575',
    description: 'Has IAM role assignment'
  },
  member_of: {
    type: 'member_of',
    label: 'Member Of',
    color: '#9E9E9E',
    description: 'Group membership'
  },
  can_impersonate_sa: {
    type: 'can_impersonate_sa',
    label: 'Can Impersonate',
    color: '#F44336',
    description: 'Can impersonate service account'
  },
  can_admin: {
    type: 'can_admin',
    label: 'Can Admin',
    color: '#FF5722',
    description: 'Administrative access'
  },
  can_write: {
    type: 'can_write',
    label: 'Can Write',
    color: '#FF9800',
    description: 'Write access'
  },
  can_read: {
    type: 'can_read',
    label: 'Can Read',
    color: '#FFC107',
    description: 'Read access'
  },
  runs_as: {
    type: 'runs_as',
    label: 'Runs As',
    color: '#8BC34A',
    description: 'Executes with service account'
  },
  parent_of: {
    type: 'parent_of',
    label: 'Parent Of',
    color: '#607D8B',
    description: 'Hierarchical parent relationship'
  },
  can_login_to_vm: {
    type: 'can_login_to_vm',
    label: 'Can SSH',
    color: '#E91E63',
    description: 'Can SSH into VM instance'
  }
};

const RISK_LEGEND_DATA: LegendItem[] = [
  {
    type: 'critical',
    label: 'Critical Risk',
    color: '#D32F2F',
    description: '≥ 80% risk score - Immediate action required'
  },
  {
    type: 'high',
    label: 'High Risk',
    color: '#F44336',
    description: '60-79% risk score - Should be addressed soon'
  },
  {
    type: 'medium',
    label: 'Medium Risk',
    color: '#FF9800',
    description: '40-59% risk score - Review and plan remediation'
  },
  {
    type: 'low',
    label: 'Low Risk',
    color: '#FFC107',
    description: '20-39% risk score - Monitor'
  },
  {
    type: 'info',
    label: 'Info/Safe',
    color: '#4CAF50',
    description: '< 20% risk score - Low priority'
  }
];

export function GraphLegend({
  nodeTypes,
  edgeTypes,
  nodeCounts = {},
  edgeCounts = {},
  visibleNodeTypes,
  visibleEdgeTypes,
  onToggleNodeType,
  onToggleEdgeType,
  onToggleSection,
  className = ''
}: GraphLegendProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set()
  );

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev);
      if (newSet.has(section)) {
        newSet.delete(section);
      } else {
        newSet.add(section);
      }
      return newSet;
    });
    onToggleSection?.(section);
  };

  const isNodeTypeVisible = (nodeType: string) => {
    return visibleNodeTypes ? visibleNodeTypes.has(nodeType) : true;
  };

  const isEdgeTypeVisible = (edgeType: string) => {
    return visibleEdgeTypes ? visibleEdgeTypes.has(edgeType) : true;
  };

  const renderLegendItem = (
    item: LegendItem,
    isVisible: boolean,
    onToggle?: () => void
  ) => {
    const IconComponent = item.icon;
    
    return (
      <div
        key={item.type}
        className={`flex items-center justify-between p-2 rounded-md hover:bg-gray-50 transition-colors ${
          !isVisible ? 'opacity-50' : ''
        }`}
      >
        <div className="flex items-center space-x-2 flex-1">
          <div
            className="w-3 h-3 rounded-sm border border-gray-300"
            style={{ backgroundColor: item.color }}
          />
          {IconComponent && (
            <IconComponent className="w-3 h-3 text-gray-800" />
          )}
          <div className="flex-1">
            <div className="text-xs font-medium text-gray-900">{item.label}</div>
            {item.description && (
              <div className="text-xs text-gray-800">{item.description}</div>
            )}
          </div>
          {item.count !== undefined && (
            <Badge variant="secondary" className="text-xs">
              {item.count}
            </Badge>
          )}
        </div>
        {onToggle && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggle}
            className="w-6 h-6 p-0 ml-2"
            title={isVisible ? 'Hide' : 'Show'}
          >
            {isVisible ? (
              <Eye className="w-3 h-3" />
            ) : (
              <EyeOff className="w-3 h-3" />
            )}
          </Button>
        )}
      </div>
    );
  };

  const renderSection = (
    title: string,
    sectionKey: string,
    content: React.ReactNode
  ) => {
    const isExpanded = expandedSections.has(sectionKey);
    
    return (
      <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
        <CardHeader className="pb-2">
          <CardTitle
            className="text-sm font-medium text-gray-900 flex items-center justify-between cursor-pointer"
            onClick={() => toggleSection(sectionKey)}
          >
            <span>{title}</span>
            {isExpanded ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
          </CardTitle>
        </CardHeader>
        {isExpanded && (
          <CardContent className="pt-0">
            {content}
          </CardContent>
        )}
      </Card>
    );
  };

  const nodeContent = (
    <div className="space-y-1">
      {nodeTypes.map(nodeType => {
        const legendData = NODE_LEGEND_DATA[nodeType];
        if (!legendData) return null;
        
        const item = {
          ...legendData,
          count: nodeCounts[nodeType] || 0
        };
        
        return renderLegendItem(
          item,
          isNodeTypeVisible(nodeType),
          onToggleNodeType ? () => onToggleNodeType(nodeType) : undefined
        );
      })}
    </div>
  );

  const edgeContent = (
    <div className="space-y-1">
      {edgeTypes.map(edgeType => {
        const legendData = EDGE_LEGEND_DATA[edgeType];
        if (!legendData) return null;
        
        const item = {
          ...legendData,
          count: edgeCounts[edgeType] || 0
        };
        
        return renderLegendItem(
          item,
          isEdgeTypeVisible(edgeType),
          onToggleEdgeType ? () => onToggleEdgeType(edgeType) : undefined
        );
      })}
    </div>
  );

  const riskContent = (
    <div className="space-y-1">
      {RISK_LEGEND_DATA.map(item => 
        renderLegendItem(item, true)
      )}
    </div>
  );

  return (
    <div className={`space-y-4 ${className}`} data-testid="graph-legend">
      {renderSection('Legend: Node Types', 'nodes', nodeContent)}
      {renderSection('Legend: Edge Types', 'edges', edgeContent)}
      {renderSection('Legend: Risk Levels', 'risk', riskContent)}
    </div>
  );
} 