import React from 'react';
import { 
  Network, 
  GitBranch, 
  Shield, 
  AlertTriangle, 
  Users,
  Activity,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react';
import { Statistics } from '../../types';
import { formatNumber } from '../../lib/utils';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';

interface StatisticsHeaderProps {
  statistics: Statistics;
}

interface MetricConfig {
  key: keyof Statistics;
  title: string;
  icon: React.ComponentType<any>;
  color: string;
  bgColor: string;
  description: string;
  trend?: 'up' | 'down' | 'stable';
  trendValue?: number;
  formatValue?: (value: number) => string;
}

export function StatisticsHeader({ statistics }: StatisticsHeaderProps) {
  const metrics: MetricConfig[] = [
    {
      key: 'total_nodes',
      title: 'Total Nodes',
      icon: Network,
      color: 'text-blue-600',
      bgColor: 'bg-gradient-to-br from-blue-50 to-blue-100',
      description: 'All entities in your GCP environment',
      trend: 'up',
      trendValue: 5.2,
    },
    {
      key: 'total_edges',
      title: 'Total Edges', 
      icon: GitBranch,
      color: 'text-emerald-700',
      bgColor: 'bg-gradient-to-br from-emerald-50 to-emerald-100',
      description: 'Relationships between entities',
      trend: 'up',
      trendValue: 3.1,
    },
    {
      key: 'attack_paths',
      title: 'Attack Paths',
      icon: Activity,
      color: statistics.attack_paths > 0 ? 'text-red-600' : 'text-emerald-700',
      bgColor: statistics.attack_paths > 0 ? 'bg-gradient-to-br from-red-50 to-red-100' : 'bg-gradient-to-br from-emerald-50 to-emerald-100',
      description: 'Potential privilege escalation paths',
      trend: statistics.attack_paths > 10 ? 'up' : 'down',
      trendValue: 12.3,
    },
    {
      key: 'high_risk_nodes',
      title: 'High Risk Nodes',
      icon: AlertTriangle,
      color: statistics.high_risk_nodes > 0 ? 'text-orange-600' : 'text-emerald-700',
      bgColor: statistics.high_risk_nodes > 0 ? 'bg-gradient-to-br from-orange-50 to-orange-100' : 'bg-gradient-to-br from-emerald-50 to-emerald-100',
      description: 'Nodes with elevated risk scores',
      trend: 'down',
      trendValue: 2.1,
    },
    {
      key: 'dangerous_roles',
      title: 'Dangerous Roles',
      icon: Shield,
      color: statistics.dangerous_roles > 0 ? 'text-red-600' : 'text-emerald-700',
      bgColor: statistics.dangerous_roles > 0 ? 'bg-gradient-to-br from-red-50 to-red-100' : 'bg-gradient-to-br from-emerald-50 to-emerald-100',
      description: 'High-privilege roles in use',
      trend: 'stable',
      trendValue: 0,
    },
    {
      key: 'critical_nodes',
      title: 'Critical Nodes',
      icon: Users,
      color: statistics.critical_nodes > 0 ? 'text-purple-600' : 'text-emerald-700',
      bgColor: statistics.critical_nodes > 0 ? 'bg-gradient-to-br from-purple-50 to-purple-100' : 'bg-gradient-to-br from-emerald-50 to-emerald-100',
      description: 'Critical security nodes detected',
      trend: 'down',
      trendValue: 8.5,
    }
  ];

  const getTrendIcon = (trend?: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="h-3 w-3" />;
      case 'down':
        return <TrendingDown className="h-3 w-3" />;
      default:
        return <Minus className="h-3 w-3" />;
    }
  };

  const getTrendColor = (trend?: string) => {
    switch (trend) {
      case 'up':
        return 'text-red-600';
      case 'down':
        return 'text-emerald-700';
      default:
        return 'text-gray-600';
    }
  };

  const getRiskBadgeVariant = (value: number, key: string) => {
    if (key === 'attack_paths' || key === 'dangerous_roles') {
      if (value > 10) return 'destructive';
      if (value > 0) return 'warning';
      return 'success';
    }
    if (key === 'high_risk_nodes' || key === 'critical_nodes') {
      if (value > 5) return 'destructive';
      if (value > 0) return 'warning';
      return 'success';
    }
    return 'default';
  };

  return (
    <div className="space-y-6">
      {/* Main Header */}
      <div className="text-center space-y-2">
        <h1 className="text-4xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
          Security Dashboard
        </h1>
        <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
          Comprehensive overview of your GCP security posture and potential attack vectors
        </p>
      </div>

      {/* Statistics Grid */}
      <div 
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4"
        data-testid="statistics-cards"
      >
        {metrics.map((metric) => {
          const Icon = metric.icon;
          const value = statistics[metric.key] as number;
          const testIdKey = metric.key.replace(/_/g, '-');
          
          return (
            <Card 
              key={metric.key}
              className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 border-0 shadow-md"
              data-testid={`stat-card-${testIdKey}`}
            >
              <button
                className="w-full h-full text-left focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 rounded-lg"
                aria-label={`${metric.title}: ${formatNumber(value)}. ${metric.description}`}
                onClick={() => {
                  console.log(`Clicked metric: ${metric.title}`);
                  // Navigate to appropriate page based on metric
                  if (metric.key === 'total_nodes') {
                    window.location.href = '/nodes';
                  } else if (metric.key === 'total_edges') {
                    window.location.href = '/edges';
                  } else if (metric.key === 'attack_paths' || metric.key === 'high_risk_nodes') {
                    window.location.href = '/findings';
                  }
                }}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    console.log(`Selected metric: ${metric.title}`);
                  }
                }}
              >
                <CardContent className="p-6">
                  <div className="space-y-4">
                    {/* Header with Icon and Badge */}
                    <div className="flex items-center justify-between">
                      <div className={`p-3 rounded-xl ${metric.bgColor} shadow-sm group-hover:scale-110 transition-transform duration-300`}>
                        <Icon className={`h-6 w-6 ${metric.color}`} />
                      </div>
                      <Badge variant={getRiskBadgeVariant(value, metric.key)}>
                        {metric.key === 'attack_paths' && value === 0 ? 'Secure' : 
                         metric.key === 'dangerous_roles' && value === 0 ? 'Good' :
                         value > 10 ? 'High' : 
                         value > 0 ? 'Medium' : 'Low'}
                      </Badge>
                    </div>

                    {/* Main Metric */}
                    <div className="space-y-1">
                      <p className="text-sm font-medium text-muted-foreground">
                        {metric.title}
                      </p>
                      <p 
                        className="text-3xl font-bold text-foreground group-hover:scale-105 transition-transform duration-300"
                        data-testid={`stat-value-${testIdKey}`}
                      >
                        {formatNumber(value)}
                      </p>
                    </div>

                    {/* Trend Indicator */}
                    <div className="flex items-center justify-between">
                      <div className={`flex items-center space-x-1 text-xs ${getTrendColor(metric.trend)}`}>
                        {getTrendIcon(metric.trend)}
                        <span className="font-medium">
                          {metric.trendValue?.toFixed(1)}%
                        </span>
                      </div>
                      <span className="text-xs text-muted-foreground">vs last scan</span>
                    </div>

                    {/* Description */}
                    <p className="text-xs text-muted-foreground leading-relaxed">
                      {metric.description}
                    </p>
                  </div>
                </CardContent>
              </button>
            </Card>
          );
        })}
      </div>

      {/* Summary Banner */}
      <Card className="border-l-4 border-l-purple-500 bg-gradient-to-r from-purple-50/50 to-blue-50/50">
        <CardContent className="p-6">
          <div className="flex items-center justify-between">
            <div className="space-y-1">
              <h3 className="text-lg font-semibold text-foreground">Security Posture Summary</h3>
              <p className="text-sm text-muted-foreground">
                {statistics.attack_paths === 0 
                  ? "Your environment shows a strong security posture with no critical attack paths detected."
                  : `${statistics.attack_paths} potential attack paths require attention. Focus on high-risk nodes and dangerous role assignments.`
                }
              </p>
            </div>
            <div className="flex items-center space-x-2">
              <Badge 
                variant={statistics.attack_paths === 0 ? "success" : statistics.attack_paths > 10 ? "destructive" : "warning"}
                className="text-sm px-3 py-1"
              >
                {statistics.attack_paths === 0 ? "Secure" : statistics.attack_paths > 10 ? "High Risk" : "Medium Risk"}
              </Badge>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 