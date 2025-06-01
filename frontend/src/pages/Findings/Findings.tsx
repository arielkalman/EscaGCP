import React, { useState, useMemo, useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { AlertTriangle, Shield, Target, Filter, SortAsc, SortDesc } from 'lucide-react';
import { dataService } from '../../services/dataService';
import { AttackPath, getRiskLevel, RiskLevel } from '../../types';
import { FindingListItem } from '../../components/findings/FindingListItem';
import { GhostUsersToggle } from '../../components/common/GhostUsersToggle';
import { Button } from '../../components/ui/button';
import { Input } from '../../components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../../components/ui/select';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { useAppSettings } from '../../context/AppSettingsContext';
import { isGhostNode, getGhostUserStats } from '../../utils/ghostUsers';

type SortOption = 'risk_score' | 'length' | 'category' | 'source' | 'target';
type SortDirection = 'asc' | 'desc';

interface CategoryStats {
  count: number;
  avgRisk: number;
  maxRisk: number;
}

interface ProcessedAttackPath extends AttackPath {
  category: string;
  riskLevel: RiskLevel;
  isGhostPath: boolean;
  searchText: string; // Pre-computed search text for faster filtering
}

export function Findings() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [riskFilter, setRiskFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<SortOption>('risk_score');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [activeTab, setActiveTab] = useState('all');

  const { settings } = useAppSettings();
  const navigate = useNavigate();

  // Load analysis data
  const { data: analysisData, isLoading, error } = useQuery({
    queryKey: ['analysis-data'],
    queryFn: () => dataService.loadAnalysisData(),
  });

  // Load graph data for ghost user stats
  const { data: graphData } = useQuery({
    queryKey: ['graph'],
    queryFn: () => dataService.loadGraphData(),
  });

  // Calculate ghost user statistics (optimized)
  const ghostUserStats = useMemo(() => {
    if (!graphData?.nodes || !graphData?.edges) {
      return {
        totalGhostNodes: 0,
        ghostUsers: 0,
        ghostServiceAccounts: 0,
        edgesWithGhostUsers: 0
      };
    }
    return getGhostUserStats(graphData.nodes, graphData.edges);
  }, [graphData?.nodes, graphData?.edges]);

  // Optimized ghost node checker - simplified for performance
  const isNodeGhostMemo = useCallback((node: { id?: string; name?: string; type?: string; properties?: Record<string, unknown> } | null): boolean => {
    if (!node || typeof node !== 'object') return false;
    
    const id = node.id || '';
    const name = node.name || '';
    
    // Fast ghost detection using common patterns
    return id.startsWith('deleted:') || 
           name.startsWith('deleted:') || 
           name.includes('deleted') || 
           id.includes('deleted') ||
           name.includes('unknown') ||
           id.includes('unknown') ||
           // Check for typical ghost user patterns
           /^deleted[_-]/.test(name) ||
           /[_-]deleted$/.test(name) ||
           name === '' ||
           id === '';
  }, []);

  // Process all attack paths once with pre-computed metadata for performance
  const processedAttackPaths = useMemo(() => {
    if (!analysisData?.attack_paths) return [];
    
    const paths: ProcessedAttackPath[] = [];
    
    Object.entries(analysisData.attack_paths).forEach(([category, categoryPaths]) => {
      if (Array.isArray(categoryPaths)) {
        categoryPaths.forEach(path => {
          // Pre-compute expensive operations
          const riskLevel = getRiskLevel(path.risk_score);
          
          // Check for ghost nodes once
          const sourceIsGhost = isNodeGhostMemo(path.source);
          const targetIsGhost = isNodeGhostMemo(path.target);
          const hasGhostInPath = path.path_nodes?.some((node: any) => isNodeGhostMemo(node)) || false;
          const isGhostPath = sourceIsGhost || targetIsGhost || hasGhostInPath;
          
          // Pre-compute search text for faster filtering
          const searchText = [
            path.source.name,
            path.target.name,
            path.description,
            category
          ].join(' ').toLowerCase();
          
          paths.push({
            ...path,
            category,
            riskLevel,
            isGhostPath,
            searchText
          });
        });
      }
    });
    
    return paths;
  }, [analysisData, isNodeGhostMemo]);

  // Filter paths based on ghost users setting (optimized)
  const ghostFilteredPaths = useMemo(() => {
    if (settings.showGhostUsers) {
      return processedAttackPaths;
    }
    return processedAttackPaths.filter(path => !path.isGhostPath);
  }, [processedAttackPaths, settings.showGhostUsers]);

  // Calculate category statistics efficiently (single pass)
  const categoryStats = useMemo(() => {
    const stats: Record<string, CategoryStats> = {};
    const categoryRiskSums: Record<string, number> = {};
    
    // Single pass through the data
    ghostFilteredPaths.forEach(path => {
      if (!stats[path.category]) {
        stats[path.category] = { count: 0, avgRisk: 0, maxRisk: 0 };
        categoryRiskSums[path.category] = 0;
      }
      
      stats[path.category].count++;
      stats[path.category].maxRisk = Math.max(stats[path.category].maxRisk, path.risk_score);
      categoryRiskSums[path.category] += path.risk_score;
    });
    
    // Calculate averages
    Object.keys(stats).forEach(category => {
      stats[category].avgRisk = categoryRiskSums[category] / stats[category].count;
    });
    
    return stats;
  }, [ghostFilteredPaths]);

  // Pre-compute risk level counts for better performance
  const riskLevelCounts = useMemo(() => {
    const counts: Record<string, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };
    
    ghostFilteredPaths.forEach(path => {
      if (counts.hasOwnProperty(path.riskLevel)) {
        counts[path.riskLevel]++;
      }
    });
    
    return counts;
  }, [ghostFilteredPaths]);

  // Filter and sort attack paths (optimized)
  const filteredAndSortedPaths = useMemo(() => {
    let filtered = ghostFilteredPaths;

    // Apply search filter (using pre-computed search text)
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(path => path.searchText.includes(query));
    }

    // Apply category filter
    if (selectedCategory !== 'all') {
      filtered = filtered.filter(path => path.category === selectedCategory);
    }

    // Apply risk level filter (using pre-computed risk level)
    if (riskFilter !== 'all') {
      filtered = filtered.filter(path => path.riskLevel === riskFilter);
    }

    // Apply tab filter (using pre-computed risk level)
    if (activeTab !== 'all') {
      filtered = filtered.filter(path => path.riskLevel === activeTab);
    }

    // Sort paths (optimized comparisons)
    filtered.sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case 'risk_score':
          comparison = a.risk_score - b.risk_score;
          break;
        case 'length':
          comparison = a.length - b.length;
          break;
        case 'category':
          comparison = a.category.localeCompare(b.category);
          break;
        case 'source':
          comparison = a.source.name.localeCompare(b.source.name);
          break;
        case 'target':
          comparison = a.target.name.localeCompare(b.target.name);
          break;
      }
      
      return sortDirection === 'desc' ? -comparison : comparison;
    });

    return filtered;
  }, [ghostFilteredPaths, searchQuery, selectedCategory, riskFilter, sortBy, sortDirection, activeTab]);

  // Group paths by risk level (optimized - use pre-filtered data)
  const pathsByRiskLevel = useMemo(() => {
    const grouped: Record<string, ProcessedAttackPath[]> = {
      critical: [],
      high: [],
      medium: [],
      low: [],
    };
    
    filteredAndSortedPaths.forEach(path => {
      if (grouped.hasOwnProperty(path.riskLevel)) {
        grouped[path.riskLevel].push(path);
      }
    });
    
    return grouped;
  }, [filteredAndSortedPaths]);

  const handleViewInGraph = useCallback((attackPath: AttackPath) => {
    console.log('View in graph:', attackPath);
    
    // Navigate to the dedicated attack path visualization page
    const attackPathData = encodeURIComponent(JSON.stringify(attackPath));
    navigate(`/attack-path?data=${attackPathData}`);
  }, [navigate]);

  const handleExport = useCallback((attackPath: AttackPath) => {
    console.log('Export finding:', attackPath);
    const data = JSON.stringify(attackPath, null, 2);
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attack-path-${attackPath.source.id}-${attackPath.target.id}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, []);

  const toggleSort = useCallback((field: SortOption) => {
    if (sortBy === field) {
      setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDirection('desc');
    }
  }, [sortBy]);

  // Memoize expensive computations
  const categories = useMemo(() => Object.keys(categoryStats), [categoryStats]);
  const totalOriginalPaths = useMemo(() => processedAttackPaths.length, [processedAttackPaths]);
  const totalFilteredPaths = useMemo(() => ghostFilteredPaths.length, [ghostFilteredPaths]);
  
  // Pre-compute original risk counts for statistics
  const originalRiskCounts = useMemo(() => {
    const counts: Record<string, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };
    
    processedAttackPaths.forEach(path => {
      if (counts.hasOwnProperty(path.riskLevel)) {
        counts[path.riskLevel]++;
      }
    });
    
    return counts;
  }, [processedAttackPaths]);

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <span className="ml-2 text-muted-foreground">Loading findings...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="text-center text-red-600">
          <AlertTriangle className="h-16 w-16 mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Error Loading Findings</h2>
          <p>There was an error loading the security findings. Please try again later.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <AlertTriangle className="h-8 w-8 text-primary" />
          <div>
            <h1 className="text-3xl font-bold text-foreground">Security Findings</h1>
            <p className="text-muted-foreground">
              Detected attack paths and privilege escalation opportunities
              {totalOriginalPaths !== totalFilteredPaths && (
                <span className="ml-2 text-sm">
                  (Showing {totalFilteredPaths} of {totalOriginalPaths} paths)
                </span>
              )}
            </p>
          </div>
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
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <div>
                <div className="text-2xl font-bold">{riskLevelCounts.critical}</div>
                <div className="text-sm text-muted-foreground">Critical</div>
                {totalOriginalPaths !== totalFilteredPaths && (
                  <div className="text-xs text-muted-foreground">
                    of {originalRiskCounts.critical}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Shield className="h-5 w-5 text-orange-500" />
              <div>
                <div className="text-2xl font-bold">{riskLevelCounts.high}</div>
                <div className="text-sm text-muted-foreground">High Risk</div>
                {totalOriginalPaths !== totalFilteredPaths && (
                  <div className="text-xs text-muted-foreground">
                    of {originalRiskCounts.high}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Target className="h-5 w-5 text-yellow-500" />
              <div>
                <div className="text-2xl font-bold">{riskLevelCounts.medium}</div>
                <div className="text-sm text-muted-foreground">Medium Risk</div>
                {totalOriginalPaths !== totalFilteredPaths && (
                  <div className="text-xs text-muted-foreground">
                    of {originalRiskCounts.medium}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <div className="h-5 w-5 bg-blue-500 rounded" />
              <div>
                <div className="text-2xl font-bold">{totalFilteredPaths}</div>
                <div className="text-sm text-muted-foreground">Total Paths</div>
                {totalOriginalPaths !== totalFilteredPaths && (
                  <div className="text-xs text-muted-foreground">
                    of {totalOriginalPaths}
                  </div>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Ghost Users Information */}
      {ghostUserStats.totalGhostNodes > 0 && !settings.showGhostUsers && (
        <Card className="border-l-4 border-l-gray-400">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-foreground">
                  {totalOriginalPaths - totalFilteredPaths} attack paths involving ghost users are hidden
                </p>
                <p className="text-xs text-muted-foreground">
                  These paths involve deleted or inactive users/service accounts
                </p>
              </div>
              <Badge variant="secondary" className="text-xs">
                {totalOriginalPaths - totalFilteredPaths} filtered
              </Badge>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Filters and Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Filter & Sort</span>
            <Badge variant="outline">
              {filteredAndSortedPaths.length} result{filteredAndSortedPaths.length !== 1 ? 's' : ''}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Search */}
            <div>
              <label className="text-sm font-medium mb-2 block">Search</label>
              <Input
                placeholder="Search findings..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>

            {/* Category Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">Category</label>
              <Select value={selectedCategory} onValueChange={setSelectedCategory}>
                <SelectTrigger>
                  <SelectValue placeholder="All categories" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Categories</SelectItem>
                  {categories.map(category => (
                    <SelectItem key={category} value={category}>
                      {category.split('_').map(word => 
                        word.charAt(0).toUpperCase() + word.slice(1)
                      ).join(' ')} ({categoryStats[category].count})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Risk Filter */}
            <div>
              <label className="text-sm font-medium mb-2 block">Risk Level</label>
              <Select value={riskFilter} onValueChange={setRiskFilter}>
                <SelectTrigger>
                  <SelectValue placeholder="All risk levels" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Risk Levels</SelectItem>
                  <SelectItem value="critical">Critical</SelectItem>
                  <SelectItem value="high">High</SelectItem>
                  <SelectItem value="medium">Medium</SelectItem>
                  <SelectItem value="low">Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Sort Options */}
            <div>
              <label className="text-sm font-medium mb-2 block">Sort By</label>
              <div className="flex space-x-2">
                <Select value={sortBy} onValueChange={(value: SortOption) => setSortBy(value)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="risk_score">Risk Score</SelectItem>
                    <SelectItem value="length">Path Length</SelectItem>
                    <SelectItem value="category">Category</SelectItem>
                    <SelectItem value="source">Source</SelectItem>
                    <SelectItem value="target">Target</SelectItem>
                  </SelectContent>
                </Select>
                
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setSortDirection(prev => prev === 'asc' ? 'desc' : 'asc')}
                >
                  {sortDirection === 'asc' ? <SortAsc className="h-4 w-4" /> : <SortDesc className="h-4 w-4" />}
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Findings List with Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">
            All ({filteredAndSortedPaths.length})
          </TabsTrigger>
          <TabsTrigger value="critical">
            Critical ({pathsByRiskLevel.critical.length})
          </TabsTrigger>
          <TabsTrigger value="high">
            High ({pathsByRiskLevel.high.length})
          </TabsTrigger>
          <TabsTrigger value="medium">
            Medium ({pathsByRiskLevel.medium.length})
          </TabsTrigger>
          <TabsTrigger value="low">
            Low ({pathsByRiskLevel.low.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          {filteredAndSortedPaths.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <AlertTriangle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No findings match your criteria</h3>
                <p className="text-muted-foreground">
                  Try adjusting your search terms or filters to see more results.
                </p>
              </CardContent>
            </Card>
          ) : (
            filteredAndSortedPaths.map((path, index) => (
              <FindingListItem
                key={`${path.source.id}-${path.target.id}-${index}`}
                attackPath={path}
                onViewInGraph={handleViewInGraph}
                onExport={handleExport}
              />
            ))
          )}
        </TabsContent>

        {(['critical', 'high', 'medium', 'low'] as const).map(riskLevel => (
          <TabsContent key={riskLevel} value={riskLevel} className="space-y-4">
            {pathsByRiskLevel[riskLevel].length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <AlertTriangle className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                  <h3 className="text-lg font-semibold mb-2">
                    No {riskLevel} risk findings
                  </h3>
                  <p className="text-muted-foreground">
                    No attack paths found with {riskLevel} risk level.
                  </p>
                </CardContent>
              </Card>
            ) : (
              pathsByRiskLevel[riskLevel].map((path, index) => (
                <FindingListItem
                  key={`${path.source.id}-${path.target.id}-${index}`}
                  attackPath={path}
                  onViewInGraph={handleViewInGraph}
                  onExport={handleExport}
                />
              ))
            )}
          </TabsContent>
        ))}
      </Tabs>
    </div>
  );
} 