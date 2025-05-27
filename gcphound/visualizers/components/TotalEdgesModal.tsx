import React, { useState, useMemo, useCallback } from 'react';
import { Search, ChevronDown, ChevronRight, ArrowRight, Key, Shield, Cloud, Zap, GitBranch, AlertTriangle, Info } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface EdgeData {
  id: string;
  source: string;
  target: string;
  type: string;
  sourceName: string;
  targetName: string;
  permission?: string;
  resourceScope?: string;
  rationale?: string;
}

interface EdgesByType {
  [key: string]: EdgeData[];
}

interface TotalEdgesModalProps {
  isOpen: boolean;
  onClose: () => void;
  edges: EdgesByType;
  onEdgeClick: (edgeId: string) => void;
  onNodeClick: (nodeId: string) => void;
  onHighlightEdge: (edgeId: string) => void;
}

const edgeTypeConfig = {
  // Privilege Escalation
  CAN_IMPERSONATE_SA: { 
    icon: Key, 
    color: 'bg-red-500', 
    label: 'Service Account Impersonation',
    category: 'escalation',
    severity: 'critical'
  },
  CAN_CREATE_SERVICE_ACCOUNT_KEY: { 
    icon: Key, 
    color: 'bg-red-500', 
    label: 'SA Key Creation',
    category: 'escalation',
    severity: 'critical'
  },
  CAN_ACT_AS_VIA_VM: { 
    icon: Cloud, 
    color: 'bg-orange-500', 
    label: 'VM-based SA Abuse',
    category: 'escalation',
    severity: 'high'
  },
  CAN_DEPLOY_FUNCTION_AS: { 
    icon: Zap, 
    color: 'bg-orange-500', 
    label: 'Cloud Function Deployment',
    category: 'escalation',
    severity: 'high'
  },
  CAN_DEPLOY_CLOUD_RUN_AS: { 
    icon: Cloud, 
    color: 'bg-orange-500', 
    label: 'Cloud Run Deployment',
    category: 'escalation',
    severity: 'high'
  },
  
  // IAM Relationships
  HAS_ROLE: { 
    icon: Shield, 
    color: 'bg-gray-500', 
    label: 'Role Assignment',
    category: 'iam',
    severity: 'low'
  },
  MEMBER_OF: { 
    icon: GitBranch, 
    color: 'bg-blue-500', 
    label: 'Group Membership',
    category: 'iam',
    severity: 'low'
  },
  
  // Lateral Movement
  CAN_LOGIN_TO_VM: { 
    icon: Cloud, 
    color: 'bg-yellow-500', 
    label: 'VM Login Access',
    category: 'lateral',
    severity: 'medium'
  },
  CAN_TRIGGER_BUILD_AS: { 
    icon: Zap, 
    color: 'bg-yellow-500', 
    label: 'Cloud Build Trigger',
    category: 'lateral',
    severity: 'medium'
  }
};

const EdgeItem: React.FC<{
  edge: EdgeData;
  onEdgeClick: (edgeId: string) => void;
  onNodeClick: (nodeId: string) => void;
  onHighlightEdge: (edgeId: string) => void;
}> = ({ edge, onEdgeClick, onNodeClick, onHighlightEdge }) => {
  const config = edgeTypeConfig[edge.type] || {
    icon: AlertTriangle,
    color: 'bg-gray-500',
    label: edge.type,
    category: 'other',
    severity: 'low'
  };
  const Icon = config.icon;

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical': return 'text-red-600 bg-red-50 border-red-200';
      case 'high': return 'text-orange-600 bg-orange-50 border-orange-200';
      case 'medium': return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default: return 'text-gray-600 bg-gray-50 border-gray-200';
    }
  };

  return (
    <div
      className="group flex flex-col p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer transition-colors border border-transparent hover:border-gray-300 dark:hover:border-gray-700"
      onClick={() => onEdgeClick(edge.id)}
      onMouseEnter={() => onHighlightEdge(edge.id)}
      onMouseLeave={() => onHighlightEdge('')}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-3 flex-1">
          <div className={`p-2 rounded-lg ${config.color} bg-opacity-10`}>
            <Icon className={`w-4 h-4 ${config.color.replace('bg-', 'text-')}`} />
          </div>
          <div className="flex items-center gap-2 flex-1">
            <button
              className="text-sm font-medium hover:underline text-left"
              onClick={(e) => {
                e.stopPropagation();
                onNodeClick(edge.source);
              }}
            >
              {edge.sourceName}
            </button>
            <ArrowRight className="w-4 h-4 text-gray-400" />
            <button
              className="text-sm font-medium hover:underline text-left"
              onClick={(e) => {
                e.stopPropagation();
                onNodeClick(edge.target);
              }}
            >
              {edge.targetName}
            </button>
          </div>
        </div>
        
        <Badge 
          variant="outline" 
          className={`text-xs ${getSeverityColor(config.severity)}`}
        >
          {config.severity}
        </Badge>
      </div>
      
      <div className="ml-11 space-y-1">
        {edge.permission && (
          <div className="text-xs text-gray-600 dark:text-gray-400">
            <span className="font-medium">Permission:</span> {edge.permission}
          </div>
        )}
        {edge.resourceScope && (
          <div className="text-xs text-gray-600 dark:text-gray-400">
            <span className="font-medium">Scope:</span> {edge.resourceScope}
          </div>
        )}
        {edge.rationale && (
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <div className="flex items-center gap-1 text-xs text-gray-600 dark:text-gray-400">
                  <Info className="w-3 h-3" />
                  <span className="truncate">{edge.rationale}</span>
                </div>
              </TooltipTrigger>
              <TooltipContent>
                <p className="max-w-xs">{edge.rationale}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        )}
      </div>
    </div>
  );
};

