import React, { useState, useRef } from 'react'
import { Card } from '@/components/common/Card'
import { Button } from '@/components/common/Button'

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

const ACTION_GROUPS = {
  add: {
    title: 'Add Content',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
      </svg>
    ),
  },
  scan: {
    title: 'Scan & Sync',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
  },
  settings: {
    title: 'Settings',
    icon: (
      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
}

function Tooltip({ content, children }: { content: string; children: React.ReactNode }) {
  const [show, setShow] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  return (
    <div
      ref={ref}
      className="relative inline-flex"
      onMouseEnter={() => setShow(true)}
      onMouseLeave={() => setShow(false)}
    >
      {children}
      {show && (
        <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 bg-slate-900 dark:bg-slate-700 text-white text-xs rounded whitespace-nowrap z-50 animate-fade-in">
          {content}
          <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-900 dark:border-t-slate-700" />
        </div>
      )}
    </div>
  )
}

export function QuickActions({ actions, className = '' }: QuickActionsProps) {
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const [showLeftScroll, setShowLeftScroll] = useState(false)
  const [showRightScroll, setShowRightScroll] = useState(true)

  const handleScroll = () => {
    if (scrollContainerRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = scrollContainerRef.current
      setShowLeftScroll(scrollLeft > 0)
      setShowRightScroll(scrollLeft + clientWidth < scrollWidth)
    }
  }

  // Group actions by their group property
  const groupedActions = actions.reduce((acc, action) => {
    const group = action.group || 'settings'
    if (!acc[group]) {
      acc[group] = []
    }
    acc[group].push(action)
    return acc
  }, {} as Record<string, QuickAction[]>)

  // Define group order
  const groupOrder: ('add' | 'scan' | 'settings')[] = ['add', 'scan', 'settings']

  const scrollBy = (amount: number) => {
    if (scrollContainerRef.current) {
      scrollContainerRef.current.scrollBy({ left: amount, behavior: 'smooth' })
    }
  }

  return (
    <Card variant="elevated" className={className}>
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-white">
          Quick Actions
        </h3>
        <div className="flex items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => scrollBy(-200)}
            className={`p-1.5 ${!showLeftScroll ? 'opacity-30' : ''}`}
            disabled={!showLeftScroll}
            aria-label="Scroll left"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => scrollBy(200)}
            className={`p-1.5 ${!showRightScroll ? 'opacity-30' : ''}`}
            disabled={!showRightScroll}
            aria-label="Scroll right"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Button>
        </div>
      </div>

      {/* Horizontal scroll container with snap */}
      <div
        ref={scrollContainerRef}
        className="flex gap-6 overflow-x-auto pb-2 scroll-smooth snap-x snap-mandatory scrollbar-hide"
        onScroll={handleScroll}
        role="list"
        aria-label="Quick actions"
      >
        {groupOrder.map((group) => {
          const groupActions = groupedActions[group]
          if (!groupActions || groupActions.length === 0) return null

          const groupInfo = ACTION_GROUPS[group]

          return (
            <div key={group} className="flex-shrink-0 snap-start">
              {/* Group header */}
              <div className="flex items-center gap-2 mb-3 text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                <span className="p-1 rounded bg-slate-100 dark:bg-slate-800">
                  {groupInfo.icon}
                </span>
                {groupInfo.title}
              </div>

              {/* Actions grid within group */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3" role="list">
                {groupActions.map((action) => (
                  <Tooltip key={action.id} content={action.label}>
                    <button
                      onClick={action.onClick}
                      className={`
                        flex flex-col items-center justify-center p-4 rounded-xl
                        transition-all duration-200
                        focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2
                        ${action.variant === 'primary'
                          ? 'bg-indigo-50 dark:bg-indigo-900/20 hover:bg-indigo-100 dark:hover:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300'
                          : 'bg-slate-50 dark:bg-slate-800/50 hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-700 dark:text-slate-300'
                        }
                        hover:shadow-md hover:-translate-y-0.5
                        min-w-[100px]
                      `}
                      role="listitem"
                      aria-label={action.label}
                    >
                      <div
                        className={`
                          p-2 rounded-lg mb-2 transition-transform duration-200
                          ${action.variant === 'primary'
                            ? 'bg-indigo-100 dark:bg-indigo-900/50'
                            : 'bg-slate-200 dark:bg-slate-700'
                          }
                        `}
                      >
                        <span className="w-6 h-6 block">
                          {action.icon}
                        </span>
                      </div>
                      <span className="text-sm font-medium text-center line-clamp-1">
                        {action.label}
                      </span>
                      {action.description && (
                        <span className="text-xs text-slate-500 dark:text-slate-400 text-center mt-1 line-clamp-1">
                          {action.description}
                        </span>
                      )}
                    </button>
                  </Tooltip>
                ))}
              </div>
            </div>
          )
        })}
      </div>

      <style>{`
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        @keyframes fade-in {
          from { opacity: 0; transform: translateY(4px); }
          to { opacity: 1; transform: translateY(0); }
        }
        .animate-fade-in {
          animation: fade-in 0.15s ease-out;
        }
      `}</style>
    </Card>
  )
}

export default QuickActions
