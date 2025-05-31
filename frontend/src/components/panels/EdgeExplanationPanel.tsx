import React from 'react';
import { 
  ArrowRight, 
  Shield, 
  Key, 
  AlertTriangle, 
  Info,
  ExternalLink,
  Copy,
  Share2
} from 'lucide-react';
import { SidePanelLayout } from '../layout/SidePanelLayout';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { EdgeType } from '../../types';
import { useGraphContext } from '../../context/GraphContext';

interface EdgeExplanationPanelProps {
  className?: string;
}

// Edge type explanations and metadata
const EDGE_EXPLANATIONS: Record<EdgeType, {
  name: string;
  icon: React.ComponentType<any>;
  description: string;
  riskLevel: 'critical' | 'high' | 'medium' | 'low';
  technique: string;
  permission: string;
  mitigation: string[];
}> = {
  [EdgeType.CAN_IMPERSONATE]: {
    name: 'Service Account Impersonation',
    icon: Key,
    description: 'Can impersonate the target service account through various means.',
    riskLevel: 'critical',
    technique: 'Service account impersonation',
    permission: 'iam.serviceAccounts.actAs or iam.serviceAccounts.getAccessToken',
    mitigation: [
      'Review impersonation permissions',
      'Use least-privilege principle',
      'Enable audit logging for impersonation events',
      'Consider using short-lived tokens'
    ]
  },
  [EdgeType.CAN_IMPERSONATE_SA]: {
    name: 'Service Account Impersonation',
    icon: Key,
    description: 'Can generate access tokens for the target service account, effectively becoming that service account.',
    riskLevel: 'critical',
    technique: 'Generate access tokens using iam.serviceAccounts.getAccessToken permission',
    permission: 'iam.serviceAccounts.getAccessToken',
    mitigation: [
      'Remove unnecessary serviceAccountTokenCreator role',
      'Use short-lived tokens only',
      'Enable audit logging for token generation',
      'Implement organizational policy constraints'
    ]
  },
  [EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY]: {
    name: 'Service Account Key Creation',
    icon: Shield,
    description: 'Can create long-lived service account keys that can be exported and used indefinitely.',
    riskLevel: 'critical',
    technique: 'Create and download service account keys',
    permission: 'iam.serviceAccountKeys.create',
    mitigation: [
      'Enforce organizational policy to disable key creation',
      'Use Workload Identity instead of keys',
      'Monitor key creation events',
      'Regularly rotate and audit existing keys'
    ]
  },
  [EdgeType.CAN_ACT_AS_VIA_VM]: {
    name: 'VM Service Account Abuse',
    icon: ExternalLink,
    description: 'Can deploy or modify VMs that run with the target service account\'s permissions.',
    riskLevel: 'high',
    technique: 'Deploy VMs with privileged service accounts',
    permission: 'compute.instances.create + iam.serviceAccounts.actAs',
    mitigation: [
      'Restrict compute.admin role',
      'Use least-privilege service accounts for VMs',
      'Enable OS Login',
      'Disable project-wide SSH keys'
    ]
  },
  [EdgeType.CAN_DEPLOY_FUNCTION_AS]: {
    name: 'Cloud Function Deployment',
    icon: ArrowRight,
    description: 'Can deploy cloud functions that execute with the target service account.',
    riskLevel: 'high',
    technique: 'Deploy malicious cloud functions',
    permission: 'cloudfunctions.functions.create + iam.serviceAccounts.actAs',
    mitigation: [
      'Restrict function deployment permissions',
      'Use dedicated SAs with minimal permissions',
      'Enable VPC Service Controls',
      'Monitor function deployments'
    ]
  },
  [EdgeType.CAN_DEPLOY_CLOUD_RUN_AS]: {
    name: 'Cloud Run Deployment',
    icon: ArrowRight,
    description: 'Can deploy Cloud Run services that execute with privileged permissions.',
    riskLevel: 'high',
    technique: 'Deploy malicious containers',
    permission: 'run.services.create + iam.serviceAccounts.actAs',
    mitigation: [
      'Restrict Cloud Run admin permissions',
      'Use Binary Authorization',
      'Implement least-privilege service accounts',
      'Monitor container deployments'
    ]
  },
  // Default for other edge types
  [EdgeType.HAS_ROLE]: {
    name: 'Role Assignment',
    icon: Shield,
    description: 'Has been assigned an IAM role granting specific permissions.',
    riskLevel: 'medium',
    technique: 'Use assigned role permissions',
    permission: 'Various based on role',
    mitigation: [
      'Review role assignments regularly',
      'Use least-privilege principle',
      'Monitor role usage'
    ]
  },
  [EdgeType.MEMBER_OF]: {
    name: 'Group Membership',
    icon: ArrowRight,
    description: 'Is a member of the target group.',
    riskLevel: 'low',
    technique: 'Inherit group permissions',
    permission: 'N/A - group membership',
    mitigation: [
      'Review group memberships',
      'Remove unused group assignments'
    ]
  },
  [EdgeType.CAN_ADMIN]: {
    name: 'Administrative Access',
    icon: AlertTriangle,
    description: 'Has full administrative control over the target resource.',
    riskLevel: 'high',
    technique: 'Full resource control',
    permission: 'resourcemanager.*.setIamPolicy',
    mitigation: [
      'Limit admin role assignments',
      'Use conditional bindings',
      'Enable audit logging'
    ]
  },
  [EdgeType.CAN_WRITE]: {
    name: 'Write Access',
    icon: ArrowRight,
    description: 'Can modify the target resource.',
    riskLevel: 'medium',
    technique: 'Resource modification',
    permission: 'Varies by resource',
    mitigation: [
      'Review write permissions',
      'Use read-only when possible'
    ]
  },
  [EdgeType.CAN_READ]: {
    name: 'Read Access',
    icon: Info,
    description: 'Can view the target resource.',
    riskLevel: 'low',
    technique: 'Resource access',
    permission: 'Varies by resource',
    mitigation: [
      'Review access permissions',
      'Remove unnecessary read access'
    ]
  },
  // Add other edge types with default values
  [EdgeType.PARENT_OF]: {
    name: 'Parent Relationship',
    icon: ArrowRight,
    description: 'Is a parent of the target resource in the hierarchy.',
    riskLevel: 'low',
    technique: 'Hierarchy relationship',
    permission: 'N/A - structural relationship',
    mitigation: []
  },
  [EdgeType.CAN_TRIGGER_BUILD_AS]: {
    name: 'Cloud Build Trigger',
    icon: ArrowRight,
    description: 'Can trigger builds that run with privileged service accounts.',
    riskLevel: 'high',
    technique: 'Trigger malicious builds',
    permission: 'cloudbuild.builds.create',
    mitigation: [
      'Use custom service accounts for builds',
      'Restrict source repository access',
      'Enable Binary Authorization'
    ]
  },
  [EdgeType.CAN_LOGIN_TO_VM]: {
    name: 'VM SSH Access',
    icon: ArrowRight,
    description: 'Can SSH into VMs and access metadata server.',
    riskLevel: 'medium',
    technique: 'SSH + metadata server access',
    permission: 'compute.instances.osLogin',
    mitigation: [
      'Enable OS Login',
      'Use IAP for SSH access',
      'Restrict metadata server access'
    ]
  },
  [EdgeType.CAN_DEPLOY_GKE_POD_AS]: {
    name: 'GKE Pod Deployment',
    icon: ArrowRight,
    description: 'Can deploy pods in GKE with service account permissions.',
    riskLevel: 'high',
    technique: 'Deploy malicious pods',
    permission: 'container.pods.create + iam.serviceAccounts.actAs',
    mitigation: [
      'Implement Pod Security Policies',
      'Use separate namespaces',
      'Audit Workload Identity bindings'
    ]
  },
  [EdgeType.RUNS_AS]: {
    name: 'Runs As',
    icon: ArrowRight,
    description: 'Resource runs using the target service account.',
    riskLevel: 'medium',
    technique: 'Resource execution context',
    permission: 'N/A - execution relationship',
    mitigation: [
      'Use least-privilege service accounts',
      'Monitor resource execution'
    ]
  },
  [EdgeType.HAS_IMPERSONATED]: {
    name: 'Confirmed Impersonation',
    icon: AlertTriangle,
    description: 'Confirmed from audit logs - has actually impersonated the target.',
    riskLevel: 'critical',
    technique: 'Confirmed impersonation activity',
    permission: 'iam.serviceAccounts.getAccessToken',
    mitigation: [
      'Investigate the impersonation event',
      'Review access patterns',
      'Consider revoking access'
    ]
  },
  [EdgeType.HAS_ESCALATED_PRIVILEGE]: {
    name: 'Confirmed Privilege Escalation',
    icon: AlertTriangle,
    description: 'Confirmed from audit logs - has escalated privileges.',
    riskLevel: 'critical',
    technique: 'Confirmed privilege escalation',
    permission: 'Various escalation permissions',
    mitigation: [
      'Immediate investigation required',
      'Review and revoke permissions',
      'Audit all recent activities'
    ]
  },
  [EdgeType.HAS_ACCESSED]: {
    name: 'Confirmed Access',
    icon: Info,
    description: 'Confirmed from audit logs - has accessed the target resource.',
    riskLevel: 'medium',
    technique: 'Confirmed resource access',
    permission: 'Varies by resource',
    mitigation: [
      'Review access patterns',
      'Ensure access is still needed'
    ]
  }
};

