import { test, expect } from '@playwright/test';

/**
 * E2E tests. All current tests are @smoke (no Databricks backend required).
 * Tag future tests that require a live Databricks connection (e.g. Build Segment, real preview)
 * with @databricks so CI can run: npx playwright test --grep @smoke
 */
test.describe('Audience Segmentation App', () => {
  test('should load and display header @smoke', async ({ page }) => {
    await page.goto('/');

    // Wait for the page to load
    await page.waitForLoadState('networkidle');

    // Check header is visible
    const header = page.locator('h1');
    await expect(header).toBeVisible();
    await expect(header).toHaveText('Audience Segmentation');
  });

  test('should display mode toggle @smoke', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check mode toggle buttons are visible
    const agentButton = page.getByRole('button', { name: 'Agent' });
    const builderButton = page.getByRole('button', { name: 'Builder' });

    await expect(agentButton).toBeVisible();
    await expect(builderButton).toBeVisible();
  });

  test('should display preview panel @smoke', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check preview panel elements
    const individualsLabel = page.getByText('Individuals', { exact: false });
    const householdsLabel = page.getByText('Households', { exact: false });

    await expect(individualsLabel).toBeVisible();
    await expect(householdsLabel).toBeVisible();
  });

  test('should toggle between Agent and Builder modes @smoke', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Start in Builder mode (default)
    const builderButton = page.getByRole('button', { name: 'Builder' });
    await expect(builderButton).toHaveClass(/bg-white/);

    // Click Agent mode
    const agentButton = page.getByRole('button', { name: 'Agent' });
    await agentButton.click();

    // Agent button should now be active
    await expect(agentButton).toHaveClass(/bg-white/);

    // Should see chat placeholder
    const chatPlaceholder = page.getByText('Start a conversation');
    await expect(chatPlaceholder).toBeVisible();
  });

  test('should show Builder mode with condition builder @smoke', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Click Builder mode to ensure we're there
    const builderButton = page.getByRole('button', { name: 'Builder' });
    await builderButton.click();

    // Check for instruction text
    const instructions = page.getByText('Build your audience segment');
    await expect(instructions).toBeVisible();

    // Check for Add Condition button
    const addConditionButton = page.getByText('+ Add Condition');
    await expect(addConditionButton).toBeVisible();
  });

  test('should have Build Segment button in preview panel @smoke', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for Build Segment button
    const buildButton = page.getByRole('button', { name: 'Build Segment' });
    await expect(buildButton).toBeVisible();
    // Should be disabled by default (no segment defined)
    await expect(buildButton).toBeDisabled();
  });

  test('should have View SQL button in preview panel @smoke', async ({ page }) => {
    await page.goto('/');
    await page.waitForLoadState('networkidle');

    // Check for View SQL button
    const sqlButton = page.getByRole('button', { name: 'View SQL' });
    await expect(sqlButton).toBeVisible();
  });
});
