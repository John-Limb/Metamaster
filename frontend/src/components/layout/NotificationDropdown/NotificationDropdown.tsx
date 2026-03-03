import React, { useState, useRef, useEffect } from 'react'
import { FaBell, FaTrash, FaChevronRight } from 'react-icons/fa'

export interface Notification {
  id: string
  title: string
  message: string
  type: 'info' | 'success' | 'warning' | 'error'
  timestamp: Date
  read: boolean
}

interface NotificationDropdownProps {
  notifications: Notification[]
  onMarkAsRead: (id: string) => void
  onMarkAllAsRead: () => void
  onClearAll: () => void
  onNotificationClick: (notification: Notification) => void
}

const notificationTypeStyles = {
  info: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-800',
  success: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-800',
  warning: 'bg-amber-50 dark:bg-amber-900/30 border-amber-200 dark:border-amber-800',
  error: 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-800',
}

const notificationIconStyles = {
  info: 'text-blue-500 dark:text-blue-400',
  success: 'text-green-500 dark:text-green-400',
  warning: 'text-amber-500 dark:text-amber-400',
  error: 'text-red-500 dark:text-red-400',
}

export const NotificationDropdown: React.FC<NotificationDropdownProps> = ({
  notifications,
  onMarkAsRead,
  onMarkAllAsRead,
  onClearAll,
  onNotificationClick,
}) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

  const unreadCount = notifications.filter((n) => !n.read).length

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node) &&
        !buttonRef.current?.contains(event.target as Node)
      ) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsOpen(false)
        buttonRef.current?.focus()
      }
    }

    if (isOpen) {
      document.addEventListener('keydown', handleEscape)
      return () => document.removeEventListener('keydown', handleEscape)
    }
  }, [isOpen])

  const formatTime = (date: Date) => {
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(diff / 3600000)
    const days = Math.floor(diff / 86400000)

    if (minutes < 1) return 'Just now'
    if (minutes < 60) return `${minutes}m ago`
    if (hours < 24) return `${hours}h ago`
    if (days < 7) return `${days}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="relative p-2 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-indigo-500"
        aria-label={`Notifications${unreadCount > 0 ? `, ${unreadCount} unread` : ''}`}
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        <FaBell className="w-5 h-5" />
        {unreadCount > 0 && (
          <span className="absolute -top-1 -right-1 flex items-center justify-center min-w-[18px] h-[18px] text-xs font-bold text-white bg-red-500 rounded-full px-1">
            {unreadCount > 99 ? '99+' : unreadCount}
          </span>
        )}
      </button>

      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 mt-2 w-80 sm:w-96 bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200"
          role="menu"
          aria-orientation="vertical"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700">
            <h3 className="font-semibold text-gray-900 dark:text-white">Notifications</h3>
            <div className="flex items-center gap-2">
              {unreadCount > 0 && (
                <button
                  onClick={onMarkAllAsRead}
                  className="text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium transition-colors"
                  role="menuitem"
                >
                  Mark all read
                </button>
              )}
              {notifications.length > 0 && (
                <button
                  onClick={onClearAll}
                  className="p-1 text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 transition-colors"
                  aria-label="Clear all notifications"
                >
                  <FaTrash className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </div>

          {/* Notification List */}
          <div className="max-h-96 overflow-y-auto">
            {notifications.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 px-4 text-center">
                <FaBell className="w-10 h-10 text-gray-300 dark:text-gray-600 mb-3" />
                <p className="text-gray-500 dark:text-gray-400 text-sm">No notifications yet</p>
                <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                  We'll notify you when something arrives
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-100 dark:divide-gray-700">
                {notifications.map((notification) => (
                  <button
                    key={notification.id}
                    onClick={() => {
                      onNotificationClick(notification)
                      if (!notification.read) {
                        onMarkAsRead(notification.id)
                      }
                    }}
                    className={`w-full px-4 py-3 text-left hover:bg-gray-50 dark:hover:bg-gray-750 transition-colors duration-150 focus:outline-none focus:bg-gray-50 dark:focus:bg-gray-750 ${
                      !notification.read ? 'bg-indigo-50/50 dark:bg-indigo-900/10' : ''
                    }`}
                    role="menuitem"
                  >
                    <div className="flex gap-3">
                      <div
                        className={`flex-shrink-0 w-8 h-8 rounded-lg flex items-center justify-center ${notificationTypeStyles[notification.type]}`}
                      >
                        <span className={notificationIconStyles[notification.type]}>
                          {notification.type === 'success' && '✓'}
                          {notification.type === 'warning' && '!'}
                          {notification.type === 'error' && '×'}
                          {notification.type === 'info' && 'i'}
                        </span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between gap-2">
                          <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                            {notification.title}
                          </p>
                          {!notification.read && (
                            <span className="flex-shrink-0 w-2 h-2 bg-indigo-500 rounded-full mt-1.5" />
                          )}
                        </div>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 line-clamp-2">
                          {notification.message}
                        </p>
                        <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                          {formatTime(notification.timestamp)}
                        </p>
                      </div>
                      <FaChevronRight className="flex-shrink-0 w-4 h-4 text-gray-400 self-center" />
                    </div>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Footer */}
          {notifications.length > 0 && (
            <div className="px-4 py-2 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-750">
              <button className="w-full text-center text-xs text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 font-medium transition-colors">
                View all notifications
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default NotificationDropdown
