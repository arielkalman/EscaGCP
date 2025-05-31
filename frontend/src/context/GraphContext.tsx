import { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';
import type { GraphNode, GraphEdge, AttackPath } from '../types';

// State interface
interface GraphState {
  selectedNode: GraphNode | null;
  selectedEdge: GraphEdge | null;
  selectedAttackPath: AttackPath | null;
  isNodePanelOpen: boolean;
  isEdgePanelOpen: boolean;
  isAttackPathPanelOpen: boolean;
  highlightedNodes: Set<string>;
  highlightedEdges: Set<string>;
}

// Action types
type GraphAction =
  | { type: 'SELECT_NODE'; payload: GraphNode }
  | { type: 'SELECT_EDGE'; payload: GraphEdge }
  | { type: 'SELECT_ATTACK_PATH'; payload: AttackPath }
  | { type: 'CLEAR_SELECTION' }
  | { type: 'OPEN_NODE_PANEL' }
  | { type: 'CLOSE_NODE_PANEL' }
  | { type: 'OPEN_EDGE_PANEL' }
  | { type: 'CLOSE_EDGE_PANEL' }
  | { type: 'OPEN_ATTACK_PATH_PANEL' }
  | { type: 'CLOSE_ATTACK_PATH_PANEL' }
  | { type: 'HIGHLIGHT_NODES'; payload: string[] }
  | { type: 'HIGHLIGHT_EDGES'; payload: string[] }
  | { type: 'CLEAR_HIGHLIGHTS' };

// Initial state
const initialState: GraphState = {
  selectedNode: null,
  selectedEdge: null,
  selectedAttackPath: null,
  isNodePanelOpen: false,
  isEdgePanelOpen: false,
  isAttackPathPanelOpen: false,
  highlightedNodes: new Set(),
  highlightedEdges: new Set(),
};

// Reducer
function graphReducer(state: GraphState, action: GraphAction): GraphState {
  switch (action.type) {
    case 'SELECT_NODE':
      return {
        ...state,
        selectedNode: action.payload,
        selectedEdge: null,
        selectedAttackPath: null,
        isNodePanelOpen: true,
        isEdgePanelOpen: false,
        isAttackPathPanelOpen: false,
      };
    
    case 'SELECT_EDGE':
      return {
        ...state,
        selectedEdge: action.payload,
        selectedNode: null,
        selectedAttackPath: null,
        isEdgePanelOpen: true,
        isNodePanelOpen: false,
        isAttackPathPanelOpen: false,
      };
    
    case 'SELECT_ATTACK_PATH':
      return {
        ...state,
        selectedAttackPath: action.payload,
        selectedNode: null,
        selectedEdge: null,
        isAttackPathPanelOpen: true,
        isNodePanelOpen: false,
        isEdgePanelOpen: false,
      };
    
    case 'CLEAR_SELECTION':
      return {
        ...state,
        selectedNode: null,
        selectedEdge: null,
        selectedAttackPath: null,
        isNodePanelOpen: false,
        isEdgePanelOpen: false,
        isAttackPathPanelOpen: false,
      };
    
    case 'OPEN_NODE_PANEL':
      return { ...state, isNodePanelOpen: true };
    
    case 'CLOSE_NODE_PANEL':
      return { ...state, isNodePanelOpen: false, selectedNode: null };
    
    case 'OPEN_EDGE_PANEL':
      return { ...state, isEdgePanelOpen: true };
    
    case 'CLOSE_EDGE_PANEL':
      return { ...state, isEdgePanelOpen: false, selectedEdge: null };
    
    case 'OPEN_ATTACK_PATH_PANEL':
      return { ...state, isAttackPathPanelOpen: true };
    
    case 'CLOSE_ATTACK_PATH_PANEL':
      return { ...state, isAttackPathPanelOpen: false, selectedAttackPath: null };
    
    case 'HIGHLIGHT_NODES':
      return {
        ...state,
        highlightedNodes: new Set(action.payload),
      };
    
    case 'HIGHLIGHT_EDGES':
      return {
        ...state,
        highlightedEdges: new Set(action.payload),
      };
    
    case 'CLEAR_HIGHLIGHTS':
      return {
        ...state,
        highlightedNodes: new Set(),
        highlightedEdges: new Set(),
      };
    
    default:
      return state;
  }
}

// Context interface
interface GraphContextType {
  state: GraphState;
  selectNode: (node: GraphNode) => void;
  selectEdge: (edge: GraphEdge) => void;
  selectAttackPath: (attackPath: AttackPath) => void;
  clearSelection: () => void;
  openNodePanel: () => void;
  closeNodePanel: () => void;
  openEdgePanel: () => void;
  closeEdgePanel: () => void;
  openAttackPathPanel: () => void;
  closeAttackPathPanel: () => void;
  highlightNodes: (nodeIds: string[]) => void;
  highlightEdges: (edgeIds: string[]) => void;
  clearHighlights: () => void;
}

// Create context
const GraphContext = createContext<GraphContextType | undefined>(undefined);

// Provider component
interface GraphProviderProps {
  children: ReactNode;
}

export function GraphProvider({ children }: GraphProviderProps) {
  const [state, dispatch] = useReducer(graphReducer, initialState);

  // Listen for test events to support E2E testing
  useEffect(() => {
    const handleNodeSelected = (event: CustomEvent) => {
      console.log('GraphContext: handleNodeSelected', event.detail);
      const { nodeData } = event.detail;
      if (nodeData) {
        dispatch({ type: 'SELECT_NODE', payload: nodeData });
      }
    };

    const handleEdgeSelected = (event: CustomEvent) => {
      console.log('GraphContext: handleEdgeSelected', event.detail);
      const { edgeData } = event.detail;
      if (edgeData) {
        dispatch({ type: 'SELECT_EDGE', payload: edgeData });
      }
    };

    // Add event listeners for test events
    window.addEventListener('nodeSelected', handleNodeSelected as EventListener);
    window.addEventListener('edgeSelected', handleEdgeSelected as EventListener);

    // Cleanup
    return () => {
      window.removeEventListener('nodeSelected', handleNodeSelected as EventListener);
      window.removeEventListener('edgeSelected', handleEdgeSelected as EventListener);
    };
  }, []); // Empty dependency array to ensure this runs once

  const contextValue: GraphContextType = {
    state,
    selectNode: (node: GraphNode) => dispatch({ type: 'SELECT_NODE', payload: node }),
    selectEdge: (edge: GraphEdge) => dispatch({ type: 'SELECT_EDGE', payload: edge }),
    selectAttackPath: (attackPath: AttackPath) => dispatch({ type: 'SELECT_ATTACK_PATH', payload: attackPath }),
    clearSelection: () => dispatch({ type: 'CLEAR_SELECTION' }),
    openNodePanel: () => dispatch({ type: 'OPEN_NODE_PANEL' }),
    closeNodePanel: () => dispatch({ type: 'CLOSE_NODE_PANEL' }),
    openEdgePanel: () => dispatch({ type: 'OPEN_EDGE_PANEL' }),
    closeEdgePanel: () => dispatch({ type: 'CLOSE_EDGE_PANEL' }),
    openAttackPathPanel: () => dispatch({ type: 'OPEN_ATTACK_PATH_PANEL' }),
    closeAttackPathPanel: () => dispatch({ type: 'CLOSE_ATTACK_PATH_PANEL' }),
    highlightNodes: (nodeIds: string[]) => dispatch({ type: 'HIGHLIGHT_NODES', payload: nodeIds }),
    highlightEdges: (edgeIds: string[]) => dispatch({ type: 'HIGHLIGHT_EDGES', payload: edgeIds }),
    clearHighlights: () => dispatch({ type: 'CLEAR_HIGHLIGHTS' }),
  };

  return (
    <GraphContext.Provider value={contextValue}>
      {children}
    </GraphContext.Provider>
  );
}

// Hook to use the context
export function useGraphContext() {
  const context = useContext(GraphContext);
  if (context === undefined) {
    throw new Error('useGraphContext must be used within a GraphProvider');
  }
  return context;
} 