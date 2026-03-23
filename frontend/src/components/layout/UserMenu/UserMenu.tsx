import React, { useState, useRef, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { FaUser, FaCog, FaSignOutAlt, FaChevronDown, FaSignInAlt } from 'react-icons/fa'
import { useAuth } from '@/context/AuthContext'
import type { User } from '@/types/auth'

interface UserMenuProps {
  user: User | null
  onProfile: () => void
  onSettings: () => void
  onLogout: () => void
}

export const UserMenu: React.FC<UserMenuProps> = ({
  user,
  onProfile,
  onSettings,
  onLogout,
}: UserMenuProps) => {
  const { isAuthenticated, isLoading } = useAuth()
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const buttonRef = useRef<HTMLButtonElement>(null)

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

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map((n) => n[0])
      .join('')
      .toUpperCase()
      .slice(0, 2)
  }

  const handleKeyDown = (event: React.KeyboardEvent, action: () => void) => {
    if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault()
      action()
    }
  }

  // Show loading state
  if (isLoading) {
    return (
      <div className="flex items-center gap-2">
        <div className="w-8 h-8 rounded-full bg-subtle animate-pulse" />
      </div>
    )
  }

  // Show login button when not authenticated
  if (!isAuthenticated || !user) {
    return (
      <div className="flex items-center gap-2">
        <Link
          to="/login"
          className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-dim hover:bg-subtle rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500"
        >
          <FaSignInAlt className="w-4 h-4" />
          <span className="hidden sm:inline">Sign in</span>
        </Link>
      </div>
    )
  }

  // Show user menu when authenticated
  return (
    <div className="relative">
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 p-1.5 pr-3 text-dim hover:bg-subtle rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500"
        aria-label="User menu"
        aria-haspopup="true"
        aria-expanded={isOpen}
      >
        {user.avatar_url ? (
          <img
            src={user.avatar_url}
            alt={user.username}
            className="w-8 h-8 rounded-full object-cover"
          />
        ) : (
          <div className="w-8 h-8 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
            <span className="text-sm font-semibold text-primary-600 dark:text-primary-300">
              {getInitials(user.username)}
            </span>
          </div>
        )}
        <div className="hidden sm:block text-left">
          <p className="text-sm font-medium text-body leading-none">
            {user.username}
          </p>
          <p className="text-xs text-hint mt-0.5 truncate max-w-[120px]">
            {user.email}
          </p>
        </div>
        <FaChevronDown
          className={`hidden sm:block w-3 h-3 text-hint transition-transform duration-150 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {isOpen && (
        <div
          ref={dropdownRef}
          className="absolute right-0 mt-2 w-56 bg-card rounded-xl shadow-lg border border-edge overflow-hidden animate-in fade-in slide-in-from-top-2 duration-200"
          role="menu"
          aria-orientation="vertical"
        >
          {/* User Info Header */}
          <div className="px-4 py-3 border-b border-edge bg-subtle">
            <div className="flex items-center gap-3">
              {user.avatar_url ? (
                <img
                  src={user.avatar_url}
                  alt={user.username}
                  className="w-10 h-10 rounded-full object-cover"
                />
              ) : (
                <div className="w-10 h-10 rounded-full bg-primary-100 dark:bg-primary-900 flex items-center justify-center">
                  <span className="text-lg font-semibold text-primary-600 dark:text-primary-300">
                    {getInitials(user.username)}
                  </span>
                </div>
              )}
              <div className="min-w-0">
                <p className="text-sm font-medium text-body truncate">
                  {user.username}
                </p>
                <p className="text-xs text-hint truncate">
                  {user.email}
                </p>
              </div>
            </div>
          </div>

          {/* Menu Items */}
          <div className="py-1">
            <button
              onClick={() => {
                onProfile()
                setIsOpen(false)
              }}
              onKeyDown={(e) => handleKeyDown(e, () => {
                onProfile()
                setIsOpen(false)
              })}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-dim hover:bg-subtle transition-colors duration-150 focus:outline-none focus:bg-subtle"
              role="menuitem"
            >
              <FaUser className="w-4 h-4 text-hint" />
              <span>Profile</span>
            </button>
            <button
              onClick={() => {
                onSettings()
                setIsOpen(false)
              }}
              onKeyDown={(e) => handleKeyDown(e, () => {
                onSettings()
                setIsOpen(false)
              })}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-dim hover:bg-subtle transition-colors duration-150 focus:outline-none focus:bg-subtle"
              role="menuitem"
            >
              <FaCog className="w-4 h-4 text-hint" />
              <span>Settings</span>
            </button>
          </div>

          {/* Divider */}
          <div className="border-t border-edge" />

          {/* Logout */}
          <div className="py-1">
            <button
              onClick={() => {
                onLogout()
                setIsOpen(false)
              }}
              onKeyDown={(e) => handleKeyDown(e, () => {
                onLogout()
                setIsOpen(false)
              })}
              className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 transition-colors duration-150 focus:outline-none focus:bg-red-50 dark:focus:bg-red-900/20"
              role="menuitem"
            >
              <FaSignOutAlt className="w-4 h-4" />
              <span>Sign out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

export default UserMenu
