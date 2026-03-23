import React from 'react'

export interface Tab {
  id: string
  label: string
  icon?: React.ReactNode
  disabled?: boolean
}

export interface TabsProps {
  tabs: Tab[]
  activeTab: string
  onChange: (tabId: string) => void
  variant?: 'default' | 'pills'
  className?: string
  children?: React.ReactNode
}

export const Tabs: React.FC<TabsProps> = ({
  tabs,
  activeTab,
  onChange,
  variant = 'default',
  className = '',
  children,
}) => {
  return (
    <div className={`w-full ${className}`}>
      <div
        className={`${
          variant === 'pills'
            ? 'flex gap-2 p-1 bg-subtle rounded-lg'
            : 'flex border-b border-edge'
        }`}
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => !tab.disabled && onChange(tab.id)}
            disabled={tab.disabled}
            className={`
              flex items-center gap-2 px-4 py-2 text-sm font-medium transition-colors duration-150
              focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
              ${
                variant === 'pills'
                  ? `
                    rounded-md
                    ${
                      activeTab === tab.id
                        ? 'bg-card text-primary-600 dark:text-primary-400 shadow-sm'
                        : 'text-dim hover:text-body'
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `
                  : `
                    border-b-2 -mb-px
                    ${
                      activeTab === tab.id
                        ? 'border-primary-600 text-primary-600 dark:text-primary-400'
                        : 'border-transparent text-hint hover:text-dim'
                    }
                    disabled:opacity-50 disabled:cursor-not-allowed
                  `
              }
            `}
          >
            {tab.icon && <span className="w-4 h-4">{tab.icon}</span>}
            {tab.label}
          </button>
        ))}
      </div>
      {children}
    </div>
  )
}
