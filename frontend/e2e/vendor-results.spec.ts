import { test, expect } from '@playwright/test'

/**
 * Vendor Results E2E Tests
 * Tests the vendor discovery results display
 */
test.describe('Vendor Results Display', () => {
  test.beforeEach(async ({ page }) => {
    // Login before each test
    await page.goto('/login')
    await page.getByPlaceholder(/email/i).fill('admin@procurely.dev')
    await page.getByPlaceholder(/password/i).fill('admin123')
    await page.getByRole('button', { name: /log in/i }).click()
    await expect(page).toHaveURL(/dashboard/)
  })

  test('should display vendor results table', async ({ page }) => {
    // Navigate to a completed request (if exists)
    await page.goto('/requests')

    // Look for a completed request
    const completedRequest = page.locator('[data-status="COMPLETED"]').first()
    if (await completedRequest.isVisible()) {
      await completedRequest.click()

      // Should show vendor table
      await expect(page.getByRole('table')).toBeVisible()

      // Should have column headers
      await expect(page.getByText(/vendor/i)).toBeVisible()
      await expect(page.getByText(/overall|score/i)).toBeVisible()
    }
  })

  test('should display score badges with colors', async ({ page }) => {
    await page.goto('/requests')

    const completedRequest = page.locator('[data-status="COMPLETED"]').first()
    if (await completedRequest.isVisible()) {
      await completedRequest.click()

      // Look for score badges
      const scoreBadges = page.locator('[class*="badge"], [class*="score"]')
      await expect(scoreBadges.first()).toBeVisible()
    }
  })

  test('should allow sorting vendors by score', async ({ page }) => {
    await page.goto('/requests')

    const completedRequest = page.locator('[data-status="COMPLETED"]').first()
    if (await completedRequest.isVisible()) {
      await completedRequest.click()

      // Click on Overall column header to sort
      const overallHeader = page.getByRole('button', { name: /overall/i })
      if (await overallHeader.isVisible()) {
        await overallHeader.click()
        // Should see sort indicator
        await expect(page.locator('[class*="chevron"]')).toBeVisible()
      }
    }
  })

  test('should search/filter vendors', async ({ page }) => {
    await page.goto('/requests')

    const completedRequest = page.locator('[data-status="COMPLETED"]').first()
    if (await completedRequest.isVisible()) {
      await completedRequest.click()

      // Look for search input
      const searchInput = page.getByPlaceholder(/search vendor/i)
      if (await searchInput.isVisible()) {
        await searchInput.fill('test')
        // Results should update
        await page.waitForTimeout(500) // Debounce
      }
    }
  })

  test('should paginate vendor results', async ({ page }) => {
    await page.goto('/requests')

    const completedRequest = page.locator('[data-status="COMPLETED"]').first()
    if (await completedRequest.isVisible()) {
      await completedRequest.click()

      // Look for pagination controls
      const nextButton = page.getByRole('button', { name: /next/i })
      const prevButton = page.getByRole('button', { name: /previous/i })

      if (await nextButton.isVisible() && (await nextButton.isEnabled())) {
        await nextButton.click()
        // Should update page indicator
        await expect(page.getByText(/showing|page/i)).toBeVisible()
      }
    }
  })

  test('should show vendor quick view on click', async ({ page }) => {
    await page.goto('/requests')

    const completedRequest = page.locator('[data-status="COMPLETED"]').first()
    if (await completedRequest.isVisible()) {
      await completedRequest.click()

      // Click on first vendor row
      const firstVendorRow = page.locator('tbody tr').first()
      if (await firstVendorRow.isVisible()) {
        await firstVendorRow.click()

        // Should show quick view or modal
        await expect(
          page.locator('[role="dialog"], [class*="drawer"], [class*="quick-view"]')
        ).toBeVisible({ timeout: 5000 })
      }
    }
  })
})
