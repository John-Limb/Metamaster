export { LoadingSpinner } from './LoadingSpinner'
export { ErrorBoundary } from './ErrorBoundary'
export { NotFound } from './NotFound'
export { Breadcrumb, type BreadcrumbItem } from './Breadcrumb'
export { Toast, ToastContainer } from './Toast'
export { ConfirmDialog } from './ConfirmDialog'
export { ErrorModal } from './ErrorModal'

// Phase 4 Empty States
export { EmptyState, LoadingState, EmptyStates } from './EmptyState/EmptyState'
export type { EmptyStateProps, EmptyStateAction, LoadingStateProps } from './EmptyState/EmptyState'

export { EmptyStateIcon, EmptyStateIcons } from './EmptyState/EmptyStateIcon'
export type { EmptyStateIconProps, EmptyStateVariant } from './EmptyState/EmptyStateIcon'

export { EmptyStateCard, EmptyStateCardSkeleton, InlineEmptyState } from './EmptyState/EmptyStateCard'
export type { EmptyStateCardProps } from './EmptyState/EmptyStateCard'

// Phase 2 Core Components
export { Card } from './Card'
export type { CardProps } from './Card'

export { Button } from './Button'
export type { ButtonProps } from './Button'

export { Badge } from './Badge'
export type { BadgeProps } from './Badge'

export { TextInput } from './TextInput'
export type { TextInputProps } from './TextInput'

export { Select } from './Select'
export type { SelectProps, SelectOption } from './Select'

export { Checkbox } from './Checkbox'
export type { CheckboxProps } from './Checkbox'

export { Toggle } from './Toggle'
export type { ToggleProps } from './Toggle'

export { DataTable } from './DataTable'
export type { DataTableProps, Column } from './DataTable'

export { Tabs } from './Tabs'
export type { TabsProps, Tab } from './Tabs'

export { Pagination } from './Pagination'
export type { PaginationProps } from './Pagination'

// Phase 7 Loading States - Skeleton with shimmer
export {
  Skeleton,
  SkeletonText,
  SkeletonAvatar,
  SkeletonCard,
  SkeletonTable,
  SkeletonMovieCard,
  SkeletonTVShowCard,
  SkeletonStatCard,
  SkeletonDataTableHeader,
  SkeletonList,
  SkeletonForm,
} from './Skeleton'
export type { SkeletonProps } from './Skeleton'

export { ProgressBar } from './ProgressBar'
export type { ProgressBarProps } from './ProgressBar'

// Error Boundaries
export { ApiErrorBoundary } from './ApiErrorBoundary'
