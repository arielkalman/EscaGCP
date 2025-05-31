// Core data structures from API specification

export enum NodeType {
  USER = "user",
  SERVICE_ACCOUNT = "service_account",
  GROUP = "group",
  PROJECT = "project",
  FOLDER = "folder",
  ORGANIZATION = "organization",
  ROLE = "role",
  CUSTOM_ROLE = "custom_role",
  BUCKET = "bucket",
  INSTANCE = "instance",
  FUNCTION = "function",
  SECRET = "secret",
  KMS_KEY = "kms_key",
  DATASET = "dataset",
  TOPIC = "topic",
  CLOUD_RUN_SERVICE = "cloud_run_service",
  GKE_CLUSTER = "gke_cluster",
  CLOUD_BUILD_TRIGGER = "cloud_build_trigger",
  COMPUTE_INSTANCE = "compute_instance"
}

export enum EdgeType {
  // Standard relationships
  HAS_ROLE = "has_role",
  MEMBER_OF = "member_of",
  PARENT_OF = "parent_of",
  CAN_READ = "can_read",
  CAN_WRITE = "can_write",
  CAN_ADMIN = "can_admin",
  
  // Privilege escalation relationships
  CAN_IMPERSONATE = "can_impersonate",
  CAN_IMPERSONATE_SA = "can_impersonate_sa",
  CAN_CREATE_SERVICE_ACCOUNT_KEY = "can_create_service_account_key",
  CAN_ACT_AS_VIA_VM = "can_act_as_via_vm",
  CAN_DEPLOY_FUNCTION_AS = "can_deploy_function_as",
  CAN_DEPLOY_CLOUD_RUN_AS = "can_deploy_cloud_run_as",
  CAN_TRIGGER_BUILD_AS = "can_trigger_build_as",
  CAN_LOGIN_TO_VM = "can_login_to_vm",
  CAN_DEPLOY_GKE_POD_AS = "can_deploy_gke_pod_as",
  RUNS_AS = "runs_as",
  
  // Audit log confirmed relationships
  HAS_IMPERSONATED = "has_impersonated",
  HAS_ESCALATED_PRIVILEGE = "has_escalated_privilege",
  HAS_ACCESSED = "has_accessed"
}

export interface Node {
  id: string;
  type: NodeType;
  name: string;
  properties: Record<string, any>;
}

export interface Edge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  properties: Record<string, any>;
}

export interface GraphMetadata {
  total_nodes: number;
  total_edges: number;
  collection_time: string;
  gcp_projects: string[];
  gcp_organization?: string;
  generator_version: string;
}

export interface GraphData {
  nodes: Node[];
  edges: Edge[];
  metadata: GraphMetadata;
}

export interface Statistics {
  total_nodes: number;
  total_edges: number;
  attack_paths: number;
  high_risk_nodes: number;
  dangerous_roles: number;
  privilege_escalation_paths: number;
  lateral_movement_paths: number;
  critical_nodes: number;
  vulnerabilities: number;
}

export interface RiskFactor {
  type: string;
  impact: number;
  description: string;
}

export interface NodeRiskScore {
  base: number;
  centrality: number;
  total: number;
  factors: RiskFactor[];
}

export interface RiskScores {
  [nodeId: string]: NodeRiskScore;
}

export interface PathNode {
  id: string;
  type: NodeType;
  name: string;
}

export interface PathEdge {
  id: string;
  source: string;
  target: string;
  type: EdgeType;
  properties: Record<string, any>;
}

export interface VisualizationMetadata {
  node_metadata?: Array<{
    id: string;
    x?: number;
    y?: number;
    color?: string;
    size?: number;
  }>;
  edge_metadata?: Array<{
    id: string;
    color?: string;
    width?: number;
  }>;
  escalation_techniques?: Array<{
    name: string;
    description: string;
    impact: string;
    mitigation: string;
  }>;
  permissions_used?: string[];
  attack_summary?: string;
}

export interface AttackPath {
  source: PathNode;
  target: PathNode;
  path_nodes: PathNode[];
  path_edges: PathEdge[];
  risk_score: number;
  description: string;
  length: number;
  category: string;
  visualization_metadata?: VisualizationMetadata;
}

export interface AttackPathsByCategory {
  critical: AttackPath[];
  critical_multi_step: AttackPath[];
  privilege_escalation: AttackPath[];
  lateral_movement: AttackPath[];
  high: AttackPath[];
  medium: AttackPath[];
  low: AttackPath[];
}

export interface Vulnerability {
  id: string;
  title: string;
  description: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW';
  risk_score: number;
  category: string;
  affected_resources: string[];
  remediation: string[];
  cve_references: string[];
  mitre_techniques: string[];
  detection_rules: string[];
}

export interface CriticalNode {
  id: string;
  type: NodeType;
  name: string;
  risk_score: number;
  criticality_factors: string[];
}

export interface DangerousRole {
  role: string;
  assignees: string[];
  risk_score: number;
  permissions_count: number;
  reasons: string[];
}

export interface AnalysisResults {
  statistics: Statistics;
  attack_paths: AttackPathsByCategory;
  risk_scores: RiskScores;
  vulnerabilities: Vulnerability[];
  critical_nodes: CriticalNode[];
  dangerous_roles: DangerousRole[];
}

// UI State Types

export type TabType = 'dictionary' | 'attack-paths' | 'found-paths' | 'settings';

export interface ModalState {
  isOpen: boolean;
  type: 'node-details' | 'edge-details' | 'attack-path' | 'settings' | null;
  data?: any;
}

export interface GraphFilters {
  nodeTypes: NodeType[];
  edgeTypes: EdgeType[];
  riskThreshold: number;
  showOnlyAttackPaths: boolean;
}

