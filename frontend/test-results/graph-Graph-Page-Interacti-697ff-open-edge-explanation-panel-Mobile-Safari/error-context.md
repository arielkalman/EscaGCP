# Test info

- Name: Graph Page >> Interactive Panels >> should open edge explanation panel
- Location: /Users/arielkalman/EscaGCP/frontend/e2e/graph.spec.ts:343:5

# Error details

```
Error: expect.toBeVisible: Error: strict mode violation: getByText(/iam.serviceAccounts.getAccessToken/i) resolved to 3 elements:
    1) <code class="bg-gray-100 px-2 py-1 rounded text-xs">iam.serviceAccounts.getAccessToken</code> aka getByRole('code').filter({ hasText: 'iam.serviceAccounts.' })
    2) <span title="iam.serviceAccounts.getAccessToken" class="text-gray-600 text-right max-w-48 truncate">iam.serviceAccounts.getAccessToken</span> aka getByTitle('iam.serviceAccounts.')
    3) <p class="text-sm text-gray-600">Generate access tokens using iam.serviceAccounts.…</p> aka getByText('Generate access tokens using')

Call log:
  - expect.toBeVisible with timeout 10000ms
  - waiting for getByText(/iam.serviceAccounts.getAccessToken/i)

    at /Users/arielkalman/EscaGCP/frontend/e2e/graph.spec.ts:366:75
```

# Page snapshot

```yaml
- dialog "Edge Details":
  - button "Close":
    - img
    - text: Close
  - heading "Edge Details" [level=2]
  - paragraph: Detailed information about the selected relationship
  - button "Close":
    - img
    - text: Close panel
  - heading "Service Account Impersonation CRITICAL" [level=3]:
    - img
    - text: Service Account Impersonation CRITICAL
  - paragraph: Can generate access tokens for the target service account, effectively becoming that service account.
  - text: "Edge Type:"
  - code: can_impersonate_sa
  - text: "Permission:"
  - code: iam.serviceAccounts.getAccessToken
  - heading "Connection Details" [level=3]
  - text: Source
  - code: user:attacker@external.com
  - button "Go to":
    - img
    - text: Go to
  - img
  - text: Target
  - code: service_account:sa@project.iam.gserviceaccount.com
  - button "Go to":
    - img
    - text: Go to
  - heading "Additional Properties" [level=3]
  - text: "permission: iam.serviceAccounts.getAccessToken riskScore: 0.9"
  - heading "Attack Technique" [level=3]:
    - img
    - text: Attack Technique
  - paragraph: Generate access tokens using iam.serviceAccounts.getAccessToken permission
  - heading "Mitigation Steps:" [level=4]
  - list:
    - listitem: Remove unnecessary serviceAccountTokenCreator role
    - listitem: Use short-lived tokens only
    - listitem: Enable audit logging for token generation
    - listitem: Implement organizational policy constraints
  - heading "Actions" [level=3]
  - button "Copy Edge Information":
    - img
    - text: Copy Edge Information
  - button "Export Detailed Report":
    - img
    - text: Export Detailed Report
```

# Test source

