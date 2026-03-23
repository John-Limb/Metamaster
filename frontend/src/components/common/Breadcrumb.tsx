import React from 'react'
import { Link } from 'react-router-dom'
import { FaChevronRight, FaHome } from 'react-icons/fa'

export interface BreadcrumbItem {
  label: string
  path?: string
  onClick?: () => void
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
  separator?: React.ReactNode
  className?: string
  showHome?: boolean
  onHomeClick?: () => void
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({
  items,
  separator = <FaChevronRight className="w-4 h-4 text-hint" />,
  className = '',
  showHome = false,
  onHomeClick,
}) => {
  const displayItems = showHome
    ? [{ label: 'Home', onClick: onHomeClick }, ...items]
    : items

  return (
    <nav className={`flex items-center gap-2 text-sm ${className}`} aria-label="Breadcrumb">
      <ol className="flex items-center gap-2">
        {displayItems.map((item, index) => (
          <li key={index} className="flex items-center gap-2">
            {index > 0 && <span className="text-hint">{separator}</span>}
            {item.path ? (
              <Link
                to={item.path}
                className="text-primary-600 hover:text-primary-700 hover:underline transition flex items-center gap-1"
              >
                {index === 0 && showHome && <FaHome className="w-3 h-3" />}
                {item.label}
              </Link>
            ) : item.onClick ? (
              <button
                onClick={item.onClick}
                className="text-primary-600 hover:text-primary-700 hover:underline transition cursor-pointer flex items-center gap-1"
              >
                {index === 0 && showHome && <FaHome className="w-3 h-3" />}
                {item.label}
              </button>
            ) : (
              <span className="text-dim font-medium flex items-center gap-1">
                {index === 0 && showHome && <FaHome className="w-3 h-3" />}
                {item.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