export function EdgeExplanationPanel({ className }: EdgeExplanationPanelProps) {
  const { state, closeEdgePanel } = useGraphContext();
  
  const edge = state.selectedEdge;
  const isOpen = state.isEdgePanelOpen && !!edge;
  
  const edgeInfo = edge ? EDGE_EXPLANATIONS[edge.type] || EDGE_EXPLANATIONS[EdgeType.HAS_ROLE] : EDGE_EXPLANATIONS[EdgeType.HAS_ROLE];
  const IconComponent = edgeInfo.icon;

  const handleGoToSource = () => {
    if (!edge) return;
    console.log('Navigate to source node:', edge.source);
    // TODO: Focus graph on source node
  };

  const handleGoToTarget = () => {
    if (!edge) return;
    console.log('Navigate to target node:', edge.target);
    // TODO: Focus graph on target node
  };

  const handleCopyInfo = () => {
    if (!edge) return;
    const info = `Edge: ${edge.type}\nFrom: ${edge.source}\nTo: ${edge.target}\nPermission: ${edgeInfo.permission}`;
    navigator.clipboard.writeText(info);
    console.log('Copied edge info to clipboard');
  };

  const handleExportDetails = () => {
    if (!edge) return;
    console.log('Export edge details:', edge);
    // TODO: Implement export functionality
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

  return (
    <SidePanelLayout
      isOpen={isOpen}
      onClose={closeEdgePanel}
      title="Edge Details"
      description="Detailed information about the selected relationship"
      width="lg"
      className={className}
    >
      <div data-testid="edge-explanation-panel">
        {/* Edge Type Header */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-3">
              <IconComponent className="w-5 h-5 text-blue-600" />
              <span>{edgeInfo.name}</span>
              <Badge variant={getRiskBadgeVariant(edgeInfo.riskLevel)}>
                {edgeInfo.riskLevel.toUpperCase()}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-gray-600 mb-4">
              {edgeInfo.description}
            </p>
            
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="font-medium">Edge Type:</span>
                <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                  {edge?.type}
                </code>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Permission:</span>
                <code className="bg-gray-100 px-2 py-1 rounded text-xs">
                  {edgeInfo.permission}
                </code>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Source and Target */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Connection Details</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-800">Source</label>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <code className="text-sm text-gray-800">{edge?.source}</code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleGoToSource}
                    className="h-7 px-2"
                  >
                    <ArrowRight className="w-3 h-3 mr-1" />
                    Go to
                  </Button>
                </div>
              </div>

              <div className="flex justify-center">
                <ArrowRight className="w-5 h-5 text-gray-400" />
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-800">Target</label>
                <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <code className="text-sm text-gray-800">{edge?.target}</code>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleGoToTarget}
                    className="h-7 px-2"
                  >
                    <ArrowRight className="w-3 h-3 mr-1" />
                    Go to
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Edge Properties */}
        {edge?.properties && Object.keys(edge.properties).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Additional Properties</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(edge.properties).map(([key, value]) => (
                  <div key={key} className="flex justify-between text-sm">
                    <span className="font-medium text-gray-800 capitalize">
                      {key.replace('_', ' ')}:
                    </span>
                    <span className="text-gray-600 text-right max-w-48 truncate" title={String(value)}>
                      {String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Attack Technique */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 text-orange-500" />
              <span>Attack Technique</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <p className="text-sm text-gray-600">
                {edgeInfo.technique}
              </p>
              
              {edgeInfo.mitigation.length > 0 && (
                <>
                  <Separator />
                  <div>
                    <h4 className="text-sm font-medium text-gray-800 mb-2">Mitigation Steps:</h4>
                    <ul className="space-y-1">
                      {edgeInfo.mitigation.map((step, index) => (
                        <li key={index} className="text-sm text-gray-600 flex items-start">
                          <span className="inline-block w-1.5 h-1.5 bg-gray-400 rounded-full mt-2 mr-2 flex-shrink-0" />
                          {step}
                        </li>
                      ))}
                    </ul>
                  </div>
                </>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Actions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Actions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              <Button
                variant="outline"
                size="sm"
                onClick={handleCopyInfo}
                className="w-full justify-start"
              >
                <Copy className="w-4 h-4 mr-2" />
                Copy Edge Information
              </Button>
              
              <Button
                variant="outline"
                size="sm"
                onClick={handleExportDetails}
                className="w-full justify-start"
              >
                <Share2 className="w-4 h-4 mr-2" />
                Export Detailed Report
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </SidePanelLayout>
  );
} 