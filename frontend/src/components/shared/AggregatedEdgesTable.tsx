import React, { useState, useMemo, useCallback } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { 
  ChevronDown,
  ChevronRight,
  ChevronLeft, 
  ChevronRight as ChevronRightIcon, 
  ChevronsLeft, 
  ChevronsRight,
  Search,
  Filter,
  Download,
  ArrowRight,
  Shield,
  Users,
  Lock,
  Key,
  Eye,
  ExternalLink,
  AlertTriangle,
  Activity,
  Zap,
  FileText,
  UserCheck,
  Crown,
  Link2,
  Database
} from 'lucide-react';
import { 
  AggregatedEdgesData, 
  AggregatedEdgeGroup, 
  EdgeTableRow, 
  Edge, 
  EdgeType, 
  Node, 
  NodeType, 
  getNodeTypeColor 
} from '../../types';

// Icon mapping for edge types (same as in EdgesPage)
const getEdgeIcon = (edgeType: EdgeType) => {
  const iconMap = {
    [EdgeType.HAS_ROLE]: Shield,
    [EdgeType.MEMBER_OF]: Users,
    [EdgeType.PARENT_OF]: ArrowRight,
    [EdgeType.CAN_READ]: Eye,
    [EdgeType.CAN_WRITE]: FileText,
    [EdgeType.CAN_ADMIN]: Crown,
    [EdgeType.CAN_IMPERSONATE]: UserCheck,
    [EdgeType.CAN_IMPERSONATE_SA]: UserCheck,
    [EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY]: Key,
    [EdgeType.CAN_ACT_AS_VIA_VM]: Activity,
    [EdgeType.CAN_DEPLOY_FUNCTION_AS]: Zap,
    [EdgeType.CAN_DEPLOY_CLOUD_RUN_AS]: Activity,
    [EdgeType.CAN_TRIGGER_BUILD_AS]: Activity,
    [EdgeType.CAN_LOGIN_TO_VM]: Lock,
    [EdgeType.CAN_DEPLOY_GKE_POD_AS]: Activity,
    [EdgeType.RUNS_AS]: ArrowRight,
    [EdgeType.HAS_IMPERSONATED]: UserCheck,
    [EdgeType.HAS_ESCALATED_PRIVILEGE]: AlertTriangle,
    [EdgeType.HAS_ACCESSED]: Eye
  };
  
  return iconMap[edgeType] || Link2;
};

// Get edge type category and risk level (same as in EdgesPage)
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
  const structuralEdges = [EdgeType.HAS_ROLE, EdgeType.MEMBER_OF, EdgeType.PARENT_OF, EdgeType.RUNS_AS];

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

export interface AggregatedEdgesTableProps {
  aggregatedData: AggregatedEdgesData;
  nodes: Node[];
  title?: string;
  searchable?: boolean;
  searchPlaceholder?: string;
  filterable?: boolean;
  selectable?: boolean;
  pagination?: boolean;
  pageSize?: number;
  exportable?: boolean;
  onExport?: (selectedData: Edge[]) => void;
  onEdgeClick?: (edge: Edge) => void;
  onViewEdgeDetails?: (edge: Edge) => void;
  loading?: boolean;
  emptyMessage?: string;
  className?: string;
  onToggleGroup: (sourceNodeId: string) => void;
}

