import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { fileService } from '@/services/fileService'
import { useFileStore } from '@/stores/fileStore'
import type { FileItem, PaginatedResponse } from '@/types'

const FILES_QUERY_KEY = ['files']

export const useFiles = (path: string, page = 1, pageSize = 20) => {
  const { setFiles, setIsLoading } = useFileStore()

  const query = useQuery<PaginatedResponse<FileItem>>({
    queryKey: [...FILES_QUERY_KEY, path, page, pageSize],
    queryFn: () => fileService.getFiles(path, page, pageSize),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  })

  // Update store when data changes
  if (query.data) {
    setFiles(query.data.items)
  }

  if (!query.isLoading) {
    setIsLoading(false)
  }

  return {
    files: query.data?.items || [],
    total: query.data?.total || 0,
    page: query.data?.page || 1,
    pageSize: query.data?.pageSize || 20,
    totalPages: query.data?.totalPages || 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

export const useFileDetails = (id: string) => {
  return useQuery({
    queryKey: [...FILES_QUERY_KEY, 'details', id],
    queryFn: () => fileService.getFileDetails(id),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!id,
  })
}

export const useFileStats = () => {
  return useQuery({
    queryKey: [...FILES_QUERY_KEY, 'stats'],
    queryFn: () => fileService.getFileStats(),
    staleTime: 10 * 60 * 1000,
    gcTime: 15 * 60 * 1000,
  })
}

export const useDeleteFile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => fileService.deleteFile(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY })
    },
  })
}

export const useMoveFile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, newPath }: { id: string; newPath: string }) =>
      fileService.moveFile(id, newPath),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY })
    },
  })
}

export const useRenameFile = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, newName }: { id: string; newName: string }) =>
      fileService.renameFile(id, newName),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY })
    },
  })
}

export const useBatchDeleteFiles = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (ids: string[]) => fileService.batchDeleteFiles(ids),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY })
    },
  })
}

export const useBatchMoveFiles = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ ids, newPath }: { ids: string[]; newPath: string }) =>
      fileService.batchMoveFiles(ids, newPath),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: FILES_QUERY_KEY })
    },
  })
}

export const useSearchFiles = (query: string, page = 1, pageSize = 20) => {
  return useQuery({
    queryKey: [...FILES_QUERY_KEY, 'search', query, page, pageSize],
    queryFn: () => fileService.searchFiles(query, page, pageSize),
    staleTime: 5 * 60 * 1000,
    gcTime: 10 * 60 * 1000,
    enabled: !!query,
  })
}
