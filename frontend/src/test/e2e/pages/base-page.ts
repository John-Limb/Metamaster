import { type Page, type Locator, expect } from '@playwright/test'

export class BasePage {
  readonly page: Page
  readonly header: Locator
  readonly sidebar: Locator
  readonly loadingSpinner: Locator

  constructor(page: Page) {
    this.page = page
    this.header = page.locator('header, [class*="header"]')
    this.sidebar = page.locator('aside, [class*="sidebar"]')
    this.loadingSpinner = page.locator('[class*="spinner"], [class*="loading"]')
  }

  async navigateTo(path: string) {
    await this.page.goto(path)
    await this.waitForLoad()
  }

  async waitForLoad() {
    await this.page.waitForLoadState('networkidle')
    await this.waitForSpinner()
  }

  async waitForSpinner() {
    await expect(this.loadingSpinner).not.toBeVisible({ timeout: 5000 }).catch(() => {})
  }

  async expectUrl(path: string) {
    await expect(this.page).toHaveURL(new RegExp(path))
  }

  async expectTitle(title: string) {
    await expect(this.page).toHaveTitle(title)
  }
}
