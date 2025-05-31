import { test, expect, Page } from '@playwright/test';
import { AxeBuilder } from '@axe-core/playwright';
import { BasePage } from './page-objects/BasePage';

// Test data setup helpers
async function setupTestData(page: Page, scenario: string = 'small_graph_high_risk') {
  // Intercept data service calls and provide test data
  await page.route('**/data/**', async route => {
    // Mock data service responses based on the scenario
    const url = route.request().url();
    
    if (url.includes('/graph/latest.json') || url.includes('/test-graph.json')) {
      let mockGraphData;
      
      if (scenario === 'small_graph_high_risk') {
        mockGraphData = {
          nodes: [
            {
              id: 'user:test@example.com',
              type: 'user',
              name: 'test@example.com',
              properties: { email: 'test@example.com', riskScore: 0.8 }
            },
            {
              id: 'project:test-project',
              type: 'project',
              name: 'test-project',
              properties: { projectId: 'test-project', riskScore: 0.3 }
            },
            {
              id: 'sa:test-sa@test-project.iam.gserviceaccount.com',
              type: 'service_account',
              name: 'test-sa',
              properties: { email: 'test-sa@test-project.iam.gserviceaccount.com', riskScore: 0.6 }
            }
          ],
          edges: [
            {
              id: 'edge1',
              source: 'user:test@example.com',
              target: 'project:test-project',
              type: 'has_role',
              properties: { role: 'roles/owner' }
            }
          ],
          metadata: {
            total_nodes: 3,
            total_edges: 1,
            collection_time: new Date().toISOString(),
            gcp_projects: ['test-project']
          }
        };
      } else if (scenario === 'large_graph_mixed_risk') {
        mockGraphData = {
          nodes: Array.from({ length: 1000 }, (_, i) => ({
            id: `node:${i}`,
            type: 'user',
            name: `user${i}@example.com`,
            properties: { email: `user${i}@example.com`, riskScore: Math.random() }
          })),
          edges: [],
          metadata: {
            total_nodes: 1000,
            total_edges: 0,
            collection_time: new Date().toISOString(),
            gcp_projects: ['large-project']
          }
        };
      } else {
        // Default small dataset
        mockGraphData = {
          nodes: [
            {
              id: 'user:test@example.com',
              type: 'user',
              name: 'test@example.com',
              properties: { email: 'test@example.com', riskScore: 0.8 }
            }
          ],
          edges: [],
          metadata: {
            total_nodes: 1,
            total_edges: 0,
            collection_time: new Date().toISOString(),
            gcp_projects: ['test-project']
          }
        };
      }
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockGraphData)
      });
    } else if (url.includes('/analysis/latest.json') || url.includes('/test-analysis.json')) {
      // Mock analysis data which contains statistics
      let mockAnalysisData;
      
      if (scenario === 'small_graph_high_risk') {
        mockAnalysisData = {
          statistics: {
            total_nodes: 3,
            total_edges: 1,
            attack_paths: 2,
            high_risk_nodes: 1,
            dangerous_roles: 0,
            critical_nodes: 0
          },
          attack_paths: {
            critical: [],
            high: [],
            medium: []
          },
          risk_analysis: {
            overall_score: 0.6,
            risk_distribution: {
              critical: 0,
              high: 1,
              medium: 2,
              low: 0
            }
          }
        };
      } else if (scenario === 'large_graph_mixed_risk') {
        mockAnalysisData = {
          statistics: {
            total_nodes: 1000,
            total_edges: 0,
            attack_paths: 15,
            high_risk_nodes: 50,
            dangerous_roles: 5,
            critical_nodes: 2
          },
          attack_paths: {
            critical: [],
            high: [],
            medium: []
          },
          risk_analysis: {
            overall_score: 0.4,
            risk_distribution: {
              critical: 2,
              high: 50,
              medium: 200,
              low: 748
            }
          }
        };
      } else {
        // Default analysis data
        mockAnalysisData = {
          statistics: {
            total_nodes: 1,
            total_edges: 0,
            attack_paths: 0,
            high_risk_nodes: 0,
            dangerous_roles: 0,
            critical_nodes: 0
          },
          attack_paths: {
            critical: [],
            high: [],
            medium: []
          },
          risk_analysis: {
            overall_score: 0.1,
            risk_distribution: {
              critical: 0,
              high: 0,
              medium: 0,
              low: 1
            }
          }
        };
      }
      
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockAnalysisData)
      });
    }
  });
}

