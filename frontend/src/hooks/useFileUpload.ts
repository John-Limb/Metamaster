import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState, useCallback } from 'react'
import { fileService } from '@/services/fileService'
import type { FileItem } from '@/types'

interface UploadProgress {
  fileName: string
  progress: number
  status: 'pending' | 'uploading' | 'completed' | 'failed'
  error?: string
}

export const useFileUpload = () => {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState<Map<string, UploadProgress>>(new Map())

  const mutation = useMutation({
    mutationFn: async ({
      file,
      path,
      onProgress,
    }: {
      file: File
      path: string
      onProgress?: (progress: number) => void
    }) => {
      const fileKey = `${file.name}-${Date.now()}`
      setUploadProgress((prev) => new Map(prev).set(fileKey, { fileName: file.name, progress: 0, status: 'uploading' }))

      try {
        const result = await fileService.uploadFile(file, path, (progress) => {
          setUploadProgress((prev) => {
            const updated = new Map(prev)
            const current = updated.get(fileKey) || { fileName: file.name, progress: 0, status: 'uploading' }
            updated.set(fileKey, { ...current, progress })
            return updated
          })
          onProgress?.(progress)
        })

        setUploadProgress((prev) => {
          const updated = new Map(prev)
          updated.set(fileKey, { fileName: file.name, progress: 100, status: 'completed' })
          return updated
        })

        return result
      } catch (error: any) {
        setUploadProgress((prev) => {
          const updated = new Map(prev)
          updated.set(fileKey, {
            fileName: file.name,
            progress: 0,
            status: 'failed',
            error: error.message,
          })
          return updated
        })
        throw error
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['files'] })
    },
  })

  const uploadFile = useCallback(
    (file: File, path: string, onProgress?: (progress: number) => void) => {
      return mutation.mutate({ file, path, onProgress })
    },
    [mutation]
  )

  const uploadMultiple = useCallback(
    async (files: File[], path: string) => {
      const results: FileItem[] = []
      const errors: { file: string; error: string }[] = []

      for (const file of files) {
        try {
          const result = await new Promise<FileItem>((resolve, reject) => {
            mutation.mutate(
              { file, path },
              {
                onSuccess: (data) => resolve(data),
                onError: (error) => reject(error),
              }
            )
          })
          results.push(result)
        } catch (error: any) {
          errors.push({ file: file.name, error: error.message })
        }
      }

      return { results, errors }
    },
    [mutation]
  )

  const clearProgress = useCallback(() => {
    setUploadProgress(new Map())
  }, [])

  const removeProgress = useCallback((fileName: string) => {
    setUploadProgress((prev) => {
      const updated = new Map(prev)
      updated.delete(fileName)
      return updated
    })
  }, [])

  return {
    uploadFile,
    uploadMultiple,
    uploadProgress: Array.from(uploadProgress.values()),
    isLoading: mutation.isPending,
    error: mutation.error,
    clearProgress,
    removeProgress,
  }
}
