import React, { useState, useMemo, useCallback } from 'react';
import { Search, Copy, ChevronDown, ChevronRight, User, Key, Cloud, Users, Folder, Building2, Shield, Box } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

interface NodeData {
  id: string;
  name: string;
  type: string;
  metadata?: {
    email?: string;
    projectId?: string;
    fullName?: string;
    description?: string;
  };
  inDegree: number;
  outDegree: number;
  riskScore?: number;
}

interface NodesByType {
  [key: string]: NodeData[];
}

interface TotalNodesModalProps {
  isOpen: boolean;
  onClose: () => void;
  nodes: NodesByType;
  onNodeClick: (nodeId: string) => void;
  onHighlightNode: (nodeId: string) => void;
}

const nodeTypeConfig = {
  user: { icon: User, color: 'bg-blue-500', label: 'Users' },
  service_account: { icon: Key, color: 'bg-green-500', label: 'Service Accounts' },
  project: { icon: Cloud, color: 'bg-red-500', label: 'Projects' },
  group: { icon: Users, color: 'bg-yellow-500', label: 'Groups' },
  folder: { icon: Folder, color: 'bg-orange-500', label: 'Folders' },
  organization: { icon: Building2, color: 'bg-purple-500', label: 'Organizations' },
  role: { icon: Shield, color: 'bg-gray-500', label: 'Roles' },
  resource: { icon: Box, color: 'bg-indigo-500', label: 'Resources' }
};

const NodeItem: React.FC<{
  node: NodeData;
  onNodeClick: (nodeId: string) => void;
  onHighlightNode: (nodeId: string) => void;
}> = ({ node, onNodeClick, onHighlightNode }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    navigator.clipboard.writeText(node.id);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }, [node.id]);

  const config = nodeTypeConfig[node.type] || nodeTypeConfig.resource;
  const Icon = config.icon;

  return (
    <div
      className="group flex items-center justify-between p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 cursor-pointer transition-colors"
      onClick={() => onNodeClick(node.id)}
      onMouseEnter={() => onHighlightNode(node.id)}
      onMouseLeave={() => onHighlightNode('')}
    >
      <div className="flex items-center gap-3 flex-1">
        <div className={`p-2 rounded-lg ${config.color} bg-opacity-10`}>
          <Icon className={`w-4 h-4 ${config.color.replace('bg-', 'text-')}`} />
        </div>
        <div className="flex-1">
          <div className="font-medium text-sm">{node.name}</div>
          {node.metadata && (
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              {node.metadata.email && <div>Email: {node.metadata.email}</div>}
              {node.metadata.projectId && <div>Project: {node.metadata.projectId}</div>}
              {node.metadata.description && <div>{node.metadata.description}</div>}
            </div>
          )}
        </div>
      </div>
      
      <div className="flex items-center gap-2">
        <div className="text-xs text-gray-500 dark:text-gray-400">
          <span title="In-degree">↓{node.inDegree}</span>
          <span className="mx-1">·</span>
          <span title="Out-degree">↑{node.outDegree}</span>
        </div>
        
        {node.riskScore && node.riskScore > 0.6 && (
          <Badge variant={node.riskScore > 0.8 ? "destructive" : "warning"} className="text-xs">
            {Math.round(node.riskScore * 100)}%
          </Badge>
        )}
        
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                variant="ghost"
                size="sm"
                className="opacity-0 group-hover:opacity-100 transition-opacity"
                onClick={handleCopy}
              >
                <Copy className="w-3 h-3" />
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <p>{copied ? 'Copied!' : 'Copy ID'}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>
    </div>
  );
};

