import React, { useState, useEffect, useRef } from 'react';
import { 
  Search, 
  X, 
  ChevronDown,
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
  Navigation
} from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { GraphNode, NodeType } from '../../types';

interface SearchResult {
  node: GraphNode;
  score: number;
  matchType: 'name' | 'id' | 'property';
  matchText: string;
}

interface GraphSearchProps {
  nodes: GraphNode[];
  onNodeSelect: (nodeId: string) => void;
  onNodeHighlight: (nodeIds: string[]) => void;
  onSearchClear: () => void;
  selectedNodeId?: string;
  highlightedNodeIds?: string[];
  className?: string;
}

const NODE_ICONS: Record<NodeType, React.ComponentType<any>> = {
  [NodeType.USER]: User,
  [NodeType.SERVICE_ACCOUNT]: Bot,
  [NodeType.GROUP]: Users,
  [NodeType.PROJECT]: FolderOpen,
  [NodeType.FOLDER]: FolderOpen,
  [NodeType.ORGANIZATION]: Building,
  [NodeType.ROLE]: Shield,
  [NodeType.CUSTOM_ROLE]: Shield,
  [NodeType.BUCKET]: Database,
  [NodeType.INSTANCE]: Server,
  [NodeType.FUNCTION]: Zap,
  [NodeType.SECRET]: Key,
  [NodeType.KMS_KEY]: Key,
  [NodeType.DATASET]: Database,
  [NodeType.TOPIC]: Database,
  [NodeType.CLOUD_RUN_SERVICE]: Server,
  [NodeType.GKE_CLUSTER]: Server,
  [NodeType.CLOUD_BUILD_TRIGGER]: Zap,
  [NodeType.COMPUTE_INSTANCE]: Server
};

const NODE_COLORS: Record<NodeType, string> = {
  [NodeType.USER]: '#4285F4',
  [NodeType.SERVICE_ACCOUNT]: '#34A853',
  [NodeType.GROUP]: '#FBBC04',
  [NodeType.PROJECT]: '#EA4335',
  [NodeType.FOLDER]: '#FF6D00',
  [NodeType.ORGANIZATION]: '#9C27B0',
  [NodeType.ROLE]: '#757575',
  [NodeType.CUSTOM_ROLE]: '#616161',
  [NodeType.BUCKET]: '#00ACC1',
  [NodeType.INSTANCE]: '#FF9800',
  [NodeType.FUNCTION]: '#9C27B0',
  [NodeType.SECRET]: '#F44336',
  [NodeType.KMS_KEY]: '#FFA726',
  [NodeType.DATASET]: '#42A5F5',
  [NodeType.TOPIC]: '#66BB6A',
  [NodeType.CLOUD_RUN_SERVICE]: '#29B6F6',
  [NodeType.GKE_CLUSTER]: '#5C6BC0',
  [NodeType.CLOUD_BUILD_TRIGGER]: '#FF8A65',
  [NodeType.COMPUTE_INSTANCE]: '#FF7043'
};

