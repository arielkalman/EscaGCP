import { Network, Zap, Eye, Tag, Layers, RotateCcw } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Switch } from '../ui/switch';
import { Input } from '../ui/input';
import { Separator } from '../ui/separator';
import { Button } from '../ui/button';
import { useSettings, type GraphLayout } from '../../context/SettingsContext';

export function GraphSettings() {
  const {
    state,
    setGraphLayout,
    togglePhysics,
    setNodeSize,
    setEdgeThickness,
    setMaxNodes,
    toggleLabels,
    toggleTooltips,
    resetToDefaults
  } = useSettings();

  const handleLayoutChange = (value: string) => {
    setGraphLayout(value as GraphLayout);
  };

  return (
    <div className="space-y-6">
      {/* Layout Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Network className="h-5 w-5" />
            <span>Graph Layout</span>
          </CardTitle>
          <CardDescription>
            Configure how the network graph is displayed and organized
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label className="text-sm font-medium">Layout Algorithm</Label>
            <RadioGroup
              value={state.graphLayout}
              onValueChange={handleLayoutChange}
              className="grid grid-cols-1 gap-3"
            >
              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="hierarchical" id="hierarchical" />
                <div className="flex-1">
                  <Label htmlFor="hierarchical" className="font-medium cursor-pointer">
                    Hierarchical
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Organizes nodes in a tree-like structure based on relationships
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="force-directed" id="force-directed" />
                <div className="flex-1">
                  <Label htmlFor="force-directed" className="font-medium cursor-pointer">
                    Force-Directed
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Uses physics simulation to position nodes naturally
                  </p>
                </div>
              </div>

              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="circular" id="circular" />
                <div className="flex-1">
                  <Label htmlFor="circular" className="font-medium cursor-pointer">
                    Circular
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Arranges nodes in a circular pattern for better overview
                  </p>
                </div>
              </div>
            </RadioGroup>
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="enable-physics" className="font-medium flex items-center space-x-2">
                <Zap className="h-4 w-4" />
                <span>Enable Physics</span>
              </Label>
              <p className="text-sm text-muted-foreground">
                Allow nodes to move and settle naturally
              </p>
            </div>
            <Switch 
              id="enable-physics"
              checked={state.enablePhysics}
              onCheckedChange={togglePhysics}
            />
          </div>
        </CardContent>
      </Card>

      {/* Visual Settings */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Eye className="h-5 w-5" />
            <span>Visual Appearance</span>
          </CardTitle>
          <CardDescription>
            Customize the look and feel of graph elements
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-2">
              <Label htmlFor="node-size" className="text-sm font-medium">
                Node Size
              </Label>
              <div className="flex items-center space-x-3">
                <Input
                  id="node-size"
                  type="number"
                  min="10"
                  max="100"
                  value={state.nodeSize}
                  onChange={(e) => setNodeSize(parseInt(e.target.value))}
                  className="w-20"
                />
                <span className="text-sm text-muted-foreground">pixels</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Size of network nodes (10-100 pixels)
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="edge-thickness" className="text-sm font-medium">
                Edge Thickness
              </Label>
              <div className="flex items-center space-x-3">
                <Input
                  id="edge-thickness"
                  type="number"
                  min="1"
                  max="10"
                  value={state.edgeThickness}
                  onChange={(e) => setEdgeThickness(parseInt(e.target.value))}
                  className="w-20"
                />
                <span className="text-sm text-muted-foreground">pixels</span>
              </div>
              <p className="text-xs text-muted-foreground">
                Thickness of connecting lines (1-10 pixels)
              </p>
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="max-nodes" className="text-sm font-medium">
              Maximum Nodes
            </Label>
            <div className="flex items-center space-x-3">
              <Input
                id="max-nodes"
                type="number"
                min="100"
                max="10000"
                step="100"
                value={state.maxNodes}
                onChange={(e) => setMaxNodes(parseInt(e.target.value))}
                className="w-32"
              />
              <span className="text-sm text-muted-foreground">nodes</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Maximum number of nodes to display for performance (100-10,000)
            </p>
          </div>

          <Separator />

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="show-labels" className="font-medium flex items-center space-x-2">
                  <Tag className="h-4 w-4" />
                  <span>Show Labels</span>
                </Label>
                <p className="text-sm text-muted-foreground">
                  Display node names and identifiers
                </p>
              </div>
              <Switch 
                id="show-labels"
                checked={state.showLabels}
                onCheckedChange={toggleLabels}
              />
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label htmlFor="enable-tooltips" className="font-medium flex items-center space-x-2">
                  <Layers className="h-4 w-4" />
                  <span>Enable Tooltips</span>
                </Label>
                <p className="text-sm text-muted-foreground">
                  Show detailed information on hover
                </p>
              </div>
              <Switch 
                id="enable-tooltips"
                checked={state.enableTooltips}
                onCheckedChange={toggleTooltips}
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Performance Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Performance</CardTitle>
          <CardDescription>
            Settings to optimize graph rendering and responsiveness
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-800 rounded-lg">
            <div className="flex items-start space-x-3">
              <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400 mt-0.5" />
              <div>
                <h4 className="font-medium text-blue-900 dark:text-blue-100">
                  Performance Tips
                </h4>
                <ul className="text-sm text-blue-800 dark:text-blue-200 mt-1 space-y-1">
                  <li>• Reduce max nodes for large datasets</li>
                  <li>• Disable physics for better performance</li>
                  <li>• Hide labels when viewing many nodes</li>
                </ul>
              </div>
            </div>
          </div>

          <div className="text-xs text-muted-foreground">
            <strong>Current settings impact:</strong> With {state.maxNodes.toLocaleString()} max nodes, 
            {state.enablePhysics ? ' physics enabled' : ' physics disabled'}, and 
            {state.showLabels ? ' labels shown' : ' labels hidden'}, 
            performance should be {state.maxNodes > 5000 || (state.enablePhysics && state.maxNodes > 1000) ? 'moderate' : 'good'}.
          </div>
        </CardContent>
      </Card>

      {/* Reset Settings */}
      <Card>
        <CardHeader>
          <CardTitle>Reset</CardTitle>
          <CardDescription>
            Restore default graph settings
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <p className="font-medium">Reset to Defaults</p>
              <p className="text-sm text-muted-foreground">
                This will restore all graph settings to their original values
              </p>
            </div>
            <Button 
              variant="outline" 
              size="sm"
              onClick={resetToDefaults}
              className="flex items-center space-x-2"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Reset</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 