const TypeSection: React.FC<{
  type: string;
  nodes: NodeData[];
  isExpanded: boolean;
  onToggle: () => void;
  onNodeClick: (nodeId: string) => void;
  onHighlightNode: (nodeId: string) => void;
  searchTerm: string;
}> = ({ type, nodes, isExpanded, onToggle, onNodeClick, onHighlightNode, searchTerm }) => {
  const config = nodeTypeConfig[type] || nodeTypeConfig.resource;
  const Icon = config.icon;
  
  const filteredNodes = useMemo(() => {
    if (!searchTerm) return nodes;
    const term = searchTerm.toLowerCase();
    return nodes.filter(node => 
      node.name.toLowerCase().includes(term) ||
      node.id.toLowerCase().includes(term) ||
      (node.metadata?.email?.toLowerCase().includes(term)) ||
      (node.metadata?.projectId?.toLowerCase().includes(term))
    );
  }, [nodes, searchTerm]);

  if (filteredNodes.length === 0) return null;

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
            {filteredNodes.length}
          </Badge>
        </div>
        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      
      {isExpanded && (
        <div className="mt-2 ml-4 space-y-1">
          {filteredNodes.map(node => (
            <NodeItem
              key={node.id}
              node={node}
              onNodeClick={onNodeClick}
              onHighlightNode={onHighlightNode}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export const TotalNodesModal: React.FC<TotalNodesModalProps> = ({
  isOpen,
  onClose,
  nodes,
  onNodeClick,
  onHighlightNode
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [filterType, setFilterType] = useState<string>('all');
  const [sortBy, setSortBy] = useState<'name' | 'degree'>('name');
  const [expandedTypes, setExpandedTypes] = useState<Set<string>>(new Set(['user', 'service_account']));

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

  const processedNodes = useMemo(() => {
    const result: NodesByType = {};
    
    Object.entries(nodes).forEach(([type, nodeList]) => {
      if (filterType !== 'all' && type !== filterType) return;
      
      let sortedNodes = [...nodeList];
      if (sortBy === 'degree') {
        sortedNodes.sort((a, b) => (b.inDegree + b.outDegree) - (a.inDegree + a.outDegree));
      } else {
        sortedNodes.sort((a, b) => a.name.localeCompare(b.name));
      }
      
      result[type] = sortedNodes;
    });
    
    return result;
  }, [nodes, filterType, sortBy]);

  const totalCount = useMemo(() => {
    return Object.values(processedNodes).reduce((sum, nodeList) => sum + nodeList.length, 0);
  }, [processedNodes]);

  const handleExport = useCallback(() => {
    const data = Object.entries(processedNodes).flatMap(([type, nodeList]) =>
      nodeList.map(node => ({
        id: node.id,
        name: node.name,
        type: type,
        inDegree: node.inDegree,
        outDegree: node.outDegree,
        riskScore: node.riskScore || 0,
        ...node.metadata
      }))
    );
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'nodes_export.json';
    a.click();
    URL.revokeObjectURL(url);
  }, [processedNodes]);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh]">
        <DialogHeader>
          <DialogTitle className="text-2xl font-bold">
            Total Nodes ({totalCount})
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <Input
                placeholder="Search nodes by name, ID, or metadata..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10"
              />
            </div>
            
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-48">
                <SelectValue placeholder="Filter by type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Types</SelectItem>
                {Object.entries(nodeTypeConfig).map(([type, config]) => (
                  <SelectItem key={type} value={type}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            
            <Select value={sortBy} onValueChange={(value: 'name' | 'degree') => setSortBy(value)}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="degree">Degree</SelectItem>
              </SelectContent>
            </Select>
            
            <Button variant="outline" onClick={handleExport}>
              Export
            </Button>
          </div>
          
          <ScrollArea className="h-[500px] pr-4">
            {Object.entries(processedNodes).map(([type, nodeList]) => (
              <TypeSection
                key={type}
                type={type}
                nodes={nodeList}
                isExpanded={expandedTypes.has(type)}
                onToggle={() => toggleType(type)}
                onNodeClick={onNodeClick}
                onHighlightNode={onHighlightNode}
                searchTerm={searchTerm}
              />
            ))}
          </ScrollArea>
        </div>
      </DialogContent>
    </Dialog>
  );
}; 