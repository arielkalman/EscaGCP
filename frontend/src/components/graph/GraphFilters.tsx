import React, { useState } from 'react';
import { 
  Filter, 
  X, 
  ChevronDown, 
  ChevronRight,
  Search,
  AlertTriangle,
  Shield,
  Clock,
  CheckCircle
} from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { NodeType, EdgeType, RiskLevel } from '../../types';

interface FilterOption {
  id: string;
  label: string;
  description?: string;
  count?: number;
  selected: boolean;
}

interface GraphFiltersProps {
  availableNodeTypes: NodeType[];
  availableEdgeTypes: EdgeType[];
  selectedNodeTypes: Set<string>;
  selectedEdgeTypes: Set<string>;
  selectedRiskLevels: Set<RiskLevel>;
  minRiskScore: number;
  maxRiskScore: number;
  onNodeTypeChange: (nodeTypes: Set<string>) => void;
  onEdgeTypeChange: (edgeTypes: Set<string>) => void;
  onRiskLevelChange: (riskLevels: Set<RiskLevel>) => void;
  onRiskScoreChange: (min: number, max: number) => void;
  onAttributeFilterChange?: (filters: Record<string, any>) => void;
  onReset: () => void;
  nodeCounts?: Record<string, number>;
  edgeCounts?: Record<string, number>;
  className?: string;
}

const RISK_LEVELS: Array<{ id: RiskLevel; label: string; color: string; description: string }> = [
  { id: 'critical', label: 'Critical', color: '#D32F2F', description: '≥ 80% risk score' },
  { id: 'high', label: 'High', color: '#F44336', description: '60-79% risk score' },
  { id: 'medium', label: 'Medium', color: '#FF9800', description: '40-59% risk score' },
  { id: 'low', label: 'Low', color: '#FFC107', description: '20-39% risk score' },
  { id: 'info', label: 'Info/Safe', color: '#4CAF50', description: '< 20% risk score' }
];

const NODE_TYPE_LABELS: Record<NodeType, string> = {
  [NodeType.USER]: 'Users',
  [NodeType.SERVICE_ACCOUNT]: 'Service Accounts',
  [NodeType.GROUP]: 'Groups',
  [NodeType.PROJECT]: 'Projects',
  [NodeType.FOLDER]: 'Folders',
  [NodeType.ORGANIZATION]: 'Organizations',
  [NodeType.ROLE]: 'Roles',
  [NodeType.CUSTOM_ROLE]: 'Custom Roles',
  [NodeType.BUCKET]: 'Storage Buckets',
  [NodeType.INSTANCE]: 'Compute Instances',
  [NodeType.FUNCTION]: 'Cloud Functions',
  [NodeType.SECRET]: 'Secrets',
  [NodeType.KMS_KEY]: 'KMS Keys',
  [NodeType.DATASET]: 'BigQuery Datasets',
  [NodeType.TOPIC]: 'Pub/Sub Topics',
  [NodeType.CLOUD_RUN_SERVICE]: 'Cloud Run Services',
  [NodeType.GKE_CLUSTER]: 'GKE Clusters',
  [NodeType.CLOUD_BUILD_TRIGGER]: 'Build Triggers',
  [NodeType.COMPUTE_INSTANCE]: 'Compute Instances'
};

const EDGE_TYPE_LABELS: Record<string, string> = {
  has_role: 'Has Role',
  member_of: 'Member Of',
  can_impersonate_sa: 'Can Impersonate',
  can_admin: 'Can Admin',
  can_write: 'Can Write',
  can_read: 'Can Read',
  runs_as: 'Runs As',
  parent_of: 'Parent Of',
  can_login_to_vm: 'Can SSH'
};

