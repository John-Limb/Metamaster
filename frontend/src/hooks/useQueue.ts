import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { queueService } from '@/services/queueService'
import { useQueueStore } from '@/stores/queueStore'
import type { QueueTask, QueueStats, PaginatedResponse } from '@/types'

const QUEUE_QUERY_KEY = ['queue']

export const useQueue = (page = 1, pageSize = 20, status?: string, autoRefresh = true) => {
  const { setTasks, setIsLoading } = useQueueStore()

  const query = useQuery<PaginatedResponse<QueueTask>>({
    queryKey: [...QUEUE_QUERY_KEY, 'tasks', page, pageSize, status],
    queryFn: () => queueService.getTasks(page, pageSize, status),
    staleTime: 10 * 1000, // 10 seconds
    gcTime: 5 * 60 * 1000, // 5 minutes
    refetchInterval: autoRefresh ? 5000 : false, // Auto-refresh every 5 seconds if enabled
  })

  // Update store when data changes
  if (query.data) {
    setTasks(query.data.items)
  }

  if (!query.isLoading) {
    setIsLoading(false)
  }

  return {
    tasks: query.data?.items || [],
    total: query.data?.total || 0,
    page: query.data?.page || 1,
    pageSize: query.data?.pageSize || 20,
    totalPages: query.data?.totalPages || 0,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

export const useQueueStats = (autoRefresh = true) => {
  const { setStats } = useQueueStore()

  const query = useQuery<QueueStats>({
    queryKey: [...QUEUE_QUERY_KEY, 'stats'],
    queryFn: () => queueService.getStats(),
    staleTime: 10 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: autoRefresh ? 5000 : false,
  })

  // Update store when data changes
  if (query.data) {
    setStats(query.data)
  }

  return {
    stats: query.data,
    isLoading: query.isLoading,
    error: query.error,
    refetch: query.refetch,
  }
}

export const useTaskDetails = (id: string) => {
  return useQuery<QueueTask>({
    queryKey: [...QUEUE_QUERY_KEY, 'task', id],
    queryFn: () => queueService.getTaskDetails(id),
    staleTime: 10 * 1000,
    gcTime: 5 * 60 * 1000,
    enabled: !!id,
  })
}

export const useTaskProgress = (id: string, autoRefresh = true) => {
  return useQuery<{ progress: number; status: string }>({
    queryKey: [...QUEUE_QUERY_KEY, 'progress', id],
    queryFn: () => queueService.getTaskProgress(id),
    staleTime: 5 * 1000,
    gcTime: 5 * 60 * 1000,
    refetchInterval: autoRefresh ? 2000 : false,
    enabled: !!id,
  })
}

export const useRetryTask = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => queueService.retryTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUEUE_QUERY_KEY })
    },
  })
}

export const useCancelTask = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: string) => queueService.cancelTask(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUEUE_QUERY_KEY })
    },
  })
}

export const useClearCompletedTasks = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: () => queueService.clearCompletedTasks(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUEUE_QUERY_KEY })
    },
  })
}
