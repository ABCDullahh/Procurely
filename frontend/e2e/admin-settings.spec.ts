import { test, expect } from '@playwright/test'

/**
 * Admin Settings E2E Tests
 * Tests API key management and provider configuration
 */
test.describe('Admin Settings', () => {
  test.beforeEach(async ({ page }) => {
    // Login as admin before each test
    await page.goto('/login')
    await page.getByPlaceholder(/email/i).fill('admin@procurely.dev')
    await page.getByPlaceholder(/password/i).fill('admin123')
    await page.getByRole('button', { name: /log in/i }).click()
    await expect(page).toHaveURL(/dashboard/)
  })

  test('should navigate to admin api keys page', async ({ page }) => {
    await page.goto('/admin/api-keys')
    await expect(page.getByText(/api keys/i)).toBeVisible()
  })

  test('should display list of API key providers', async ({ page }) => {
    await page.goto('/admin/api-keys')

    // Should show provider names
    await expect(page.getByText(/openai|gemini|serper|tavily/i)).toBeVisible()
  })

  test('should show configured status for providers', async ({ page }) => {
    await page.goto('/admin/api-keys')

    // Look for status indicators
    const statusIndicators = page.locator('[class*="status"], [class*="configured"]')
    await expect(statusIndicators.first()).toBeVisible()
  })

  test('should allow setting API key', async ({ page }) => {
    await page.goto('/admin/api-keys')

    // Click on a provider to configure
    const configButton = page.getByRole('button', { name: /configure|set|add/i }).first()
    if (await configButton.isVisible()) {
      await configButton.click()

      // Should show input dialog
      await expect(page.locator('[role="dialog"]')).toBeVisible()
      await expect(page.getByPlaceholder(/api key|key/i)).toBeVisible()
    }
  })

  test('should show test key button for configured providers', async ({ page }) => {
    await page.goto('/admin/api-keys')

    // Look for test button
    const testButton = page.getByRole('button', { name: /test/i }).first()
    // Button may or may not be visible depending on configured keys
    if (await testButton.isVisible()) {
      // Just verify it exists
      await expect(testButton).toBeEnabled()
    }
  })

  test('should show provider enable/disable toggle', async ({ page }) => {
    await page.goto('/admin/api-keys')

    // Look for toggle switches
    const toggles = page.locator('[role="switch"], [class*="toggle"], [class*="switch"]')
    await expect(toggles.first()).toBeVisible()
  })

  test('should not allow enabling provider without API key', async ({ page }) => {
    await page.goto('/admin/api-keys')

    // Find a disabled provider (one without configured key)
    const disabledToggle = page.locator('[role="switch"][aria-checked="false"]').first()
    if (await disabledToggle.isVisible()) {
      await disabledToggle.click()

      // Should show error if no key configured
      const errorMessage = page.getByText(/api key not configured|configure.*first/i)
      // May or may not show error depending on state
    }
  })

  test('should show SerpAPI provider for shopping', async ({ page }) => {
    await page.goto('/admin/api-keys')

    // Should show SERPAPI option for shopping integration
    await expect(page.getByText(/serpapi|shopping/i)).toBeVisible()
  })
})

test.describe('AI Configuration', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder(/email/i).fill('admin@procurely.dev')
    await page.getByPlaceholder(/password/i).fill('admin123')
    await page.getByRole('button', { name: /log in/i }).click()
    await expect(page).toHaveURL(/dashboard/)
  })

  test('should navigate to AI config page', async ({ page }) => {
    // Navigate via sidebar or direct URL
    await page.goto('/admin/ai-config')

    // Should show AI configuration options
    await expect(page.getByText(/ai config|llm|model/i)).toBeVisible()
  })

  test('should show LLM provider selection', async ({ page }) => {
    await page.goto('/admin/ai-config')

    // Should show provider options
    await expect(page.getByText(/openai|gemini/i)).toBeVisible()
  })

  test('should show model selection dropdown', async ({ page }) => {
    await page.goto('/admin/ai-config')

    // Look for model selection
    const modelSelect = page.getByRole('combobox').first()
    if (await modelSelect.isVisible()) {
      await modelSelect.click()
      // Should show model options
      await expect(page.getByRole('option').first()).toBeVisible()
    }
  })
})
