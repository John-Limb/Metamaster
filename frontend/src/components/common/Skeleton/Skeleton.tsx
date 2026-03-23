import React from 'react'

export interface SkeletonProps {
  variant?: 'text' | 'circular' | 'rectangular'
  width?: string | number
  height?: string | number
  radius?: number
  className?: string
  animation?: 'pulse' | 'shimmer' | 'none'
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = 'text',
  width,
  height,
  radius,
  className = '',
  animation = 'shimmer',
}: SkeletonProps) => {
  const baseClasses = 'bg-subtle'

  const animationClasses = {
    pulse: 'animate-pulse',
    shimmer: 'animate-shimmer dark:animate-shimmer-diagonal',
    none: '',
  }

  const variantClasses = {
    text: 'rounded',
    circular: 'rounded-full',
    rectangular: '',
  }

  const customRadius = radius ? `rounded-[${radius}px]` : ''

  const style: React.CSSProperties = {
    width: width || (variant === 'text' ? '100%' : undefined),
    height: height || (variant === 'text' ? '1em' : undefined),
    borderRadius: radius,
  }

  return (
    <div
      className={`
        ${baseClasses}
        ${animationClasses[animation]}
        ${variantClasses[variant]}
        ${customRadius}
        ${className}
      `}
      style={style}
      role="status"
      aria-label="Loading..."
    />
  )
}

export const SkeletonText: React.FC<{ lines?: number; className?: string }> = ({
  lines = 3,
  className = '',
}: { lines?: number; className?: string }) => {
  return (
    <div className={`space-y-2 ${className}`} role="status" aria-label="Loading text">
      {Array.from({ length: lines }).map((_, index) => (
        <Skeleton
          key={index}
          variant="text"
          width={index === lines - 1 ? '60%' : '100%'}
          animation="shimmer"
        />
      ))}
    </div>
  )
}

export const SkeletonAvatar: React.FC<{ size?: number; className?: string }> = ({
  size = 40,
  className = '',
}: { size?: number; className?: string }) => {
  return (
    <Skeleton
      variant="circular"
      width={size}
      height={size}
      className={className}
      animation="shimmer"
    />
  )
}

export const SkeletonCard: React.FC<{ className?: string; children?: React.ReactNode }> = ({ className = '', children }: { className?: string; children?: React.ReactNode }) => {
  return (
    <div className={`space-y-4 p-4 ${className}`} role="status" aria-label="Loading card">
      {children || (
        <>
          <div className="flex items-center gap-4">
            <SkeletonAvatar size={48} />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" width="40%" animation="shimmer" />
              <Skeleton variant="text" width="60%" animation="shimmer" />
            </div>
          </div>
          <SkeletonText lines={4} />
        </>
      )}
    </div>
  )
}

export const SkeletonTable: React.FC<{
  rows?: number
  columns?: number
  className?: string
  showHeader?: boolean
}> = ({ rows = 5, columns = 4, className = '', showHeader = true }: {
  rows?: number
  columns?: number
  className?: string
  showHeader?: boolean
}) => {
  return (
    <div className={`space-y-3 ${className}`} role="status" aria-label="Loading table">
      {showHeader && (
        <div className="flex gap-4 border-b border-edge pb-2">
          {Array.from({ length: columns }).map((_, index) => (
            <Skeleton
              key={index}
              variant="text"
              width={`${100 / columns}%`}
              height="20px"
              animation="shimmer"
            />
          ))}
        </div>
      )}
      {Array.from({ length: rows }).map((_, rowIndex) => (
        <div key={rowIndex} className="flex gap-4">
          {Array.from({ length: columns }).map((_, colIndex) => (
            <Skeleton
              key={colIndex}
              variant="text"
              width={`${100 / columns}%`}
              animation="shimmer"
            />
          ))}
        </div>
      ))}
    </div>
  )
}