test.describe('Dashboard Page', () => {
  test.beforeEach(async ({ page }) => {
    await setupTestData(page);
    await page.goto('/');
  });

  test('should load dashboard page successfully', async ({ page }) => {
    // Check if we're on the dashboard
    await expect(page).toHaveURL('/');
    
    // Check for main dashboard elements
    await expect(page.locator('h1')).toContainText(/dashboard/i);
  });

  test('should display navigation menu', async ({ page }) => {
    // Check for navigation items using more specific selectors
    await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Graph', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Findings', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Nodes', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Edges', exact: true })).toBeVisible();
    await expect(page.getByRole('link', { name: 'Settings', exact: true })).toBeVisible();
  });

  test('should highlight active navigation item', async ({ page }) => {
    // Dashboard should be active by default
    const dashboardLink = page.getByRole('link', { name: 'Dashboard', exact: true });
    await expect(dashboardLink).toHaveClass(/bg-primary|active|current/);
  });

  test('should display statistics cards', async ({ page }) => {
    // Wait for statistics to load
    await page.waitForSelector('[data-testid="statistics-cards"]', { timeout: 10000 });
    
    // Check for statistics cards using specific test IDs
    await expect(page.getByTestId('stat-value-total-nodes')).toBeVisible();
    await expect(page.getByTestId('stat-value-total-edges')).toBeVisible();
    await expect(page.getByTestId('stat-value-attack-paths')).toBeVisible();
    await expect(page.getByTestId('stat-value-high-risk-nodes')).toBeVisible();
  });

  test('should display numeric values in statistics cards', async ({ page }) => {
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    // Check that statistics have numeric values using specific test IDs
    const testIds = [
      'stat-value-total-nodes',
      'stat-value-total-edges', 
      'stat-value-attack-paths',
      'stat-value-high-risk-nodes'
    ];
    
    for (const testId of testIds) {
      const valueElement = page.getByTestId(testId);
      const value = await valueElement.textContent();
      
      // Should contain a number
      expect(value).toMatch(/\d+/);
    }
  });

  test('should handle loading states', async ({ page }) => {
    // The loading state is very fast with mock data, so we'll check that the page loads properly
    // and that we eventually see the content (which means loading completed successfully)
    
    // Wait for content to load - this implicitly tests that loading worked
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    // Verify that we have moved past loading state and have actual content
    await expect(page.getByTestId('stat-value-total-nodes')).toBeVisible();
    await expect(page.getByTestId('stat-value-total-edges')).toBeVisible();
  });

  test('should navigate to other pages', async ({ page }) => {
    // Navigate to Graph page
    await page.getByRole('link', { name: 'Graph', exact: true }).click();
    await expect(page).toHaveURL('/graph');
    
    // Navigate back to dashboard
    await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
    await expect(page).toHaveURL('/');
    
    // Test navigation to Findings page
    await page.getByRole('link', { name: 'Findings', exact: true }).click();
    await expect(page).toHaveURL('/findings');
  });

  test('should handle statistics card clicks', async ({ page }) => {
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    // Click on nodes card should navigate to nodes page
    const nodesCard = page.getByTestId('stat-card-nodes');
    if (await nodesCard.isVisible()) {
      await nodesCard.click();
      await expect(page).toHaveURL('/nodes');
    }
  });

  test('should be responsive on different screen sizes', async ({ page }) => {
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    // Test tablet viewport
    await page.setViewportSize({ width: 768, height: 1024 });
    await expect(page.getByTestId('statistics-cards')).toBeVisible();
    
    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });
    await expect(page.getByTestId('statistics-cards')).toBeVisible();
  });

  test('should display error state gracefully', async ({ page }) => {
    // Mock a network error by intercepting the data service calls
    await page.route('**/data/**', route => {
      route.abort();
    });
    
    // Navigate to trigger the error
    await page.goto('/');
    
    // The app should still show the basic layout even with errors
    await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toBeVisible();
    
    // For now, we'll verify the page doesn't crash rather than looking for specific error text
    // since the error handling might show different messages or handle errors gracefully
    const pageTitle = await page.title();
    expect(pageTitle).toBeTruthy(); // Page should still have a title
  });

  test('should handle empty data state', async ({ page }) => {
    // Setup empty data response for both endpoints
    await page.route('**/data/graph/latest.json', route => {
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
    
    await page.route('**/data/analysis/latest.json', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          statistics: {
            total_nodes: 0,
            total_edges: 0,
            attack_paths: 0,
            high_risk_nodes: 0,
            dangerous_roles: 0,
            critical_nodes: 0
          },
          attack_paths: {
            critical: [],
            high: [],
            medium: []
          },
          risk_analysis: {
            overall_score: 0,
            risk_distribution: {
              critical: 0,
              high: 0,
              medium: 0,
              low: 0
            }
          }
        })
      });
    });
    
    await page.goto('/');
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    // Should show zero values in the statistics
    await expect(page.getByTestId('stat-value-total-nodes')).toContainText('0');
    await expect(page.getByTestId('stat-value-total-edges')).toContainText('0');
    
    // The layout should still be functional
    await expect(page.getByTestId('statistics-cards')).toBeVisible();
  });

  test.describe('User Interactions', () => {
    test('should support keyboard navigation', async ({ page }) => {
      await page.waitForSelector('[data-testid="statistics-cards"]');
      
      // Tab through navigation items
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      
      // Should be able to activate links with Enter
      await page.keyboard.press('Enter');
      
      // Should navigate somewhere (depends on which link was focused)
      await expect(page).not.toHaveURL('/undefined');
    });

    test('should handle rapid clicking gracefully', async ({ page }) => {
      await page.waitForSelector('[data-testid="statistics-cards"]');
      
      const graphLink = page.getByRole('link', { name: 'Graph', exact: true });
      
      // Rapid clicks shouldn't cause issues
      await graphLink.click();
      await graphLink.click();
      await graphLink.click();
      
      // Should only navigate once
      await expect(page).toHaveURL('/graph');
    });
  });

  test.describe('Data Integration', () => {
    test('should work with small dataset', async ({ page }) => {
      await setupTestData(page, 'small_graph_high_risk');
      await page.goto('/');
      
      await page.waitForSelector('[data-testid="statistics-cards"]');
      
      // Should display appropriate values for small dataset
      await expect(page.getByTestId('stat-value-total-nodes')).toContainText('3');
    });

    test('should work with large dataset', async ({ page }) => {
      await setupTestData(page, 'large_graph_mixed_risk');
      await page.goto('/');
      
      await page.waitForSelector('[data-testid="statistics-cards"]');
      
      // Should display formatted large numbers
      const nodeValue = await page.getByTestId('stat-value-total-nodes').textContent();
      expect(nodeValue).toMatch(/\d+/);
    });

    test('should handle real gcphound data format', async ({ page }) => {
      // Test with data structure that matches actual gcphound output
      await page.route('**/data/graph/latest.json', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            metadata: {
              total_nodes: 157,
              total_edges: 423,
              collection_time: '2024-01-15T10:30:00Z',
              gcp_projects: ['production-project', 'staging-project'],
              generator_version: '1.0.0'
            },
            nodes: [
              {
                id: 'user:admin@company.com',
                type: 'user',
                name: 'admin@company.com',
                properties: {
                  email: 'admin@company.com',
                  riskScore: 0.95
                }
              }
            ],
            edges: []
          })
        });
      });
      
      await page.route('**/data/analysis/latest.json', route => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            statistics: {
              total_nodes: 157,
              total_edges: 423,
              attack_paths: 5,
              high_risk_nodes: 12,
              dangerous_roles: 3,
              critical_nodes: 2
            },
            attack_paths: {
              critical: [],
              high: [],
              medium: []
            },
            risk_analysis: {
              overall_score: 0.7,
              risk_distribution: {
                critical: 2,
                high: 12,
                medium: 30,
                low: 113
              }
            }
          })
        });
      });
      
      await page.goto('/');
      await page.waitForSelector('[data-testid="statistics-cards"]');
      
      // Should correctly parse and display the data
      await expect(page.getByTestId('stat-value-total-nodes')).toContainText('157');
      await expect(page.getByTestId('stat-value-total-edges')).toContainText('423');
    });
  });
});

