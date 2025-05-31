import { test, expect, Page } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';

// Helper to setup graph test data
async function setupGraphData(page: Page, scenario: string = 'small_graph_high_risk') {
  await page.route('**/api/graph', route => {
    const testData = {
      small_graph_high_risk: {
        nodes: [
          {
            id: 'user:attacker@external.com',
            type: 'user',
            name: 'attacker@external.com',
            properties: { email: 'attacker@external.com', riskScore: 0.9 }
          },
          {
            id: 'service_account:sa@project.iam.gserviceaccount.com',
            type: 'service_account',
            name: 'sa@project.iam.gserviceaccount.com',
            properties: { email: 'sa@project.iam.gserviceaccount.com', riskScore: 0.95 }
          },
          {
            id: 'project:production-project',
            type: 'project',
            name: 'production-project',
            properties: { projectId: 'production-project', riskScore: 0.8 }
          }
        ],
        edges: [
          {
            source: 'user:attacker@external.com',
            target: 'service_account:sa@project.iam.gserviceaccount.com',
            type: 'can_impersonate_sa',
            properties: { permission: 'iam.serviceAccounts.getAccessToken', riskScore: 0.9 }
          },
          {
            source: 'service_account:sa@project.iam.gserviceaccount.com',
            target: 'project:production-project',
            type: 'has_role',
            properties: { role: 'roles/owner', riskScore: 0.95 }
          }
        ],
        metadata: {
          total_nodes: 3,
          total_edges: 2,
          collection_time: new Date().toISOString(),
          gcp_projects: ['production-project']
        }
      }
    };

    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(testData[scenario] || testData.small_graph_high_risk)
    });
  });

  // Mock attack paths API
  await page.route('**/api/attack-paths', route => {
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify([
        {
          id: 'path_1',
          source: 'user:attacker@external.com',
          target: 'project:production-project',
          path: ['user:attacker@external.com', 'service_account:sa@project.iam.gserviceaccount.com', 'project:production-project'],
          riskScore: 0.95,
          category: 'privilege_escalation',
          techniques: ['service_account_impersonation'],
          description: 'External user can escalate to project owner via service account impersonation'
        }
      ])
    });
  });
}