export function GraphSearch({
  nodes,
  onNodeSelect,
  onNodeHighlight,
  onSearchClear,
  selectedNodeId,
  highlightedNodeIds = [],
  className = ''
}: GraphSearchProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [recentSearches, setRecentSearches] = useState<string[]>([]);
  
  const searchRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Search function
  const searchNodes = (searchQuery: string): SearchResult[] => {
    if (!searchQuery.trim()) return [];

    const query = searchQuery.toLowerCase();
    const results: SearchResult[] = [];

    nodes.forEach(node => {
      let score = 0;
      let matchType: 'name' | 'id' | 'property' = 'name';
      let matchText = '';

      // Exact name match (highest priority)
      if (node.name.toLowerCase() === query) {
        score = 100;
        matchType = 'name';
        matchText = node.name;
      }
      // Name starts with query
      else if (node.name.toLowerCase().startsWith(query)) {
        score = 90;
        matchType = 'name';
        matchText = node.name;
      }
      // Name contains query
      else if (node.name.toLowerCase().includes(query)) {
        score = 80;
        matchType = 'name';
        matchText = node.name;
      }
      // ID exact match
      else if (node.id.toLowerCase() === query) {
        score = 95;
        matchType = 'id';
        matchText = node.id;
      }
      // ID starts with query
      else if (node.id.toLowerCase().startsWith(query)) {
        score = 85;
        matchType = 'id';
        matchText = node.id;
      }
      // ID contains query
      else if (node.id.toLowerCase().includes(query)) {
        score = 75;
        matchType = 'id';
        matchText = node.id;
      }
      // Property search
      else {
        const props = node.properties || {};
        for (const [key, value] of Object.entries(props)) {
          if (typeof value === 'string' && value.toLowerCase().includes(query)) {
            score = 60;
            matchType = 'property';
            matchText = `${key}: ${value}`;
            break;
          }
        }
      }

      // Boost score for dangerous/high-risk nodes
      if (node.properties?.is_dangerous) score += 10;
      if (node.properties?.risk_score > 0.8) score += 8;
      else if (node.properties?.risk_score > 0.6) score += 5;

      // Boost score for certain node types
      if ([NodeType.USER, NodeType.SERVICE_ACCOUNT, NodeType.PROJECT].includes(node.type)) {
        score += 5;
      }

      if (score > 0) {
        results.push({
          node,
          score,
          matchType,
          matchText
        });
      }
    });

    // Sort by score (highest first)
    return results.sort((a, b) => b.score - a.score).slice(0, 10);
  };

  // Handle search input change
  useEffect(() => {
    const searchResults = searchNodes(query);
    setResults(searchResults);
    setSelectedIndex(-1);
    setIsOpen(query.length > 0);
    
    // Highlight matching nodes
    if (searchResults.length > 0) {
      const nodeIds = searchResults.map(r => r.node.id);
      onNodeHighlight(nodeIds);
    } else if (query.length === 0) {
      onNodeHighlight([]);
    }
  }, [query, nodes]);

  // Handle keyboard navigation
  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < results.length - 1 ? prev + 1 : prev
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => prev > 0 ? prev - 1 : prev);
        break;
      case 'Enter':
        e.preventDefault();
        if (selectedIndex >= 0 && selectedIndex < results.length) {
          handleResultSelect(results[selectedIndex]);
        } else if (results.length > 0) {
          handleResultSelect(results[0]);
        }
        break;
      case 'Escape':
        e.preventDefault();
        handleClear();
        break;
    }
  };

  // Handle result selection
  const handleResultSelect = (result: SearchResult) => {
    onNodeSelect(result.node.id);
    setQuery(result.node.name);
    setIsOpen(false);
    
    // Add to recent searches
    setRecentSearches(prev => {
      const updated = [result.node.name, ...prev.filter(s => s !== result.node.name)];
      return updated.slice(0, 5);
    });
  };

  // Handle search clear
  const handleClear = () => {
    setQuery('');
    setResults([]);
    setIsOpen(false);
    setSelectedIndex(-1);
    onSearchClear();
    inputRef.current?.focus();
  };

  // Handle outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (searchRef.current && !searchRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const formatNodeTitle = (node: GraphNode): string => {
    const parts = [node.type.replace('_', ' ').toUpperCase()];
    if (node.properties?.project_id) {
      parts.push(`Project: ${node.properties.project_id}`);
    }
    return parts.join(' • ');
  };

  const getRiskBadge = (node: GraphNode) => {
    const riskScore = node.properties?.risk_score || 0;
    let variant: 'destructive' | 'warning' | 'secondary' | 'outline' = 'outline';
    let label = 'Low';
    
    if (riskScore >= 0.8) {
      variant = 'destructive';
      label = 'Critical';
    } else if (riskScore >= 0.6) {
      variant = 'destructive';
      label = 'High';
    } else if (riskScore >= 0.4) {
      variant = 'warning';
      label = 'Medium';
    } else if (riskScore >= 0.2) {
      variant = 'secondary';
      label = 'Low';
    }

    return <Badge variant={variant} className="text-xs">{label}</Badge>;
  };

  const highlightMatch = (text: string, query: string): React.ReactNode => {
    if (!query.trim()) return text;
    
    const index = text.toLowerCase().indexOf(query.toLowerCase());
    if (index === -1) return text;
    
    return (
      <>
        {text.substring(0, index)}
        <mark className="bg-yellow-200 text-yellow-900 px-0.5 rounded">
          {text.substring(index, index + query.length)}
        </mark>
        {text.substring(index + query.length)}
      </>
    );
  };

  return (
    <div ref={searchRef} className={`relative ${className}`}>
      <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
        <CardContent className="p-3">
          <div className="space-y-3">
            {/* Search Input */}
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                ref={inputRef}
                type="text"
                placeholder="Search nodes by name, ID, or properties..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsOpen(query.length > 0 || results.length > 0)}
                className="w-full pl-10 pr-10 py-2.5 text-sm border border-gray-300 rounded-lg focus:ring-blue-500 focus:border-blue-500 bg-white"
              />
              {query && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleClear}
                  className="absolute right-2 top-1/2 transform -translate-y-1/2 w-6 h-6 p-0"
                >
                  <X className="w-3 h-3" />
                </Button>
              )}
            </div>

            {/* Quick Stats */}
            {query && (
              <div className="flex items-center justify-between text-xs text-gray-600">
                <span>{results.length} result{results.length !== 1 ? 's' : ''} found</span>
                {highlightedNodeIds.length > 0 && (
                  <span>{highlightedNodeIds.length} node{highlightedNodeIds.length !== 1 ? 's' : ''} highlighted</span>
                )}
              </div>
            )}

            {/* Recent Searches */}
            {!query && recentSearches.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-700 mb-2">Recent Searches</div>
                <div className="flex flex-wrap gap-1">
                  {recentSearches.map((search, index) => (
                    <Button
                      key={index}
                      variant="outline"
                      size="sm"
                      onClick={() => setQuery(search)}
                      className="h-6 text-xs"
                    >
                      {search}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Search Results Dropdown */}
      {isOpen && results.length > 0 && (
        <Card className="absolute top-full left-0 right-0 mt-1 border-0 shadow-lg bg-white z-50 max-h-96 overflow-y-auto">
          <CardContent className="p-0">
            {results.map((result, index) => {
              const IconComponent = NODE_ICONS[result.node.type] || Database;
              const isSelected = index === selectedIndex;
              const isCurrentlySelected = result.node.id === selectedNodeId;
              
              return (
                <div
                  key={result.node.id}
                  className={`p-3 border-b border-gray-100 last:border-b-0 cursor-pointer transition-colors ${
                    isSelected ? 'bg-blue-50' : 'hover:bg-gray-50'
                  } ${isCurrentlySelected ? 'bg-blue-100' : ''}`}
                  onClick={() => handleResultSelect(result)}
                >
                  <div className="flex items-start space-x-3">
                    <div className="flex-shrink-0 mt-0.5">
                      <div
                        className="w-8 h-8 rounded-lg flex items-center justify-center"
                        style={{ backgroundColor: NODE_COLORS[result.node.type] + '20' }}
                      >
                        <IconComponent 
                          className="w-4 h-4" 
                          style={{ color: NODE_COLORS[result.node.type] }}
                        />
                      </div>
                    </div>
                    
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between">
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {highlightMatch(result.node.name, query)}
                          </div>
                          <div className="text-xs text-gray-500 truncate">
                            {formatNodeTitle(result.node)}
                          </div>
                          {result.matchType === 'property' && (
                            <div className="text-xs text-blue-600 mt-1">
                              Match: {highlightMatch(result.matchText, query)}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex items-center space-x-2 ml-2">
                          {result.node.properties?.is_dangerous && (
                            <Badge variant="destructive" className="text-xs">
                              Dangerous
                            </Badge>
                          )}
                          {getRiskBadge(result.node)}
                          {isCurrentlySelected && (
                            <Eye className="w-3 h-3 text-blue-600" />
                          )}
                        </div>
                      </div>
                      
                      {result.node.id !== result.node.name && (
                        <div className="text-xs text-gray-400 mt-1 font-mono truncate">
                          {result.matchType === 'id' ? 
                            highlightMatch(result.node.id, query) : 
                            result.node.id
                          }
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              );
            })}
            
            {/* Search Tips */}
            <div className="p-3 bg-gray-50 border-t border-gray-100">
              <div className="text-xs text-gray-600">
                <div className="font-medium mb-1">Search Tips:</div>
                <div>• Use arrow keys to navigate • Enter to select • Esc to clear</div>
                <div>• Search by name, ID, or any property</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
} 