import { Page, Locator, expect } from '@playwright/test';

/**
 * Base Page Object Model
 * Provides common functionality for all page objects
 */
export abstract class BasePage {
  readonly page: Page;

  constructor(page: Page) {
    this.page = page;
  }

  // Common elements across all pages
  get navigation() {
    return this.page.locator('nav, [role="navigation"]');
  }

  get header() {
    return this.page.locator('header');
  }

  get main() {
    return this.page.locator('main');
  }

  get loadingSpinner() {
    return this.page.getByRole('img', { name: /loading/i });
  }

  get errorMessage() {
    return this.page.getByText(/error|failed/i);
  }

  // Navigation links
  get dashboardLink() {
    return this.page.getByRole('link', { name: /dashboard/i });
  }

  get graphLink() {
    return this.page.getByRole('link', { name: /graph/i });
  }

  get findingsLink() {
    return this.page.getByRole('link', { name: /findings/i });
  }

  get nodesLink() {
    return this.page.getByRole('link', { name: /nodes/i });
  }

  get edgesLink() {
    return this.page.getByRole('link', { name: /edges/i });
  }

  get settingsLink() {
    return this.page.getByRole('link', { name: /settings/i });
  }

  // Common actions
  async goto(path: string = '') {
    await this.page.goto(path);
  }

  async waitForPageLoad() {
    await this.page.waitForLoadState('networkidle');
  }

  async waitForDataLoad() {
    // Wait for loading spinner to disappear
    await this.loadingSpinner.waitFor({ state: 'hidden', timeout: 10000 });
  }

  async navigateTo(pageName: 'dashboard' | 'graph' | 'findings' | 'nodes' | 'edges' | 'settings') {
    const linkMap = {
      dashboard: this.dashboardLink,
      graph: this.graphLink,
      findings: this.findingsLink,
      nodes: this.nodesLink,
      edges: this.edgesLink,
      settings: this.settingsLink
    };

    await linkMap[pageName].click();
    await this.waitForPageLoad();
  }

  async verifyPageTitle(expectedTitle: string | RegExp) {
    const title = this.page.locator('h1').first();
    if (typeof expectedTitle === 'string') {
      await expect(title).toContainText(expectedTitle);
    } else {
      await expect(title).toContainText(expectedTitle);
    }
  }

  async verifyUrl(expectedUrl: string | RegExp) {
    await expect(this.page).toHaveURL(expectedUrl);
  }

  async verifyNoErrors() {
    await expect(this.errorMessage).not.toBeVisible();
  }

  async verifyPageIsLoaded() {
    await this.waitForDataLoad();
    await this.verifyNoErrors();
  }

  // Common assertions
  async assertNavigationVisible() {
    await expect(this.navigation).toBeVisible();
    await expect(this.dashboardLink).toBeVisible();
    await expect(this.graphLink).toBeVisible();
    await expect(this.findingsLink).toBeVisible();
  }

  async assertActiveNavigation(pageName: string) {
    const activeLink = this.page.getByRole('link', { name: new RegExp(pageName, 'i') });
    await expect(activeLink).toHaveClass(/active|current/);
  }

  // Responsive testing helpers
  async setTabletViewport() {
    await this.page.setViewportSize({ width: 768, height: 1024 });
  }

  async setDesktopViewport() {
    await this.page.setViewportSize({ width: 1920, height: 1080 });
  }

  // Accessibility helpers
  async checkKeyboardNavigation() {
    await this.page.keyboard.press('Tab');
    const focused = this.page.locator(':focus');
    await expect(focused).toBeVisible();
  }

  async activateWithKeyboard(action: 'Enter' | 'Space' = 'Enter') {
    await this.page.keyboard.press(action);
  }

  // Data mocking helpers
  async mockApiResponse(route: string, response: any) {
    await this.page.route(route, route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(response)
      });
    });
  }

  async mockApiError(route: string, status: number = 500) {
    await this.page.route(route, route => {
      route.fulfill({
        status,
        contentType: 'application/json',
        body: JSON.stringify({ error: 'Mock error for testing' })
      });
    });
  }

  // Performance helpers
  async measurePageLoadTime(): Promise<number> {
    const startTime = Date.now();
    await this.waitForPageLoad();
    return Date.now() - startTime;
  }

  // Screenshot helpers
  async takeScreenshot(name: string) {
    await this.page.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png`,
      fullPage: true 
    });
  }

  async takeElementScreenshot(element: Locator, name: string) {
    await element.screenshot({ 
      path: `test-results/screenshots/${name}-${Date.now()}.png` 
    });
  }
} 