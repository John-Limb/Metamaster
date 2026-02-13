// API Constants
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
export const API_TIMEOUT = parseInt(import.meta.env.VITE_API_TIMEOUT || '30000')
export const MAX_RETRIES = parseInt(import.meta.env.VITE_MAX_RETRIES || '3')
export const RETRY_DELAY = parseInt(import.meta.env.VITE_RETRY_DELAY || '1000')

// File Constants
export const MAX_FILE_SIZE = parseInt(import.meta.env.VITE_MAX_FILE_SIZE || '5368709120')
export const ALLOWED_FILE_TYPES = (import.meta.env.VITE_ALLOWED_FILE_TYPES || '').split(',')

// Cache Constants
export const CACHE_DURATION = parseInt(import.meta.env.VITE_CACHE_DURATION || '300000')
export const QUERY_STALE_TIME = parseInt(import.meta.env.VITE_QUERY_STALE_TIME || '60000')

// UI Constants
export const ITEMS_PER_PAGE = parseInt(import.meta.env.VITE_ITEMS_PER_PAGE || '20')
export const THEME_MODE = import.meta.env.VITE_THEME_MODE || 'light'

// Status Constants
export const TASK_STATUS = {
  PENDING: 'pending',
  PROCESSING: 'processing',
  COMPLETED: 'completed',
  FAILED: 'failed',
} as const

export const FILE_STATUS = {
  INDEXED: 'indexed',
  PROCESSING: 'processing',
  FAILED: 'failed',
  PENDING: 'pending',
} as const

// Toast Duration
export const TOAST_DURATION = 3000

// Pagination
export const DEFAULT_PAGE_SIZE = 20
export const MAX_PAGE_SIZE = 100

// Debounce Delays
export const SEARCH_DEBOUNCE_DELAY = 300
export const RESIZE_DEBOUNCE_DELAY = 150

// Error Messages
export const ERROR_MESSAGES = {
  NETWORK_ERROR: 'Network error occurred. Please check your connection.',
  UNAUTHORIZED: 'You are not authorized to perform this action.',
  FORBIDDEN: 'Access denied.',
  NOT_FOUND: 'Resource not found.',
  SERVER_ERROR: 'Server error occurred. Please try again later.',
  VALIDATION_ERROR: 'Validation error occurred.',
  FILE_TOO_LARGE: 'File size exceeds the maximum allowed size.',
  INVALID_FILE_TYPE: 'Invalid file type.',
} as const

// Success Messages
export const SUCCESS_MESSAGES = {
  FILE_UPLOADED: 'File uploaded successfully.',
  FILE_DELETED: 'File deleted successfully.',
  FILE_MOVED: 'File moved successfully.',
  FILE_RENAMED: 'File renamed successfully.',
  OPERATION_COMPLETED: 'Operation completed successfully.',
} as const
