# Test info

- Name: Graph Page >> should handle node clicks
- Location: /Users/arielkalman/GCPHound/frontend/e2e/graph.spec.ts:149:3

# Error details

```
Error: Timed out 5000ms waiting for expect(locator).toBeVisible()

Locator: getByTestId('node-detail-panel')
Expected: visible
Received: <element(s) not found>
Call log:
  - expect.toBeVisible with timeout 5000ms
  - waiting for getByTestId('node-detail-panel')

    at /Users/arielkalman/GCPHound/frontend/e2e/graph.spec.ts:158:57
```

# Page snapshot

```yaml
- banner:
  - link "GCPHound Security Dashboard":
    - /url: /
    - img
    - text: GCPHound
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
   58 |
   59 |   // Mock attack paths API
   60 |   await page.route('**/api/attack-paths', route => {
   61 |     route.fulfill({
   62 |       status: 200,
   63 |       contentType: 'application/json',
   64 |       body: JSON.stringify([
   65 |         {
   66 |           id: 'path_1',
   67 |           source: 'user:attacker@external.com',
   68 |           target: 'project:production-project',
   69 |           path: ['user:attacker@external.com', 'service_account:sa@project.iam.gserviceaccount.com', 'project:production-project'],
   70 |           riskScore: 0.95,
   71 |           category: 'privilege_escalation',
   72 |           techniques: ['service_account_impersonation'],
   73 |           description: 'External user can escalate to project owner via service account impersonation'
   74 |         }
   75 |       ])
   76 |     });
   77 |   });
   78 | }
   79 |
   80 | test.describe('Graph Page', () => {
   81 |   test.beforeEach(async ({ page }) => {
   82 |     await setupGraphData(page);
   83 |     await page.goto('/graph');
   84 |   });
   85 |
   86 |   test('should load graph page successfully', async ({ page }) => {
   87 |     await expect(page).toHaveURL('/graph');
   88 |     await expect(page.locator('h1')).toContainText(/graph/i);
   89 |   });
   90 |
   91 |   test('should display graph canvas', async ({ page }) => {
   92 |     // Wait for graph to load
   93 |     await page.waitForSelector('[data-testid="graph-canvas"]', { timeout: 15000 });
   94 |     
   95 |     const graphCanvas = page.getByTestId('graph-canvas');
   96 |     await expect(graphCanvas).toBeVisible();
   97 |     
   98 |     // Should have a canvas or svg element for vis.js
   99 |     const visElement = graphCanvas.locator('canvas, svg').first();
  100 |     await expect(visElement).toBeVisible();
  101 |   });
  102 |
  103 |   test('should display graph controls', async ({ page }) => {
  104 |     await page.waitForSelector('[data-testid="graph-controls"]');
  105 |     
  106 |     // Check for zoom controls
  107 |     await expect(page.getByRole('button', { name: /zoom in/i })).toBeVisible();
  108 |     await expect(page.getByRole('button', { name: /zoom out/i })).toBeVisible();
  109 |     await expect(page.getByRole('button', { name: /reset/i })).toBeVisible();
  110 |   });
  111 |
  112 |   test('should display graph legend', async ({ page }) => {
  113 |     await page.waitForSelector('[data-testid="graph-legend"]');
  114 |     
  115 |     const legend = page.getByTestId('graph-legend');
  116 |     
  117 |     // Check for node type legend within the legend container
  118 |     await expect(legend.getByText(/node types/i)).toBeVisible();
  119 |     await expect(legend.getByText(/edge types/i)).toBeVisible();
  120 |     await expect(legend.getByText(/risk levels/i)).toBeVisible();
  121 |   });
  122 |
  123 |   test('should display graph filters', async ({ page }) => {
  124 |     await page.waitForSelector('[data-testid="graph-filters"]');
  125 |     
  126 |     const filters = page.getByTestId('graph-filters');
  127 |     
  128 |     // Check for filter controls within the filters container
  129 |     await expect(filters.getByText(/filter by/i)).toBeVisible();
  130 |     
  131 |     // Should have node type filters
  132 |     await expect(filters.getByText(/users/i)).toBeVisible();
  133 |     await expect(filters.getByText(/service accounts/i)).toBeVisible();
  134 |     await expect(filters.getByText(/projects/i)).toBeVisible();
  135 |   });
  136 |
  137 |   test('should render nodes on the graph', async ({ page }) => {
  138 |     await page.waitForSelector('[data-testid="graph-canvas"]');
  139 |     
  140 |     // Wait for vis.js to render
  141 |     await page.waitForTimeout(2000);
  142 |     
  143 |     // Check that nodes are rendered (this depends on vis.js implementation)
  144 |     // We can check for specific node elements or use custom data attributes
  145 |     const nodeElements = page.locator('[data-node-id]');
  146 |     await expect(nodeElements.first()).toBeVisible({ timeout: 10000 });
  147 |   });
  148 |
  149 |   test('should handle node clicks', async ({ page }) => {
  150 |     await page.waitForSelector('[data-testid="graph-canvas"]');
  151 |     await page.waitForTimeout(2000);
  152 |     
  153 |     // Click on a node (this may require custom event handling)
  154 |     const graphCanvas = page.getByTestId('graph-canvas');
  155 |     await graphCanvas.click({ position: { x: 200, y: 200 } });
  156 |     
  157 |     // Should open node detail panel
> 158 |     await expect(page.getByTestId('node-detail-panel')).toBeVisible({ timeout: 5000 });
      |                                                         ^ Error: Timed out 5000ms waiting for expect(locator).toBeVisible()
  159 |   });
  160 |
  161 |   test('should handle edge clicks', async ({ page }) => {
  162 |     await page.waitForSelector('[data-testid="graph-canvas"]');
  163 |     await page.waitForTimeout(2000);
  164 |     
  165 |     // Click on an edge area
  166 |     const graphCanvas = page.getByTestId('graph-canvas');
  167 |     await graphCanvas.click({ position: { x: 300, y: 250 } });
  168 |     
  169 |     // Should open edge explanation panel (if an edge was clicked)
  170 |     // This test might need adjustment based on actual graph rendering
  171 |   });
  172 |
  173 |   test('should handle zoom controls', async ({ page }) => {
  174 |     await page.waitForSelector('[data-testid="graph-controls"]');
  175 |     
  176 |     const zoomInButton = page.getByRole('button', { name: /zoom in/i });
  177 |     const zoomOutButton = page.getByRole('button', { name: /zoom out/i });
  178 |     const resetButton = page.getByRole('button', { name: /reset/i });
  179 |     
  180 |     // Test zoom in
  181 |     await zoomInButton.click();
  182 |     await page.waitForTimeout(500);
  183 |     
  184 |     // Test zoom out
  185 |     await zoomOutButton.click();
  186 |     await page.waitForTimeout(500);
  187 |     
  188 |     // Test reset
  189 |     await resetButton.click();
  190 |     await page.waitForTimeout(500);
  191 |     
  192 |     // All operations should complete without errors
  193 |     const errorMessage = page.getByText(/error/i);
  194 |     await expect(errorMessage).not.toBeVisible();
  195 |   });
  196 |
  197 |   test('should apply node type filters', async ({ page }) => {
  198 |     await page.waitForSelector('[data-testid="graph-filters"]');
  199 |     
  200 |     // Find and click user filter checkbox
  201 |     const userFilter = page.getByRole('checkbox', { name: /users/i });
  202 |     
  203 |     if (await userFilter.isVisible()) {
  204 |       // Uncheck users filter
  205 |       await userFilter.uncheck();
  206 |       
  207 |       // Wait for graph to update
  208 |       await page.waitForTimeout(1000);
  209 |       
  210 |       // Graph should update (this test would need to verify node visibility)
  211 |       // For now, just ensure no errors occurred
  212 |       const errorMessage = page.getByText(/error/i);
  213 |       await expect(errorMessage).not.toBeVisible();
  214 |     }
  215 |   });
  216 |
  217 |   test('should handle search functionality', async ({ page }) => {
  218 |     const searchInput = page.getByRole('textbox', { name: /search/i });
  219 |     
  220 |     if (await searchInput.isVisible()) {
  221 |       await searchInput.fill('attacker@external.com');
  222 |       await page.keyboard.press('Enter');
  223 |       
  224 |       // Should highlight or focus on the searched node
  225 |       await page.waitForTimeout(1000);
  226 |       
  227 |       // Verify no errors
  228 |       const errorMessage = page.getByText(/error/i);
  229 |       await expect(errorMessage).not.toBeVisible();
  230 |     }
  231 |   });
  232 |
  233 |   test('should be responsive', async ({ page }) => {
  234 |     await page.waitForSelector('[data-testid="graph-canvas"]');
  235 |     
  236 |     // Test tablet viewport
  237 |     await page.setViewportSize({ width: 768, height: 1024 });
  238 |     await expect(page.getByTestId('graph-canvas')).toBeVisible();
  239 |     
  240 |     // Test desktop viewport
  241 |     await page.setViewportSize({ width: 1920, height: 1080 });
  242 |     await expect(page.getByTestId('graph-canvas')).toBeVisible();
  243 |   });
  244 |
  245 |   test.describe('Interactive Panels', () => {
  246 |     test('should open and close node detail panel', async ({ page }) => {
  247 |       await page.waitForSelector('[data-testid="graph-canvas"]');
  248 |       
  249 |       // First, check that the panel is not visible initially
  250 |       await expect(page.getByTestId('node-detail-panel')).not.toBeVisible();
  251 |       
  252 |       // Simulate node click (this might require custom implementation)
  253 |       await page.evaluate(() => {
  254 |         // Dispatch custom event to simulate node selection
  255 |         const nodeData = {
  256 |           id: 'user:attacker@external.com',
  257 |           type: 'user',
  258 |           name: 'attacker@external.com',
```