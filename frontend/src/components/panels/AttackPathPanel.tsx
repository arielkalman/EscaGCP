import { 
  MapPin, 
  AlertTriangle, 
  ArrowRight,
  Shield,
  Clock,
  TrendingUp,
  Eye,
  Download,
  PlayCircle
} from 'lucide-react';
import { SidePanelLayout } from '../layout/SidePanelLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { getRiskLevel } from '../../types';
import { useGraphContext } from '../../context/GraphContext';

interface AttackPathPanelProps {
  className?: string;
}

export function AttackPathPanel({ className }: AttackPathPanelProps) {
  const { state, closeAttackPathPanel } = useGraphContext();
  
  const attackPath = state.selectedAttackPath;
  const isOpen = state.isAttackPathPanelOpen && !!attackPath;
  
  const riskLevel = attackPath ? getRiskLevel(attackPath.risk_score) : 'low';

  const handleHighlightPath = () => {
    if (!attackPath) return;
    
    // Close the panel to show the graph
    closeAttackPathPanel();
    
    // Dispatch an event to highlight the attack path in the graph
    const nodeIds = attackPath.path_nodes.map(node => node.id);
    const edgeIds = attackPath.path_edges.map((edge, index) => `edge-${index}`);
    
    window.dispatchEvent(new CustomEvent('highlightAttackPath', {
      detail: { 
        nodeIds, 
        edgeIds,
        attackPath: attackPath
      }
    }));
    
    console.log('Highlighting attack path in graph:', { nodeIds, edgeIds });
  };

  const handleExportPath = () => {
    if (!attackPath) return;
    
    const exportData = {
      attackPath: attackPath,
      exportedAt: new Date().toISOString(),
      summary: {
        sourceNode: attackPath.source?.name,
        targetNode: attackPath.target?.name,
        pathLength: attackPath.length,
        riskScore: attackPath.risk_score,
        category: attackPath.category
      }
    };
    
    const blob = new Blob([JSON.stringify(exportData, null, 2)], {
      type: 'application/json'
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `attack-path-${attackPath.source?.name?.replace(/[^a-zA-Z0-9]/g, '_') || 'path'}-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.log('Exported attack path:', exportData);
  };

  const handleSimulatePath = () => {
    if (!attackPath) return;
    
    // Show an alert with simulation information for now
    const steps = attackPath.path_nodes.map((node, index) => 
      `${index + 1}. ${node.name} (${node.type})`
    ).join('\n');
    
    alert(`Attack Path Simulation:\n\n${steps}\n\nThis would demonstrate how an attacker could move from ${attackPath.source?.name} to ${attackPath.target?.name}.`);
    
    console.log('Simulating attack path:', attackPath);
  };

  const getRiskBadgeVariant = (riskLevel: string) => {
    switch (riskLevel) {
      case 'critical': return 'destructive';
      case 'high': return 'destructive';
      case 'medium': return 'secondary';
      case 'low': return 'outline';
      default: return 'outline';
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category.toLowerCase()) {
      case 'critical': return 'text-red-600 bg-red-50';
      case 'privilege_escalation': return 'text-orange-600 bg-orange-50';
      case 'lateral_movement': return 'text-blue-600 bg-blue-50';
      case 'high': return 'text-red-600 bg-red-50';
      case 'medium': return 'text-yellow-600 bg-yellow-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  return (
    <SidePanelLayout
      isOpen={isOpen}
      onClose={closeAttackPathPanel}
      title="Attack Path Details"
      description="Detailed analysis of the selected attack path"
      width="xl"
      className={className}
    >
      {/* Attack Path Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-3">
            <MapPin className="w-5 h-5 text-red-500" />
            <div className="flex-1">
              <div className="flex items-center space-x-2">
                <span>Attack Path</span>
                <Badge variant={getRiskBadgeVariant(riskLevel)}>
                  {riskLevel.toUpperCase()}
                </Badge>
                <Badge 
                  variant="outline" 
                  className={getCategoryColor(attackPath?.category || 'medium')}
                >
                  {(attackPath?.category || 'unknown').replace(/_/g, ' ').toUpperCase()}
                </Badge>
              </div>
              <p className="text-sm text-gray-600 mt-1">
                {attackPath?.path_nodes?.length || 0} steps • Risk score: {((attackPath?.risk_score || 0) * 100).toFixed(0)}%
              </p>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-gray-600">
                {attackPath?.description || 'No attack path description available'}
              </p>
            </div>

            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <span className="font-medium text-gray-800">Source:</span>
                <div className="mt-1 p-2 bg-gray-50 rounded">
                  <code className="text-xs">{attackPath?.source?.name || 'No source'}</code>
                  <p className="text-xs text-gray-600 mt-1">
                    {attackPath?.source?.type || 'Unknown type'}
                  </p>
                </div>
              </div>
              <div>
                <span className="font-medium text-gray-800">Target:</span>
                <div className="mt-1 p-2 bg-red-50 rounded">
                  <code className="text-xs">{attackPath?.target?.name || 'No target'}</code>
                  <p className="text-xs text-red-600 mt-1">
                    {attackPath?.target?.type || 'Unknown type'}
                  </p>
                </div>
              </div>
            </div>

            <div className="flex space-x-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleHighlightPath}
                className="flex items-center space-x-1"
              >
                <Eye className="w-3 h-3" />
                <span>Highlight in Graph</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleSimulatePath}
                className="flex items-center space-x-1"
              >
                <PlayCircle className="w-3 h-3" />
                <span>Simulate</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportPath}
                className="flex items-center space-x-1"
              >
                <Download className="w-3 h-3" />
                <span>Export</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Path Steps */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            <TrendingUp className="w-4 h-4 text-orange-500" />
            <span>Attack Steps</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {(attackPath?.path_nodes || []).map((node, nodeIndex) => (
              <div key={node?.id || nodeIndex} className="relative">
                {/* Node */}
                <div className="flex items-center space-x-3">
                  <div className="flex-shrink-0 w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                    {nodeIndex + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-sm">{node?.name || 'Unknown node'}</div>
                    <div className="text-xs text-gray-600">{node?.type || 'Unknown type'}</div>
                  </div>
                  <Badge variant="outline" className="text-xs">
                    {nodeIndex === 0 ? 'START' : nodeIndex === (attackPath?.path_nodes?.length || 1) - 1 ? 'TARGET' : 'STEP'}
                  </Badge>
                </div>

                {/* Edge (if not last node) */}
                {nodeIndex < (attackPath?.path_nodes?.length || 1) - 1 && (
                  <div className="ml-4 mt-2 mb-2 pl-4 border-l-2 border-gray-200">
                    <div className="flex items-center space-x-2 text-sm">
                      <ArrowRight className="w-3 h-3 text-gray-400" />
                      <span className="text-gray-600">
                        {attackPath?.path_edges?.[nodeIndex]?.type?.replace(/_/g, ' ') || 'relationship'}
                      </span>
                    </div>
                    {attackPath?.path_edges?.[nodeIndex]?.properties && (
                      <div className="mt-1 text-xs text-gray-500">
                        {Object.entries(attackPath.path_edges[nodeIndex].properties).map(([key, value]) => (
                          <div key={key} className="truncate">
                            {key}: {String(value)}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
            {(!attackPath?.path_nodes || attackPath.path_nodes.length === 0) && (
              <p className="text-sm text-gray-600 italic">No attack path steps available</p>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Risk Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            <span>Risk Analysis</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm font-medium text-gray-800">Path Length:</span>
                <p className="text-sm text-gray-600 mt-1">{attackPath?.length || 0} steps</p>
              </div>
              <div>
                <span className="text-sm font-medium text-gray-800">Category:</span>
                <p className="text-sm text-gray-600 mt-1 capitalize">
                  {(attackPath?.category || 'unknown').replace(/_/g, ' ')}
                </p>
              </div>
            </div>

            <Separator />

            <div>
              <span className="text-sm font-medium text-gray-800">Impact Assessment:</span>
              <ul className="mt-2 space-y-1">
                <li className="text-sm text-gray-600 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-red-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Complete access to target resource
                </li>
                <li className="text-sm text-gray-600 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-orange-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Potential for lateral movement
                </li>
                <li className="text-sm text-gray-600 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-yellow-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Privilege escalation opportunity
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Mitigation */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base flex items-center space-x-2">
            <Shield className="w-4 h-4 text-green-600" />
            <span>Mitigation Recommendations</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
              <h4 className="text-sm font-medium text-green-800 mb-2">
                Immediate Actions
              </h4>
              <ul className="space-y-1">
                <li className="text-sm text-green-700 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Review and remove unnecessary role assignments
                </li>
                <li className="text-sm text-green-700 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-green-600 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Implement principle of least privilege
                </li>
              </ul>
            </div>

            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="text-sm font-medium text-blue-800 mb-2">
                Long-term Security
              </h4>
              <ul className="space-y-1">
                <li className="text-sm text-blue-700 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Enable audit logging for all services
                </li>
                <li className="text-sm text-blue-700 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Implement organizational policy constraints
                </li>
                <li className="text-sm text-blue-700 flex items-start">
                  <span className="inline-block w-1.5 h-1.5 bg-blue-600 rounded-full mt-2 mr-2 flex-shrink-0" />
                  Regular access reviews and monitoring
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Metadata */}
      {attackPath?.visualization_metadata && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <Clock className="w-4 h-4 text-gray-600" />
              <span>Additional Information</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              {attackPath.visualization_metadata.attack_summary && (
                <div>
                  <span className="font-medium text-gray-800">Summary:</span>
                  <p className="text-gray-600 mt-1">
                    {attackPath.visualization_metadata.attack_summary}
                  </p>
                </div>
              )}
              
              {attackPath.visualization_metadata.permissions_used && 
               attackPath.visualization_metadata.permissions_used.length > 0 && (
                <div>
                  <span className="font-medium text-gray-800">Permissions Used:</span>
                  <div className="mt-1 flex flex-wrap gap-1">
                    {attackPath.visualization_metadata.permissions_used.map((permission, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {permission}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}
    </SidePanelLayout>
  );
} 