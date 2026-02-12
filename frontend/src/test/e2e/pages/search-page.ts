import { type Page, type Locator, expect } from '@playwright/test'
import { BasePage } from './base-page'

export class SearchPage extends BasePage {
  readonly searchInput: Locator
  readonly searchButton: Locator
  readonly filterPanel: Locator
  readonly advancedSearch: Locator
  readonly searchResults: Locator
  readonly searchResultItem: Locator
  readonly savedSearches: Locator
  readonly recentSearches: Locator
  readonly clearSearchButton: Locator
  readonly typeFilter: Locator
  readonly dateFromFilter: Locator
  readonly dateToFilter: Locator
  readonly sizeMinFilter: Locator
  readonly sizeMaxFilter: Locator

  constructor(page: Page) {
    super(page)
    this.searchInput = page.locator('input[type="search"], [placeholder*="Search"]')
    this.searchButton = page.locator('button[type="submit"], button:has(svg[class*="search"])')
    this.filterPanel = page.locator('[class*="filter-panel"], [class*="FilterPanel"]')
    this.advancedSearch = page.locator('[class*="advanced-search"], [class*="AdvancedSearch"]')
    this.searchResults = page.locator('[class*="search-results"], [class*="SearchResults"]')
    this.searchResultItem = page.locator('[class*="search-result"], [class*="SearchResult"]')
    this.savedSearches = page.locator('[class*="saved-searches"], [class*="SavedSearches"]')
    this.recentSearches = page.locator('[class*="recent-searches"], text=Recent Searches')
    this.clearSearchButton = page.locator('button:has-text("Clear"), button[title="Clear"]')
    this.typeFilter = page.locator('[class*="filter"]:has-text("Type"), select')
    this.dateFromFilter = page.locator('input[placeholder*="From"], [class*="date-from"]')
    this.dateToFilter = page.locator('input[placeholder*="To"], [class*="date-to"]')
    this.sizeMinFilter = page.locator('[class*="size-min"], input[placeholder*="Min size"]')
    this.sizeMaxFilter = page.locator('[class*="size-max"], input[placeholder*="Max size"]')
  }

  async expectLoaded() {
    await expect(this.searchInput).toBeVisible()
  }

  async fillSearchQuery(query: string) {
    await this.searchInput.fill(query)
  }

  async submitSearch() {
    await this.searchButton.click()
    await this.waitForLoad()
  }

  async pressEnter() {
    await this.searchInput.press('Enter')
    await this.waitForLoad()
  }

  async clearSearch() {
    await this.clearSearchButton.click()
  }

  async selectTypeFilter(type: 'file' | 'movie' | 'tvshow') {
    await this.typeFilter.selectOption(type)
  }

  async expectResultsVisible() {
    await expect(this.searchResults).toBeVisible()
  }

  async expectResultsCount(count: number) {
    await expect(this.searchResultItem).toHaveCount(count)
  }

  async clickOnResult(index: number) {
    await this.searchResultItem.nth(index).click()
  }

  async expectRecentSearchesVisible() {
    await expect(this.recentSearches).toBeVisible()
  }

  async clickOnRecentSearch(index: number) {
    const recentSearch = this.recentSearches.locator('..').locator('button').nth(index)
    await recentSearch.click()
  }

  async expandAdvancedSearch() {
    await this.advancedSearch.click()
  }

  async expectFilterPanelVisible() {
    await expect(this.filterPanel).toBeVisible()
  }
}
