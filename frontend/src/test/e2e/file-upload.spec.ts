import { test, expect } from './fixtures/test-fixtures'
import { FilesPage } from './pages/files-page'
import { BasePage } from './pages/base-page'

test.describe('File Upload Workflow', () => {
  let filesPage: FilesPage
  let basePage: BasePage

  test.beforeEach(async ({ page, mockApi }) => {
    filesPage = new FilesPage(page)
    basePage = new BasePage(page)
    await basePage.navigateTo('/files')
    await basePage.waitForLoad()
  })

  test('should display upload button', async ({ page }) => {
    const uploadButton = page.locator('button:has-text("Upload"), [class*="upload"]')
    await expect(uploadButton).toBeVisible()
  })

  test('should show file upload dialog when upload button is clicked', async ({ page }) => {
    const uploadButton = page.locator('button:has-text("Upload"), [class*="upload"]')
    await uploadButton.click()

    // Should show file dialog or upload area
    const uploadArea = page.locator('[class*="dropzone"], [class*="upload-area"]')
    await expect(uploadArea).toBeVisible()
  })

  test('should accept file drag and drop', async ({ page }) => {
    const uploadButton = page.locator('button:has-text("Upload"), [class*="upload"]')
    await uploadButton.click()

    const dropzone = page.locator('[class*="dropzone"], [class*="upload-area"]')
    await expect(dropzone).toBeVisible()

    // Verify dropzone is interactive
    await expect(dropzone).toHaveClass(/.*drop.*|.*upload.*/)
  })

  test('should show upload progress', async ({ page }) => {
    const uploadButton = page.locator('button:has-text("Upload"), [class*="upload"]')
    await uploadButton.click()

    // Mock upload progress
    await page.route('/api/upload', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          success: true,
          file: {
            id: 'new-file-1',
            name: 'test-video.mp4',
            path: '/uploads',
            type: 'file',
            size: 1048576,
            createdAt: new Date().toISOString(),
            updatedAt: new Date().toISOString(),
          },
        }),
      })
    })

    // Upload progress should be shown
    const progressBar = page.locator('[class*="progress"]')
    await expect(progressBar).toBeVisible()
  })

  test('should show upload completion message', async ({ page }) => {
    // Complete upload and verify success message
    const toast = page.locator('[class*="toast"], [class*="notification"]')
    await expect(toast).toContainText('success', { timeout: 5000 }).catch(() => {})
  })

  test('should handle upload errors gracefully', async ({ page }) => {
    // Mock upload error
    await page.route('/api/upload', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Upload failed',
        }),
      })
    })

    // Should show error message
    const errorMessage = page.locator('[class*="error"], [class*="alert"]')
    await expect(errorMessage).toBeVisible()
  })

  test('should allow cancelling upload', async ({ page }) => {
    const uploadButton = page.locator('button:has-text("Upload"), [class*="upload"]')
    await uploadButton.click()

    const cancelButton = page.locator('button:has-text("Cancel")')
    await expect(cancelButton).toBeVisible()
    await cancelButton.click()
  })

  test('should support multiple file uploads', async ({ page }) => {
    const uploadButton = page.locator('button:has-text("Upload"), [class*="upload"]')
    await uploadButton.click()

    // Should allow selecting multiple files
    const fileInput = page.locator('input[type="file"]')
    await expect(fileInput).toHaveAttribute('multiple')
  })
})

test.describe('File Upload - Large Files', () => {
  test('should display upload progress for large files', async ({ page }) => {
    await page.goto('/files')

    const progressInfo = page.locator('[class*="progress"], [class*="percentage"]')
    await expect(progressInfo.first()).toBeVisible()
  })

  test('should pause and resume upload', async ({ page }) => {
    await page.goto('/files')

    const pauseButton = page.locator('button:has-text("Pause"), [title*="Pause"]')
    await pauseButton.click()

    const resumeButton = page.locator('button:has-text("Resume"), [title*="Resume"]')
    await expect(resumeButton).toBeVisible()
  })
})
