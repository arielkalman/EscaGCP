import { render, RenderOptions } from '@testing-library/react';
import { ReactElement, ReactNode } from 'react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import userEvent from '@testing-library/user-event';
import { AppSettingsProvider } from '@/context/AppSettingsContext';

// Import contexts that need to be provided in tests
// Note: These would be imported from the actual context files
// import { ThemeProvider } from '@/context/ThemeContext';
// import { SettingsProvider } from '@/context/SettingsContext';
// import { GraphProvider } from '@/context/GraphContext';

interface AllTheProvidersProps {
  children: ReactNode;
}

/**
 * Test wrapper component that provides all necessary context providers
 */
const AllTheProviders = ({ children }: AllTheProvidersProps) => {
  // Create a fresh QueryClient for each test
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <BrowserRouter>
      <QueryClientProvider client={queryClient}>
        <AppSettingsProvider>
          {/* Add other providers here as they become available */}
          {/* <ThemeProvider>
            <SettingsProvider>
              <GraphProvider>
                {children}
              </GraphProvider>
            </SettingsProvider>
          </ThemeProvider> */}
          {children}
        </AppSettingsProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );
};

/**
 * Custom render function that includes all providers
 */
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => {
  return render(ui, { wrapper: AllTheProviders, ...options });
};

/**
 * Custom render function for components that need specific providers
 */
const renderWithProviders = (
  ui: ReactElement,
  {
    queryClient,
    initialEntries = ['/'],
    ...renderOptions
  }: {
    queryClient?: QueryClient;
    initialEntries?: string[];
  } & Omit<RenderOptions, 'wrapper'> = {}
) => {
  const testQueryClient = queryClient || new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        staleTime: Infinity,
      },
      mutations: {
        retry: false,
      },
    },
  });

  const Wrapper = ({ children }: { children: ReactNode }) => (
    <BrowserRouter>
      <QueryClientProvider client={testQueryClient}>
        <AppSettingsProvider>
          {children}
        </AppSettingsProvider>
      </QueryClientProvider>
    </BrowserRouter>
  );

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

/**
 * Setup user event for tests
 */
const setupUser = () => userEvent.setup();

/**
 * Common test data generators
 */
const createMockNode = (overrides = {}) => ({
  id: 'test-node-id',
  type: 'user',
  name: 'test-user@example.com',
  properties: {
    email: 'test-user@example.com',
    riskScore: 0.5,
  },
  ...overrides,
});

const createMockEdge = (overrides = {}) => ({
  id: 'test-edge-id',
  source: 'source-node',
  target: 'target-node',
  type: 'has_role',
  properties: {
    role: 'roles/viewer',
    riskScore: 0.3,
  },
  ...overrides,
});

const createMockAttackPath = (overrides = {}) => ({
  id: 'test-path-id',
  source: 'user:attacker@example.com',
  target: 'project:production',
  path: ['user:attacker@example.com', 'project:production'],
  riskScore: 0.8,
  category: 'privilege_escalation',
  techniques: ['direct_access'],
  description: 'Test attack path',
  ...overrides,
});

/**
 * Wait for async operations to complete
 */
const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0));

/**
 * Mock localStorage for tests
 */
