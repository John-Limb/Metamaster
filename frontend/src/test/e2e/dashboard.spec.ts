import { test, expect } from './fixtures/test-fixtures'
import { DashboardPage } from './pages/dashboard-page'

test.describe('Dashboard Workflow', () => {
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page, mockApi }) => {
    dashboardPage = new DashboardPage(page)
    await dashboardPage.navigateTo('/dashboard')
    await dashboardPage.waitForLoad()
  })

  test('should navigate to dashboard', async () => {
    await dashboardPage.expectLoaded()
    await expect(dashboardPage.page).toHaveURL(/\/dashboard/)
  })

  test('should display statistics cards', async () => {
    await dashboardPage.expectStatsVisible()
  })

  test('should display quick actions', async () => {
    await dashboardPage.expectQuickActionsVisible()
  })

  test('should display recent activity', async () => {
    await dashboardPage.expectRecentActivityVisible()
  })

  test('should display library stats', async ({ page }) => {
    const libraryStats = page.locator('[class*="library-stats"], [class*="LibraryStats"]')
    await expect(libraryStats).toBeVisible()
  })

  test('should display storage chart', async ({ page }) => {
    const storageChart = page.locator('[class*="storage-chart"], [class*="StorageChart"]')
    await expect(storageChart).toBeVisible()
  })

  test('should have scan button', async () => {
    await dashboardPage.clickScanButton()
    // Should initiate scan or show scan dialog
  })

  test('should have settings button', async () => {
    await dashboardPage.clickSettingsButton()
    await expect(dashboardPage.page).toHaveURL(/\/settings/)
  })

  test('should display total files count', async () => {
    const totalFiles = await dashboardPage.getTotalFilesCount()
    expect(totalFiles).not.toBeNull()
  })

  test('should display indexed files count', async ({ page }) => {
    const indexedFiles = page.locator('text=Indexed Files')
    await expect(indexedFiles).toBeVisible()
  })

  test('should display total storage size', async ({ page }) => {
    const totalSize = page.locator('text=Total Size')
    await expect(totalSize).toBeVisible()
  })
})

test.describe('Dashboard - Quick Actions', () => {
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page, mockApi }) => {
    dashboardPage = new DashboardPage(page)
    await dashboardPage.navigateTo('/dashboard')
  })

  test('should display scan action', async ({ page }) => {
    const scanAction = page.locator('button:has-text("Scan"), [class*="scan"]')
    await expect(scanAction).toBeVisible()
  })

  test('should display upload action', async ({ page }) => {
    const uploadAction = page.locator('button:has-text("Upload"), [class*="upload"]')
    await expect(uploadAction).toBeVisible()
  })

  test('should display search action', async ({ page }) => {
    const searchAction = page.locator('button:has-text("Search"), [class*="search"]')
    await expect(searchAction).toBeVisible()
  })

  test('should display settings action', async ({ page }) => {
    const settingsAction = page.locator('button:has-text("Settings"), [class*="settings"]')
    await expect(settingsAction).toBeVisible()
  })

  test('should navigate to files page from quick action', async ({ page }) => {
    const filesAction = page.locator('button:has-text("Browse Files"), [class*="files"]')
    await filesAction.click()
    await expect(page).toHaveURL(/\/files/)
  })
})

test.describe('Dashboard - Recent Activity', () => {
  let dashboardPage: DashboardPage

  test.beforeEach(async ({ page, mockApi }) => {
    dashboardPage = new DashboardPage(page)
    await dashboardPage.navigateTo('/dashboard')
  })

  test('should display recent activity items', async ({ page }) => {
    const activityItems = page.locator('[class*="activity-item"], [class*="RecentActivity"] > div')
    await expect(activityItems.first()).toBeVisible()
  })

  test('should show activity timestamps', async ({ page }) => {
    const timestamps = page.locator('[class*="timestamp"], [class*="time"]')
    await expect(timestamps.first()).toBeVisible()
  })

  test('should show activity types', async ({ page }) => {
    const activityTypes = page.locator('[class*="action-type"], [class*="activity-type"]')
    await expect(activityTypes.first()).toBeVisible()
  })
})
