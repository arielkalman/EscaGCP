import { Node, Edge, NodeType } from '../types';

/**
 * Check if a node ID represents a ghost user (deleted user/service account)
 */
export function isGhostUser(nodeId: string): boolean {
  return nodeId.toLowerCase().includes('deleted:') || 
         nodeId.toLowerCase().startsWith('deleted:') ||
         (nodeId.includes('@') && nodeId.toLowerCase().includes('deleted'));
}

/**
 * Check if a node represents a ghost user
 */
export function isGhostNode(node: Node): boolean {
  if (!node) return false;
  
  // Check if it's a user or service account type
  const isUserOrSA = node.type === NodeType.USER || node.type === NodeType.SERVICE_ACCOUNT;
  if (!isUserOrSA) return false;
  
  // Check various ways a user might be marked as deleted
  return (
    isGhostUser(node.id) ||
    isGhostUser(node.name) ||
    (node.properties?.email && isGhostUser(node.properties.email)) ||
    (node.properties?.deleted === true) ||
    (node.properties?.state === 'DELETED') ||
    (node.properties?.lifecycleState === 'DELETE_REQUESTED')
  );
}

/**
 * Check if an edge involves ghost users
 */
export function isEdgeWithGhostUser(edge: Edge, nodes: Node[]): boolean {
  const sourceNode = nodes.find(n => n.id === edge.source);
  const targetNode = nodes.find(n => n.id === edge.target);
  
  const sourceIsGhost = sourceNode ? isGhostNode(sourceNode) : false;
  const targetIsGhost = targetNode ? isGhostNode(targetNode) : false;
  
  return sourceIsGhost || targetIsGhost;
}

/**
 * Filter out ghost nodes from a list of nodes
 */
export function filterGhostNodes(nodes: Node[], showGhostUsers: boolean): Node[] {
  if (showGhostUsers) {
    return nodes;
  }
  
  return nodes.filter(node => !isGhostNode(node));
}

/**
 * Filter out edges that involve ghost users
 */
export function filterGhostEdges(edges: Edge[], nodes: Node[], showGhostUsers: boolean): Edge[] {
  if (showGhostUsers) {
    return edges;
  }
  
  return edges.filter(edge => !isEdgeWithGhostUser(edge, nodes));
}

/**
 * Get statistics about ghost users in the data
 */
export function getGhostUserStats(nodes: Node[], edges: Edge[]): {
  totalGhostNodes: number;
  ghostUsers: number;
  ghostServiceAccounts: number;
  edgesWithGhostUsers: number;
} {
  const ghostNodes = nodes.filter(isGhostNode);
  const ghostUsers = ghostNodes.filter(n => n.type === NodeType.USER).length;
  const ghostServiceAccounts = ghostNodes.filter(n => n.type === NodeType.SERVICE_ACCOUNT).length;
  const edgesWithGhostUsers = edges.filter(edge => isEdgeWithGhostUser(edge, nodes)).length;
  
  return {
    totalGhostNodes: ghostNodes.length,
    ghostUsers,
    ghostServiceAccounts,
    edgesWithGhostUsers
  };
} 