const mockLocalStorage = () => {
  const storage: Record<string, string> = {};
  
  return {
    getItem: jest.fn((key: string) => storage[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      storage[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete storage[key];
    }),
    clear: jest.fn(() => {
      Object.keys(storage).forEach(key => delete storage[key]);
    }),
  };
};

/**
 * Mock window.matchMedia for responsive tests
 */
const mockMatchMedia = (query: string) => ({
  matches: false,
  media: query,
  onchange: null,
  addListener: jest.fn(), // deprecated
  removeListener: jest.fn(), // deprecated
  addEventListener: jest.fn(),
  removeEventListener: jest.fn(),
  dispatchEvent: jest.fn(),
});

/**
 * Create mock theme context value
 */
const createMockThemeContext = (overrides = {}) => ({
  theme: 'light',
  setTheme: jest.fn(),
  toggleTheme: jest.fn(),
  isDark: false,
  isLight: true,
  systemTheme: 'light',
  ...overrides,
});

/**
 * Create mock settings context value
 */
const createMockSettingsContext = (overrides = {}) => ({
  settings: {
    theme: 'light',
    graphLayout: 'hierarchical',
    nodeSize: 20,
    edgeThickness: 2,
    maxNodes: 1000,
    showLabels: true,
    showTooltips: true,
    enablePhysics: true,
    exportFormat: 'json',
    includeMetadata: true,
    enableCompression: false,
    autoRefresh: false,
    refreshInterval: 300,
  },
  updateSettings: jest.fn(),
  resetSettings: jest.fn(),
  ...overrides,
});

/**
 * Create mock app settings context value
 */
const createMockAppSettingsContext = (overrides = {}) => ({
  settings: {
    showGhostUsers: false,
    autoRefresh: false,
    refreshInterval: 30000,
    theme: 'system' as const,
  },
  updateSetting: jest.fn(),
  toggleGhostUsers: jest.fn(),
  ...overrides,
});

/**
 * Create mock graph context value
 */
const createMockGraphContext = (overrides = {}) => ({
  graphData: null,
  isLoading: false,
  error: null,
  selectedNode: null,
  selectedEdge: null,
  selectedAttackPath: null,
  isNodePanelOpen: false,
  isEdgePanelOpen: false,
  isAttackPathPanelOpen: false,
  highlightedNodes: new Set(),
  highlightedEdges: new Set(),
  selectNode: jest.fn(),
  selectEdge: jest.fn(),
  selectAttackPath: jest.fn(),
  clearSelection: jest.fn(),
  openNodePanel: jest.fn(),
  closeNodePanel: jest.fn(),
  openEdgePanel: jest.fn(),
  closeEdgePanel: jest.fn(),
  openAttackPathPanel: jest.fn(),
  closeAttackPathPanel: jest.fn(),
  highlightNodes: jest.fn(),
  highlightEdges: jest.fn(),
  clearHighlights: jest.fn(),
  ...overrides,
});

/**
 * Accessibility testing helpers
 */
const checkA11y = async (container: HTMLElement) => {
  // This would integrate with axe-core for accessibility testing
  // For now, we'll do basic checks
  const elements = container.querySelectorAll('button, input, select, textarea, a, [tabindex]');
  const issues: string[] = [];

  elements.forEach((element) => {
    // Check for missing labels
    if ((element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') && 
        !element.getAttribute('aria-label') && 
        !element.getAttribute('aria-labelledby') &&
        !element.closest('label')) {
      issues.push(`Element ${element.tagName} missing accessible label`);
    }

    // Check for missing alt text on images
    if (element.tagName === 'IMG' && !element.getAttribute('alt')) {
      issues.push('Image missing alt text');
    }
  });

  return issues;
};

/**
 * Performance testing helpers
 */
const measureRenderTime = async (renderFn: () => void) => {
  const start = performance.now();
  renderFn();
  const end = performance.now();
  return end - start;
};

/**
 * Network request mocking helpers
 */
const createMockFetch = (mockResponse: any) => {
  return jest.fn().mockResolvedValue({
    ok: true,
    status: 200,
    json: async () => mockResponse,
    text: async () => JSON.stringify(mockResponse),
  });
};

// Export everything
export * from '@testing-library/react';
export { 
  customRender as render, 
  renderWithProviders,
  setupUser,
  waitForLoadingToFinish,
  mockLocalStorage,
  mockMatchMedia,
  createMockThemeContext,
  createMockSettingsContext,
  createMockAppSettingsContext,
  createMockGraphContext,
  createMockNode,
  createMockEdge,
  createMockAttackPath,
  checkA11y,
  measureRenderTime,
  createMockFetch,
}; 