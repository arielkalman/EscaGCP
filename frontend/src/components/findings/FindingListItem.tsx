import React from 'react';
import { AttackPath, getRiskLevel } from '../../types';
import { Badge } from '../ui/badge';
import { Button } from '../ui/button';
import { Card, CardContent } from '../ui/card';
import { 
  Eye, 
  Download, 
  AlertTriangle, 
  ArrowRight,
  Clock,
  Shield,
  Target,
  User
} from 'lucide-react';

interface FindingListItemProps {
  attackPath: AttackPath;
  onViewInGraph: (attackPath: AttackPath) => void;
  onExport?: (attackPath: AttackPath) => void;
  className?: string;
}

export function FindingListItem({
  attackPath,
  onViewInGraph,
  onExport,
  className = ""
}: FindingListItemProps) {
  const riskLevel = getRiskLevel(attackPath.risk_score);
  
  const getRiskBadgeColor = (level: string) => {
    switch (level) {
      case 'critical': return 'bg-red-600 text-white border-red-600';
      case 'high': return 'bg-orange-600 text-white border-orange-600';
      case 'medium': return 'bg-yellow-600 text-white border-yellow-600';
      case 'low': return 'bg-blue-600 text-white border-blue-600';
      default: return 'bg-gray-600 text-white border-gray-600';
    }
  };

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'critical':
      case 'critical_multi_step':
        return <AlertTriangle className="h-4 w-4" />;
      case 'privilege_escalation':
        return <Shield className="h-4 w-4" />;
      case 'lateral_movement':
        return <Target className="h-4 w-4" />;
      default:
        return <AlertTriangle className="h-4 w-4" />;
    }
  };

  const formatCategoryName = (category: string) => {
    return category
      .split('_')
      .map(word => word.charAt(0).toUpperCase() + word.slice(1))
      .join(' ');
  };

  const getComplexityBadge = (length: number) => {
    if (length === 1) return { text: 'Direct', color: 'bg-red-100 text-red-800' };
    if (length <= 2) return { text: 'Simple', color: 'bg-orange-100 text-orange-800' };
    if (length <= 3) return { text: 'Moderate', color: 'bg-yellow-100 text-yellow-800' };
    return { text: 'Complex', color: 'bg-blue-100 text-blue-800' };
  };

  const complexity = getComplexityBadge(attackPath.length);

  const getEscalationTechniques = () => {
    const metadata = attackPath.visualization_metadata;
    if (!metadata?.escalation_techniques) return [];
    
    return metadata.escalation_techniques.slice(0, 3); // Show first 3 techniques
  };

  const techniques = getEscalationTechniques();

  return (
    <Card className={`border-l-4 border-l-${riskLevel === 'critical' ? 'red' : riskLevel === 'high' ? 'orange' : riskLevel === 'medium' ? 'yellow' : 'blue'}-500 hover:shadow-md transition-shadow ${className}`}>
      <CardContent className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-3">
            <div className={`p-2 rounded-lg ${riskLevel === 'critical' ? 'bg-red-100' : riskLevel === 'high' ? 'bg-orange-100' : riskLevel === 'medium' ? 'bg-yellow-100' : 'bg-blue-100'}`}>
              {getCategoryIcon(attackPath.category)}
            </div>
            <div>
              <div className="flex items-center space-x-2 mb-1">
                <Badge className={getRiskBadgeColor(riskLevel)}>
                  {riskLevel.toUpperCase()}
                </Badge>
                <Badge variant="outline" className={complexity.color}>
                  {complexity.text}
                </Badge>
                <Badge variant="outline">
                  {formatCategoryName(attackPath.category)}
                </Badge>
              </div>
              <h3 className="font-semibold text-lg text-foreground">
                Attack Path: {attackPath.source.name} → {attackPath.target.name}
              </h3>
            </div>
          </div>
          
          <div className="text-right">
            <div className="text-2xl font-bold text-foreground mb-1">
              {Math.round(attackPath.risk_score * 100)}%
            </div>
            <div className="text-sm text-muted-foreground">Risk Score</div>
          </div>
        </div>

        {/* Description */}
        <p className="text-muted-foreground mb-4 leading-relaxed">
          {attackPath.description}
        </p>

        {/* Path Information */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div className="flex items-center space-x-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="text-sm font-medium">Source</div>
              <div className="text-sm text-muted-foreground truncate">
                {attackPath.source.name}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Target className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="text-sm font-medium">Target</div>
              <div className="text-sm text-muted-foreground truncate">
                {attackPath.target.name}
              </div>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            <Clock className="h-4 w-4 text-muted-foreground" />
            <div>
              <div className="text-sm font-medium">Steps</div>
              <div className="text-sm text-muted-foreground">
                {attackPath.length} hop{attackPath.length !== 1 ? 's' : ''}
              </div>
            </div>
          </div>
        </div>

        {/* Attack Path Preview */}
        <div className="bg-muted/50 rounded-lg p-4 mb-4">
          <div className="text-sm font-medium mb-2">Attack Path</div>
          <div className="flex items-center space-x-2 text-sm text-muted-foreground overflow-x-auto">
            {attackPath.path_nodes.map((node, index) => (
              <React.Fragment key={node.id}>
                <span className="whitespace-nowrap font-medium text-foreground">
                  {node.name.length > 20 ? `${node.name.substring(0, 20)}...` : node.name}
                </span>
                {index < attackPath.path_nodes.length - 1 && (
                  <ArrowRight className="h-4 w-4 flex-shrink-0" />
                )}
              </React.Fragment>
            ))}
          </div>
        </div>

        {/* Techniques Used */}
        {techniques.length > 0 && (
          <div className="mb-4">
            <div className="text-sm font-medium mb-2">Attack Techniques</div>
            <div className="flex flex-wrap gap-2">
              {techniques.map((technique, index) => (
                <Badge key={index} variant="outline" className="text-xs">
                  {technique.name}
                </Badge>
              ))}
              {attackPath.visualization_metadata?.escalation_techniques && 
               attackPath.visualization_metadata.escalation_techniques.length > 3 && (
                <Badge variant="outline" className="text-xs">
                  +{attackPath.visualization_metadata.escalation_techniques.length - 3} more
                </Badge>
              )}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-between pt-4 border-t">
          <div className="flex items-center space-x-2">
            <Button
              variant="default"
              size="sm"
              onClick={() => onViewInGraph(attackPath)}
              className="flex items-center space-x-2"
            >
              <Eye className="h-4 w-4" />
              <span>View in Graph</span>
            </Button>
            
            {onExport && (
              <Button
                variant="outline"
                size="sm"
                onClick={() => onExport(attackPath)}
                className="flex items-center space-x-2"
              >
                <Download className="h-4 w-4" />
                <span>Export</span>
              </Button>
            )}
          </div>

          {/* Additional info */}
          <div className="text-xs text-muted-foreground">
            ID: {attackPath.source.id.split(':')[1]?.substring(0, 8)}...
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 