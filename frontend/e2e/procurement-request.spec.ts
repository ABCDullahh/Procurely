import { test, expect } from '@playwright/test'

/**
 * Procurement Request E2E Tests
 * Tests the full flow of creating and submitting a procurement request
 */
test.describe('Procurement Request Flow', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.getByPlaceholder(/email/i).fill('admin@procurely.dev')
    await page.getByPlaceholder(/password/i).fill('admin123')
    await page.getByRole('button', { name: /log in/i }).click()
    await expect(page).toHaveURL(/dashboard/)
  })

  test('should navigate to new request page', async ({ page }) => {
    await page.goto('/requests')
    await page.getByRole('link', { name: /new request/i }).click()
    await expect(page).toHaveURL(/requests\/new/)
  })

  test('should create a new procurement request - step by step', async ({ page }) => {
    await page.goto('/requests/new')

    // Step 1: Basics
    await expect(page.getByText(/basics/i)).toBeVisible()
    await page.getByLabel(/request title/i).fill('Cloud Infrastructure Provider')
    await page.getByText('Cloud Services').click()
    await page.getByRole('button', { name: /next/i }).click()

    // Step 2: Requirements (Keywords)
    await expect(page.getByText(/requirements/i)).toBeVisible()
    await page.getByPlaceholder(/add a keyword/i).fill('cloud hosting')
    await page.getByRole('button', { name: /add/i }).click()
    await page.getByPlaceholder(/add a keyword/i).fill('scalable')
    await page.getByRole('button', { name: /add/i }).click()
    await page.getByRole('button', { name: /next/i }).click()

    // Step 3: Criteria
    await expect(page.getByText(/criteria/i)).toBeVisible()
    await page.getByRole('button', { name: /next/i }).click()

    // Step 4: Data Sources (Provider Selection)
    await expect(page.getByText(/data sources/i)).toBeVisible()
    // Should have default providers selected
    await page.getByRole('button', { name: /next/i }).click()

    // Step 5: Review
    await expect(page.getByText(/review/i)).toBeVisible()
    await expect(page.getByText('Cloud Infrastructure Provider')).toBeVisible()
    await expect(page.getByText('Cloud Services')).toBeVisible()
    await expect(page.getByText(/cloud hosting/i)).toBeVisible()

    // Create draft
    await page.getByRole('button', { name: /create draft/i }).click()

    // Should redirect to requests list
    await expect(page).toHaveURL(/requests/)
  })

  test('should show provider selection in step 4', async ({ page }) => {
    await page.goto('/requests/new')

    // Navigate to step 4
    await page.getByLabel(/request title/i).fill('Test Request')
    await page.getByText('Software Development').click()
    await page.getByRole('button', { name: /next/i }).click()

    await page.getByPlaceholder(/add a keyword/i).fill('test')
    await page.getByRole('button', { name: /add/i }).click()
    await page.getByRole('button', { name: /next/i }).click()
    await page.getByRole('button', { name: /next/i }).click()

    // Step 4: Data Sources
    await expect(page.getByText(/data sources/i)).toBeVisible()
    await expect(page.getByText(/select which data sources/i)).toBeVisible()

    // Should show provider options
    await expect(page.getByText(/serper|jina|tavily/i)).toBeVisible()
  })

  test('should submit request and start search', async ({ page }) => {
    // First create a request
    await page.goto('/requests/new')
    await page.getByLabel(/request title/i).fill('E2E Test Request')
    await page.getByText('IT Infrastructure').click()
    await page.getByRole('button', { name: /next/i }).click()

    await page.getByPlaceholder(/add a keyword/i).fill('networking')
    await page.getByRole('button', { name: /add/i }).click()
    await page.getByRole('button', { name: /next/i }).click()
    await page.getByRole('button', { name: /next/i }).click()
    await page.getByRole('button', { name: /next/i }).click()
    await page.getByRole('button', { name: /create draft/i }).click()

    await expect(page).toHaveURL(/requests/)

    // Find and click on the request
    await page.getByText('E2E Test Request').click()

    // Submit the request
    await page.getByRole('button', { name: /submit|start search/i }).click()

    // Should show progress
    await expect(page.getByText(/running|queued|searching/i)).toBeVisible({ timeout: 10000 })
  })
})
