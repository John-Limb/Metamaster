import { test, expect } from './fixtures/test-fixtures'
import { SearchPage } from './pages/search-page'

test.describe('Search Workflow', () => {
  let searchPage: SearchPage

  test.beforeEach(async ({ page, mockApi }) => {
    searchPage = new SearchPage(page)
    await searchPage.navigateTo('/search')
    await searchPage.waitForLoad()
  })

  test('should navigate to search page', async () => {
    await searchPage.expectLoaded()
    await expect(searchPage.page).toHaveURL(/\/search/)
  })

  test('should display search input', async () => {
    await expect(searchPage.searchInput).toBeVisible()
  })

  test('should perform basic search', async () => {
    await searchPage.fillSearchQuery('test')
    await searchPage.pressEnter()
    await searchPage.expectResultsVisible()
  })

  test('should show results after search', async () => {
    await searchPage.fillSearchQuery('movie')
    await searchPage.submitSearch()
    await searchPage.expectResultsVisible()
    await searchPage.expectResultsCount(1)
  })

  test('should display search suggestions', async ({ page }) => {
    await searchPage.fillSearchQuery('mov')
    // Wait for debounced suggestions
    await page.waitForTimeout(500)

    const suggestions = page.locator('[role="option"]')
    await expect(suggestions.first()).toBeVisible()
  })

  test('should filter by type', async () => {
    await searchPage.selectTypeFilter('file')
    await searchPage.pressEnter()
    await searchPage.expectResultsVisible()
  })

  test('should clear search', async () => {
    await searchPage.fillSearchQuery('test query')
    await searchPage.clearSearch()
    await expect(searchPage.searchInput).toHaveValue('')
  })

  test('should show recent searches', async () => {
    await searchPage.searchInput.click()
    await searchPage.expectRecentSearchesVisible()
  })

  test('should navigate to result on click', async () => {
    await searchPage.fillSearchQuery('movie')
    await searchPage.pressEnter()
    await searchPage.expectResultsVisible()

    await searchPage.clickOnResult(0)
    // Should navigate to the file or show details
  })

  test('should accept keyboard navigation', async ({ page }) => {
    await searchPage.fillSearchQuery('test')
    await searchPage.searchInput.press('ArrowDown')
    // Should navigate through suggestions
  })

  test('should close suggestions on escape', async ({ page }) => {
    await searchPage.fillSearchQuery('test')
    await searchPage.searchInput.press('Escape')
    const suggestions = page.locator('[role="option"]')
    await expect(suggestions).not.toBeVisible()
  })
})

test.describe('Advanced Search', () => {
  let searchPage: SearchPage

  test.beforeEach(async ({ page, mockApi }) => {
    searchPage = new SearchPage(page)
    await searchPage.navigateTo('/search')
  })

  test('should display filter panel', async () => {
    await searchPage.expectFilterPanelVisible()
  })

  test('should filter by date range', async () => {
    await searchPage.dateFromFilter.fill('2024-01-01')
    await searchPage.dateToFilter.fill('2024-12-31')
    await searchPage.pressEnter()
    await searchPage.expectResultsVisible()
  })

  test('should filter by size range', async () => {
    await searchPage.sizeMinFilter.fill('1000000')
    await searchPage.sizeMaxFilter.fill('5000000000')
    await searchPage.pressEnter()
    await searchPage.expectResultsVisible()
  })

  test('should combine multiple filters', async () => {
    await searchPage.fillSearchQuery('video')
    await searchPage.selectTypeFilter('file')
    await searchPage.sizeMinFilter.fill('1000000')
    await searchPage.pressEnter()
    await searchPage.expectResultsVisible()
  })

  test('should show advanced search options', async ({ page }) => {
    const advancedSearchToggle = page.locator('button:has-text("Advanced"), [class*="advanced"]')
    await expect(advancedSearchToggle).toBeVisible()
  })
})

test.describe('Search - Empty States', () => {
  let searchPage: SearchPage

  test.beforeEach(async ({ page }) => {
    searchPage = new SearchPage(page)
  })

  test('should show no results message', async ({ page }) => {
    await searchPage.navigateTo('/search')
    await searchPage.fillSearchQuery('nonexistent')
    await searchPage.pressEnter()

    const noResults = page.locator('text=No results, text=No files found')
    await expect(noResults.first()).toBeVisible({ timeout: 5000 })
  })

  test('should show initial state with hints', async ({ page }) => {
    await searchPage.navigateTo('/search')

    const hints = page.locator('text=Search, text=Start typing')
    await expect(hints.first()).toBeVisible()
  })
})