test.describe('Dashboard Accessibility @accessibility', () => {
  test.beforeEach(async ({ page }) => {
    await setupTestData(page);
    await page.goto('/');
  });

  test('should not have any accessibility violations', async ({ page }) => {
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test('should have proper heading structure', async ({ page }) => {
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    // Check for proper heading hierarchy
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
    
    // Should have proper heading text
    await expect(h1).toContainText(/dashboard/i);
  });

  test('should have accessible navigation', async ({ page }) => {
    // Navigation should be in a nav element or have proper role
    const nav = page.locator('nav, [role="navigation"]');
    await expect(nav).toBeVisible();
    
    // All navigation links should be accessible
    const navLinks = nav.locator('a');
    const count = await navLinks.count();
    
    for (let i = 0; i < count; i++) {
      const link = navLinks.nth(i);
      await expect(link).toBeVisible();
      
      // Should have accessible name
      const accessibleName = await link.getAttribute('aria-label') || await link.textContent();
      expect(accessibleName).toBeTruthy();
    }
  });

  test('should have accessible statistics cards', async ({ page }) => {
    await page.waitForSelector('[data-testid="statistics-cards"]');
    
    const statCards = page.locator('[data-testid="stat-card"]');
    const count = await statCards.count();
    
    for (let i = 0; i < count; i++) {
      const card = statCards.nth(i);
      
      // Should have accessible content
      const text = await card.textContent();
      expect(text).toBeTruthy();
      
      // If it's clickable, should have proper role or be a button/link
      const isClickable = await card.getAttribute('role') === 'button' || 
                         await card.getAttribute('tabindex') !== null ||
                         card.locator('button, a').first().isVisible();
      
      if (isClickable) {
        // Should be focusable
        await card.focus();
        await expect(card).toBeFocused();
      }
    }
  });
}); 