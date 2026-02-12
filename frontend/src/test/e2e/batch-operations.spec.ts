import { test, expect } from './fixtures/test-fixtures'
import { FilesPage } from './pages/files-page'

test.describe('Batch Operations Workflow', () => {
  let filesPage: FilesPage

  test.beforeEach(async ({ page, mockApi }) => {
    filesPage = new FilesPage(page)
    await filesPage.navigateTo('/files')
    await filesPage.waitForLoad()
  })

  test('should display batch operations button when files are selected', async ({ page }) => {
    // Select multiple files
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    // Batch operations button should appear
    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await expect(batchButton).toBeVisible()
  })

  test('should open batch operation modal when button is clicked', async ({ page }) => {
    // Select files
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    // Click batch operations button
    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await batchButton.click()

    // Modal should open
    const modal = page.locator('[class*="modal"], [class*="dialog"]')
    await expect(modal).toBeVisible()
  })

  test('should display selected file count', async ({ page }) => {
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    // Should show count of selected files
    const selectionCount = page.locator('[class*="selection-count"], [class*="selected"]')
    await expect(selectionCount).toContainText('2')
  })

  test('should allow selecting all files', async ({ page }) => {
    const selectAllCheckbox = page.locator('[class*="select-all"], input[type="checkbox"]')
    await selectAllCheckbox.click()

    // All files should be selected
    await expect(selectAllCheckbox).toBeChecked()
  })

  test('should allow deselecting all files', async ({ page }) => {
    // Select all first
    const selectAllCheckbox = page.locator('[class*="select-all"], input[type="checkbox"]')
    await selectAllCheckbox.click()
    await selectAllCheckbox.click()

    // All files should be deselected
    await expect(selectAllCheckbox).not.toBeChecked()
  })

  test('should show delete option in batch operations', async ({ page }) => {
    // Select files and open batch modal
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await batchButton.click()

    // Delete option should be available
    const deleteOption = page.locator('button:has-text("Delete"), [class*="delete"]')
    await expect(deleteOption).toBeVisible()
  })

  test('should show move option in batch operations', async ({ page }) => {
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await batchButton.click()

    // Move option should be available
    const moveOption = page.locator('button:has-text("Move"), [class*="move"]')
    await expect(moveOption).toBeVisible()
  })

  test('should show copy option in batch operations', async ({ page }) => {
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await batchButton.click()

    // Copy option should be available
    const copyOption = page.locator('button:has-text("Copy"), [class*="copy"]')
    await expect(copyOption).toBeVisible()
  })

  test('should show tag option in batch operations', async ({ page }) => {
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await batchButton.click()

    // Tag option should be available
    const tagOption = page.locator('button:has-text("Tag"), [class*="tag"]')
    await expect(tagOption).toBeVisible()
  })

  test('should confirm delete operation', async ({ page }) => {
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await batchButton.click()

    const deleteOption = page.locator('button:has-text("Delete"), [class*="delete"]')
    await deleteOption.click()

    // Confirmation dialog should appear
    const confirmButton = page.locator('button:has-text("Confirm"), [class*="confirm"]')
    await expect(confirmButton).toBeVisible()
  })

  test('should cancel batch operation', async ({ page }) => {
    await page.keyboard.down('Control')
    await filesPage.clickFileCard(0)
    await filesPage.clickFileCard(1)
    await page.keyboard.up('Control')

    const batchButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    await batchButton.click()

    const cancelButton = page.locator('button:has-text("Cancel"), [class*="cancel"]')
    await expect(cancelButton).toBeVisible()
    await cancelButton.click()

    // Modal should close
    const modal = page.locator('[class*="modal"], [class*="dialog"]')
    await expect(modal).not.toBeVisible()
  })
})