export interface DisplayOptions {
  showNodeLabels: boolean;
  showEdgeLabels: boolean;
  enablePhysics: boolean;
  hierarchicalLayout: boolean;
  colorByRisk: boolean;
}

export interface AppSettings {
  autoRefresh: boolean;
  refreshInterval: number;
  displayOptions: DisplayOptions;
  theme: 'light' | 'dark' | 'system';
}

// vis.js specific types for network visualization

export interface VisNode {
  id: string;
  label: string;
  group?: string;
  color?: string | { background: string; border: string; };
  size?: number;
  shape?: string;
  title?: string;
  physics?: boolean;
  x?: number;
  y?: number;
}

export interface VisEdge {
  id: string;
  from: string;
  to: string;
  label?: string;
  color?: string | { color: string; };
  width?: number;
  arrows?: string | { to: boolean; };
  dashes?: boolean;
  title?: string;
}

export interface VisNetworkData {
  nodes: VisNode[];
  edges: VisEdge[];
}

// API Response Types

export interface APIError {
  error: {
    code: string;
    message: string;
    details?: any;
    timestamp: string;
  };
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    has_more: boolean;
    next_cursor?: string;
  };
}

// Form and Input Types

export interface SearchFilters {
  query: string;
  nodeTypes: NodeType[];
  riskLevels: ('critical' | 'high' | 'medium' | 'low')[];
  categories: string[];
}

export interface NodeDetailsProps {
  node: Node;
  riskScore?: NodeRiskScore;
  onClose: () => void;
}

export interface EdgeDetailsProps {
  edge: Edge;
  sourceNode: Node;
  targetNode: Node;
  onClose: () => void;
}

export interface AttackPathDetailsProps {
  attackPath: AttackPath;
  onClose: () => void;
  onHighlight: (pathId: string) => void;
}

// Component Props Types

export interface StatisticsCardProps {
  title: string;
  value: number;
  icon: React.ComponentType<any>;
  color?: string;
  onClick?: () => void;
}

export interface RiskBadgeProps {
  riskScore: number;
  size?: 'sm' | 'md' | 'lg';
  showPercentage?: boolean;
}

export interface NodeIconProps {
  nodeType: NodeType;
  size?: number;
  className?: string;
}

// Graph Layout and Styling Types

export interface GraphLayout {
  hierarchical: {
    enabled: boolean;
    levelSeparation: number;
    nodeSpacing: number;
    treeSpacing: number;
    blockShifting: boolean;
    edgeMinimization: boolean;
    parentCentralization: boolean;
    direction: 'UD' | 'DU' | 'LR' | 'RL';
    sortMethod: 'hubsize' | 'directed';
  };
}

export interface NetworkOptions {
  autoResize?: boolean;
  height?: string;
  width?: string;
  locale?: string;
  clickToUse?: boolean;
  configure?: any;
  edges?: any;
  nodes?: any;
  groups?: any;
  layout?: GraphLayout;
  interaction?: any;
  manipulation?: any;
  physics?: any;
}

// Utility Types

export type RiskLevel = 'critical' | 'high' | 'medium' | 'low' | 'info';

export interface ColorScheme {
  [key: string]: string;
}

export interface ThemeColors {
  nodes: ColorScheme;
  edges: ColorScheme;
  risk: ColorScheme;
}

export function getRiskLevel(score: number): RiskLevel {
  if (score >= 0.8) return 'critical';
  if (score >= 0.6) return 'high';
  if (score >= 0.4) return 'medium';
  if (score >= 0.2) return 'low';
  return 'info';
}

export function getNodeTypeColor(type: NodeType): string {
  const colors: Record<NodeType, string> = {
    [NodeType.USER]: '#4285F4',
    [NodeType.SERVICE_ACCOUNT]: '#34A853',
    [NodeType.GROUP]: '#FBBC04',
    [NodeType.PROJECT]: '#EA4335',
    [NodeType.FOLDER]: '#FF6D00',
    [NodeType.ORGANIZATION]: '#9C27B0',
    [NodeType.ROLE]: '#757575',
    [NodeType.CUSTOM_ROLE]: '#8E24AA',
    [NodeType.BUCKET]: '#00ACC1',
    [NodeType.INSTANCE]: '#FF7043',
    [NodeType.FUNCTION]: '#26A69A',
    [NodeType.SECRET]: '#AB47BC',
    [NodeType.KMS_KEY]: '#FFA726',
    [NodeType.DATASET]: '#42A5F5',
    [NodeType.TOPIC]: '#66BB6A',
    [NodeType.CLOUD_RUN_SERVICE]: '#29B6F6',
    [NodeType.GKE_CLUSTER]: '#5C6BC0',
    [NodeType.CLOUD_BUILD_TRIGGER]: '#FF8A65',
    [NodeType.COMPUTE_INSTANCE]: '#FF7043'
  };
  
  return colors[type] || '#757575';
}

// Type aliases for graph components consistency
export type GraphNode = Node;
export type GraphEdge = Edge;

// Aggregated Edges Types for hierarchical display
export interface AggregatedEdgeGroup {
  sourceNodeId: string;
  sourceNode: Node | null;
  edges: Edge[];
  targetCount: number;
  highestRiskScore: number;
  riskCategoryCounts: Record<string, number>;
  isExpanded: boolean;
}

export interface AggregatedEdgesData {
  groups: AggregatedEdgeGroup[];
  totalEdges: number;
  totalGroups: number;
}

// Row types for the aggregated table
export type EdgeTableRowType = 'group' | 'edge';

export interface EdgeTableRow {
  type: EdgeTableRowType;
  id: string;
  data: AggregatedEdgeGroup | Edge;
  level: number; // 0 for groups, 1 for individual edges
} 