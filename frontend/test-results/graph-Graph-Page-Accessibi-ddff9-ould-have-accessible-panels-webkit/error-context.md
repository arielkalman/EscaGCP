# Test info

- Name: Graph Page Accessibility @accessibility >> should have accessible panels
- Location: /Users/arielkalman/EscaGCP/frontend/e2e/graph.spec.ts:533:3

# Error details

```
Error: Timed out 10000ms waiting for expect(locator).toBeVisible()

Locator: getByTestId('node-detail-panel')
Expected: visible
Received: <element(s) not found>
Call log:
  - expect.toBeVisible with timeout 10000ms
  - waiting for getByTestId('node-detail-panel')

    at /Users/arielkalman/EscaGCP/frontend/e2e/graph.spec.ts:549:57
```

# Page snapshot

```yaml
- banner:
  - link "EscaGCP Security Dashboard":
    - /url: /
    - img
    - text: EscaGCP
    - paragraph: Security Dashboard
  - navigation:
    - link "Dashboard":
      - /url: /
      - img
      - text: Dashboard
    - link "Graph":
      - /url: /graph
      - img
      - text: Graph
    - link "Findings":
      - /url: /findings
      - img
      - text: Findings
    - link "Nodes":
      - /url: /nodes
      - img
      - text: Nodes
    - link "Edges":
      - /url: /edges
      - img
      - text: Edges
    - link "Settings":
      - /url: /settings
      - img
      - text: Settings
  - button "Switch to dark theme":
    - img
  - text: Online
- main:
  - heading "Graph Visualization" [level=1]
  - heading "Search & Filters" [level=2]
  - button "Close search and filters panel":
    - img
  - img
  - textbox "Search nodes by name, ID, or properties..."
  - img
  - text: Filter By 2
  - button "Clear All":
    - img
    - text: Clear All
  - heading "Search & Quick Filters" [level=3]:
    - text: Search & Quick Filters
    - img
  - 'heading "Filter: Node Types" [level=3]':
    - text: "Filter: Node Types"
    - img
  - button "Select All"
  - button "Deselect All"
  - checkbox "Filter by Projects"
  - text: Projects 1
  - checkbox "Filter by Service Accounts"
  - text: Service Accounts 32
  - checkbox "Filter by Roles"
  - text: Roles 29
  - checkbox "Filter by Custom Roles"
  - text: Custom Roles 2
  - checkbox "Filter by Users"
  - text: Users 63
  - checkbox "Filter by Groups"
  - text: Groups 1
  - checkbox "Filter by Storage Buckets"
  - text: Storage Buckets 15
  - checkbox "Filter by Compute Instances"
  - text: Compute Instances 6
  - checkbox "Filter by Cloud Functions"
  - text: Cloud Functions 1
  - 'heading "Filter: Edge Types" [level=3]':
    - text: "Filter: Edge Types"
    - img
  - 'heading "Filter: Risk Levels" [level=3]':
    - text: "Filter: Risk Levels"
    - img
  - checkbox "Filter by Critical risk level" [checked]
  - text: Critical ≥ 80% risk score
  - checkbox "Filter by High risk level" [checked]
  - text: High 60-79% risk score
  - checkbox "Filter by Medium risk level" [checked]
  - text: Medium 40-59% risk score
  - checkbox "Filter by Low risk level" [checked]
  - text: Low 20-39% risk score
  - checkbox "Filter by Info/Safe risk level" [checked]
  - text: Info/Safe < 20% risk score Showing 150 nodes, 498 edges
  - heading "Controls & Legend" [level=2]
  - button "Close controls and legend panel":
    - img
  - text: "Graph Statistics Nodes: 150 Edges: 498 View Controls"
  - button "Zoom In":
    - img
    - text: Zoom In
  - button "Zoom Out":
    - img
    - text: Zoom Out
  - button "Fit to View":
    - img
    - text: Fit to View
  - button "Reset":
    - img
    - text: Reset
  - text: Layout
  - button "Physics On":
    - img
    - text: Physics On
  - button "Force Layout":
    - img
    - text: Force Layout
  - text: Actions
  - button "Export Image":
    - img
    - text: Export Image
  - button "Settings":
    - img
    - text: Settings
  - text: Quick Actions
  - button "🔴 Focus High-Risk"
  - button "⚡ Show Attack Paths"
  - button "🏢 Center Organization"
  - 'heading "Legend: Node Types" [level=3]':
    - text: "Legend: Node Types"
    - img
  - img
  - text: Projects GCP projects 1
  - button "Show":
    - img
  - img
  - text: Service Accounts Automated service accounts 32
  - button "Show":
    - img
  - img
  - text: Roles IAM roles and permissions 29
  - button "Show":
    - img
  - img
  - text: Custom Roles Custom IAM roles 2
  - button "Show":
    - img
  - img
  - text: Users Human users and accounts 63
  - button "Show":
    - img
  - img
  - text: Groups User and service account groups 1
  - button "Show":
    - img
  - img
  - text: Storage Buckets Cloud Storage buckets 15
  - button "Show":
    - img
  - img
  - text: Compute Instances Virtual machine instances 6
  - button "Show":
    - img
  - img
  - text: Cloud Functions Serverless functions 1
  - button "Show":
    - img
  - 'heading "Legend: Edge Types" [level=3]':
    - text: "Legend: Edge Types"
    - img
  - text: Has Role Has IAM role assignment 175
  - button "Show":
    - img
  - 'heading "Legend: Risk Levels" [level=3]':
    - text: "Legend: Risk Levels"
    - img
  - text: Critical Risk ≥ 80% risk score - Immediate action required High Risk 60-79% risk score - Should be addressed soon Medium Risk 40-59% risk score - Review and plan remediation Low Risk 20-39% risk score - Monitor Info/Safe < 20% risk score - Low priority
```

