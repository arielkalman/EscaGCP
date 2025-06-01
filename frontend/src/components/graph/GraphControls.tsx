import React from 'react';
import { 
  ZoomIn, 
  ZoomOut, 
  Maximize, 
  Download, 
  Settings, 
  Play, 
  Pause,
  RotateCcw,
  Grid3X3,
  Network,
  HelpCircle,
  Target,
  Zap,
  Building
} from 'lucide-react';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';

interface GraphControlsProps {
  onZoomIn: () => void;
  onZoomOut: () => void;
  onFit: () => void;
  onReset?: () => void;
  onExport?: () => void;
  onTogglePhysics?: () => void;
  onToggleLayout?: () => void;
  onSettings?: () => void;
  onFocusHighRisk?: () => void;
  onShowAttackPaths?: () => void;
  onCenterOrganization?: () => void;
  isPhysicsEnabled?: boolean;
  isHierarchicalLayout?: boolean;
  totalNodes?: number;
  totalEdges?: number;
  selectedNodes?: number;
  className?: string;
}

export function GraphControls({
  onZoomIn,
  onZoomOut,
  onFit,
  onReset,
  onExport,
  onTogglePhysics,
  onToggleLayout,
  onSettings,
  onFocusHighRisk,
  onShowAttackPaths,
  onCenterOrganization,
  isPhysicsEnabled = true,
  isHierarchicalLayout = false,
  totalNodes = 0,
  totalEdges = 0,
  selectedNodes = 0,
  className = ''
}: GraphControlsProps) {

  const handleExportImage = () => {
    if (onExport) {
      onExport();
    } else {
      // Default export implementation using canvas
      try {
        const canvas = document.querySelector('canvas') as HTMLCanvasElement;
        if (canvas) {
          const link = document.createElement('a');
          link.download = `graph-visualization-${new Date().toISOString().split('T')[0]}.png`;
          link.href = canvas.toDataURL();
          link.click();
        } else {
          console.warn('No canvas found for export');
          alert('Export functionality is not available - no canvas found');
        }
      } catch (error) {
        console.error('Export failed:', error);
        alert('Export failed. Please try again.');
      }
    }
  };

  const handleFocusHighRisk = () => {
    if (onFocusHighRisk) {
      onFocusHighRisk();
    } else {
      console.log('Focus on high-risk nodes');
      // Default behavior: scroll to high-risk section or highlight high-risk nodes
      alert('Focusing on high-risk nodes...');
    }
  };

  const handleShowAttackPaths = () => {
    if (onShowAttackPaths) {
      onShowAttackPaths();
    } else {
      console.log('Show attack paths');
      // Default behavior: highlight attack paths in the graph
      alert('Highlighting attack paths...');
    }
  };

  const handleCenterOrganization = () => {
    if (onCenterOrganization) {
      onCenterOrganization();
    } else {
      console.log('Center on organization');
      // Default behavior: center the view on organization nodes
      alert('Centering on organization...');
    }
  };

  return (
    <TooltipProvider>
      <div className={`space-y-4 ${className}`} data-testid="graph-controls">
        {/* Graph Statistics */}
        <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="text-xs font-medium text-gray-700 mb-2">Graph Statistics</div>
            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600">Nodes:</span>
                <Badge variant="secondary" className="text-xs">
                  {totalNodes.toLocaleString()}
                </Badge>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-xs text-gray-600">Edges:</span>
                <Badge variant="secondary" className="text-xs">
                  {totalEdges.toLocaleString()}
                </Badge>
              </div>
              {selectedNodes > 0 && (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Selected:</span>
                  <Badge variant="outline" className="text-xs">
                    {selectedNodes}
                  </Badge>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* View Controls */}
        <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="text-xs font-medium text-gray-700 mb-3">View Controls</div>
            <div className="grid grid-cols-2 gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={onZoomIn}
                className="h-8 text-xs"
                title="Zoom In"
              >
                <ZoomIn className="w-3 h-3 mr-1" />
                Zoom In
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={onZoomOut}
                className="h-8 text-xs"
                title="Zoom Out"
              >
                <ZoomOut className="w-3 h-3 mr-1" />
                Zoom Out
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={onFit}
                className="h-8 text-xs col-span-2"
                title="Fit to View"
              >
                <Maximize className="w-3 h-3 mr-1" />
                Fit to View
              </Button>
              
              {onReset && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onReset}
                  className="h-8 text-xs col-span-2"
                  title="Reset Graph"
                  aria-label="Reset"
                >
                  <RotateCcw className="w-3 h-3 mr-1" />
                  Reset
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Layout Controls */}
        <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="text-xs font-medium text-gray-700 mb-3">Layout</div>
            <div className="space-y-2">
              {onTogglePhysics && (
                <Button
                  variant={isPhysicsEnabled ? "default" : "outline"}
                  size="sm"
                  onClick={onTogglePhysics}
                  className="w-full h-8 text-xs justify-start"
                  title={isPhysicsEnabled ? "Disable Physics" : "Enable Physics"}
                >
                  {isPhysicsEnabled ? (
                    <Pause className="w-3 h-3 mr-2" />
                  ) : (
                    <Play className="w-3 h-3 mr-2" />
                  )}
                  Physics {isPhysicsEnabled ? 'On' : 'Off'}
                </Button>
              )}
              
              {onToggleLayout && (
                <Button
                  variant={isHierarchicalLayout ? "default" : "outline"}
                  size="sm"
                  onClick={onToggleLayout}
                  className="w-full h-8 text-xs justify-start"
                  title="Toggle Hierarchical Layout"
                >
                  {isHierarchicalLayout ? (
                    <Grid3X3 className="w-3 h-3 mr-2" />
                  ) : (
                    <Network className="w-3 h-3 mr-2" />
                  )}
                  {isHierarchicalLayout ? 'Hierarchical' : 'Force Layout'}
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Export and Settings */}
        <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="text-xs font-medium text-gray-700 mb-3">Actions</div>
            <div className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportImage}
                className="w-full h-8 text-xs justify-start"
                title="Export Graph as Image (PNG)"
              >
                <Download className="w-3 h-3 mr-2" />
                Export Image
              </Button>
              
              {onSettings && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={onSettings}
                  className="w-full h-8 text-xs justify-start"
                  title="Graph Settings"
                >
                  <Settings className="w-3 h-3 mr-2" />
                  Settings
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Quick Actions */}
        <Card className="border-0 shadow-sm bg-white/95 backdrop-blur-sm">
          <CardContent className="p-3">
            <div className="flex items-center space-x-1 mb-3">
              <span className="text-xs font-medium text-gray-700">Quick Actions</span>
              <Tooltip>
                <TooltipTrigger asChild>
                  <HelpCircle className="w-3 h-3 text-gray-400 cursor-help" />
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">Shortcuts for common graph operations</p>
                </TooltipContent>
              </Tooltip>
            </div>
            <div className="grid grid-cols-1 gap-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs justify-start text-gray-600 hover:text-gray-900"
                    onClick={handleFocusHighRisk}
                  >
                    <Target className="w-3 h-3 mr-2 text-red-500" />
                    Focus High-Risk
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">Highlight and focus on high-risk nodes (score ≥ 0.6)</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs justify-start text-gray-600 hover:text-gray-900"
                    onClick={handleShowAttackPaths}
                  >
                    <Zap className="w-3 h-3 mr-2 text-orange-500" />
                    Show Attack Paths
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">Highlight privilege escalation paths in the graph</p>
                </TooltipContent>
              </Tooltip>

              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 text-xs justify-start text-gray-600 hover:text-gray-900"
                    onClick={handleCenterOrganization}
                  >
                    <Building className="w-3 h-3 mr-2 text-purple-500" />
                    Center Organization
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p className="text-xs">Center the view on the organization root node</p>
                </TooltipContent>
              </Tooltip>
            </div>
          </CardContent>
        </Card>
      </div>
    </TooltipProvider>
  );
} 