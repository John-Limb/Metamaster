import { apiClient } from '@/utils/api'
import { errorHandler } from '@/utils/errorHandler'
import type { FileItem, PaginatedResponse, ApiResponse, FileStats } from '@/types'
import type { AxiosProgressEvent } from 'axios'

export const fileService = {
  // Get files in directory
  getFiles: async (path: string, page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get<PaginatedResponse<FileItem>>(
        `/files?path=${encodeURIComponent(path)}&page=${page}&pageSize=${pageSize}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getFiles: ${path}`)
      throw error
    }
  },

  // Get file details
  getFileDetails: async (id: string) => {
    try {
      const response = await apiClient.get<FileItem>(`/files/${id}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `getFileDetails: ${id}`)
      throw error
    }
  },

  // Get file statistics
  getFileStats: async () => {
    try {
      const response = await apiClient.get<FileStats>('/files/stats')
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, 'getFileStats')
      throw error
    }
  },

  // Delete file
  deleteFile: async (id: string) => {
    try {
      const response = await apiClient.delete<ApiResponse<void>>(`/files/${id}`)
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `deleteFile: ${id}`)
      throw error
    }
  },

  // Move file
  moveFile: async (id: string, newPath: string) => {
    try {
      const response = await apiClient.patch<FileItem>(`/files/${id}`, {
        path: newPath,
      })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `moveFile: ${id} to ${newPath}`)
      throw error
    }
  },

  // Rename file
  renameFile: async (id: string, newName: string) => {
    try {
      const response = await apiClient.patch<FileItem>(`/files/${id}`, {
        name: newName,
      })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `renameFile: ${id} to ${newName}`)
      throw error
    }
  },

  // Upload file
  uploadFile: async (file: File, path: string, onProgress?: (progress: number) => void) => {
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('path', path)

      const response = await apiClient.post<FileItem>('/files/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        onUploadProgress: (progressEvent: AxiosProgressEvent) => {
          if (onProgress && progressEvent.total) {
            const progress = Math.round((progressEvent.loaded / progressEvent.total) * 100)
            onProgress(progress)
          }
        },
      })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `uploadFile: ${file.name}`)
      throw error
    }
  },

  // Batch delete files
  batchDeleteFiles: async (ids: string[]) => {
    try {
      const response = await apiClient.post<ApiResponse<void>>('/files/batch-delete', {
        ids,
      })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `batchDeleteFiles: ${ids.length} files`)
      throw error
    }
  },

  // Batch move files
  batchMoveFiles: async (ids: string[], newPath: string) => {
    try {
      const response = await apiClient.post<ApiResponse<void>>('/files/batch-move', {
        ids,
        path: newPath,
      })
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `batchMoveFiles: ${ids.length} files to ${newPath}`)
      throw error
    }
  },

  // Search files
  searchFiles: async (query: string, page = 1, pageSize = 20) => {
    try {
      const response = await apiClient.get<PaginatedResponse<FileItem>>(
        `/files/search?query=${encodeURIComponent(query)}&page=${page}&pageSize=${pageSize}`
      )
      return response.data
    } catch (error: any) {
      errorHandler.handleError(error, `searchFiles: ${query}`)
      throw error
    }
  },
}
