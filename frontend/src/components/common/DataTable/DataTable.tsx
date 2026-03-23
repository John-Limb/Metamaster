import React from 'react'
import { Skeleton } from '../Skeleton/Skeleton'
import { CheckboxInput } from '../Checkbox'

export interface Column<T> {
  key: string
  header: string
  render?: (row: T) => React.ReactNode
  sortable?: boolean
  width?: string
  align?: 'left' | 'center' | 'right'
}

export interface DataTableProps<T> {
  columns: Column<T>[]
  data: T[]
  keyExtractor: (row: T) => string
  loading?: boolean
  skeletonRows?: number
  sortColumn?: string
  sortDirection?: 'asc' | 'desc'
  onSort?: (column: string, direction: 'asc' | 'desc') => void
  pagination?: {
    page: number
    pageSize: number
    total: number
    onPageChange: (page: number) => void
  }
  rowSelection?: {
    selectedKeys: string[]
    onSelectionChange: (keys: string[]) => void
  }
  onRowClick?: (row: T) => void
  className?: string
  ariaLabel?: string
}

export function DataTable<T>({
  columns,
  data,
  keyExtractor,
  loading = false,
  skeletonRows = 5,
  sortColumn,
  sortDirection,
  onSort,
  pagination,
  rowSelection,
  onRowClick,
  className = '',
  ariaLabel = 'Data table',
}: DataTableProps<T>) {
  const page = pagination?.page ?? 1
  const pageSize = pagination?.pageSize ?? 10
  const total = pagination?.total ?? 0
  const onPageChange = pagination?.onPageChange ?? (() => {})

  const totalPages = Math.ceil(total / pageSize)

  const handleSort = (column: string) => {
    if (!onSort) return
    const newDirection = sortColumn === column && sortDirection === 'asc' ? 'desc' : 'asc'
    onSort(column, newDirection)
  }

  const handleSelectAll = (checked: boolean) => {
    if (!rowSelection) return
    if (checked) {
      rowSelection.onSelectionChange(data.map(keyExtractor))
    } else {
      rowSelection.onSelectionChange([])
    }
  }

  const handleSelectRow = (key: string, checked: boolean) => {
    if (!rowSelection) return
    if (checked) {
      rowSelection.onSelectionChange([...rowSelection.selectedKeys, key])
    } else {
      rowSelection.onSelectionChange(rowSelection.selectedKeys.filter((k) => k !== key))
    }
  }

  const isAllSelected = rowSelection && data.length > 0 && rowSelection.selectedKeys.length === data.length
  const isIndeterminate = rowSelection && rowSelection.selectedKeys.length > 0 && rowSelection.selectedKeys.length < data.length

  const alignClasses = {
    left: 'text-left',
    center: 'text-center',
    right: 'text-right',
  }

  return (
    <div className={`w-full ${className}`} role="region" aria-label={ariaLabel} tabIndex={-1}>
      <div className="overflow-x-auto rounded-lg border border-edge">
        <table className="min-w-full divide-y divide-edge">
          <thead className="bg-subtle">
            <tr>
              {rowSelection && (
                <th scope="col" className="px-6 py-3 w-12">
                  <CheckboxInput
                    checked={isAllSelected ?? false}
                    indeterminate={isIndeterminate ?? false}
                    onChange={(checked) => handleSelectAll(checked)}
                    aria-label="Select all rows"
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={column.key}
                  scope="col"
                  className={`
                    px-6 py-3 text-xs font-medium text-hint uppercase tracking-wider
                    ${column.sortable ? 'cursor-pointer hover:bg-subtle transition-colors duration-150' : ''}
                    ${column.width ? column.width : ''}
                    ${alignClasses[column.align || 'left']}
                  `}
                  onClick={() => column.sortable && handleSort(column.key)}
                  aria-sort={sortColumn === column.key ? (sortDirection === 'asc' ? 'ascending' : 'descending') : undefined}
                >
                  <div className="flex items-center gap-2">
                    {column.header}
                    {column.sortable && (
                      <svg
                        className={`w-4 h-4 transition-transform duration-150 ${
                          sortColumn === column.key ? 'opacity-100' : 'opacity-50'
                        } ${
                          sortColumn === column.key && sortDirection === 'desc' ? 'rotate-180' : ''
                        }`}
                        xmlns="http://www.w3.org/2000/svg"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                        aria-hidden="true"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 15l7-7 7 7"
                        />
                      </svg>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-card divide-y divide-edge">
            {loading ? (
              // Skeleton loading state
              <>
                {Array.from({ length: skeletonRows }).map((_, rowIndex) => (
                  <tr key={rowIndex} className="table-row-hover">
                    {rowSelection && (
                      <td className="px-6 py-4 w-12">
                        <CheckboxInput
                          checked={false}
                          onChange={() => {}}
                          disabled
                          aria-label="Loading"
                        />
                      </td>
                    )}
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={`px-6 py-4 whitespace-nowrap text-sm ${alignClasses[column.align || 'left']}`}
                      >
                        <Skeleton
                          variant="text"
                          width={column.width || '100px'}
                          height="16px"
                          animation="shimmer"
                        />
                      </td>
                    ))}
                  </tr>
                ))}
              </>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className="px-6 py-12 text-center text-hint"
                >
                  <div className="flex flex-col items-center gap-2">
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="48"
                      height="48"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="1"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="text-hint"
                      aria-hidden="true"
                    >
                      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                    <p>No data available</p>
                  </div>
                </td>
              </tr>
            ) : (
              data.map((row) => {
                const key = keyExtractor(row)
                const isSelected = rowSelection?.selectedKeys.includes(key)
                return (
                  <tr
                    key={key}
                    className={`
                      table-row-hover
                      transition-colors duration-150
                      ${onRowClick ? 'cursor-pointer' : ''}
                      ${isSelected ? 'bg-primary-50 dark:bg-primary-900/20' : ''}
                    `}
                    onClick={() => onRowClick?.(row)}
                    tabIndex={onRowClick ? 0 : undefined}
                    role={onRowClick ? 'button' : undefined}
                    aria-label={onRowClick ? `Row for ${key}` : undefined}
                    onKeyDown={(e) => {
                      if (onRowClick && (e.key === 'Enter' || e.key === ' ')) {
                        e.preventDefault()
                        onRowClick(row)
                      }
                    }}
                  >
                    {rowSelection && (
                      <td className="px-6 py-4 w-12">
                        <CheckboxInput
                          checked={isSelected ?? false}
                          onChange={(checked) => handleSelectRow(key, checked)}
                          onClick={(e) => e.stopPropagation()}
                          aria-label={`Select row ${key}`}
                        />
                      </td>
                    )}
                    {columns.map((column) => (
                      <td
                        key={column.key}
                        className={`
                          px-6 py-4 whitespace-nowrap text-sm text-dim
                          ${alignClasses[column.align || 'left']}
                        `}
                      >
                        {column.render ? column.render(row) : (row as Record<string, unknown>)[column.key] as React.ReactNode}
                      </td>
                    ))}
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>
      {pagination && (
        <div className="flex items-center justify-between mt-4 flex-wrap gap-2">
          <div className="text-sm text-hint">
            Showing {((page - 1) * pageSize) + 1} to {Math.min(page * pageSize, total)} of {total} results
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => onPageChange(page - 1)}
              disabled={page === 1}
              className="px-3 py-1.5 text-sm min-h-[36px] border border-edge rounded-md
                         text-dim
                         disabled:opacity-50 disabled:cursor-not-allowed
                         hover:bg-subtle
                         focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                         transition-colors duration-150"
              aria-label="Go to previous page"
            >
              Previous
            </button>
            <button
              onClick={() => onPageChange(page + 1)}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-sm min-h-[36px] border border-edge rounded-md
                         text-dim
                         disabled:opacity-50 disabled:cursor-not-allowed
                         hover:bg-subtle
                         focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2
                         transition-colors duration-150"
              aria-label="Go to next page"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default DataTable
