import { Settings as SettingsIcon, Palette, Network, Download, Database, Eye, EyeOff } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Switch } from '../../components/ui/switch';
import { Badge } from '../../components/ui/badge';
import { ThemeSettings, GraphSettings, ExportSettings } from '../../components/settings';
import { useAppSettings } from '../../context/AppSettingsContext';
import { GhostUsersToggle } from '../../components/common/GhostUsersToggle';
import { useQuery } from '@tanstack/react-query';
import { dataService } from '../../services/dataService';
import { getGhostUserStats } from '../../utils/ghostUsers';
import { useMemo } from 'react';

export function Settings() {
  const { settings, updateSetting } = useAppSettings();

  // Load graph data for ghost user stats
  const { data: graphData } = useQuery({
    queryKey: ['graph'],
    queryFn: () => dataService.loadGraphData(),
  });

  // Calculate ghost user statistics
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

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center space-x-3 mb-6">
        <SettingsIcon className="h-8 w-8 text-primary" />
        <div>
          <h1 className="text-3xl font-bold text-foreground">Settings</h1>
          <p className="text-muted-foreground">Configure your EscaGCP dashboard preferences</p>
        </div>
      </div>

      <Tabs defaultValue="theme" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 max-w-lg">
          <TabsTrigger value="theme" className="flex items-center space-x-2">
            <Palette className="h-4 w-4" />
            <span className="hidden sm:inline">Theme</span>
          </TabsTrigger>
          <TabsTrigger value="data" className="flex items-center space-x-2">
            <Database className="h-4 w-4" />
            <span className="hidden sm:inline">Data</span>
          </TabsTrigger>
          <TabsTrigger value="graph" className="flex items-center space-x-2">
            <Network className="h-4 w-4" />
            <span className="hidden sm:inline">Graph</span>
          </TabsTrigger>
          <TabsTrigger value="export" className="flex items-center space-x-2">
            <Download className="h-4 w-4" />
            <span className="hidden sm:inline">Export</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="theme" className="space-y-6">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">Theme & Appearance</h2>
            <p className="text-muted-foreground">
              Customize the visual appearance and theme of your dashboard
            </p>
          </div>
          <ThemeSettings />
        </TabsContent>

        <TabsContent value="data" className="space-y-6">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">Data Filtering</h2>
            <p className="text-muted-foreground">
              Configure how data is filtered and displayed across all views
            </p>
          </div>
          
          {/* Ghost Users Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <div className="p-2 bg-gray-100 rounded-lg">
                  <Eye className="h-5 w-5 text-gray-600" />
                </div>
                <span>Ghost Users</span>
              </CardTitle>
              <CardDescription>
                Control the visibility of deleted or inactive user accounts and service accounts
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Main Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <div className="flex items-center space-x-2">
                    <h3 className="font-medium">Show Ghost Users</h3>
                    <Badge variant={settings.showGhostUsers ? "default" : "secondary"}>
                      {settings.showGhostUsers ? "Visible" : "Hidden"}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground mt-1">
                    Include deleted or inactive accounts in all views and analysis
                  </p>
                </div>
                <Switch
                  checked={settings.showGhostUsers}
                  onCheckedChange={(checked) => updateSetting('showGhostUsers', checked)}
                />
              </div>

              {/* Statistics */}
              {ghostUserStats.totalGhostNodes > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">
                      {ghostUserStats.totalGhostNodes}
                    </div>
                    <div className="text-sm text-muted-foreground">Total Ghost Users</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">
                      {ghostUserStats.ghostUsers}
                    </div>
                    <div className="text-sm text-muted-foreground">Ghost User Accounts</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-foreground">
                      {ghostUserStats.ghostServiceAccounts}
                    </div>
                    <div className="text-sm text-muted-foreground">Ghost Service Accounts</div>
                  </div>
                </div>
              )}

              {/* Information */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="flex items-start space-x-3">
                  <div className="p-1 bg-blue-100 rounded">
                    <Database className="h-4 w-4 text-blue-600" />
                  </div>
                  <div>
                    <h4 className="font-medium text-blue-900">What are Ghost Users?</h4>
                    <div className="text-sm text-blue-800 mt-1 space-y-1">
                      <p>Ghost users are accounts that have been deleted or marked as inactive but may still have residual permissions or relationships in your GCP environment.</p>
                      <p>These typically include:</p>
                      <ul className="list-disc list-inside mt-2 space-y-1">
                        <li>User accounts with "deleted:" prefix in their ID or name</li>
                        <li>Service accounts marked as deleted or disabled</li>
                        <li>Accounts with state = "DELETED" in their properties</li>
                      </ul>
                    </div>
                  </div>
                </div>
              </div>

              {/* Impact Information */}
              <div className={`p-4 rounded-lg border ${
                settings.showGhostUsers 
                  ? 'bg-yellow-50 border-yellow-200' 
                  : 'bg-green-50 border-green-200'
              }`}>
                <div className="flex items-start space-x-3">
                  <div className={`p-1 rounded ${
                    settings.showGhostUsers 
                      ? 'bg-yellow-100' 
                      : 'bg-green-100'
                  }`}>
                    {settings.showGhostUsers ? (
                      <EyeOff className="h-4 w-4 text-yellow-600" />
                    ) : (
                      <Eye className="h-4 w-4 text-green-600" />
                    )}
                  </div>
                  <div>
                    <h4 className={`font-medium ${
                      settings.showGhostUsers 
                        ? 'text-yellow-900' 
                        : 'text-green-900'
                    }`}>
                      Current Impact
                    </h4>
                    <p className={`text-sm mt-1 ${
                      settings.showGhostUsers 
                        ? 'text-yellow-800' 
                        : 'text-green-800'
                    }`}>
                      {settings.showGhostUsers ? (
                        <>
                          Ghost users are currently <strong>visible</strong> in all views. This provides complete transparency but may include less actionable security findings since ghost users pose lower immediate risk.
                        </>
                      ) : (
                        <>
                          Ghost users are currently <strong>hidden</strong> from all views. This focuses your attention on active security threats and live accounts that require immediate attention.
                        </>
                      )}
                    </p>
                  </div>
                </div>
              </div>

              {/* Quick Toggle Component */}
              <div className="pt-4 border-t">
                <div className="flex items-center justify-between">
                  <div>
                    <h4 className="font-medium">Quick Toggle</h4>
                    <p className="text-sm text-muted-foreground">
                      Use this component across the application to quickly toggle ghost user visibility
                    </p>
                  </div>
                  <GhostUsersToggle 
                    ghostUserStats={ghostUserStats}
                    size="md"
                    showLabel={true}
                    showStats={true}
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Auto Refresh Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Auto Refresh</CardTitle>
              <CardDescription>
                Automatically refresh data and analysis at regular intervals
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-medium">Enable Auto Refresh</h3>
                  <p className="text-sm text-muted-foreground">
                    Automatically refresh dashboard data every {settings.refreshInterval} minutes
                  </p>
                </div>
                <Switch
                  checked={settings.autoRefresh}
                  onCheckedChange={(checked) => updateSetting('autoRefresh', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="graph" className="space-y-6">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">Graph Visualization</h2>
            <p className="text-muted-foreground">
              Configure how the network graph is displayed and behaves
            </p>
          </div>
          <GraphSettings />
        </TabsContent>

        <TabsContent value="export" className="space-y-6">
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">Export & Data</h2>
            <p className="text-muted-foreground">
              Manage data export preferences and refresh settings
            </p>
          </div>
          <ExportSettings />
        </TabsContent>
      </Tabs>
    </div>
  );
} 