# Test source

```ts
  449 |       await page.goto('/graph');
  450 |       
  451 |       // Should show error message
  452 |       await expect(page.getByText(/error|failed/i)).toBeVisible();
  453 |       
  454 |       // Should still show basic layout
  455 |       await expect(page.getByRole('link', { name: /dashboard/i })).toBeVisible();
  456 |     });
  457 |
  458 |     test('should handle empty graph data', async ({ page }) => {
  459 |       await page.route('**/api/graph', route => {
  460 |         route.fulfill({
  461 |           status: 200,
  462 |           contentType: 'application/json',
  463 |           body: JSON.stringify({
  464 |             nodes: [],
  465 |             edges: [],
  466 |             metadata: {
  467 |               total_nodes: 0,
  468 |               total_edges: 0,
  469 |               collection_time: new Date().toISOString(),
  470 |               gcp_projects: []
  471 |             }
  472 |           })
  473 |         });
  474 |       });
  475 |       
  476 |       await page.goto('/graph');
  477 |       
  478 |       // Should show empty state message
  479 |       await expect(page.getByText(/no data|empty/i)).toBeVisible();
  480 |       
  481 |       // Graph controls should still be available
  482 |       await expect(page.getByTestId('graph-controls')).toBeVisible();
  483 |     });
  484 |   });
  485 | });
  486 |
  487 | test.describe('Graph Page Accessibility @accessibility', () => {
  488 |   test.beforeEach(async ({ page }) => {
  489 |     await setupGraphData(page);
  490 |     await page.goto('/graph');
  491 |   });
  492 |
  493 |   test('should not have accessibility violations', async ({ page }) => {
  494 |     await page.waitForSelector('[data-testid="graph-canvas"]');
  495 |     
  496 |     const accessibilityScanResults = await new AxeBuilder({ page })
  497 |       .withTags(['wcag2a', 'wcag2aa', 'wcag21aa'])
  498 |       .analyze();
  499 |
  500 |     expect(accessibilityScanResults.violations).toEqual([]);
  501 |   });
  502 |
  503 |   test('should have accessible controls', async ({ page }) => {
  504 |     await page.waitForSelector('[data-testid="graph-controls"]');
  505 |     
  506 |     // All buttons should have accessible names
  507 |     const buttons = page.locator('[data-testid="graph-controls"] button');
  508 |     const count = await buttons.count();
  509 |     
  510 |     for (let i = 0; i < count; i++) {
  511 |       const button = buttons.nth(i);
  512 |       const accessibleName = await button.getAttribute('aria-label') || await button.textContent();
  513 |       expect(accessibleName?.trim()).toBeTruthy();
  514 |     }
  515 |   });
  516 |
  517 |   test('should support keyboard navigation', async ({ page }) => {
  518 |     await page.waitForSelector('[data-testid="graph-controls"]');
  519 |     
  520 |     // Should be able to tab through controls
  521 |     await page.keyboard.press('Tab');
  522 |     const focusedElement = await page.locator(':focus').first();
  523 |     await expect(focusedElement).toBeVisible();
  524 |     
  525 |     // Should be able to activate with Enter or Space
  526 |     await page.keyboard.press('Enter');
  527 |     
  528 |     // Should not cause errors
  529 |     const errorMessage = page.getByText(/error/i);
  530 |     await expect(errorMessage).not.toBeVisible();
  531 |   });
  532 |
  533 |   test('should have accessible panels', async ({ page }) => {
  534 |     // Open a panel
  535 |     await page.evaluate(() => {
  536 |       window.dispatchEvent(new CustomEvent('nodeSelected', {
  537 |         detail: {
  538 |           nodeId: 'user:test@example.com',
  539 |           nodeData: {
  540 |             id: 'user:test@example.com',
  541 |             type: 'user',
  542 |             name: 'test@example.com',
  543 |             properties: { email: 'test@example.com', riskScore: 0.8 }
  544 |           }
  545 |         }
  546 |       }));
  547 |     });
  548 |     
> 549 |     await expect(page.getByTestId('node-detail-panel')).toBeVisible();
      |                                                         ^ Error: Timed out 10000ms waiting for expect(locator).toBeVisible()
  550 |     
  551 |     // Panel should have proper heading
  552 |     const heading = page.locator('[data-testid="node-detail-panel"] h1, [data-testid="node-detail-panel"] h2');
  553 |     await expect(heading.first()).toBeVisible();
  554 |     
  555 |     // Close button should be accessible
  556 |     const closeButton = page.getByRole('button', { name: /close/i });
  557 |     await expect(closeButton).toBeVisible();
  558 |     await expect(closeButton).toBeFocused();
  559 |   });
  560 | }); 
```