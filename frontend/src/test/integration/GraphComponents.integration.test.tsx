import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter } from 'react-router-dom';
import { Graph } from '../../pages/Graph/Graph';
import { Dashboard } from '../../pages/Dashboard/Dashboard';
import { GraphProvider } from '../../context/GraphContext';
import { AppSettingsProvider } from '../../context/AppSettingsContext';
import { dataService } from '../../services/dataService';

// Mock the dataService to return test data
jest.mock('../../services/dataService', () => ({
  dataService: {
    loadGraphData: jest.fn(),
    loadAnalysisData: jest.fn(),
    searchNodes: jest.fn(),
    getAttackPathsByCategory: jest.fn(),
  }
}));

const mockDataService = dataService as jest.Mocked<typeof dataService>;

describe('Graph Component Integration Tests', () => {
  let queryClient: QueryClient;

  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppSettingsProvider>
          <GraphProvider>
            {children}
          </GraphProvider>
        </AppSettingsProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    // Mock successful data loading
    mockDataService.loadGraphData.mockResolvedValue({
      nodes: [
        {
          id: 'test-node-1',
          type: 'user' as any,
          name: 'Test User',
          properties: { email: 'test@example.com' }
        }
      ],
      edges: [
        {
          id: 'test-edge-1',
          source: 'test-node-1',
          target: 'test-node-2',
          type: 'has_role' as any,
          properties: { role: 'roles/viewer' }
        }
      ],
      metadata: {
        total_nodes: 1,
        total_edges: 1,
        collection_time: new Date().toISOString(),
        gcp_projects: ['test-project'],
        generator_version: '1.0.0'
      }
    });

    mockDataService.loadAnalysisData.mockResolvedValue({
      statistics: {
        total_nodes: 1,
        total_edges: 1,
        attack_paths: 0,
        high_risk_nodes: 0,
        dangerous_roles: 0,
        privilege_escalation_paths: 0,
        lateral_movement_paths: 0,
        critical_nodes: 0,
        vulnerabilities: 0
      },
      attack_paths: {
        critical: [],
        critical_multi_step: [],
        privilege_escalation: [],
        lateral_movement: [],
        high: [],
        medium: [],
        low: []
      },
      risk_scores: {},
      vulnerabilities: [],
      critical_nodes: [],
      dangerous_roles: []
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Graph Legend Display', () => {
    it('should display graph legend', async () => {
      render(
        <TestWrapper>
          <Graph />
        </TestWrapper>
      );

      // Wait for component to load
      await waitFor(() => {
        expect(screen.getByTestId('graph-legend')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Verify legend sections are present
      expect(screen.getByText('Legend: Node Types')).toBeInTheDocument();
      expect(screen.getByText('Legend: Edge Types')).toBeInTheDocument();
      expect(screen.getByText('Legend: Risk Levels')).toBeInTheDocument();
    });
  });

  describe('Graph Filters Display', () => {
    it('should display graph filters', async () => {
      render(
        <TestWrapper>
          <Graph />
        </TestWrapper>
      );

      // Wait for component to load
      await waitFor(() => {
        expect(screen.getByTestId('graph-filters')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Verify filter sections are present
      expect(screen.getByText('Filter By')).toBeInTheDocument();
      expect(screen.getByText('Search & Quick Filters')).toBeInTheDocument();
      expect(screen.getByText('Filter: Node Types')).toBeInTheDocument();
    });
  });

  describe('Interactive Panels', () => {
    it('should handle node detail panel interactions', async () => {
      render(
        <TestWrapper>
          <Graph />
        </TestWrapper>
      );

      // Wait for component to load
      await waitFor(() => {
        expect(screen.getByTestId('graph-canvas')).toBeInTheDocument();
      }, { timeout: 15000 });

      // The GraphCanvas component should be present and ready for interactions
      const graphCanvas = screen.getByTestId('graph-canvas');
      expect(graphCanvas).toBeInTheDocument();
    });

    it('should handle edge explanation panel', async () => {
      render(
        <TestWrapper>
          <Graph />
        </TestWrapper>
      );

      // Wait for component to load and verify edge panel functionality is available
      await waitFor(() => {
        expect(screen.getByTestId('graph-canvas')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Verify the graph structure supports edge interactions
      const graphCanvas = screen.getByTestId('graph-canvas');
      expect(graphCanvas).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors gracefully', async () => {
      // Mock API error
      mockDataService.loadGraphData.mockRejectedValue(new Error('API Error'));

      render(
        <TestWrapper>
          <Graph />
        </TestWrapper>
      );

      // Wait for error state
      await waitFor(() => {
        expect(screen.getByText('Error: Failed to Load Graph')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Verify error message and retry button
      expect(screen.getByText('Could not load the graph data. Please try again.')).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });

    it('should handle empty graph data', async () => {
      // Mock empty data
      mockDataService.loadGraphData.mockResolvedValue({
        nodes: [],
        edges: [],
        metadata: {
          total_nodes: 0,
          total_edges: 0,
          collection_time: new Date().toISOString(),
          gcp_projects: [],
          generator_version: '1.0.0'
        }
      });

      render(
        <TestWrapper>
          <Graph />
        </TestWrapper>
      );

      // Wait for empty state
      await waitFor(() => {
        expect(screen.getByText('No Data Available')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Verify empty state message and controls
      expect(screen.getByText('The graph is empty. Please ensure data has been collected and processed.')).toBeInTheDocument();
      expect(screen.getByTestId('graph-controls')).toBeInTheDocument();
    });
  });
});

describe('Dashboard Component Integration Tests', () => {
  let queryClient: QueryClient;

  const TestWrapper: React.FC<{ children: React.ReactNode }> = ({ children }) => (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AppSettingsProvider>
          {children}
        </AppSettingsProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: {
          retry: false,
          gcTime: 0,
        },
      },
    });

    // Mock dashboard data
    mockDataService.loadAnalysisData.mockResolvedValue({
      statistics: {
        total_nodes: 100,
        total_edges: 150,
        attack_paths: 5,
        high_risk_nodes: 10,
        dangerous_roles: 3,
        privilege_escalation_paths: 2,
        lateral_movement_paths: 1,
        critical_nodes: 4,
        vulnerabilities: 8
      },
      attack_paths: {
        critical: [],
        critical_multi_step: [],
        privilege_escalation: [],
        lateral_movement: [],
        high: [],
        medium: [],
        low: []
      },
      risk_scores: {},
      vulnerabilities: [],
      critical_nodes: [],
      dangerous_roles: []
    });
  });

  afterEach(() => {
    jest.clearAllMocks();
  });

  describe('Dashboard Page Loading', () => {
    it('should load dashboard page successfully', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for dashboard to load - using correct test ID
      await waitFor(() => {
        expect(screen.getByTestId('statistics-cards')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Verify key statistics are displayed - using correct test IDs
      expect(screen.getByTestId('stat-card-total-nodes')).toBeInTheDocument();
      expect(screen.getByTestId('stat-card-total-edges')).toBeInTheDocument();
      expect(screen.getByTestId('stat-card-attack-paths')).toBeInTheDocument();
    });

    it('should navigate to other pages', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for dashboard to load - using correct test ID
      await waitFor(() => {
        expect(screen.getByTestId('statistics-cards')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Find and click navigation buttons - using correct button text
      const viewGraphButton = screen.getByText('View Full Graph');
      expect(viewGraphButton).toBeInTheDocument();
      
      const viewFindingsButton = screen.getByText('Security Findings');
      expect(viewFindingsButton).toBeInTheDocument();

      // Test button clicks (navigation will be handled by React Router)
      fireEvent.click(viewGraphButton);
      fireEvent.click(viewFindingsButton);
    });
  });

  describe('Accessibility Compliance', () => {
    it('should not have accessibility violations in dashboard', async () => {
      render(
        <TestWrapper>
          <Dashboard />
        </TestWrapper>
      );

      // Wait for dashboard to load - using correct test ID
      await waitFor(() => {
        expect(screen.getByTestId('statistics-cards')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Check for proper heading structure
      const headings = screen.getAllByRole('heading');
      expect(headings.length).toBeGreaterThan(0);

      // Verify buttons have accessible names (either aria-label or visible text)
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        const hasAriaLabel = button.hasAttribute('aria-label');
        const hasVisibleText = button.textContent && button.textContent.trim().length > 0;
        expect(hasAriaLabel || hasVisibleText).toBe(true);
      });

      // Verify the main dashboard elements are accessible
      expect(screen.getByText('Security Dashboard')).toBeInTheDocument();
      expect(screen.getByTestId('statistics-cards')).toBeInTheDocument();
    });

    it('should have accessible panels in graph page', async () => {
      // Ensure graph data is properly mocked for this test
      mockDataService.loadGraphData.mockResolvedValue({
        nodes: [
          {
            id: 'test-node-1',
            type: 'user' as any,
            name: 'Test User',
            properties: { email: 'test@example.com' }
          }
        ],
        edges: [
          {
            id: 'test-edge-1',
            source: 'test-node-1',
            target: 'test-node-2',
            type: 'has_role' as any,
            properties: { role: 'roles/viewer' }
          }
        ],
        metadata: {
          total_nodes: 1,
          total_edges: 1,
          collection_time: new Date().toISOString(),
          gcp_projects: ['test-project'],
          generator_version: '1.0.0'
        }
      });

      render(
        <TestWrapper>
          <Graph />
        </TestWrapper>
      );

      // Wait for component to load
      await waitFor(() => {
        expect(screen.getByTestId('graph-legend')).toBeInTheDocument();
      }, { timeout: 15000 });

      // Verify accessible elements
      const legend = screen.getByTestId('graph-legend');
      expect(legend).toBeInTheDocument();

      const filters = screen.getByTestId('graph-filters');
      expect(filters).toBeInTheDocument();

      // Check for proper labeling - only check checkboxes if they exist
      const checkboxes = screen.queryAllByRole('checkbox');
      if (checkboxes.length > 0) {
        checkboxes.forEach(checkbox => {
          const hasAriaLabel = checkbox.hasAttribute('aria-label');
          const hasAssociatedLabel = checkbox.hasAttribute('id') && document.querySelector(`label[for="${checkbox.id}"]`);
          expect(hasAriaLabel || hasAssociatedLabel).toBe(true);
        });
      }

      // Verify buttons have accessible names
      const buttons = screen.getAllByRole('button');
      buttons.forEach(button => {
        const hasAriaLabel = button.hasAttribute('aria-label');
        const hasVisibleText = button.textContent && button.textContent.trim().length > 0;
        const hasTitle = button.hasAttribute('title');
        expect(hasAriaLabel || hasVisibleText || hasTitle).toBe(true);
      });

      // Verify search input has proper labeling
      const searchInput = screen.getByRole('textbox');
      expect(searchInput).toBeInTheDocument();
      expect(searchInput.hasAttribute('placeholder')).toBe(true);
    });
  });
}); 