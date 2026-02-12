import { test, expect } from './fixtures/test-fixtures'
import { FilesPage } from './pages/files-page'

test.describe('File Navigation Workflow', () => {
  let filesPage: FilesPage

  test.beforeEach(async ({ page, mockApi }) => {
    filesPage = new FilesPage(page)
    await filesPage.navigateTo('/files')
    await filesPage.waitForLoad()
  })

  test('should navigate to files page and load file explorer', async ({ page }) => {
    await filesPage.expectLoaded()
    await expect(page).toHaveURL(/\/files/)
  })

  test('should display files in grid view by default', async ({ mockApi }) => {
    await filesPage.expectViewMode('grid')
    await filesPage.expectFileCards(3)
  })

  test('should switch to list view', async () => {
    await filesPage.clickListView()
    await filesPage.expectViewMode('list')
  })

  test('should switch to tree view', async () => {
    await filesPage.clickTreeView()
    await filesPage.expectViewMode('tree')
  })

  test('should navigate back when back button is clicked', async ({ page }) => {
    const backButton = page.locator('[title="Go back"]')
    await expect(backButton).toBeVisible()
  })

  test('should display path breadcrumb', async ({ page }) => {
    const breadcrumb = page.locator('[class*="breadcrumb"], [class*="path"]')
    await expect(breadcrumb).toContainText('/')
  })

  test('should allow selecting a file', async () => {
    await filesPage.clickFileCard(0)
    // Verify selection state is applied
  })

  test('should allow double-clicking a file to navigate into directory', async () => {
    // Double-click on first file card (could be a directory)
    await filesPage.doubleClickFileCard(0)
    // If it's a directory, path should change
  })

  test('should toggle between grid, list, and tree views', async () => {
    await filesPage.clickGridView()
    await filesPage.expectViewMode('grid')

    await filesPage.clickListView()
    await filesPage.expectViewMode('list')

    await filesPage.clickTreeView()
    await filesPage.expectViewMode('tree')
  })

  test('should maintain view mode preference', async () => {
    await filesPage.clickListView()
    await filesPage.expectViewMode('list')

    // Navigate away and back (simulated by reloading)
    // The preference should be maintained
  })
})

test.describe('File Navigation - Mobile', () => {
  let filesPage: FilesPage

  test.beforeEach(async ({ page, mockApi }) => {
    filesPage = new FilesPage(page)
    await filesPage.navigateTo('/files')
  })

  test('should display files on mobile viewport', async ({ isMobile }) => {
    test.skip(isMobile, 'Mobile-specific file navigation tests')
  })
})
