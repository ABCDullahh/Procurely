import { test, expect } from '@playwright/test'

/**
 * Authentication E2E Tests
 */
test.describe('Authentication', () => {
  test('should show login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByRole('heading', { name: /log in/i })).toBeVisible()
    await expect(page.getByPlaceholder(/email/i)).toBeVisible()
    await expect(page.getByPlaceholder(/password/i)).toBeVisible()
  })

  test('should login with valid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder(/email/i).fill('admin@procurely.dev')
    await page.getByPlaceholder(/password/i).fill('admin123')
    await page.getByRole('button', { name: /log in/i }).click()

    // Should redirect to dashboard
    await expect(page).toHaveURL(/dashboard/)
  })

  test('should show error for invalid credentials', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder(/email/i).fill('wrong@email.com')
    await page.getByPlaceholder(/password/i).fill('wrongpassword')
    await page.getByRole('button', { name: /log in/i }).click()

    // Should show error
    await expect(page.getByText(/invalid|incorrect|failed/i)).toBeVisible()
  })

  test('should redirect unauthenticated users to login', async ({ page }) => {
    await page.goto('/dashboard')
    await expect(page).toHaveURL(/login/)
  })
})