test.describe('Graph Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupGraphData(page);
    await page.goto('/graph');
  });

  test('should load graph page successfully', async ({ page }) => {
    await expect(page).toHaveURL('/graph');
    await expect(page.locator('h1')).toContainText(/graph/i);
  });

  test('should display graph canvas', async ({ page }) => {
    // Wait for graph to load
    await page.waitForSelector('[data-testid="graph-canvas"]', { timeout: 15000 });
    
    const graphCanvas = page.getByTestId('graph-canvas');
    await expect(graphCanvas).toBeVisible();
    
    // Should have a canvas or svg element for vis.js
    const visElement = graphCanvas.locator('canvas, svg').first();
    await expect(visElement).toBeVisible();
  });

  test('should display graph controls', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-controls"]');
    
    // Check for zoom controls
    await expect(page.getByRole('button', { name: /zoom in/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /zoom out/i })).toBeVisible();
    await expect(page.getByRole('button', { name: /reset/i })).toBeVisible();
  });

  test('should display graph legend', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-legend"]');
    
    const legend = page.getByTestId('graph-legend');
    
    // Check for node type legend within the legend container
    await expect(legend.getByText(/node types/i)).toBeVisible();
    await expect(legend.getByText(/edge types/i)).toBeVisible();
    await expect(legend.getByText(/risk levels/i)).toBeVisible();
  });

  test('should display graph filters', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-filters"]');
    
    const filters = page.getByTestId('graph-filters');
    
    // Check for filter controls within the filters container
    await expect(filters.getByText(/filter by/i)).toBeVisible();
    
    // Should have node type filters
    await expect(filters.getByText(/users/i)).toBeVisible();
    await expect(filters.getByText(/service accounts/i)).toBeVisible();
    await expect(filters.getByText(/projects/i)).toBeVisible();
  });

  test('should render nodes on the graph', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-canvas"]');
    
    // Wait for vis.js to render
    await page.waitForTimeout(2000);
    
    // Check that nodes are rendered (this depends on vis.js implementation)
    // We can check for specific node elements or use custom data attributes
    const nodeElements = page.locator('[data-node-id]');
    await expect(nodeElements.first()).toBeVisible({ timeout: 10000 });
  });

  test('should handle node clicks', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-canvas"]');
    await page.waitForTimeout(2000);
    
    // Click on a node (this may require custom event handling)
    const graphCanvas = page.getByTestId('graph-canvas');
    await graphCanvas.click({ position: { x: 200, y: 200 } });
    
    // Should open node detail panel
    await expect(page.getByTestId('node-detail-panel')).toBeVisible({ timeout: 5000 });
  });

  test('should handle edge clicks', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-canvas"]');
    await page.waitForTimeout(2000);
    
    // Click on an edge area
    const graphCanvas = page.getByTestId('graph-canvas');
    await graphCanvas.click({ position: { x: 300, y: 250 } });
    
    // Should open edge explanation panel (if an edge was clicked)
    // This test might need adjustment based on actual graph rendering
  });

  test('should handle zoom controls', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-controls"]');
    
    const zoomInButton = page.getByRole('button', { name: /zoom in/i });
    const zoomOutButton = page.getByRole('button', { name: /zoom out/i });
    const resetButton = page.getByRole('button', { name: /reset/i });
    
    // Test zoom in
    await zoomInButton.click();
    await page.waitForTimeout(500);
    
    // Test zoom out
    await zoomOutButton.click();
    await page.waitForTimeout(500);
    
    // Test reset
    await resetButton.click();
    await page.waitForTimeout(500);
    
    // All operations should complete without errors
    const errorMessage = page.getByText(/error/i);
    await expect(errorMessage).not.toBeVisible();
  });

  test('should apply node type filters', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-filters"]');
    
    // Find and click user filter checkbox
    const userFilter = page.getByRole('checkbox', { name: /users/i });
    
    if (await userFilter.isVisible()) {
      // Uncheck users filter
      await userFilter.uncheck();
      
      // Wait for graph to update
      await page.waitForTimeout(1000);
      
      // Graph should update (this test would need to verify node visibility)
      // For now, just ensure no errors occurred
      const errorMessage = page.getByText(/error/i);
      await expect(errorMessage).not.toBeVisible();
    }
  });

  test('should handle search functionality', async ({ page }) => {
    const searchInput = page.getByRole('textbox', { name: /search/i });
    
    if (await searchInput.isVisible()) {
      await searchInput.fill('attacker@external.com');
      await page.keyboard.press('Enter');
      
      // Should highlight or focus on the searched node
      await page.waitForTimeout(1000);
      
      // Verify no errors
      const errorMessage = page.getByText(/error/i);
      await expect(errorMessage).not.toBeVisible();
    }
  });

  test('should be responsive', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-canvas"]');
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByTestId('graph-canvas')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.getByTestId('graph-canvas')).toBeVisible();
  });

  test.describe('Interactive Panels', () => {
    test('should open and close node detail panel', async ({ page }) => {
      await page.waitForSelector('[data-testid="graph-canvas"]');
      
      // First, check that the panel is not visible initially
      await expect(page.getByTestId('node-detail-panel')).not.toBeVisible();
      
      // Simulate node click (this might require custom implementation)
      await page.evaluate(() => {
        // Dispatch custom event to simulate node selection
        const nodeData = {
          id: 'user:attacker@external.com',
          type: 'user',
          name: 'attacker@external.com',
          properties: { email: 'attacker@external.com', riskScore: 0.9 }
        };
        
        console.log('Test: Dispatching nodeSelected event with:', nodeData);
        
        window.dispatchEvent(new CustomEvent('nodeSelected', {
          detail: {
            nodeId: nodeData.id,
            nodeData: nodeData
          }
        }));
      });
      
      // Wait a bit for the event to process
      await page.waitForTimeout(1000);
      
      // Check if panel exists in DOM first
      const panel = page.getByTestId('node-detail-panel');
      const panelExists = await panel.count() > 0;
      console.log('Panel exists in DOM:', panelExists);
      
      // Also check for the debug container
      const debugContainer = page.getByTestId('debug-panel-container');
      const debugExists = await debugContainer.count() > 0;
      console.log('Debug container exists:', debugExists);
      
      if (panelExists) {
        // Should open node detail panel
        await expect(panel).toBeVisible({ timeout: 5000 });
        
        // Should display node information
        await expect(page.getByText('attacker@external.com')).toBeVisible();
        
        // Close panel
        const closeButton = page.getByRole('button', { name: /close/i });
        await closeButton.click();
        
        // Panel should be closed
        await expect(panel).toBeHidden();
      } else {
        // If panel doesn't exist, let's check what elements DO exist
        const allTestIds = await page.evaluate(() => {
          return Array.from(document.querySelectorAll('[data-testid]'))
            .map(el => el.getAttribute('data-testid'));
        });
        console.log('Available test IDs:', allTestIds);
        
        // For now, just check that the event was dispatched (this test will still fail but with better info)
        await expect(panel).toBeVisible({ timeout: 1000 });
      }
    });

    test('should display tabbed content in node panel', async ({ page }) => {
      // Open node panel
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('nodeSelected', {
          detail: {
            nodeId: 'user:attacker@external.com',
            nodeData: {
              id: 'user:attacker@external.com',
              type: 'user',
              name: 'attacker@external.com',
              properties: { email: 'attacker@external.com', riskScore: 0.9 }
            }
          }
        }));
      });
      
      await expect(page.getByTestId('node-detail-panel')).toBeVisible();
      
      // Check for tabs
      await expect(page.getByRole('tab', { name: /overview/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /permissions/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /relationships/i })).toBeVisible();
      await expect(page.getByRole('tab', { name: /activity/i })).toBeVisible();
      
      // Click on different tabs
      await page.getByRole('tab', { name: /permissions/i }).click();
      await expect(page.getByText(/permissions/i)).toBeVisible();
      
      await page.getByRole('tab', { name: /relationships/i }).click();
      await expect(page.getByText(/relationships/i)).toBeVisible();
    });

    test('should open edge explanation panel', async ({ page }) => {
      await page.waitForSelector('[data-testid="graph-canvas"]');
      
      // Simulate edge click
      await page.evaluate(() => {
        window.dispatchEvent(new CustomEvent('edgeSelected', {
          detail: {
            edgeId: 'edge_1',
            edgeData: {
              source: 'user:attacker@external.com',
              target: 'service_account:sa@project.iam.gserviceaccount.com',
              type: 'can_impersonate_sa',
              properties: { permission: 'iam.serviceAccounts.getAccessToken', riskScore: 0.9 }
            }
          }
        }));
      });
      
      // Should open edge explanation panel
      await expect(page.getByTestId('edge-explanation-panel')).toBeVisible({ timeout: 5000 });
      
      // Should display edge information
      await expect(page.getByText(/can_impersonate_sa/i)).toBeVisible();
      await expect(page.getByText(/iam.serviceAccounts.getAccessToken/i)).toBeVisible();
    });
  });

  test.describe('Performance', () => {
    test('should handle large graphs', async ({ page }) => {
      // Setup large graph data
      await page.route('**/api/graph', route => {
        const nodes = [];
        const edges = [];
        
        // Generate 500 nodes
        for (let i = 0; i < 500; i++) {
          nodes.push({
            id: `node_${i}`,
            type: i % 2 === 0 ? 'user' : 'project',
            name: `node_${i}`,
            properties: { riskScore: Math.random() }
          });
        }
        
        // Generate 1000 edges
        for (let i = 0; i < 1000; i++) {
          const source = nodes[Math.floor(Math.random() * nodes.length)];
          const target = nodes[Math.floor(Math.random() * nodes.length)];
          
          if (source.id !== target.id) {
            edges.push({
              source: source.id,
              target: target.id,
              type: 'has_role',
              properties: { riskScore: Math.random() }
            });
          }
        }
        
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            nodes,
            edges,
            metadata: {
              total_nodes: nodes.length,
              total_edges: edges.length,
              collection_time: new Date().toISOString(),
              gcp_projects: ['large-project']
            }
          })
        });
      });
      
      await page.goto('/graph');
      
      // Should load within reasonable time
      await page.waitForSelector('[data-testid="graph-canvas"]', { timeout: 30000 });
      
      // Should still be responsive
      const zoomButton = page.getByRole('button', { name: /zoom in/i });
      await zoomButton.click();
      
      // Should not show performance warnings or errors
      const errorMessage = page.getByText(/error|warning/i);
      await expect(errorMessage).not.toBeVisible();
    });

    test('should load within performance budget', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/graph');
      await page.waitForSelector('[data-testid="graph-canvas"]');
      
      const loadTime = Date.now() - startTime;
      
      // Should load within 10 seconds
      expect(loadTime).toBeLessThan(10000);
    });
  });

  test.describe('Error Handling', () => {
    test('should handle API errors gracefully', async ({ page }) => {
      await page.route('**/api/graph', route => route.abort('failed'));
      
      await page.goto('/graph');
      
      // Should show error message
      await expect(page.getByText(/error|failed/i)).toBeVisible();
      
      // Should still show basic layout
      await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
    });

    test('should handle empty graph data', async ({ page }) => {
      await page.route('**/api/graph', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            nodes: [],
            edges: [],
            metadata: {
              total_nodes: 0,
              total_edges: 0,
              collection_time: new Date().toISOString(),
              gcp_projects: []
            }
          })
        });
      });
      
      await page.goto('/graph');
      
      // Should show empty state message
      await expect(page.getByText(/no data|empty/i)).toBeVisible();
      
      // Graph controls should still be available
      await expect(page.getByTestId('graph-controls')).toBeVisible();
    });
  });
});

