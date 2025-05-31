import { createContext, useContext, useReducer } from 'react';
import type { ReactNode } from 'react';

// Graph layout options
export type GraphLayout = 'hierarchical' | 'force-directed' | 'circular';

// Export format options
export type ExportFormat = 'json' | 'csv' | 'png' | 'svg';

// Settings state interface
interface SettingsState {
  // Graph preferences
  graphLayout: GraphLayout;
  enablePhysics: boolean;
  nodeSize: number;
  edgeThickness: number;
  maxNodes: number;
  showLabels: boolean;
  enableTooltips: boolean;
  
  // Export preferences
  defaultExportFormat: ExportFormat;
  includeMetadata: boolean;
  compressExports: boolean;
  
  // Performance settings
  autoRefresh: boolean;
  refreshInterval: number; // in minutes
}

// Action types
type SettingsAction =
  | { type: 'SET_GRAPH_LAYOUT'; payload: GraphLayout }
  | { type: 'TOGGLE_PHYSICS' }
  | { type: 'SET_NODE_SIZE'; payload: number }
  | { type: 'SET_EDGE_THICKNESS'; payload: number }
  | { type: 'SET_MAX_NODES'; payload: number }
  | { type: 'TOGGLE_LABELS' }
  | { type: 'TOGGLE_TOOLTIPS' }
  | { type: 'SET_EXPORT_FORMAT'; payload: ExportFormat }
  | { type: 'TOGGLE_METADATA' }
  | { type: 'TOGGLE_COMPRESSION' }
  | { type: 'TOGGLE_AUTO_REFRESH' }
  | { type: 'SET_REFRESH_INTERVAL'; payload: number }
  | { type: 'RESET_TO_DEFAULTS' };

// Default settings
const defaultSettings: SettingsState = {
  // Graph preferences
  graphLayout: 'hierarchical',
  enablePhysics: true,
  nodeSize: 25,
  edgeThickness: 2,
  maxNodes: 1000,
  showLabels: true,
  enableTooltips: true,
  
  // Export preferences
  defaultExportFormat: 'json',
  includeMetadata: true,
  compressExports: false,
  
  // Performance settings
  autoRefresh: false,
  refreshInterval: 30,
};

// Load settings from localStorage
const loadSettings = (): SettingsState => {
  if (typeof window === 'undefined') return defaultSettings;
  
  try {
    const stored = localStorage.getItem('gcphound-settings');
    if (stored) {
      const parsed = JSON.parse(stored);
      // Merge with defaults to handle new settings
      return { ...defaultSettings, ...parsed };
    }
  } catch (error) {
    console.warn('Failed to load settings from localStorage:', error);
  }
  
  return defaultSettings;
};

// Save settings to localStorage
const saveSettings = (settings: SettingsState) => {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem('gcphound-settings', JSON.stringify(settings));
  } catch (error) {
    console.warn('Failed to save settings to localStorage:', error);
  }
};

// Initial state
const initialState = loadSettings();

// Reducer
function settingsReducer(state: SettingsState, action: SettingsAction): SettingsState {
  let newState: SettingsState;
  
  switch (action.type) {
    case 'SET_GRAPH_LAYOUT':
      newState = { ...state, graphLayout: action.payload };
      break;
      
    case 'TOGGLE_PHYSICS':
      newState = { ...state, enablePhysics: !state.enablePhysics };
      break;
      
    case 'SET_NODE_SIZE':
      newState = { ...state, nodeSize: Math.max(10, Math.min(100, action.payload)) };
      break;
      
    case 'SET_EDGE_THICKNESS':
      newState = { ...state, edgeThickness: Math.max(1, Math.min(10, action.payload)) };
      break;
      
    case 'SET_MAX_NODES':
      newState = { ...state, maxNodes: Math.max(100, Math.min(10000, action.payload)) };
      break;
      
    case 'TOGGLE_LABELS':
      newState = { ...state, showLabels: !state.showLabels };
      break;
      
    case 'TOGGLE_TOOLTIPS':
      newState = { ...state, enableTooltips: !state.enableTooltips };
      break;
      
    case 'SET_EXPORT_FORMAT':
      newState = { ...state, defaultExportFormat: action.payload };
      break;
      
    case 'TOGGLE_METADATA':
      newState = { ...state, includeMetadata: !state.includeMetadata };
      break;
      
    case 'TOGGLE_COMPRESSION':
      newState = { ...state, compressExports: !state.compressExports };
      break;
      
    case 'TOGGLE_AUTO_REFRESH':
      newState = { ...state, autoRefresh: !state.autoRefresh };
      break;
      
    case 'SET_REFRESH_INTERVAL':
      newState = { ...state, refreshInterval: Math.max(1, Math.min(1440, action.payload)) };
      break;
      
    case 'RESET_TO_DEFAULTS':
      newState = { ...defaultSettings };
      break;
      
    default:
      return state;
  }
  
  // Save to localStorage
  saveSettings(newState);
  
  return newState;
}

// Context interface
interface SettingsContextType {
  state: SettingsState;
  setGraphLayout: (layout: GraphLayout) => void;
  togglePhysics: () => void;
  setNodeSize: (size: number) => void;
  setEdgeThickness: (thickness: number) => void;
  setMaxNodes: (maxNodes: number) => void;
  toggleLabels: () => void;
  toggleTooltips: () => void;
  setExportFormat: (format: ExportFormat) => void;
  toggleMetadata: () => void;
  toggleCompression: () => void;
  toggleAutoRefresh: () => void;
  setRefreshInterval: (interval: number) => void;
  resetToDefaults: () => void;
}

// Create context
const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

// Provider component
interface SettingsProviderProps {
  children: ReactNode;
}

export function SettingsProvider({ children }: SettingsProviderProps) {
  const [state, dispatch] = useReducer(settingsReducer, initialState);

  const contextValue: SettingsContextType = {
    state,
    setGraphLayout: (layout: GraphLayout) => dispatch({ type: 'SET_GRAPH_LAYOUT', payload: layout }),
    togglePhysics: () => dispatch({ type: 'TOGGLE_PHYSICS' }),
    setNodeSize: (size: number) => dispatch({ type: 'SET_NODE_SIZE', payload: size }),
    setEdgeThickness: (thickness: number) => dispatch({ type: 'SET_EDGE_THICKNESS', payload: thickness }),
    setMaxNodes: (maxNodes: number) => dispatch({ type: 'SET_MAX_NODES', payload: maxNodes }),
    toggleLabels: () => dispatch({ type: 'TOGGLE_LABELS' }),
    toggleTooltips: () => dispatch({ type: 'TOGGLE_TOOLTIPS' }),
    setExportFormat: (format: ExportFormat) => dispatch({ type: 'SET_EXPORT_FORMAT', payload: format }),
    toggleMetadata: () => dispatch({ type: 'TOGGLE_METADATA' }),
    toggleCompression: () => dispatch({ type: 'TOGGLE_COMPRESSION' }),
    toggleAutoRefresh: () => dispatch({ type: 'TOGGLE_AUTO_REFRESH' }),
    setRefreshInterval: (interval: number) => dispatch({ type: 'SET_REFRESH_INTERVAL', payload: interval }),
    resetToDefaults: () => dispatch({ type: 'RESET_TO_DEFAULTS' }),
  };

  return (
    <SettingsContext.Provider value={contextValue}>
      {children}
    </SettingsContext.Provider>
  );
}

// Hook to use the context
export function useSettings() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
} 