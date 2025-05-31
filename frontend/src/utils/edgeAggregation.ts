import { Edge, Node, AggregatedEdgeGroup, AggregatedEdgesData, EdgeType } from '../types';
import { filterGhostEdges } from './ghostUsers';

// Get edge type category and risk level
const getEdgeCategory = (edgeType: EdgeType): { category: string; risk: 'critical' | 'high' | 'medium' | 'low' } => {
  const privilegeEscalationEdges = [
    EdgeType.CAN_IMPERSONATE,
    EdgeType.CAN_IMPERSONATE_SA,
    EdgeType.CAN_CREATE_SERVICE_ACCOUNT_KEY,
    EdgeType.CAN_ACT_AS_VIA_VM,
    EdgeType.CAN_DEPLOY_FUNCTION_AS,
    EdgeType.CAN_DEPLOY_CLOUD_RUN_AS,
    EdgeType.CAN_TRIGGER_BUILD_AS,
    EdgeType.CAN_DEPLOY_GKE_POD_AS,
    EdgeType.HAS_IMPERSONATED,
    EdgeType.HAS_ESCALATED_PRIVILEGE
  ];

  const adminEdges = [EdgeType.CAN_ADMIN, EdgeType.CAN_LOGIN_TO_VM];
  const accessEdges = [EdgeType.CAN_READ, EdgeType.CAN_WRITE, EdgeType.HAS_ACCESSED];
  const structuralEdges = [EdgeType.HAS_ROLE, EdgeType.MEMBER_OF, EdgeType.PARENT_OF, EdgeType.RUNS_AS];

  if (privilegeEscalationEdges.includes(edgeType)) {
    return { category: 'Privilege Escalation', risk: 'critical' };
  } else if (adminEdges.includes(edgeType)) {
    return { category: 'Administrative', risk: 'high' };
  } else if (accessEdges.includes(edgeType)) {
    return { category: 'Access Control', risk: 'medium' };
  } else {
    return { category: 'Structural', risk: 'low' };
  }
};

// Calculate risk score for an edge (simplified)
const calculateEdgeRiskScore = (edge: Edge): number => {
  const { risk } = getEdgeCategory(edge.type);
  
  const riskScores = {
    critical: 0.9,
    high: 0.7,
    medium: 0.5,
    low: 0.3
  };
  
  let baseScore = riskScores[risk];
  
  // Adjust for properties
  if (edge.properties?.external) {
    baseScore += 0.1;
  }
  
  if (edge.properties?.condition) {
    baseScore -= 0.1; // Conditional access is less risky
  }
  
  if (edge.properties?.inherited) {
    baseScore -= 0.05; // Inherited might be less direct
  }
  
  return Math.min(Math.max(baseScore, 0), 1);
};

export function aggregateEdgesBySource(
  edges: Edge[], 
  nodes: Node[], 
  expandedGroups: Set<string> = new Set(),
  showGhostUsers: boolean = false
): AggregatedEdgesData {
  // Filter out ghost users if needed
  const filteredEdges = filterGhostEdges(edges, nodes, showGhostUsers);
  
  // Group edges by source node ID
  const edgeGroups = new Map<string, Edge[]>();
  
  filteredEdges.forEach(edge => {
    const sourceId = edge.source;
    if (!edgeGroups.has(sourceId)) {
      edgeGroups.set(sourceId, []);
    }
    edgeGroups.get(sourceId)!.push(edge);
  });
  
  // Convert to aggregated groups
  const groups: AggregatedEdgeGroup[] = [];
  
  edgeGroups.forEach((groupEdges, sourceNodeId) => {
    // Find the source node
    const sourceNode = nodes.find(n => n.id === sourceNodeId) || null;
    
    // Count unique targets
    const uniqueTargets = new Set(groupEdges.map(e => e.target));
    const targetCount = uniqueTargets.size;
    
    // Calculate risk statistics
    const riskScores = groupEdges.map(edge => calculateEdgeRiskScore(edge));
    const highestRiskScore = Math.max(...riskScores);
    
    // Count by risk category
    const riskCategoryCounts: Record<string, number> = {
      critical: 0,
      high: 0,
      medium: 0,
      low: 0
    };
    
    groupEdges.forEach(edge => {
      const { risk } = getEdgeCategory(edge.type);
      riskCategoryCounts[risk]++;
    });
    
    groups.push({
      sourceNodeId,
      sourceNode,
      edges: groupEdges,
      targetCount,
      highestRiskScore,
      riskCategoryCounts,
      isExpanded: expandedGroups.has(sourceNodeId)
    });
  });
  
  // Sort groups by risk score (highest first) and then by number of edges
  groups.sort((a, b) => {
    if (a.highestRiskScore !== b.highestRiskScore) {
      return b.highestRiskScore - a.highestRiskScore;
    }
    return b.edges.length - a.edges.length;
  });
  
  return {
    groups,
    totalEdges: filteredEdges.length,
    totalGroups: groups.length
  };
}

export function updateGroupExpansion(
  aggregatedData: AggregatedEdgesData,
  sourceNodeId: string,
  isExpanded: boolean
): AggregatedEdgesData {
  return {
    ...aggregatedData,
    groups: aggregatedData.groups.map(group => 
      group.sourceNodeId === sourceNodeId 
        ? { ...group, isExpanded }
        : group
    )
  };
}

export function toggleGroupExpansion(
  aggregatedData: AggregatedEdgesData,
  sourceNodeId: string
): AggregatedEdgesData {
  return {
    ...aggregatedData,
    groups: aggregatedData.groups.map(group => 
      group.sourceNodeId === sourceNodeId 
        ? { ...group, isExpanded: !group.isExpanded }
        : group
    )
  };
}

export function expandAllGroups(aggregatedData: AggregatedEdgesData): AggregatedEdgesData {
  return {
    ...aggregatedData,
    groups: aggregatedData.groups.map(group => ({ ...group, isExpanded: true }))
  };
}

export function collapseAllGroups(aggregatedData: AggregatedEdgesData): AggregatedEdgesData {
  return {
    ...aggregatedData,
    groups: aggregatedData.groups.map(group => ({ ...group, isExpanded: false }))
  };
} 