const TypeSection: React.FC<{
  type: string;
  edges: EdgeData[];
  isExpanded: boolean;
  onToggle: () => void;
  onEdgeClick: (edgeId: string) => void;
  onNodeClick: (nodeId: string) => void;
  onHighlightEdge: (edgeId: string) => void;
  searchTerm: string;
}> = ({ type, edges, isExpanded, onToggle, onEdgeClick, onNodeClick, onHighlightEdge, searchTerm }) => {
  const config = edgeTypeConfig[type] || {
    icon: AlertTriangle,
    color: 'bg-gray-500',
    label: type,
    category: 'other',
    severity: 'low'
  };
  const Icon = config.icon;
  
  const filteredEdges = useMemo(() => {
    if (!searchTerm) return edges;
    const term = searchTerm.toLowerCase();
    return edges.filter(edge => 
      edge.sourceName.toLowerCase().includes(term) ||
      edge.targetName.toLowerCase().includes(term) ||
      edge.type.toLowerCase().includes(term) ||
      (edge.permission?.toLowerCase().includes(term)) ||
      (edge.resourceScope?.toLowerCase().includes(term))
    );
  }, [edges, searchTerm]);

  if (filteredEdges.length === 0) return null;

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'escalation': return 'bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200';
      case 'lateral': return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200';
      case 'iam': return 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900 dark:text-gray-200';
    }
  };

  return (
    <div className="mb-4">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
      >
        <div className="flex items-center gap-3">
          <div className={`p-2 rounded-lg ${config.color} bg-opacity-10`}>
            <Icon className={`w-5 h-5 ${config.color.replace('bg-', 'text-')}`} />
          </div>
          <span className="font-semibold">{config.label}</span>
          <Badge variant="secondary" className="ml-2">
            {filteredEdges.length}
          </Badge>
          <Badge className={`ml-2 text-xs ${getCategoryColor(config.category)}`}>
            {config.category}
          </Badge>
        </div>
        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      
      {isExpanded && (
        <div className="mt-2 ml-4 space-y-2">
          {filteredEdges.map(edge => (
            <EdgeItem
              key={edge.id}
              edge={edge}
              onEdgeClick={onEdgeClick}
              onNodeClick={onNodeClick}
              onHighlightEdge={onHighlightEdge}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const TotalEdgesModal: React.FC<TotalEdgesModalProps> = ({
  isOpen,
  onClose,
  edges,
  onEdgeClick,
  onNodeClick,
  onHighlightEdge
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterCategory, setFilterCategory] = useState<string>('all');
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set(['CAN_IMPERSONATE_SA', 'CAN_CREATE_SERVICE_ACCOUNT_KEY']));

  const toggleType = useCallback((type: string) => {
    setExpandedTypes(prev => {
      const newSet = new Set(prev);
      if (newSet.has(type)) {
        newSet.delete(type);
      } else {
        newSet.add(type);
      }
      return newSet;
    });
  }, []);

  const processedEdges = useMemo(() => {
    const result: EdgesByType = {};
    
    Object.entries(edges).forEach(([type, edgeList]) => {
      const config = edgeTypeConfig[type] || { category: 'other', severity: 'low' };
      
      if (filterCategory !== 'all' && config.category !== filterCategory) return;
      if (filterSeverity !== 'all' && config.severity !== filterSeverity) return;
      
      result[type] = edgeList;
    });
    
    // Sort by severity
    const severityOrder = { critical: 0, high: 1, medium: 2, low: 3 };
    const sortedEntries = Object.entries(result).sort(([typeA], [typeB]) => {
      const configA = edgeTypeConfig[typeA] || { severity: 'low' };
      const configB = edgeTypeConfig[typeB] || { severity: 'low' };
      return severityOrder[configA.severity] - severityOrder[configB.severity];
    });
    
    return Object.fromEntries(sortedEntries);
  }, [edges, filterCategory, filterSeverity]);

  const totalCount = useMemo(() => {
    return Object.values(processedEdges).reduce((sum, edgeList) => sum + edgeList.length, 0);
  }, [processedEdges]);

  const handleExport = useCallback(() => {
    const data = Object.entries(processedEdges).flatMap(([type, edgeList]) =>
      edgeList.map(edge => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        sourceName: edge.sourceName,
        targetName: edge.targetName,
        type: type,
        permission: edge.permission || '',
        resourceScope: edge.resourceScope || '',
        rationale: edge.rationale || '',
        category: edgeTypeConfig[type]?.category || 'other',
        severity: edgeTypeConfig[type]?.severity || 'low'
      }))
    );
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'edges_export.json';
    a.click();
    URL.revokeObjectURL(url);
  }, [processedEdges]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-5xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">
            Total Edges ({totalCount})
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search edges by nodes, type, or permission..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={filterCategory} onValueChange={setFilterCategory}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Categories</SelectItem>
                <SelectItem value="escalation">Escalation</SelectItem>
                <SelectItem value="lateral">Lateral Movement</SelectItem>
                <SelectItem value="iam">IAM</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
            
            <Select value={filterSeverity} onValueChange={setFilterSeverity}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Severity" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Severities</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="low">Low</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={handleExport}>
              Export
            </Button>
          </div>
          
          <ScrollArea className="h-[500px] pr-4">
            {Object.entries(processedEdges).map(([type, edgeList]) => (
              <TypeSection
                key={type}
                type={type}
                edges={edgeList}
                isExpanded={expandedTypes.has(type)}
                onToggle={() => toggleType(type)}
                onEdgeClick={onEdgeClick}
                onNodeClick={onNodeClick}
                onHighlightEdge={onHighlightEdge}
                searchTerm={searchTerm}
              />
            ))}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}; 