export function GraphFilters({
  availableNodeTypes,
  availableEdgeTypes,
  selectedNodeTypes,
  selectedEdgeTypes,
  selectedRiskLevels,
  minRiskScore,
  maxRiskScore,
  onNodeTypeChange,
  onEdgeTypeChange,
  onRiskLevelChange,
  onRiskScoreChange,
  onAttributeFilterChange,
  onReset,
  nodeCounts = {},
  edgeCounts = {},
  className = ''
}: GraphFiltersProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(
    new Set()
  );
  const [searchQuery, setSearchQuery] = useState('');
  const [showDangerousOnly, setShowDangerousOnly] = useState(false);
  const [showPrivilegedOnly, setShowPrivilegedOnly] = useState(false);

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
  };

  const handleNodeTypeToggle = (nodeType: string) => {
    const newSet = new Set(selectedNodeTypes);
    if (newSet.has(nodeType)) {
      newSet.delete(nodeType);
    } else {
      newSet.add(nodeType);
    }
    onNodeTypeChange(newSet);
  };

  const handleEdgeTypeToggle = (edgeType: string) => {
    const newSet = new Set(selectedEdgeTypes);
    if (newSet.has(edgeType)) {
      newSet.delete(edgeType);
    } else {
      newSet.add(edgeType);
    }
    onEdgeTypeChange(newSet);
  };

  const handleRiskLevelToggle = (riskLevel: RiskLevel) => {
    const newSet = new Set(selectedRiskLevels);
    if (newSet.has(riskLevel)) {
      newSet.delete(riskLevel);
    } else {
      newSet.add(riskLevel);
    }
    onRiskLevelChange(newSet);
  };

  const handleSelectAllNodeTypes = () => {
    onNodeTypeChange(new Set(availableNodeTypes));
  };

  const handleDeselectAllNodeTypes = () => {
    onNodeTypeChange(new Set());
  };

  const handleSelectAllEdgeTypes = () => {
    onEdgeTypeChange(new Set(availableEdgeTypes));
  };

  const handleDeselectAllEdgeTypes = () => {
    onEdgeTypeChange(new Set());
  };

  const getActiveFiltersCount = () => {
    let count = 0;
    if (selectedNodeTypes.size !== availableNodeTypes.length) count++;
    if (selectedEdgeTypes.size !== availableEdgeTypes.length) count++;
    if (selectedRiskLevels.size !== RISK_LEVELS.length) count++;
    if (minRiskScore > 0 || maxRiskScore < 1) count++;
    if (searchQuery.trim()) count++;
    if (showDangerousOnly || showPrivilegedOnly) count++;
    return count;
  };

  const renderSection = (
    title: string,
    sectionKey: string,
    content: React.ReactNode,
    rightContent?: React.ReactNode
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
            <div className="flex items-center space-x-2">
              {rightContent}
              {isExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </div>
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

  const renderFilterOption = (
    id: string,
    label: string,
    isSelected: boolean,
    count: number | undefined,
    onToggle: () => void
  ) => (
    <label
      key={id}
      className="flex items-center justify-between p-2 rounded hover:bg-gray-50 cursor-pointer"
      htmlFor={`checkbox-${id}`}
    >
      <div className="flex items-center space-x-2">
        <input
          id={`checkbox-${id}`}
          type="checkbox"
          checked={isSelected}
          onChange={onToggle}
          className="w-3 h-3 text-blue-600 rounded focus:ring-blue-500"
          aria-label={`Filter by ${label}`}
          title={`Filter by ${label}`}
        />
        <span className="text-xs text-gray-900">{label}</span>
      </div>
      {count !== undefined && (
        <Badge variant="secondary" className="text-xs">
          {count}
        </Badge>
      )}
    </label>
  );

  const nodeTypesContent = (
    <div className="space-y-2">
      <div className="flex space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleSelectAllNodeTypes}
          className="h-6 text-xs flex-1"
        >
          Select All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDeselectAllNodeTypes}
          className="h-6 text-xs flex-1"
        >
          Deselect All
        </Button>
      </div>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {availableNodeTypes.map(nodeType =>
          renderFilterOption(
            nodeType,
            NODE_TYPE_LABELS[nodeType] || nodeType,
            selectedNodeTypes.has(nodeType),
            nodeCounts[nodeType],
            () => handleNodeTypeToggle(nodeType)
          )
        )}
      </div>
    </div>
  );

  const edgeTypesContent = (
    <div className="space-y-2">
      <div className="flex space-x-2">
        <Button
          variant="outline"
          size="sm"
          onClick={handleSelectAllEdgeTypes}
          className="h-6 text-xs flex-1"
        >
          Select All
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={handleDeselectAllEdgeTypes}
          className="h-6 text-xs flex-1"
        >
          Deselect All
        </Button>
      </div>
      <div className="space-y-1 max-h-48 overflow-y-auto">
        {availableEdgeTypes.map(edgeType =>
          renderFilterOption(
            edgeType,
            EDGE_TYPE_LABELS[edgeType] || edgeType.replace('_', ' '),
            selectedEdgeTypes.has(edgeType),
            edgeCounts[edgeType],
            () => handleEdgeTypeToggle(edgeType)
          )
        )}
      </div>
    </div>
  );

  const riskLevelsContent = (
    <div className="space-y-1">
      {RISK_LEVELS.map(risk =>
        <label
          key={risk.id}
          className="flex items-center justify-between p-2 rounded hover:bg-gray-50 cursor-pointer"
          htmlFor={`risk-${risk.id}`}
        >
          <div className="flex items-center space-x-2">
            <input
              id={`risk-${risk.id}`}
              type="checkbox"
              checked={selectedRiskLevels.has(risk.id)}
              onChange={() => handleRiskLevelToggle(risk.id)}
              className="w-3 h-3 text-blue-600 rounded focus:ring-blue-500"
              aria-label={`Filter by ${risk.label} risk level`}
              title={`Filter by ${risk.label} risk level`}
            />
            <div
              className="w-3 h-3 rounded-sm"
              style={{ backgroundColor: risk.color }}
            />
            <div>
              <span className="text-xs text-gray-900 font-medium">{risk.label}</span>
              <div className="text-xs text-gray-500">{risk.description}</div>
            </div>
          </div>
        </label>
      )}
    </div>
  );

  const searchContent = (
    <div className="space-y-3">
      <div className="relative">
        <Search className="absolute left-2 top-1/2 transform -translate-y-1/2 w-3 h-3 text-gray-400" />
        <input
          type="text"
          placeholder="Search nodes by name or ID..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full pl-7 pr-3 py-2 text-xs border border-gray-300 rounded-md focus:ring-blue-500 focus:border-blue-500"
        />
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="dangerous-only"
            checked={showDangerousOnly}
            onChange={(e) => setShowDangerousOnly(e.target.checked)}
            className="w-3 h-3 text-red-600 rounded focus:ring-red-500"
            aria-label="Show only dangerous nodes"
            title="Show only dangerous nodes"
          />
          <label htmlFor="dangerous-only" className="text-xs text-gray-900 flex items-center">
            <AlertTriangle className="w-3 h-3 mr-1 text-red-500" />
            Show only dangerous nodes
          </label>
        </div>
        
        <div className="flex items-center space-x-2">
          <input
            type="checkbox"
            id="privileged-only"
            checked={showPrivilegedOnly}
            onChange={(e) => setShowPrivilegedOnly(e.target.checked)}
            className="w-3 h-3 text-orange-600 rounded focus:ring-orange-500"
            aria-label="Show only privileged nodes"
            title="Show only privileged nodes"
          />
          <label htmlFor="privileged-only" className="text-xs text-gray-900 flex items-center">
            <Shield className="w-3 h-3 mr-1 text-orange-500" />
            Show only privileged nodes
          </label>
        </div>
      </div>
    </div>
  );

  const activeFiltersCount = getActiveFiltersCount();

  return (
    <div className={`space-y-4 ${className}`} data-testid="graph-filters">
      {/* Filter Header */}
      <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
        <CardContent className="p-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Filter className="w-4 h-4 text-gray-600" />
              <span className="text-sm font-medium text-gray-900">Filter By</span>
              {activeFiltersCount > 0 && (
                <Badge variant="destructive" className="text-xs">
                  {activeFiltersCount}
                </Badge>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="h-6 text-xs"
              disabled={activeFiltersCount === 0}
            >
              <X className="w-3 h-3 mr-1" />
              Clear All
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Search and Quick Filters */}
      {renderSection('Search & Quick Filters', 'search', searchContent)}

      {/* Node Types */}
      {renderSection('Filter: Node Types', 'nodeTypes', nodeTypesContent)}

      {/* Edge Types */}
      {renderSection('Filter: Edge Types', 'edgeTypes', edgeTypesContent)}

      {/* Risk Levels */}
      {renderSection('Filter: Risk Levels', 'riskLevels', riskLevelsContent)}
    </div>
  );
} 