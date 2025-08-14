# GCPHound Technical Requirements & Integration Documentation

## Overview

This document defines the technical requirements, integration points, and implementation considerations for the React frontend refactoring project.

## Frontend Technology Requirements

### Core Dependencies

#### React Ecosystem
- **React**: v18.2+ (latest stable)
- **TypeScript**: v5.0+ for type safety
- **React DOM**: v18.2+ for rendering
- **React Router**: v6.8+ for client-side routing

#### Styling & UI Components
- **Tailwind CSS**: v3.3+ for utility-first styling
- **shadcn/ui**: Component library for consistent design system
- **Lucide React**: v0.263+ for modern icons
- **clsx**: For conditional CSS classes
- **tailwind-merge**: For merging Tailwind classes

#### Visualization & Data
- **vis.js/vis-network**: v9.1.2 (maintain compatibility with current implementation)
- **recharts**: v2.8+ for charts and graphs
- **D3.js**: v7.8+ for complex data visualization (if needed)

#### State Management & Data Fetching
- **React Context API**: For global state management
- **React Query/TanStack Query**: v4.29+ for data fetching and caching
- **Zustand**: v4.3+ for lightweight state management (alternative to Context)

#### Development & Build Tools
- **Vite**: v4.4+ for fast development and building
- **ESLint**: v8.45+ for code linting
- **Prettier**: v3.0+ for code formatting
- **TypeScript ESLint**: For TypeScript-specific linting

#### Testing
- **Vitest**: For unit testing (Vite-native)
- **React Testing Library**: For component testing
- **jsdom**: For DOM environment in tests
- **Playwright**: For end-to-end testing

### Development Environment Setup

#### Node.js Requirements
- **Node.js**: v18.16+ or v20.5+ (LTS versions)
- **npm**: v9.5+ or **yarn**: v1.22+ or **pnpm**: v8.6+

#### IDE/Editor Configuration
- **VS Code Extensions**:
  - ES7+ React/Redux/React-Native snippets
  - Tailwind CSS IntelliSense
  - TypeScript Importer
  - Auto Rename Tag
  - Prettier - Code formatter
  - ESLint

#### Browser Support
- **Modern Browsers**: Chrome 90+, Firefox 88+, Safari 14+, Edge 90+
- **ES2020+ Features**: Native support required
- **WebGL**: Required for vis.js network visualization

## Architecture & Project Structure

### Recommended Directory Structure
```
frontend/
├── public/                     # Static assets
│   ├── favicon.ico
│   └── index.html
├── src/
│   ├── components/            # Reusable UI components
│   │   ├── ui/               # shadcn/ui components
│   │   ├── common/           # Common components
│   │   ├── graph/            # Graph-specific components
│   │   └── panels/           # Interactive panels
│   ├── pages/                # Page components
│   │   ├── Dashboard/
│   │   ├── Graph/
│   │   ├── Findings/
│   │   └── Settings/
│   ├── hooks/                # Custom React hooks
│   ├── services/             # API and data services
│   ├── types/                # TypeScript type definitions
│   ├── utils/                # Utility functions
│   ├── styles/               # Global styles and Tailwind config
│   ├── lib/                  # Third-party library configurations
│   ├── context/              # React Context providers
│   └── App.tsx               # Root component
├── tests/                     # Test files
├── docs/                      # Component documentation
├── package.json
├── tsconfig.json
├── tailwind.config.js
├── vite.config.ts
└── README.md
```

### Key Architecture Patterns

#### Component Architecture
- **Atomic Design**: Organize components from atoms to organisms
- **Compound Components**: For complex UI patterns (e.g., panel systems)
- **Render Props**: For sharing logic between components
- **Higher-Order Components**: For cross-cutting concerns

#### State Management Strategy
- **Local State**: useState for component-specific state
- **Global State**: Context API for app-wide state
- **Server State**: React Query for API data management
- **URL State**: React Router for navigation state

#### Data Flow Patterns
- **Unidirectional Data Flow**: Props down, events up
- **Event-Driven Architecture**: Custom events for complex interactions
- **Observer Pattern**: For graph node/edge selection updates

## Integration with Python Backend

### Data Loading Strategy

#### File-Based Integration (Phase 1)
```typescript
// Service for loading JSON data files
class DataService {
  async loadGraphData(): Promise<GraphData> {
    const response = await fetch('/data/graph/latest.json');
    return response.json();
  }
  
  async loadAnalysisData(): Promise<AnalysisResults> {
    const response = await fetch('/data/analysis/latest.json');
    return response.json();
  }
}
```

#### Future HTTP API Integration
```typescript
// API client for future REST endpoints
class APIClient {
  constructor(private baseURL: string = '/api/v1') {}
  
  async getGraph(timestamp?: string): Promise<GraphData> {
    const url = timestamp ? `${this.baseURL}/graph/${timestamp}` : `${this.baseURL}/graph/latest`;
    const response = await fetch(url);
    return response.json();
  }
}
```

