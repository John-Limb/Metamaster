import { test as base, type Page } from '@playwright/test'

export interface Fixtures {
  page: Page
  mockApi: boolean
}

export const test = base.extend<Fixtures>({
  mockApi: async ({ page }, use) => {
    // Mock API responses for testing
    await page.route('/api/**', async (route) => {
      const url = route.request().url()
      const method = route.request().method()

      // Mock file list response
      if (url.includes('/api/files') && method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'file-1',
                name: 'Movie 1.mp4',
                path: '/movies',
                type: 'file',
                size: 1073741824,
                mimeType: 'video/mp4',
                createdAt: '2024-01-01T00:00:00Z',
                updatedAt: '2024-01-01T00:00:00Z',
                isIndexed: true,
              },
              {
                id: 'file-2',
                name: 'Movie 2.mkv',
                path: '/movies',
                type: 'file',
                size: 2147483648,
                mimeType: 'video/x-matroska',
                createdAt: '2024-01-02T00:00:00Z',
                updatedAt: '2024-01-02T00:00:00Z',
                isIndexed: true,
              },
              {
                id: 'dir-1',
                name: 'Documents',
                path: '/documents',
                type: 'directory',
                size: 0,
                mimeType: undefined,
                createdAt: '2024-01-03T00:00:00Z',
                updatedAt: '2024-01-03T00:00:00Z',
                isIndexed: false,
              },
            ],
            total: 3,
            page: 1,
            pageSize: 20,
            totalPages: 1,
          }),
        })
        return
      }

      // Mock dashboard stats response
      if (url.includes('/api/dashboard/stats') && method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            totalFiles: 1250,
            totalSize: 107374182400,
            indexedFiles: 980,
            recentActivity: [
              { id: '1', action: 'indexed', fileName: 'Movie 1.mp4', timestamp: '2024-01-15T10:00:00Z' },
              { id: '2', action: 'added', fileName: 'Document.pdf', timestamp: '2024-01-15T09:30:00Z' },
            ],
          }),
        })
        return
      }

      // Mock search response
      if (url.includes('/api/search') && method === 'GET') {
        await route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify({
            items: [
              {
                id: 'search-1',
                title: 'Movie 1.mp4',
                type: 'file',
                path: '/movies',
                relevance: 1.0,
              },
            ],
            total: 1,
            page: 1,
            pageSize: 20,
            totalPages: 1,
          }),
        })
        return
      }

      // Default: continue with real request
      await route.continue()
    })

    await use(true)
  },
})

export { expect } from '@playwright/test'