export const SkeletonMovieCard: React.FC<{ className?: string }> = ({ className = '' }: { className?: string }) => {
  return (
    <div
      className={`rounded-lg overflow-hidden bg-card ${className}`}
      role="status"
      aria-label="Loading movie card"
    >
      {/* Poster placeholder */}
      <div className="aspect-[2/3] bg-subtle animate-shimmer" />

      {/* Content */}
      <div className="p-4 space-y-3">
        <Skeleton variant="text" width="80%" height="20px" animation="shimmer" />
        <div className="flex gap-2">
          <Skeleton variant="text" width="60px" height="24px" radius={4} animation="shimmer" />
          <Skeleton variant="text" width="40px" height="24px" radius={4} animation="shimmer" />
        </div>
        <Skeleton variant="text" width="40%" height="14px" animation="shimmer" />
      </div>
    </div>
  )
}

export const SkeletonTVShowCard: React.FC<{ className?: string }> = ({ className = '' }: { className?: string }) => {
  return (
    <div
      className={`rounded-lg overflow-hidden bg-card ${className}`}
      role="status"
      aria-label="Loading TV show card"
    >
      {/* Poster placeholder */}
      <div className="aspect-[2/3] bg-subtle animate-shimmer" />
      
      {/* Content */}
      <div className="p-4 space-y-3">
        <Skeleton variant="text" width="80%" height="20px" animation="shimmer" />
        <Skeleton variant="text" width="60%" height="14px" animation="shimmer" />
        <div className="flex gap-2">
          <Skeleton variant="text" width="50px" height="24px" radius={4} animation="shimmer" />
          <Skeleton variant="text" width="70px" height="24px" radius={4} animation="shimmer" />
        </div>
      </div>
    </div>
  )
}

export const SkeletonStatCard: React.FC<{ className?: string }> = ({ className = '' }: { className?: string }) => {
  return (
    <div
      className={`p-6 rounded-lg bg-card ${className}`}
      role="status"
      aria-label="Loading stat card"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 space-y-3">
          <Skeleton variant="text" width="60%" height="14px" animation="shimmer" />
          <Skeleton variant="text" width="40%" height="32px" animation="shimmer" />
          <Skeleton variant="text" width="80%" height="12px" animation="shimmer" />
        </div>
        <SkeletonAvatar size={48} />
      </div>
    </div>
  )
}

export const SkeletonDataTableHeader: React.FC<{
  columns: { width?: string | number }[]
  className?: string
}> = ({ columns, className = '' }: {
  columns: { width?: string | number }[]
  className?: string
}) => {
  return (
    <div
      className={`flex gap-4 p-4 border-b border-edge ${className}`}
      role="rowheader"
      aria-label="Loading table header"
    >
      {columns.map((col, index) => (
        <Skeleton
          key={index}
          variant="text"
          width={col.width || `${100 / columns.length}%`}
          height="20px"
          animation="shimmer"
        />
      ))}
    </div>
  )
}

export const SkeletonList: React.FC<{
  items?: number
  children?: React.ReactNode
  className?: string
}> = ({ items = 5, children, className = '' }: {
  items?: number
  children?: React.ReactNode
  className?: string
}) => {
  return (
    <div className={`space-y-3 ${className}`} role="list" aria-label="Loading list">
      {children ||
        Array.from({ length: items }).map((_, index) => (
          <div
            key={index}
            className="flex items-center gap-4 p-3 bg-card rounded-lg"
          >
            <SkeletonAvatar size={40} />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" width="40%" animation="shimmer" />
              <Skeleton variant="text" width="60%" animation="shimmer" />
            </div>
          </div>
        ))}
    </div>
  )
}

export const SkeletonForm: React.FC<{
  fields?: number
  className?: string
}> = ({ fields = 4, className = '' }: {
  fields?: number
  className?: string
}) => {
  return (
    <div className={`space-y-4 ${className}`} role="form" aria-label="Loading form">
      {Array.from({ length: fields }).map((_, index) => (
        <div key={index} className="space-y-2">
          <Skeleton variant="text" width="30%" height="16px" animation="shimmer" />
          <Skeleton variant="rectangular" width="100%" height="40px" radius={6} animation="shimmer" />
        </div>
      ))}
    </div>
  )
}

export default Skeleton