### Data Validation & Error Handling

#### TypeScript Interfaces
```typescript
// Type guards for runtime validation
function isValidNode(obj: any): obj is Node {
  return obj && 
    typeof obj.id === 'string' &&
    typeof obj.type === 'string' &&
    typeof obj.name === 'string' &&
    obj.properties !== undefined;
}

// Validation service
class ValidationService {
  validateGraphData(data: any): GraphData {
    if (!Array.isArray(data.nodes) || !Array.isArray(data.edges)) {
      throw new Error('Invalid graph data structure');
    }
    return data as GraphData;
  }
}
```

#### Error Boundary Implementation
```typescript
class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('Frontend error:', error, errorInfo);
    // Report to error tracking service
  }
}
```

## Visualization Library Integration

### vis.js Network Configuration

#### React Component Wrapper
```typescript
interface NetworkGraphProps {
  nodes: Node[];
  edges: Edge[];
  options?: NetworkOptions;
  onNodeClick?: (nodeId: string) => void;
  onEdgeClick?: (edgeId: string) => void;
}

const NetworkGraph: React.FC<NetworkGraphProps> = ({
  nodes,
  edges,
  options,
  onNodeClick,
  onEdgeClick
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<Network | null>(null);
  
  useEffect(() => {
    if (containerRef.current) {
      const data = { nodes: new DataSet(nodes), edges: new DataSet(edges) };
      networkRef.current = new Network(containerRef.current, data, options);
      
      if (onNodeClick) {
        networkRef.current.on('click', (params) => {
          if (params.nodes.length > 0) {
            onNodeClick(params.nodes[0]);
          }
        });
      }
    }
    
    return () => {
      networkRef.current?.destroy();
    };
  }, [nodes, edges, options, onNodeClick]);
  
  return <div ref={containerRef} className="w-full h-full" />;
};
```

#### Configuration Management
```typescript
const defaultNetworkOptions: NetworkOptions = {
  nodes: {
    shape: 'dot',
    size: 16,
    font: { size: 14, face: 'Inter' },
    borderWidth: 2,
    shadow: true
  },
  edges: {
    width: 2,
    color: { inherit: 'from' },
    smooth: { type: 'continuous' },
    arrows: { to: { enabled: true, scaleFactor: 1.2 } }
  },
  physics: {
    enabled: true,
    hierarchicalRepulsion: {
      centralGravity: 0.0,
      springLength: 100,
      springConstant: 0.01,
      nodeDistance: 120,
      damping: 0.09
    }
  },
  layout: {
    hierarchical: {
      enabled: true,
      levelSeparation: 150,
      nodeSpacing: 100,
      treeSpacing: 200,
      blockShifting: true,
      edgeMinimization: true,
      parentCentralization: true,
      direction: 'UD',
      sortMethod: 'directed'
    }
  }
};
```

### Performance Optimization

#### Large Dataset Handling
```typescript
class GraphOptimizer {
  static optimizeForLargeDatasets(
    nodes: Node[], 
    edges: Edge[], 
    maxNodes: number = 1000
  ): { nodes: Node[], edges: Edge[] } {
    if (nodes.length <= maxNodes) {
      return { nodes, edges };
    }
    
    // Implement clustering or filtering logic
    const highRiskNodes = nodes
      .filter(node => this.getNodeRiskScore(node) > 0.6)
      .slice(0, maxNodes);
    
    const relevantEdges = edges.filter(edge => 
      highRiskNodes.some(node => node.id === edge.source) ||
      highRiskNodes.some(node => node.id === edge.target)
    );
    
    return { nodes: highRiskNodes, edges: relevantEdges };
  }
}
```

#### Virtual Scrolling for Lists
```typescript
import { FixedSizeList as List } from 'react-window';

const AttackPathsList: React.FC<{ paths: AttackPath[] }> = ({ paths }) => {
  const Row = ({ index, style }: { index: number, style: CSSProperties }) => (
    <div style={style}>
      <AttackPathItem path={paths[index]} />
    </div>
  );
  
  return (
    <List
      height={600}
      itemCount={paths.length}
      itemSize={120}
      itemData={paths}
    >
      {Row}
    </List>
  );
};
```

## State Management Implementation

### Global State Structure
```typescript
interface AppState {
  graph: {
    data: GraphData | null;
    selectedNodes: string[];
    selectedEdges: string[];
    filters: GraphFilters;
    loading: boolean;
    error: string | null;
  };
  analysis: {
    results: AnalysisResults | null;
    attackPaths: AttackPath[];
    statistics: Statistics | null;
    loading: boolean;
    error: string | null;
  };
  ui: {
    sidebarOpen: boolean;
    activeTab: TabType;
    modalState: ModalState;
    theme: ThemeType;
  };
  settings: {
    autoRefresh: boolean;
    refreshInterval: number;
    displayOptions: DisplayOptions;
  };
}
```

