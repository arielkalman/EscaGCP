# Test info

- Name: Dashboard Page >> should navigate to other pages
- Location: /Users/arielkalman/EscaGCP/frontend/e2e/dashboard.spec.ts:259:3

# Error details

```
TimeoutError: locator.click: Timeout 15000ms exceeded.
Call log:
  - waiting for getByRole('link', { name: 'Findings', exact: true })
    - locator resolved to <a href="/findings" class="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground hover:text-foreground hover:bg-accent">…</a>
  - attempting click action
    2 × waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <span>Graph</span> from <a href="/graph" class="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground hover:text-foreground hover:bg-accent">…</a> subtree intercepts pointer events
    - retrying click action
    - waiting 20ms
    - waiting for element to be visible, enabled and stable
    - element is visible, enabled and stable
    - scrolling into view if needed
    - done scrolling
    - <a href="/" class="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground">…</a> intercepts pointer events
  2 × retrying click action
      - waiting 100ms
      - waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <a href="/" class="flex items-center space-x-3 text-foreground hover:text-primary transition-colors">…</a> from <div class="flex items-center">…</div> subtree intercepts pointer events
  7 × retrying click action
      - waiting 500ms
      - waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <span>Graph</span> from <a href="/graph" class="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors text-muted-foreground hover:text-foreground hover:bg-accent">…</a> subtree intercepts pointer events
    - retrying click action
      - waiting 500ms
      - waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <a href="/" class="flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors bg-primary text-primary-foreground">…</a> intercepts pointer events
    - retrying click action
      - waiting 500ms
      - waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <a href="/" class="flex items-center space-x-3 text-foreground hover:text-primary transition-colors">…</a> from <div class="flex items-center">…</div> subtree intercepts pointer events
    - retrying click action
      - waiting 500ms
      - waiting for element to be visible, enabled and stable
      - element is visible, enabled and stable
      - scrolling into view if needed
      - done scrolling
      - <a href="/" class="flex items-center space-x-3 text-foreground hover:text-primary transition-colors">…</a> from <div class="flex items-center">…</div> subtree intercepts pointer events
  - retrying click action
    - waiting 500ms

    at /Users/arielkalman/EscaGCP/frontend/e2e/dashboard.spec.ts:269:69
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
  - heading "Security Dashboard" [level=1]
  - paragraph: Comprehensive overview of your GCP security posture and potential attack vectors
  - 'button "Total Nodes: 3. All entities in your GCP environment"':
    - img
    - text: Medium
    - paragraph: Total Nodes
    - paragraph: "3"
    - img
    - text: 5.2% vs last scan
    - paragraph: All entities in your GCP environment
  - 'button "Total Edges: 1. Relationships between entities"':
    - img
    - text: Medium
    - paragraph: Total Edges
    - paragraph: "1"
    - img
    - text: 3.1% vs last scan
    - paragraph: Relationships between entities
  - 'button "Attack Paths: 2. Potential privilege escalation paths"':
    - img
    - text: Medium
    - paragraph: Attack Paths
    - paragraph: "2"
    - img
    - text: 12.3% vs last scan
    - paragraph: Potential privilege escalation paths
  - 'button "High Risk Nodes: 1. Nodes with elevated risk scores"':
    - img
    - text: Medium
    - paragraph: High Risk Nodes
    - paragraph: "1"
    - img
    - text: 2.1% vs last scan
    - paragraph: Nodes with elevated risk scores
  - 'button "Dangerous Roles: 0. High-privilege roles in use"':
    - img
    - text: Good
    - paragraph: Dangerous Roles
    - paragraph: "0"
    - img
    - text: 0.0% vs last scan
    - paragraph: High-privilege roles in use
  - 'button "Critical Nodes: 0. Critical security nodes detected"':
    - img
    - text: Low
    - paragraph: Critical Nodes
    - paragraph: "0"
    - img
    - text: 8.5% vs last scan
    - paragraph: Critical security nodes detected
  - heading "Security Posture Summary" [level=3]
  - paragraph: 2 potential attack paths require attention. Focus on high-risk nodes and dangerous role assignments.
  - text: Medium Risk
  - img
  - heading "Attack Path Distribution" [level=3]
  - paragraph: Breakdown of attack paths by risk level
  - img: Critical High Medium Low 0 1 2 3 4
  - text: "Critical: 0 High: 0 Medium: 0 Low: 0"
  - img
  - heading "Node Type Distribution" [level=3]
  - paragraph: Composition of entities in your environment
  - img:
    - img
    - img
    - img
    - img
    - img
    - text: 25% 35% 15% 8% 17%
  - text: "Users: 25 Service Accounts: 35 Groups: 15 Projects: 8 Resources: 17"
  - img
  - heading "Risk Score Distribution" [level=3]
  - paragraph: Histogram of risk scores across all nodes
  - img: 0-20% 41-60% 81-100% 0 15 30 45 60
  - text: Lower Risk Higher Risk
  - img
  - heading "Security Trends" [level=3]
  - paragraph: Attack paths and risk score trends over time
  - text: Improving 6 Months
  - img: Jan Feb Mar Apr May Jun 0 20 40 60 80
  - list:
    - listitem:
      - img
      - text: Attack Paths
    - listitem:
      - img
      - text: Avg Risk Score
  - paragraph: "-65%"
  - paragraph: Attack paths reduced
  - paragraph: "-35%"
  - paragraph: Risk score improved
  - heading "Quick Actions" [level=3]:
    - img
    - text: Quick Actions
  - paragraph: Common security operations and views
  - button "View Full Graph":
    - img
    - text: View Full Graph
    - img
  - button "Security Findings":
    - img
    - text: Security Findings
    - img
  - button "Risk Assessment":
    - img
    - text: Risk Assessment
    - img
  - heading "Environment Overview" [level=3]
  - paragraph: Your GCP infrastructure at a glance
  - paragraph: Projects
  - paragraph: "1"
  - paragraph: Last Scan
  - paragraph: 5/31/2025
  - paragraph: Recent Projects
  - text: test-project Active
  - heading "Critical Findings" [level=3]:
    - img
    - text: Critical Findings
  - paragraph: High-priority security issues requiring immediate attention
  - img
  - paragraph: No Critical Findings
  - paragraph: Your environment shows a strong security posture
  - heading "System Status" [level=3]
  - paragraph: Current status of security monitoring components
  - img
  - text: Data Collection Active
  - img
  - text: Analysis Engine Active
  - img
  - text: Real-time Monitoring Planned
  - paragraph: "Last updated: 5/31/2025, 9:08:39 AM •Next scan in 24 hours"
```

