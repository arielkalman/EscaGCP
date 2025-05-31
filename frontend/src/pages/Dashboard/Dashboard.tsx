import React, { useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { dataService } from '../../services/dataService';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';
import { GhostUsersToggle } from '../../components/common/GhostUsersToggle';
import { StatisticsHeader } from '../../components/dashboard/StatisticsHeader';
import { DashboardCharts } from '../../components/dashboard/DashboardCharts';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { Badge } from '../../components/ui/badge';
import { 
  ArrowRight, 
  Eye, 
  AlertTriangle, 
  Shield, 
  Activity,
  Clock,
  CheckCircle,
  XCircle,
  Info
} from 'lucide-react';
import { useAppSettings } from '../../context/AppSettingsContext';
import { getGhostUserStats } from '../../utils/ghostUsers';

export function Dashboard() {
  const navigate = useNavigate();
  const { settings } = useAppSettings();
  
  const {
    data: analysisData,
    isLoading: isLoadingAnalysis,
    error: analysisError,
  } = useQuery({
    queryKey: ['analysis'],
    queryFn: () => dataService.loadAnalysisData(),
  });

  const {
    data: graphData,
    isLoading: isLoadingGraph,
    error: graphError,
  } = useQuery({
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

  if (isLoadingAnalysis || isLoadingGraph) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <div className="text-center space-y-4">
          <LoadingSpinner size="lg" />
          <div className="space-y-2">
            <h2 className="text-xl font-semibold text-foreground">
              Loading Security Dashboard
            </h2>
            <p className="text-muted-foreground">
              Analyzing your GCP environment...
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (analysisError || graphError) {
    return (
      <div className="flex items-center justify-center h-[calc(100vh-4rem)]">
        <Card className="max-w-md">
          <CardContent className="p-6 text-center space-y-4">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto">
              <XCircle className="h-6 w-6 text-red-600" />
            </div>
            <div className="space-y-2">
              <h2 className="text-xl font-semibold text-foreground">
                Failed to Load Dashboard
              </h2>
              <p className="text-muted-foreground">
                {analysisError?.message || graphError?.message || 'An error occurred while loading the dashboard.'}
              </p>
              <p className="text-red-600 text-sm">
                Error: {analysisError?.message || graphError?.message || 'Failed to load data'}
              </p>
            </div>
            <Button onClick={() => window.location.reload()}>
              Try Again
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 via-blue-50/20 to-purple-50/20">
      <div className="p-6 space-y-8 max-w-7xl mx-auto">
        {/* Header with Ghost Users Toggle */}
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="flex items-center space-x-3">
              <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
              {ghostUserStats.totalGhostNodes > 0 && !settings.showGhostUsers && (
                <Badge variant="secondary" className="text-xs">
                  {ghostUserStats.totalGhostNodes} ghost users hidden
                </Badge>
              )}
            </div>
            <p className="text-muted-foreground">
              Comprehensive overview of your GCP security posture
            </p>
          </div>
          
          {/* Ghost Users Toggle */}
          <GhostUsersToggle 
            ghostUserStats={ghostUserStats}
            size="md"
            showLabel={true}
            showStats={true}
          />
        </div>

        {/* Statistics Header */}
        {analysisData && (
          <StatisticsHeader statistics={analysisData.statistics} />
        )}

        {/* Main Content Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Charts Section - Takes up 2 columns */}
          <div className="xl:col-span-2 space-y-6">
            {/* Charts */}
            {analysisData && (
              <DashboardCharts analysisData={analysisData} />
            )}
          </div>

          {/* Sidebar - Takes up 1 column */}
          <div className="xl:col-span-1 space-y-6">
            {/* Quick Actions */}
            <Card className="border-0 shadow-md">
              <CardHeader>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <Activity className="h-5 w-5 text-purple-600" />
                  </div>
                  <span>Quick Actions</span>
                </CardTitle>
                <CardDescription>
                  Common security operations and views
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  variant="outline" 
                  className="w-full justify-between group"
                  onClick={() => navigate('/graph')}
                >
                  <span className="flex items-center space-x-2">
                    <Eye className="h-4 w-4" />
                    <span>View Full Graph</span>
                  </span>
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
                
                <Button 
                  variant="outline" 
                  className="w-full justify-between group"
                  onClick={() => navigate('/findings')}
                >
                  <span className="flex items-center space-x-2">
                    <AlertTriangle className="h-4 w-4" />
                    <span>Security Findings</span>
                  </span>
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
                
                <Button 
                  variant="outline" 
                  className="w-full justify-between group"
                  onClick={() => navigate('/findings')}
                >
                  <span className="flex items-center space-x-2">
                    <Shield className="h-4 w-4" />
                    <span>Risk Assessment</span>
                  </span>
                  <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
                </Button>
              </CardContent>
            </Card>

            {/* Environment Overview */}
            <Card className="border-0 shadow-md">
              <CardHeader>
                <CardTitle className="text-lg">Environment Overview</CardTitle>
                <CardDescription>
                  Your GCP infrastructure at a glance
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="space-y-1">
                    <p className="text-muted-foreground">Projects</p>
                    <p className="text-2xl font-bold text-foreground">
                      {graphData?.metadata.gcp_projects.length || 0}
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-muted-foreground">Last Scan</p>
                    <p className="font-medium text-foreground">
                      {graphData?.metadata.collection_time 
                        ? new Date(graphData.metadata.collection_time).toLocaleDateString()
                        : 'N/A'
                      }
                    </p>
                  </div>
                </div>
                
                {/* Project List */}
                <div className="space-y-2">
                  <p className="text-sm font-medium text-muted-foreground">Recent Projects</p>
                  <div className="space-y-2 max-h-32 overflow-y-auto">
                    {graphData?.metadata.gcp_projects.slice(0, 3).map((project, index) => (
                      <div key={index} className="flex items-center justify-between p-2 bg-muted/50 rounded-lg">
                        <span className="text-sm font-medium truncate">{project}</span>
                        <Badge variant="outline" className="text-xs">Active</Badge>
                      </div>
                    ))}
                    {(graphData?.metadata.gcp_projects.length || 0) > 3 && (
                      <p className="text-xs text-muted-foreground text-center">
                        +{(graphData?.metadata.gcp_projects.length || 0) - 3} more projects
                      </p>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Ghost Users Summary */}
            {ghostUserStats.totalGhostNodes > 0 && (
              <Card className="border-0 shadow-md border-l-4 border-l-gray-400">
                <CardHeader>
                  <CardTitle className="text-lg flex items-center space-x-2">
                    <div className="p-2 bg-gray-100 rounded-lg">
                      <Info className="h-5 w-5 text-gray-600" />
                    </div>
                    <span>Ghost Users Detected</span>
                  </CardTitle>
                  <CardDescription>
                    Inactive or deleted user accounts that may pose security risks
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div className="space-y-1">
                        <p className="text-muted-foreground">Ghost Users</p>
                        <p className="text-xl font-bold text-foreground">
                          {ghostUserStats.ghostUsers}
                        </p>
                      </div>
                      <div className="space-y-1">
                        <p className="text-muted-foreground">Ghost SAs</p>
                        <p className="text-xl font-bold text-foreground">
                          {ghostUserStats.ghostServiceAccounts}
                        </p>
                      </div>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {settings.showGhostUsers 
                        ? "Ghost users are currently visible in all views"
                        : "Ghost users are hidden. Use the toggle above to show them."
                      }
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Critical Findings */}
            <Card className="border-0 shadow-md">
              <CardHeader>
                <CardTitle className="text-lg flex items-center space-x-2">
                  <div className="p-2 bg-red-100 rounded-lg">
                    <AlertTriangle className="h-5 w-5 text-red-600" />
                  </div>
                  <span>Critical Findings</span>
                </CardTitle>
                <CardDescription>
                  High-priority security issues requiring immediate attention
                </CardDescription>
              </CardHeader>
              <CardContent>
                {analysisData?.attack_paths.critical.length ? (
                  <div className="space-y-3">
                    {analysisData.attack_paths.critical.slice(0, 3).map((path, index) => (
                      <div key={index} className="group p-3 border border-red-200 bg-red-50/50 rounded-lg hover:bg-red-50 transition-colors cursor-pointer">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Badge variant="destructive" className="text-xs">
                              Critical
                            </Badge>
                            <span className="text-xs text-muted-foreground">
                              Risk: {Math.round(path.risk_score * 100)}%
                            </span>
                          </div>
                          <p className="text-sm font-medium text-red-900 line-clamp-2">
                            {path.description}
                          </p>
                          <div className="flex items-center text-xs text-red-700">
                            <Clock className="h-3 w-3 mr-1" />
                            <span>Detected recently</span>
                          </div>
                        </div>
                      </div>
                    ))}
                    
                    {analysisData.attack_paths.critical.length > 3 && (
                      <Button 
                        variant="outline" 
                        className="w-full"
                        onClick={() => navigate('/findings')}
                      >
                        View {analysisData.attack_paths.critical.length - 3} More Critical Findings
                      </Button>
                    )}
                  </div>
                ) : (
                  <div className="text-center py-8 space-y-3">
                    <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                      <CheckCircle className="h-6 w-6 text-green-600" />
                    </div>
                    <div className="space-y-1">
                      <p className="font-medium text-foreground">No Critical Findings</p>
                      <p className="text-sm text-muted-foreground">
                        Your environment shows a strong security posture
                      </p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {/* System Status */}
            <Card className="border-0 shadow-md">
              <CardHeader>
                <CardTitle className="text-lg">System Status</CardTitle>
                <CardDescription>
                  Current status of security monitoring components
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {[
                    { name: 'Data Collection', status: 'operational', icon: CheckCircle, color: 'text-green-600' },
                    { name: 'Analysis Engine', status: 'operational', icon: CheckCircle, color: 'text-green-600' },
                    { name: 'Real-time Monitoring', status: 'maintenance', icon: Info, color: 'text-blue-600' },
                  ].map((service, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <div className="flex items-center space-x-3">
                        <service.icon className={`h-5 w-5 ${service.color}`} />
                        <span className="text-sm font-medium">{service.name}</span>
                      </div>
                      <Badge 
                        variant={service.status === 'operational' ? 'success' : 'default'}
                        className="text-xs"
                      >
                        {service.status === 'operational' ? 'Active' : 'Planned'}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-6">
          <p className="text-sm text-muted-foreground">
            Last updated: {new Date().toLocaleString()} • 
            <span className="ml-1">
              Next scan in 24 hours
            </span>
          </p>
        </div>
      </div>
    </div>
  );
} 