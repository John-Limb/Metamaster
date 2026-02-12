import { type Page, type Locator, expect } from '@playwright/test'
import { BasePage } from './base-page'

export class FilesPage extends BasePage {
  readonly fileExplorer: Locator
  readonly fileGrid: Locator
  readonly fileList: Locator
  readonly fileTree: Locator
  readonly backButton: Locator
  readonly pathBreadcrumb: Locator
  readonly gridViewButton: Locator
  readonly listViewButton: Locator
  readonly treeViewButton: Locator
  readonly uploadButton: Locator
  readonly batchOperationsButton: Locator
  readonly fileCard: Locator

  constructor(page: Page) {
    super(page)
    this.fileExplorer = page.locator('[class*="file-explorer"], [class*="FileExplorer"]')
    this.fileGrid = page.locator('[class*="file-grid"], [class*="FileGrid"]')
    this.fileList = page.locator('[class*="file-list"], [class*="FileList"]')
    this.fileTree = page.locator('[class*="file-tree"], [class*="FileTree"]')
    this.backButton = page.locator('[title="Go back"], button:has-text("Back")')
    this.pathBreadcrumb = page.locator('[class*="breadcrumb"], [class*="path"]')
    this.gridViewButton = page.locator('[title="Grid view"], button:has(svg[class*="th-large"])')
    this.listViewButton = page.locator('[title="List view"], button:has(svg[class*="list"])')
    this.treeViewButton = page.locator('[title="Tree view"], button:has(svg[class*="tree"])')
    this.uploadButton = page.locator('button:has-text("Upload"), [class*="upload"]')
    this.batchOperationsButton = page.locator('button:has-text("Batch"), [class*="batch"]')
    this.fileCard = page.locator('[class*="file-card"], [class*="FileCard"]')
  }

  async expectLoaded() {
    await expect(this.fileExplorer).toBeVisible()
  }

  async clickGridView() {
    await this.gridViewButton.click()
  }

  async clickListView() {
    await this.listViewButton.click()
  }

  async clickTreeView() {
    await this.treeViewButton.click()
  }

  async clickBackButton() {
    await this.backButton.click()
  }

  async clickFileCard(index: number) {
    const cards = this.fileCard
    await cards.nth(index).click()
  }

  async doubleClickFileCard(index: number) {
    const cards = this.fileCard
    await cards.nth(index).dblclick()
  }

  async expectFileCards(count: number) {
    await expect(this.fileCard).toHaveCount(count)
  }

  async expectViewMode(mode: 'grid' | 'list' | 'tree') {
    switch (mode) {
      case 'grid':
        await expect(this.fileGrid).toBeVisible()
        break
      case 'list':
        await expect(this.fileList).toBeVisible()
        break
      case 'tree':
        await expect(this.fileTree).toBeVisible()
        break
    }
  }

  async selectMultipleFiles(indices: number[]) {
    for (const index of indices) {
      await this.page.keyboard.down('Control')
      await this.clickFileCard(index)
      await this.page.keyboard.up('Control')
    }
  }
}
