import { type Page, type Locator, expect } from '@playwright/test'
import { BasePage } from './base-page'

export class DashboardPage extends BasePage {
  readonly statsCards: Locator
  readonly quickActions: Locator
  readonly recentActivity: Locator
  readonly storageChart: Locator
  readonly libraryStats: Locator
  readonly totalFilesStat: Locator
  readonly indexedFilesStat: Locator
  readonly totalSizeStat: Locator
  readonly scanButton: Locator
  readonly settingsButton: Locator

  constructor(page: Page) {
    super(page)
    this.statsCards = page.locator('[class*="stat-card"], [class*="StatCard"]')
    this.quickActions = page.locator('[class*="quick-actions"], [class*="QuickActions"]')
    this.recentActivity = page.locator('[class*="recent-activity"], [class*="RecentActivity"]')
    this.storageChart = page.locator('[class*="storage-chart"], [class*="StorageChart"]')
    this.libraryStats = page.locator('[class*="library-stats"], [class*="LibraryStats"]')
    this.totalFilesStat = page.locator('text=Total Files')
    this.indexedFilesStat = page.locator('text=Indexed Files')
    this.totalSizeStat = page.locator('text=Total Size')
    this.scanButton = page.locator('button:has-text("Scan"), [class*="scan"]')
    this.settingsButton = page.locator('button:has-text("Settings"), [class*="settings"]')
  }

  async expectLoaded() {
    await expect(this.statsCards.first()).toBeVisible()
    await expect(this.libraryStats).toBeVisible()
  }

  async expectStatsVisible() {
    await expect(this.totalFilesStat).toBeVisible()
    await expect(this.indexedFilesStat).toBeVisible()
    await expect(this.totalSizeStat).toBeVisible()
  }

  async expectQuickActionsVisible() {
    await expect(this.quickActions).toBeVisible()
  }

  async expectRecentActivityVisible() {
    await expect(this.recentActivity).toBeVisible()
  }

  async clickScanButton() {
    await this.scanButton.click()
  }

  async clickSettingsButton() {
    await this.settingsButton.click()
  }

  async getTotalFilesCount(): Promise<string | null> {
    const statCard = this.statsCards.filter({ hasText: 'Total Files' })
    const count = statCard.locator('[class*="count"], [class*="value"]')
    return count.textContent()
  }
}