export function AggregatedEdgesTable({
  aggregatedData,
  nodes,
  title,
  searchable = true,
  searchPlaceholder = "Search edges or source entities...",
  filterable = true,
  selectable = false,
  pagination = true,
  pageSize = 10,
  exportable = false,
  onExport,
  onEdgeClick,
  onViewEdgeDetails,
  loading = false,
  emptyMessage = "No edges available",
  className = "",
  onToggleGroup
}: AggregatedEdgesTableProps) {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);
  const [isFilterOpen, setIsFilterOpen] = useState(false);
  const [riskFilter, setRiskFilter] = useState<string>('');
  const [categoryFilter, setCategoryFilter] = useState<string>('');

  // Helper function to get node name from ID
  const getNodeName = useCallback((nodeId: string): string => {
    const node = nodes.find(n => n.id === nodeId);
    return node?.name || nodeId.split(':').pop() || nodeId;
  }, [nodes]);

  // Helper function to get node type from ID
  const getNodeType = useCallback((nodeId: string): NodeType | null => {
    const node = nodes.find(n => n.id === nodeId);
    return node?.type || null;
  }, [nodes]);

  // Create flat table rows from aggregated data
  const tableRows = useMemo(() => {
    const rows: EdgeTableRow[] = [];
    
    aggregatedData.groups.forEach((group) => {
      // Add the group row
      rows.push({
        type: 'group',
        id: `group-${group.sourceNodeId}`,
        data: group,
        level: 0
      });
      
      // If expanded, add the individual edge rows
      if (group.isExpanded) {
        group.edges.forEach((edge) => {
          rows.push({
            type: 'edge',
            id: `edge-${edge.id}`,
            data: edge,
            level: 1
          });
        });
      }
    });
    
    return rows;
  }, [aggregatedData]);

  // Filter and search rows
  const filteredRows = useMemo(() => {
    let result = tableRows;

    // Apply search
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter((row) => {
        if (row.type === 'group') {
          const group = row.data as AggregatedEdgeGroup;
          const sourceName = getNodeName(group.sourceNodeId).toLowerCase();
          const sourceType = getNodeType(group.sourceNodeId)?.toLowerCase() || '';
          return sourceName.includes(query) || sourceType.includes(query) || group.sourceNodeId.toLowerCase().includes(query);
        } else {
          const edge = row.data as Edge;
          const sourceName = getNodeName(edge.source).toLowerCase();
          const targetName = getNodeName(edge.target).toLowerCase();
          const edgeType = edge.type.toLowerCase();
          return sourceName.includes(query) || targetName.includes(query) || edgeType.includes(query);
        }
      });
    }

    // Apply risk filter
    if (riskFilter && riskFilter !== '') {
      result = result.filter((row) => {
        if (row.type === 'group') {
          const group = row.data as AggregatedEdgeGroup;
          const hasHighRisk = group.edges.some(edge => {
            const { risk } = getEdgeCategory(edge.type);
            return risk === riskFilter;
          });
          return hasHighRisk;
        } else {
          const edge = row.data as Edge;
          const { risk } = getEdgeCategory(edge.type);
          return risk === riskFilter;
        }
      });
    }

    // Apply category filter
    if (categoryFilter && categoryFilter !== '') {
      result = result.filter((row) => {
        if (row.type === 'group') {
          const group = row.data as AggregatedEdgeGroup;
          const hasCategory = group.edges.some(edge => {
            const { category } = getEdgeCategory(edge.type);
            return category === categoryFilter;
          });
          return hasCategory;
        } else {
          const edge = row.data as Edge;
          const { category } = getEdgeCategory(edge.type);
          return category === categoryFilter;
        }
      });
    }

    return result;
  }, [tableRows, searchQuery, riskFilter, categoryFilter, getNodeName, getNodeType]);

  // Paginate rows
  const paginatedRows = useMemo(() => {
    if (!pagination) return filteredRows;
    
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;
    return filteredRows.slice(startIndex, endIndex);
  }, [filteredRows, currentPage, pageSize, pagination]);

  const totalPages = Math.ceil(filteredRows.length / pageSize);

  const handleSelectRow = (rowId: string, checked: boolean) => {
    const newSelected = new Set(selectedRows);
    if (checked) {
      newSelected.add(rowId);
    } else {
      newSelected.delete(rowId);
    }
    setSelectedRows(newSelected);
  };

  const handleExport = () => {
    if (!onExport) return;
    
    // Collect all edges from selected groups and individual edges
    const selectedEdges: Edge[] = [];
    
    selectedRows.forEach(rowId => {
      const row = tableRows.find(r => r.id === rowId);
      if (!row) return;
      
      if (row.type === 'group') {
        const group = row.data as AggregatedEdgeGroup;
        selectedEdges.push(...group.edges);
      } else {
        const edge = row.data as Edge;
        selectedEdges.push(edge);
      }
    });
    
    // If no specific selection, export all edges
    const edgesToExport = selectedEdges.length > 0 ? selectedEdges : aggregatedData.groups.flatMap(g => g.edges);
    onExport(edgesToExport);
  };

  const renderGroupRow = (group: AggregatedEdgeGroup) => {
    const sourceName = getNodeName(group.sourceNodeId);
    const sourceType = getNodeType(group.sourceNodeId);
    const isSelected = selectedRows.has(`group-${group.sourceNodeId}`);
    
    // Calculate summary statistics
    const riskCounts = Object.entries(group.riskCategoryCounts)
      .filter(([_, count]) => count > 0)
      .sort(([a], [b]) => {
        const order = { critical: 0, high: 1, medium: 2, low: 3 };
        return (order[a as keyof typeof order] || 4) - (order[b as keyof typeof order] || 4);
      });

    return (
      <TableRow 
        key={`group-${group.sourceNodeId}`}
        className="border-b-2 bg-slate-50/50 hover:bg-slate-100/50 font-medium"
      >
        {selectable && (
          <TableCell>
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => handleSelectRow(`group-${group.sourceNodeId}`, e.target.checked)}
              className="rounded border-gray-300"
            />
          </TableCell>
        )}
        
        {/* Expand/Collapse + Source Entity */}
        <TableCell className="py-4">
          <div className="flex items-center space-x-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggleGroup(group.sourceNodeId)}
              className="p-1 h-6 w-6"
            >
              {group.isExpanded ? (
                <ChevronDown className="h-4 w-4" />
              ) : (
                <ChevronRight className="h-4 w-4" />
              )}
            </Button>
            
            <div className="space-y-1">
              <div className="font-medium text-foreground break-words">
                {sourceName}
              </div>
              <div className="flex items-center space-x-2">
                {sourceType && (
                  <Badge 
                    variant="outline" 
                    className="text-xs"
                    style={{ 
                      borderColor: getNodeTypeColor(sourceType),
                      color: getNodeTypeColor(sourceType)
                    }}
                  >
                    {sourceType.replace(/_/g, ' ')}
                  </Badge>
                )}
              </div>
            </div>
          </div>
        </TableCell>
        
        {/* Summary Information */}
        <TableCell className="py-4">
          <div className="space-y-2">
            <div className="text-sm font-medium">
              Can access {group.targetCount} resource{group.targetCount !== 1 ? 's' : ''}
            </div>
            <div className="flex items-center space-x-2 flex-wrap">
              {riskCounts.map(([risk, count]) => {
                const riskColors = {
                  critical: 'bg-red-100 text-red-800',
                  high: 'bg-orange-100 text-orange-800',
                  medium: 'bg-yellow-100 text-yellow-800',
                  low: 'bg-blue-100 text-blue-800'
                };
                
                return (
                  <Badge 
                    key={risk} 
                    className={`text-xs ${riskColors[risk as keyof typeof riskColors]}`}
                  >
                    {count} {risk}
                  </Badge>
                );
              })}
            </div>
          </div>
        </TableCell>
        
        {/* Risk Score */}
        <TableCell className="py-4">
          <div className="flex items-center space-x-2">
            <div className="text-lg font-bold">
              {(group.highestRiskScore * 100).toFixed(0)}%
            </div>
            <Badge 
              variant="outline" 
              className={`text-xs ${
                group.highestRiskScore >= 0.8 ? 'bg-red-100 text-red-800' :
                group.highestRiskScore >= 0.6 ? 'bg-orange-100 text-orange-800' :
                group.highestRiskScore >= 0.4 ? 'bg-yellow-100 text-yellow-800' :
                'bg-blue-100 text-blue-800'
              }`}
            >
              highest
            </Badge>
          </div>
        </TableCell>
        
        {/* Actions */}
        <TableCell className="py-4">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onToggleGroup(group.sourceNodeId)}
            >
              {group.isExpanded ? 'Collapse' : 'Expand'}
            </Button>
          </div>
        </TableCell>
      </TableRow>
    );
  };

  const renderEdgeRow = (edge: Edge) => {
    const sourceName = getNodeName(edge.source);
    const targetName = getNodeName(edge.target);
    const sourceType = getNodeType(edge.source);
    const targetType = getNodeType(edge.target);
    const { category, risk } = getEdgeCategory(edge.type);
    const IconComponent = getEdgeIcon(edge.type);
    const isSelected = selectedRows.has(`edge-${edge.id}`);
    
    const riskColors = {
      critical: 'bg-red-100 text-red-800',
      high: 'bg-orange-100 text-orange-800',
      medium: 'bg-yellow-100 text-yellow-800',
      low: 'bg-blue-100 text-blue-800'
    };

    return (
      <TableRow 
        key={`edge-${edge.id}`}
        className="border-l-4 border-l-blue-200 bg-white hover:bg-slate-50"
        onClick={() => onEdgeClick?.(edge)}
      >
        {selectable && (
          <TableCell>
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => {
                e.stopPropagation();
                handleSelectRow(`edge-${edge.id}`, e.target.checked);
              }}
              className="rounded border-gray-300 ml-4"
            />
          </TableCell>
        )}
        
        {/* Edge Type - indented */}
        <TableCell className="py-3">
          <div className="ml-8 space-y-2">
            <div className="flex items-center space-x-2">
              <IconComponent className="h-4 w-4 text-muted-foreground" />
              <span className="font-medium text-sm">
                {edge.type.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
              </span>
            </div>
            <div className="flex items-center space-x-2">
              <Badge className={`text-xs ${riskColors[risk]}`}>
                {risk}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {category}
              </Badge>
            </div>
          </div>
        </TableCell>
        
        {/* Target Node */}
        <TableCell className="py-3">
          <div className="space-y-1">
            <div className="font-medium text-foreground break-words">
              {targetName}
            </div>
            <div className="flex items-center space-x-2">
              {targetType && (
                <Badge 
                  variant="outline" 
                  className="text-xs"
                  style={{ 
                    borderColor: getNodeTypeColor(targetType),
                    color: getNodeTypeColor(targetType)
                  }}
                >
                  {targetType.replace(/_/g, ' ')}
                </Badge>
              )}
            </div>
          </div>
        </TableCell>
        
        {/* Properties */}
        <TableCell className="py-3">
          <div className="space-y-1">
            {edge.properties?.role && (
              <div className="text-xs text-muted-foreground break-words">
                Role: {edge.properties.role}
              </div>
            )}
            {edge.properties?.condition && (
              <div className="text-xs text-muted-foreground">
                Conditional
              </div>
            )}
            {edge.properties?.inherited && (
              <div className="text-xs text-muted-foreground">
                Inherited
              </div>
            )}
          </div>
        </TableCell>
        
        {/* Actions */}
        <TableCell className="py-3">
          <div className="flex items-center space-x-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                onViewEdgeDetails?.(edge);
              }}
            >
              <Eye className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                // TODO: Navigate to graph focused on this edge
                alert(`Focus graph on edge: ${edge.source} -> ${edge.target}`);
              }}
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </TableCell>
      </TableRow>
    );
  };

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="p-8">
          <div className="flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
            <span className="ml-2 text-muted-foreground">Loading...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      {title && (
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>{title}</span>
            <div className="flex items-center space-x-2">
              {filterable && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setIsFilterOpen(!isFilterOpen)}
                >
                  <Filter className="h-4 w-4 mr-2" />
                  Filters
                </Button>
              )}
              {exportable && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleExport}
                >
                  <Download className="h-4 w-4 mr-2" />
                  {selectable && selectedRows.size > 0 
                    ? `Export Selected`
                    : `Export All`
                  }
                </Button>
              )}
            </div>
          </CardTitle>
        </CardHeader>
      )}
      
      <CardContent>
        {/* Search and filter controls */}
        <div className="space-y-4 mb-6">
          {searchable && (
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder={searchPlaceholder}
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          )}

          {/* Filters */}
          {filterable && isFilterOpen && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 p-4 border rounded-lg bg-muted/50">
              <div>
                <label className="text-sm font-medium mb-2 block">Risk Level</label>
                <select
                  value={riskFilter}
                  onChange={(e) => setRiskFilter(e.target.value)}
                  className="w-full p-2 border rounded text-sm"
                >
                  <option value="">All Risk Levels</option>
                  <option value="critical">Critical</option>
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">Category</label>
                <select
                  value={categoryFilter}
                  onChange={(e) => setCategoryFilter(e.target.value)}
                  className="w-full p-2 border rounded text-sm"
                >
                  <option value="">All Categories</option>
                  <option value="Privilege Escalation">Privilege Escalation</option>
                  <option value="Administrative">Administrative</option>
                  <option value="Access Control">Access Control</option>
                  <option value="Structural">Structural</option>
                </select>
              </div>
            </div>
          )}
        </div>

        {/* Data display info */}
        <div className="flex items-center justify-between mb-4">
          <p className="text-sm text-muted-foreground">
            Showing {aggregatedData.totalGroups} source entities with {aggregatedData.totalEdges} total relationships
            {selectable && selectedRows.size > 0 && (
              <span className="ml-2">({selectedRows.size} selected)</span>
            )}
          </p>
          {pagination && totalPages > 1 && (
            <p className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </p>
          )}
        </div>

        {/* Table */}
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                {selectable && (
                  <TableHead className="w-12">
                    <span className="sr-only">Select</span>
                  </TableHead>
                )}
                <TableHead className="min-w-[250px]">Source Entity / Relationship</TableHead>
                <TableHead className="min-w-[200px]">Target / Summary</TableHead>
                <TableHead className="w-32">Risk Score</TableHead>
                <TableHead className="w-32">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {paginatedRows.length === 0 ? (
                <TableRow>
                  <TableCell 
                    colSpan={5} 
                    className="text-center py-8 text-muted-foreground"
                  >
                    {emptyMessage}
                  </TableCell>
                </TableRow>
              ) : (
                paginatedRows.map((row) => {
                  if (row.type === 'group') {
                    return renderGroupRow(row.data as AggregatedEdgeGroup);
                  } else {
                    return renderEdgeRow(row.data as Edge);
                  }
                })
              )}
            </TableBody>
          </Table>
        </div>

        {/* Pagination */}
        {pagination && totalPages > 1 && (
          <div className="flex items-center justify-between mt-4">
            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(1)}
                disabled={currentPage === 1}
              >
                <ChevronsLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
                disabled={currentPage === 1}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
            </div>

            <span className="text-sm text-muted-foreground">
              Page {currentPage} of {totalPages}
            </span>

            <div className="flex items-center space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
                disabled={currentPage === totalPages}
              >
                <ChevronRightIcon className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setCurrentPage(totalPages)}
                disabled={currentPage === totalPages}
              >
                <ChevronsRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
} 