# Test source

```ts
  169 |               high: 0,
  170 |               medium: 0,
  171 |               low: 1
  172 |             }
  173 |           }
  174 |         };
  175 |       }
  176 |       
  177 |       await route.fulfill({
  178 |         status: 200,
  179 |         contentType: 'application/json',
  180 |         body: JSON.stringify(mockAnalysisData)
  181 |       });
  182 |     }
  183 |   });
  184 | }
  185 |
  186 | test.describe('Dashboard Page', () => {
  187 |   test.beforeEach(async ({ page }) => {
  188 |     await setupTestData(page);
  189 |     await page.goto('/');
  190 |   });
  191 |
  192 |   test('should load dashboard page successfully', async ({ page }) => {
  193 |     // Check if we're on the dashboard
  194 |     await expect(page).toHaveURL('/');
  195 |     
  196 |     // Check for main dashboard elements
  197 |     await expect(page.locator('h1')).toContainText(/dashboard/i);
  198 |   });
  199 |
  200 |   test('should display navigation menu', async ({ page }) => {
  201 |     // Check for navigation items using more specific selectors
  202 |     await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toBeVisible();
  203 |     await expect(page.getByRole('link', { name: 'Graph', exact: true })).toBeVisible();
  204 |     await expect(page.getByRole('link', { name: 'Findings', exact: true })).toBeVisible();
  205 |     await expect(page.getByRole('link', { name: 'Nodes', exact: true })).toBeVisible();
  206 |     await expect(page.getByRole('link', { name: 'Edges', exact: true })).toBeVisible();
  207 |     await expect(page.getByRole('link', { name: 'Settings', exact: true })).toBeVisible();
  208 |   });
  209 |
  210 |   test('should highlight active navigation item', async ({ page }) => {
  211 |     // Dashboard should be active by default
  212 |     const dashboardLink = page.getByRole('link', { name: 'Dashboard', exact: true });
  213 |     await expect(dashboardLink).toHaveClass(/bg-primary|active|current/);
  214 |   });
  215 |
  216 |   test('should display statistics cards', async ({ page }) => {
  217 |     // Wait for statistics to load
  218 |     await page.waitForSelector('[data-testid="statistics-cards"]', { timeout: 10000 });
  219 |     
  220 |     // Check for statistics cards using specific test IDs
  221 |     await expect(page.getByTestId('stat-value-total-nodes')).toBeVisible();
  222 |     await expect(page.getByTestId('stat-value-total-edges')).toBeVisible();
  223 |     await expect(page.getByTestId('stat-value-attack-paths')).toBeVisible();
  224 |     await expect(page.getByTestId('stat-value-high-risk-nodes')).toBeVisible();
  225 |   });
  226 |
  227 |   test('should display numeric values in statistics cards', async ({ page }) => {
  228 |     await page.waitForSelector('[data-testid="statistics-cards"]');
  229 |     
  230 |     // Check that statistics have numeric values using specific test IDs
  231 |     const testIds = [
  232 |       'stat-value-total-nodes',
  233 |       'stat-value-total-edges', 
  234 |       'stat-value-attack-paths',
  235 |       'stat-value-high-risk-nodes'
  236 |     ];
  237 |     
  238 |     for (const testId of testIds) {
  239 |       const valueElement = page.getByTestId(testId);
  240 |       const value = await valueElement.textContent();
  241 |       
  242 |       // Should contain a number
  243 |       expect(value).toMatch(/\d+/);
  244 |     }
  245 |   });
  246 |
  247 |   test('should handle loading states', async ({ page }) => {
  248 |     // The loading state is very fast with mock data, so we'll check that the page loads properly
  249 |     // and that we eventually see the content (which means loading completed successfully)
  250 |     
  251 |     // Wait for content to load - this implicitly tests that loading worked
  252 |     await page.waitForSelector('[data-testid="statistics-cards"]');
  253 |     
  254 |     // Verify that we have moved past loading state and have actual content
  255 |     await expect(page.getByTestId('stat-value-total-nodes')).toBeVisible();
  256 |     await expect(page.getByTestId('stat-value-total-edges')).toBeVisible();
  257 |   });
  258 |
  259 |   test('should navigate to other pages', async ({ page }) => {
  260 |     // Navigate to Graph page
  261 |     await page.getByRole('link', { name: 'Graph', exact: true }).click();
  262 |     await expect(page).toHaveURL('/graph');
  263 |     
  264 |     // Navigate back to dashboard
  265 |     await page.getByRole('link', { name: 'Dashboard', exact: true }).click();
  266 |     await expect(page).toHaveURL('/');
  267 |     
  268 |     // Test navigation to Findings page
> 269 |     await page.getByRole('link', { name: 'Findings', exact: true }).click();
      |                                                                     ^ TimeoutError: locator.click: Timeout 15000ms exceeded.
  270 |     await expect(page).toHaveURL('/findings');
  271 |   });
  272 |
  273 |   test('should handle statistics card clicks', async ({ page }) => {
  274 |     await page.waitForSelector('[data-testid="statistics-cards"]');
  275 |     
  276 |     // Click on nodes card should navigate to nodes page
  277 |     const nodesCard = page.getByTestId('stat-card-nodes');
  278 |     if (await nodesCard.isVisible()) {
  279 |       await nodesCard.click();
  280 |       await expect(page).toHaveURL('/nodes');
  281 |     }
  282 |   });
  283 |
  284 |   test('should be responsive on different screen sizes', async ({ page }) => {
  285 |     await page.waitForSelector('[data-testid="statistics-cards"]');
  286 |     
  287 |     // Test tablet viewport
  288 |     await page.setViewportSize({ width: 768, height: 1024 });
  289 |     await expect(page.getByTestId('statistics-cards')).toBeVisible();
  290 |     
  291 |     // Test desktop viewport
  292 |     await page.setViewportSize({ width: 1920, height: 1080 });
  293 |     await expect(page.getByTestId('statistics-cards')).toBeVisible();
  294 |   });
  295 |
  296 |   test('should display error state gracefully', async ({ page }) => {
  297 |     // Mock a network error by intercepting the data service calls
  298 |     await page.route('**/data/**', route => {
  299 |       route.abort();
  300 |     });
  301 |     
  302 |     // Navigate to trigger the error
  303 |     await page.goto('/');
  304 |     
  305 |     // The app should still show the basic layout even with errors
  306 |     await expect(page.getByRole('link', { name: 'Dashboard', exact: true })).toBeVisible();
  307 |     
  308 |     // For now, we'll verify the page doesn't crash rather than looking for specific error text
  309 |     // since the error handling might show different messages or handle errors gracefully
  310 |     const pageTitle = await page.title();
  311 |     expect(pageTitle).toBeTruthy(); // Page should still have a title
  312 |   });
  313 |
  314 |   test('should handle empty data state', async ({ page }) => {
  315 |     // Setup empty data response for both endpoints
  316 |     await page.route('**/data/graph/latest.json', route => {
  317 |       route.fulfill({
  318 |         status: 200,
  319 |         contentType: 'application/json',
  320 |         body: JSON.stringify({
  321 |           nodes: [],
  322 |           edges: [],
  323 |           metadata: {
  324 |             total_nodes: 0,
  325 |             total_edges: 0,
  326 |             collection_time: new Date().toISOString(),
  327 |             gcp_projects: []
  328 |           }
  329 |         })
  330 |       });
  331 |     });
  332 |     
  333 |     await page.route('**/data/analysis/latest.json', route => {
  334 |       route.fulfill({
  335 |         status: 200,
  336 |         contentType: 'application/json',
  337 |         body: JSON.stringify({
  338 |           statistics: {
  339 |             total_nodes: 0,
  340 |             total_edges: 0,
  341 |             attack_paths: 0,
  342 |             high_risk_nodes: 0,
  343 |             dangerous_roles: 0,
  344 |             critical_nodes: 0
  345 |           },
  346 |           attack_paths: {
  347 |             critical: [],
  348 |             high: [],
  349 |             medium: []
  350 |           },
  351 |           risk_analysis: {
  352 |             overall_score: 0,
  353 |             risk_distribution: {
  354 |               critical: 0,
  355 |               high: 0,
  356 |               medium: 0,
  357 |               low: 0
  358 |             }
  359 |           }
  360 |         })
  361 |       });
  362 |     });
  363 |     
  364 |     await page.goto('/');
  365 |     await page.waitForSelector('[data-testid="statistics-cards"]');
  366 |     
  367 |     // Should show zero values in the statistics
  368 |     await expect(page.getByTestId('stat-value-total-nodes')).toContainText('0');
  369 |     await expect(page.getByTestId('stat-value-total-edges')).toContainText('0');
```