### Context Providers
```typescript
const GraphContext = createContext<{
  state: GraphState;
  actions: GraphActions;
} | null>(null);

export const GraphProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(graphReducer, initialGraphState);
  
  const actions = useMemo(() => ({
    loadGraph: () => dispatch({ type: 'LOAD_GRAPH_START' }),
    selectNode: (nodeId: string) => dispatch({ type: 'SELECT_NODE', payload: nodeId }),
    setFilters: (filters: GraphFilters) => dispatch({ type: 'SET_FILTERS', payload: filters })
  }), []);
  
  return (
    <GraphContext.Provider value={{ state, actions }}>
      {children}
    </GraphContext.Provider>
  );
};
```

## Testing Strategy

### Unit Testing
```typescript
// Component testing with React Testing Library
describe('NetworkGraph', () => {
  it('renders nodes and edges correctly', () => {
    const mockNodes = [{ id: '1', type: 'user', name: 'test' }];
    const mockEdges = [{ source: '1', target: '2', type: 'has_role' }];
    
    render(<NetworkGraph nodes={mockNodes} edges={mockEdges} />);
    
    expect(screen.getByRole('graphics-document')).toBeInTheDocument();
  });
  
  it('calls onNodeClick when node is clicked', async () => {
    const onNodeClick = jest.fn();
    render(<NetworkGraph onNodeClick={onNodeClick} />);
    
    // Simulate vis.js click event
    fireEvent.click(screen.getByTestId('network-container'));
    
    await waitFor(() => {
      expect(onNodeClick).toHaveBeenCalledWith('node-id');
    });
  });
});
```

### Integration Testing
```typescript
// API integration testing
describe('DataService', () => {
  beforeEach(() => {
    fetchMock.resetMocks();
  });
  
  it('loads graph data successfully', async () => {
    const mockData = { nodes: [], edges: [], metadata: {} };
    fetchMock.mockResponseOnce(JSON.stringify(mockData));
    
    const service = new DataService();
    const result = await service.loadGraphData();
    
    expect(result).toEqual(mockData);
    expect(fetchMock).toHaveBeenCalledWith('/data/graph/latest.json');
  });
});
```

### E2E Testing with Playwright
```typescript
// End-to-end testing
test('user can explore attack paths', async ({ page }) => {
  await page.goto('/dashboard');
  
  // Wait for graph to load
  await page.waitForSelector('[data-testid="network-graph"]');
  
  // Click on attack paths tab
  await page.click('[data-testid="attack-paths-tab"]');
  
  // Verify attack paths are displayed
  await expect(page.locator('[data-testid="attack-path-item"]')).toHaveCount(4);
  
  // Click on first attack path
  await page.click('[data-testid="attack-path-item"]:first-child');
  
  // Verify path is highlighted in graph
  await expect(page.locator('[data-testid="highlighted-path"]')).toBeVisible();
});
```

## Build & Deployment Configuration

### Vite Configuration
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
    sourcemap: true,
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'visualization': ['vis-network', 'recharts'],
          'ui': ['@radix-ui/react-dialog', '@radix-ui/react-tabs']
        }
      }
    }
  },
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/data': 'http://localhost:8000'
    }
  }
});
```

### Environment Configuration
```typescript
// Environment variables
interface EnvironmentConfig {
  NODE_ENV: 'development' | 'production' | 'test';
  VITE_API_BASE_URL: string;
  VITE_DATA_PATH: string;
  VITE_ENABLE_MOCK_DATA: boolean;
}

const config: EnvironmentConfig = {
  NODE_ENV: import.meta.env.NODE_ENV,
  VITE_API_BASE_URL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  VITE_DATA_PATH: import.meta.env.VITE_DATA_PATH || '/data',
  VITE_ENABLE_MOCK_DATA: import.meta.env.VITE_ENABLE_MOCK_DATA === 'true'
};
```

## Security Considerations

### Content Security Policy
```html
<!-- CSP header for production -->
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline'; 
               style-src 'self' 'unsafe-inline'; 
               img-src 'self' data:; 
               connect-src 'self';">
```

### Input Validation
```typescript
// Sanitize user inputs
import DOMPurify from 'dompurify';

const sanitizeInput = (input: string): string => {
  return DOMPurify.sanitize(input, { 
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: []
  });
};
```

### Error Information Disclosure
```typescript
// Error handling that doesn't expose sensitive information
const handleError = (error: Error, context: string): void => {
  // Log full error details server-side
  console.error(`[${context}]`, error);
  
  // Show generic message to user
  toast.error('An unexpected error occurred. Please try again.');
};
```

This technical documentation provides the foundation for implementing a robust, maintainable, and secure React frontend for GCPHound while preserving all existing functionality and enhancing the user experience. 