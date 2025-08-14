# Test info

- Name: Graph Page Accessibility @accessibility >> should have accessible panels
- Location: /Users/arielkalman/EscaGCP/frontend/e2e/graph.spec.ts:533:3

# Error details

```
Error: expect.toBeVisible: Error: strict mode violation: getByRole('button', { name: /close/i }) resolved to 2 elements:
    1) <button type="button" class="absolute right-4 top-4 rounded-sm opacity-70 ring-offset-background transition-opacity hover:opacity-100 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none data-[state=open]:bg-secondary">…</button> aka locator('button').filter({ hasText: /^Close$/ })
    2) <button aria-label="Close" class="inline-flex items-center justify-center whitespace-nowrap text-sm font-medium ring-offset-background transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 hover:text-accent-foreground rounded-md h-6 w-6 p-0 hover:bg-gray-100">…</button> aka getByLabel('Close', { exact: true })

Call log:
  - expect.toBeVisible with timeout 10000ms
  - waiting for getByRole('button', { name: /close/i })

    at /Users/arielkalman/EscaGCP/frontend/e2e/graph.spec.ts:557:31
```

# Page snapshot

```yaml
- dialog "Node Details":
  - button "Close":
    - img
    - text: Close
  - heading "Node Details" [level=2]
  - paragraph: Detailed information about the selected node
  - button "Close":
    - img
    - text: Close panel
  - heading "test@example.com HIGH User Account" [level=3]:
    - img
    - heading "test@example.com" [level=2]
    - text: HIGH
    - paragraph: User Account
  - text: "Node ID:"
  - code: user:test@example.com
  - button:
    - img
  - text: "Type:"
  - paragraph: User Account
  - text: "Description:"
  - paragraph: A Google Cloud user account
  - button "View in Console":
    - img
    - text: View in Console
  - button "Export":
    - img
    - text: Export
  - tablist:
    - tab "Overview" [selected]
    - tab "Permissions"
    - tab "Relationships"
    - tab "Activity"
  - tabpanel "Overview":
    - heading "Properties" [level=3]
    - text: "email: test@example.com riskScore: 0.8"
    - heading "Risk Assessment" [level=3]:
      - img
      - text: Risk Assessment
    - text: "Risk Score: HIGH 65% Risk Factors:"
    - list:
      - listitem: High privilege level
      - listitem: Access to sensitive resources
      - listitem: Multiple escalation paths
```

# Test source

```ts
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
  549 |     await expect(page.getByTestId('node-detail-panel')).toBeVisible();
  550 |     
  551 |     // Panel should have proper heading
  552 |     const heading = page.locator('[data-testid="node-detail-panel"] h1, [data-testid="node-detail-panel"] h2');
  553 |     await expect(heading.first()).toBeVisible();
  554 |     
  555 |     // Close button should be accessible
  556 |     const closeButton = page.getByRole('button', { name: /close/i });
> 557 |     await expect(closeButton).toBeVisible();
      |                               ^ Error: expect.toBeVisible: Error: strict mode violation: getByRole('button', { name: /close/i }) resolved to 2 elements:
  558 |     await expect(closeButton).toBeFocused();
  559 |   });
  560 | }); 
```