```ts
  266 |             nodeId: nodeData.id,
  267 |             nodeData: nodeData
  268 |           }
  269 |         }));
  270 |       });
  271 |       
  272 |       // Wait a bit for the event to process
  273 |       await page.waitForTimeout(1000);
  274 |       
  275 |       // Check if panel exists in DOM first
  276 |       const panel = page.getByTestId('node-detail-panel');
  277 |       const panelExists = await panel.count() > 0;
  278 |       console.log('Panel exists in DOM:', panelExists);
  279 |       
  280 |       // Also check for the debug container
  281 |       const debugContainer = page.getByTestId('debug-panel-container');
  282 |       const debugExists = await debugContainer.count() > 0;
  283 |       console.log('Debug container exists:', debugExists);
  284 |       
  285 |       if (panelExists) {
  286 |         // Should open node detail panel
  287 |         await expect(panel).toBeVisible({ timeout: 5000 });
  288 |         
  289 |         // Should display node information
  290 |         await expect(page.getByText('attacker@external.com')).toBeVisible();
  291 |         
  292 |         // Close panel
  293 |         const closeButton = page.getByRole('button', { name: /close/i });
  294 |         await closeButton.click();
  295 |         
  296 |         // Panel should be closed
  297 |         await expect(panel).toBeHidden();
  298 |       } else {
  299 |         // If panel doesn't exist, let's check what elements DO exist
  300 |         const allTestIds = await page.evaluate(() => {
  301 |           return Array.from(document.querySelectorAll('[data-testid]'))
  302 |             .map(el => el.getAttribute('data-testid'));
  303 |         });
  304 |         console.log('Available test IDs:', allTestIds);
  305 |         
  306 |         // For now, just check that the event was dispatched (this test will still fail but with better info)
  307 |         await expect(panel).toBeVisible({ timeout: 1000 });
  308 |       }
  309 |     });
  310 |
  311 |     test('should display tabbed content in node panel', async ({ page }) => {
  312 |       // Open node panel
  313 |       await page.evaluate(() => {
  314 |         window.dispatchEvent(new CustomEvent('nodeSelected', {
  315 |           detail: {
  316 |             nodeId: 'user:attacker@external.com',
  317 |             nodeData: {
  318 |               id: 'user:attacker@external.com',
  319 |               type: 'user',
  320 |               name: 'attacker@external.com',
  321 |               properties: { email: 'attacker@external.com', riskScore: 0.9 }
  322 |             }
  323 |           }
  324 |         }));
  325 |       });
  326 |       
  327 |       await expect(page.getByTestId('node-detail-panel')).toBeVisible();
  328 |       
  329 |       // Check for tabs
  330 |       await expect(page.getByRole('tab', { name: /overview/i })).toBeVisible();
  331 |       await expect(page.getByRole('tab', { name: /permissions/i })).toBeVisible();
  332 |       await expect(page.getByRole('tab', { name: /relationships/i })).toBeVisible();
  333 |       await expect(page.getByRole('tab', { name: /activity/i })).toBeVisible();
  334 |       
  335 |       // Click on different tabs
  336 |       await page.getByRole('tab', { name: /permissions/i }).click();
  337 |       await expect(page.getByText(/permissions/i)).toBeVisible();
  338 |       
  339 |       await page.getByRole('tab', { name: /relationships/i }).click();
  340 |       await expect(page.getByText(/relationships/i)).toBeVisible();
  341 |     });
  342 |
  343 |     test('should open edge explanation panel', async ({ page }) => {
  344 |       await page.waitForSelector('[data-testid="graph-canvas"]');
  345 |       
  346 |       // Simulate edge click
  347 |       await page.evaluate(() => {
  348 |         window.dispatchEvent(new CustomEvent('edgeSelected', {
  349 |           detail: {
  350 |             edgeId: 'edge_1',
  351 |             edgeData: {
  352 |               source: 'user:attacker@external.com',
  353 |               target: 'service_account:sa@project.iam.gserviceaccount.com',
  354 |               type: 'can_impersonate_sa',
  355 |               properties: { permission: 'iam.serviceAccounts.getAccessToken', riskScore: 0.9 }
  356 |             }
  357 |           }
  358 |         }));
  359 |       });
  360 |       
  361 |       // Should open edge explanation panel
  362 |       await expect(page.getByTestId('edge-explanation-panel')).toBeVisible({ timeout: 5000 });
  363 |       
  364 |       // Should display edge information
  365 |       await expect(page.getByText(/can_impersonate_sa/i)).toBeVisible();
> 366 |       await expect(page.getByText(/iam.serviceAccounts.getAccessToken/i)).toBeVisible();
      |                                                                           ^ Error: expect.toBeVisible: Error: strict mode violation: getByText(/iam.serviceAccounts.getAccessToken/i) resolved to 3 elements:
  367 |     });
  368 |   });
  369 |
  370 |   test.describe('Performance', () => {
  371 |     test('should handle large graphs', async ({ page }) => {
  372 |       // Setup large graph data
  373 |       await page.route('**/api/graph', route => {
  374 |         const nodes = [];
  375 |         const edges = [];
  376 |         
  377 |         // Generate 500 nodes
  378 |         for (let i = 0; i < 500; i++) {
  379 |           nodes.push({
  380 |             id: `node_${i}`,
  381 |             type: i % 2 === 0 ? 'user' : 'project',
  382 |             name: `node_${i}`,
  383 |             properties: { riskScore: Math.random() }
  384 |           });
  385 |         }
  386 |         
  387 |         // Generate 1000 edges
  388 |         for (let i = 0; i < 1000; i++) {
  389 |           const source = nodes[Math.floor(Math.random() * nodes.length)];
  390 |           const target = nodes[Math.floor(Math.random() * nodes.length)];
  391 |           
  392 |           if (source.id !== target.id) {
  393 |             edges.push({
  394 |               source: source.id,
  395 |               target: target.id,
  396 |               type: 'has_role',
  397 |               properties: { riskScore: Math.random() }
  398 |             });
  399 |           }
  400 |         }
  401 |         
  402 |         route.fulfill({
  403 |           status: 200,
  404 |           contentType: 'application/json',
  405 |           body: JSON.stringify({
  406 |             nodes,
  407 |             edges,
  408 |             metadata: {
  409 |               total_nodes: nodes.length,
  410 |               total_edges: edges.length,
  411 |               collection_time: new Date().toISOString(),
  412 |               gcp_projects: ['large-project']
  413 |             }
  414 |           })
  415 |         });
  416 |       });
  417 |       
  418 |       await page.goto('/graph');
  419 |       
  420 |       // Should load within reasonable time
  421 |       await page.waitForSelector('[data-testid="graph-canvas"]', { timeout: 30000 });
  422 |       
  423 |       // Should still be responsive
  424 |       const zoomButton = page.getByRole('button', { name: /zoom in/i });
  425 |       await zoomButton.click();
  426 |       
  427 |       // Should not show performance warnings or errors
  428 |       const errorMessage = page.getByText(/error|warning/i);
  429 |       await expect(errorMessage).not.toBeVisible();
  430 |     });
  431 |
  432 |     test('should load within performance budget', async ({ page }) => {
  433 |       const startTime = Date.now();
  434 |       
  435 |       await page.goto('/graph');
  436 |       await page.waitForSelector('[data-testid="graph-canvas"]');
  437 |       
  438 |       const loadTime = Date.now() - startTime;
  439 |       
  440 |       // Should load within 10 seconds
  441 |       expect(loadTime).toBeLessThan(10000);
  442 |     });
  443 |   });
  444 |
  445 |   test.describe('Error Handling', () => {
  446 |     test('should handle API errors gracefully', async ({ page }) => {
  447 |       await page.route('**/api/graph', route => route.abort('failed'));
  448 |       
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
```