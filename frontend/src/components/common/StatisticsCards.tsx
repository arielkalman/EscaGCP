import React from 'react';
import { 
  Network, 
  GitBranch, 
  Shield, 
  AlertTriangle, 
  Users,
  Activity
} from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Statistics } from '../../types';
import { formatNumber } from '../../lib/utils';

interface StatisticsCardsProps {
  statistics: Statistics;
}

export function StatisticsCards({ statistics }: StatisticsCardsProps) {
  const cards = [
    {
      title: 'Total Nodes',
      value: statistics.total_nodes,
      icon: Network,
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      description: 'All entities in your GCP environment',
      testId: 'stat-card-total-nodes'
    },
    {
      title: 'Total Edges',
      value: statistics.total_edges,
      icon: GitBranch,
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      description: 'Relationships between entities',
      testId: 'stat-card-total-edges'
    },
    {
      title: 'Attack Paths',
      value: statistics.attack_paths,
      icon: Activity,
      color: statistics.attack_paths > 0 ? 'text-red-600' : 'text-green-600',
      bgColor: statistics.attack_paths > 0 ? 'bg-red-50' : 'bg-green-50',
      description: 'Potential privilege escalation paths',
      testId: 'stat-card-attack-paths'
    },
    {
      title: 'High Risk Nodes',
      value: statistics.high_risk_nodes,
      icon: AlertTriangle,
      color: statistics.high_risk_nodes > 0 ? 'text-orange-600' : 'text-green-600',
      bgColor: statistics.high_risk_nodes > 0 ? 'bg-orange-50' : 'bg-green-50',
      description: 'Nodes with elevated risk scores',
      testId: 'stat-card-high-risk-nodes'
    },
    {
      title: 'Dangerous Roles',
      value: statistics.dangerous_roles,
      icon: Shield,
      color: statistics.dangerous_roles > 0 ? 'text-red-600' : 'text-green-600',
      bgColor: statistics.dangerous_roles > 0 ? 'bg-red-50' : 'bg-green-50',
      description: 'High-privilege roles in use',
      testId: 'stat-card-dangerous-roles'
    },
    {
      title: 'Vulnerabilities',
      value: statistics.vulnerabilities,
      icon: Users,
      color: statistics.vulnerabilities > 0 ? 'text-red-600' : 'text-green-600',
      bgColor: statistics.vulnerabilities > 0 ? 'bg-red-50' : 'bg-green-50',
      description: 'Security vulnerabilities detected',
      testId: 'stat-card-vulnerabilities'
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
      {cards.map((card) => {
        const Icon = card.icon;
        
        return (
          <Card
            key={card.title}
            data-testid="stat-card"
            data-testid-specific={card.testId}
            className="rounded-lg bg-card text-card-foreground group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 border-0 shadow-md"
            tabIndex={0}
            role="button"
            aria-label={`${card.title}: ${formatNumber(card.value)} - ${card.description}`}
          >
            <CardContent className="p-4">
              <div className="flex items-center">
                <div className={`p-2 rounded-lg ${card.bgColor}`}>
                  <Icon className={`h-5 w-5 ${card.color}`} />
                </div>
                <div className="ml-3 flex-1">
                  <p className="text-sm font-medium text-muted-foreground">
                    {card.title}
                  </p>
                  <p className="text-2xl font-bold text-foreground">
                    {formatNumber(card.value)}
                  </p>
                </div>
              </div>
              <p className="mt-2 text-xs text-muted-foreground">
                {card.description}
              </p>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
} 