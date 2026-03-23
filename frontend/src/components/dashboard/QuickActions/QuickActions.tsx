import React from 'react'
import { Card } from '@/components/common/Card'

export interface QuickAction {
  id: string
  label: string
  description?: string
  icon: React.ReactNode
  onClick: () => void
  variant?: 'primary' | 'secondary'
  group?: 'add' | 'scan' | 'settings'
}

export interface QuickActionsProps {
  actions: QuickAction[]
  className?: string
}

export function QuickActions({ actions, className = '' }: QuickActionsProps) {
  return (
    <Card variant="elevated" className={className}>
      <h3 className="text-base font-semibold text-body mb-4">
        Quick Actions
      </h3>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={action.onClick}
            aria-label={action.label}
            className={`
              flex flex-col items-center justify-center gap-2 p-4 rounded-xl
              transition-all duration-200
              focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
              hover:shadow-md hover:-translate-y-0.5
              ${action.variant === 'primary'
                ? 'bg-primary-50 dark:bg-primary-900/20 hover:bg-primary-100 dark:hover:bg-primary-900/30 text-primary-700 dark:text-primary-300'
                : 'bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 text-dim'
              }
            `}
          >
            <div
              className={`p-2 rounded-lg ${
                action.variant === 'primary'
                  ? 'bg-primary-100 dark:bg-primary-900/50'
                  : 'bg-slate-200 dark:bg-slate-700'
              }`}
            >
              <span className="w-5 h-5 block">{action.icon}</span>
            </div>
            <div className="text-center">
              <p className="text-sm font-medium leading-tight">{action.label}</p>
              {action.description && (
                <p className="text-xs text-hint mt-0.5 leading-tight">
                  {action.description}
                </p>
              )}
            </div>
          </button>
        ))}
      </div>
    </Card>
  )
}

export default QuickActions