test.describe('Graph Page Accessibility @accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await setupGraphData(page);
    await page.goto('/graph');
  });

  test('should not have accessibility violations', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-canvas"]');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have accessible controls', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-controls"]');
    
    // All buttons should have accessible names
    const buttons = page.locator('[data-testid="graph-controls"] button');
    const count = await buttons.count();
    
    for (let i = 0; i < count; i++) {
      const button = buttons.nth(i);
      const accessibleName = await button.getAttribute('aria-label') || await button.textContent();
      expect(accessibleName?.trim()).toBeTruthy();
    }
  });

  test('should support keyboard navigation', async ({ page }) => {
    await page.waitForSelector('[data-testid="graph-controls"]');
    
    // Should be able to tab through controls
    await page.keyboard.press('Tab');
    const focusedElement = await page.locator(':focus').first();
    await expect(focusedElement).toBeVisible();
    
    // Should be able to activate with Enter or Space
    await page.keyboard.press('Enter');
    
    // Should not cause errors
    const errorMessage = page.getByText(/error/i);
    await expect(errorMessage).not.toBeVisible();
  });

  test('should have accessible panels', async ({ page }) => {
    // Open a panel
    await page.evaluate(() => {
      window.dispatchEvent(new CustomEvent('nodeSelected', {
        detail: {
          nodeId: 'user:test@example.com',
          nodeData: {
            id: 'user:test@example.com',
            type: 'user',
            name: 'test@example.com',
            properties: { email: 'test@example.com', riskScore: 0.8 }
          }
        }
      }));
    });
    
    await expect(page.getByTestId('node-detail-panel')).toBeVisible();
    
    // Panel should have proper heading
    const heading = page.locator('[data-testid="node-detail-panel"] h1, [data-testid="node-detail-panel"] h2');
    await expect(heading.first()).toBeVisible();
    
    // Close button should be accessible
    const closeButton = page.getByRole('button', { name: /close/i });
    await expect(closeButton).toBeVisible();
    await expect(closeButton).toBeFocused();
  });
}); 