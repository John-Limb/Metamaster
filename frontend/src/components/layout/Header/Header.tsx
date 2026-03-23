import React, { useState, useRef, useEffect, type ChangeEvent, type KeyboardEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import {
  FaSearch,
  FaSun,
  FaMoon,
  FaTimes,
  FaHome,
  FaFilm,
  FaTv,
  FaFolderOpen,
  FaLayerGroup,
  FaCog,
} from 'react-icons/fa'
import { useTheme } from '@/context/ThemeContext'
import { useAuth } from '@/context/AuthContext'
import { NotificationDropdown, type Notification } from '../NotificationDropdown'
import { UserMenu } from '../UserMenu'

interface HeaderProps {
  onMenuClick?: () => void
}

interface SearchResult {
  id: string
  title: string
  type: string
}

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const Header: React.FC<HeaderProps> = ({ onMenuClick: _onMenuClick }: HeaderProps) => {
  const { setTheme, resolvedTheme, colourTheme } = useTheme()
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [isSearchOpen, setIsSearchOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [isSearchFocused, setIsSearchFocused] = useState(false)
  const searchInputRef = useRef<HTMLInputElement>(null)
  const searchContainerRef = useRef<HTMLDivElement>(null)

  // Notifications state - would be populated from API/notification service
  const [notifications, setNotifications] = useState<Notification[]>([])

  // Handle scroll for shadow
  const [isScrolled, setIsScrolled] = useState(false)
  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 8)
    }
    window.addEventListener('scroll', handleScroll, { passive: true })
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  // Handle search outside click
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        searchContainerRef.current &&
        !searchContainerRef.current.contains(event.target as Node)
      ) {
        setIsSearchFocused(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  // Mock search function
  const handleSearch = (query: string) => {
    setSearchQuery(query)
    if (query.length > 1) {
      // Mock search results
      setSearchResults([
        { id: '1', title: `${query} - Movie`, type: 'movie' },
        { id: '2', title: `${query} - TV Show`, type: 'tv' },
        { id: '3', title: `${query} - File`, type: 'file' },
      ])
    } else {
      setSearchResults([])
    }
  }

  const toggleTheme = () => {
    const newTheme = resolvedTheme === 'dark' ? 'light' : 'dark'
    setTheme(newTheme)
  }

  const handleMarkAsRead = (id: string) => {
    setNotifications((prev) =>
      prev.map((n) => (n.id === id ? { ...n, read: true } : n))
    )
  }

  const handleMarkAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })))
  }

  const handleClearAll = () => {
    setNotifications([])
  }

  const handleNotificationClick = () => {
    console.log('Notification clicked')
  }

  const handleProfile = () => {
    navigate('/profile')
  }

  const handleSettings = () => {
    navigate('/settings')
  }

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  // Keyboard navigation for search
  const handleSearchKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Escape') {
      setIsSearchFocused(false)
      searchInputRef.current?.blur()
    } else if (e.key === 'ArrowDown') {
      e.preventDefault()
      const firstResult = searchContainerRef.current?.querySelector(
        '[role="option"]'
      ) as HTMLElement
      firstResult?.focus()
    }
  }

  return (
    <header
      className={`fixed top-0 left-0 right-0 h-16 bg-card border-b border-edge z-50 transition-shadow duration-200 ${
        isScrolled ? 'shadow-md' : 'shadow-sm'
      }`}
    >
      <div className="flex items-center justify-between h-full px-4 lg:px-6">
        {/* Left Section */}
        <div className="flex items-center gap-4">
          {/* Logo */}
          <Link to="/" className="flex items-center gap-3">
            <div className="w-9 h-9 bg-gradient-to-br from-indigo-500 to-indigo-600 rounded-xl flex items-center justify-center shadow-md">
              <span className="text-white font-bold text-lg">M</span>
            </div>
            <span className="hidden sm:inline-block font-bold text-xl text-body">
              Metamaster
            </span>
          </Link>

          {/* Nav Links */}
          <nav className="flex items-center gap-1 ml-4 sm:ml-6">
            {[
              { to: '/', label: 'Home', icon: <FaHome className="w-4 h-4" /> },
              { to: '/movies', label: 'Movies', icon: <FaFilm className="w-4 h-4" /> },
              { to: '/tv-shows', label: 'TV Shows', icon: <FaTv className="w-4 h-4" /> },
              { to: '/organisation', label: 'Organisation', icon: <FaFolderOpen className="w-4 h-4" /> },
              { to: '/plex/collections', label: 'Plex', icon: <FaLayerGroup className="w-4 h-4" /> },
              { to: '/settings', label: 'Settings', icon: <FaCog className="w-4 h-4" /> },
            ].map((item) => {
              const active = item.to === '/'
                ? location.pathname === '/'
                : location.pathname === item.to || location.pathname.startsWith(item.to + '/')
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-sm font-medium transition-colors duration-150 ${
                    active
                      ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400'
                      : 'text-dim hover:bg-subtle'
                  }`}
                >
                  {item.icon}
                  <span className="hidden sm:inline">{item.label}</span>
                </Link>
              )
            })}
          </nav>
        </div>

        {/* Center Section - Search */}
        <div className="hidden md:flex flex-1 max-w-xl mx-8">
          <div className="relative w-full" ref={searchContainerRef}>
            <div
              className={`relative flex items-center transition-all duration-200 ${
                isSearchFocused
                  ? 'bg-card shadow-md ring-2 ring-primary-500 rounded-xl -ml-2'
                  : 'bg-subtle rounded-xl'
              }`}
            >
              <FaSearch
                className={`absolute left-3 w-4 h-4 transition-colors ${
                  isSearchFocused
                    ? 'text-primary-500'
                    : 'text-hint'
                }`}
              />
              <input
                ref={searchInputRef}
                type="text"
                placeholder="Search movies, TV shows, files..."
                value={searchQuery}
                onChange={(e: ChangeEvent<HTMLInputElement>) => handleSearch(e.target.value)}
                onFocus={() => setIsSearchFocused(true)}
                onKeyDown={handleSearchKeyDown}
                className="w-full py-2.5 pl-10 pr-10 bg-transparent border-0 text-sm text-body placeholder-hint focus:outline-none"
                aria-label="Search"
                aria-expanded={isSearchFocused}
                aria-controls="search-results"
              />
              {searchQuery && (
                <button
                  onClick={() => {
                    setSearchQuery('')
                    setSearchResults([])
                  }}
                  className="absolute right-3 p-1 text-hint hover:text-dim transition-colors"
                  aria-label="Clear search"
                >
                  <FaTimes className="w-3.5 h-3.5" />
                </button>
              )}
            </div>

            {/* Search Results Dropdown */}
            {isSearchFocused && (searchQuery.length > 1 || searchResults.length > 0) && (
              <div
                id="search-results"
                className="absolute top-full left-0 right-0 mt-2 bg-card rounded-xl shadow-lg border border-edge overflow-hidden animate-in fade-in slide-in-from-top-2 duration-150"
                role="listbox"
              >
                {searchResults.length > 0 ? (
                  <div className="py-2">
                    {searchResults.map((result) => (
                      <button
                        key={result.id}
                        role="option"
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-left text-sm text-dim hover:bg-subtle transition-colors focus:outline-none focus:bg-subtle"
                        onClick={() => {
                          console.log('Search result clicked:', result)
                          setIsSearchFocused(false)
                          setSearchQuery('')
                        }}
                      >
                        <FaSearch className="w-4 h-4 text-gray-400" />
                        <span className="flex-1">{result.title}</span>
                        <span className="text-xs text-gray-400 dark:text-gray-500 capitalize">
                          {result.type}
                        </span>
                      </button>
                    ))}
                  </div>
                ) : searchQuery.length > 1 ? (
                  <div className="px-4 py-6 text-center text-sm text-hint">
                    No results found for &quot;{searchQuery}&quot;
                  </div>
                ) : null}
              </div>
            )}
          </div>
        </div>

        {/* Right Section */}
        <div className="flex items-center gap-2">
          {/* Mobile search button */}
          <button
            onClick={() => setIsSearchOpen(!isSearchOpen)}
            className="md:hidden p-2 text-dim hover:bg-subtle rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500"
            aria-label="Open search"
          >
            <FaSearch className="w-5 h-5" />
          </button>

          {/* Theme Toggle */}
          {colourTheme === 'default' && (
            <button
              onClick={toggleTheme}
              className="p-2 text-dim hover:bg-subtle rounded-lg transition-colors duration-150 focus:outline-none focus:ring-2 focus:ring-primary-500"
              aria-label={`Switch to ${resolvedTheme === 'dark' ? 'light' : 'dark'} mode`}
            >
              {resolvedTheme === 'dark' ? (
                <FaSun className="w-5 h-5" />
              ) : (
                <FaMoon className="w-5 h-5" />
              )}
            </button>
          )}

          {/* Notifications */}
          <NotificationDropdown
            notifications={notifications}
            onMarkAsRead={handleMarkAsRead}
            onMarkAllAsRead={handleMarkAllAsRead}
            onClearAll={handleClearAll}
            onNotificationClick={handleNotificationClick}
          />

          {/* User Menu */}
          <UserMenu
            user={user}
            onProfile={handleProfile}
            onSettings={handleSettings}
            onLogout={handleLogout}
          />
        </div>
      </div>

      {/* Mobile Search Overlay */}
      {isSearchOpen && (
        <div className="md:hidden absolute top-full left-0 right-0 bg-card border-b border-edge p-4 animate-in fade-in duration-150">
          <div className="relative">
            <FaSearch className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search movies, TV shows, files..."
              value={searchQuery}
              onChange={(e: ChangeEvent<HTMLInputElement>) => handleSearch(e.target.value)}
              className="w-full py-2.5 pl-10 pr-10 bg-subtle border-0 rounded-lg text-sm text-body placeholder-hint focus:outline-none focus:ring-2 focus:ring-primary-500"
              autoFocus
            />
            {searchQuery && (
              <button
                onClick={() => {
                  setSearchQuery('')
                  setSearchResults([])
                }}
                className="absolute right-3 top-1/2 -translate-y-1/2 p-1 text-hint hover:text-dim"
              >
                <FaTimes className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      )}
    </header>
  )
}

export default Header
