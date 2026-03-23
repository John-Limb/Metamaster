import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import {
  FaHome,
  FaFolder,
  FaSearch,
  FaFilm,
  FaTv,
  FaFolderOpen,
  FaCog,
  FaChevronLeft,
  FaChevronRight,
  FaInfoCircle,
  FaDatabase,
  FaList,
  FaServer,
  FaLayerGroup,
  FaListUl,
} from 'react-icons/fa'
import { useUIStore } from '@/stores/uiStore'

interface SidebarProps {
  isOpen?: boolean
  onClose?: () => void
}

interface NavItem {
  label: string
  path: string
  icon: React.ReactNode
  badge?: string
}

const navItems: NavItem[] = [
  { label: 'Home', path: '/', icon: <FaHome className="w-5 h-5" /> },
  { label: 'Files', path: '/files', icon: <FaFolder className="w-5 h-5" /> },
  { label: 'Search', path: '/search', icon: <FaSearch className="w-5 h-5" /> },
  { label: 'Movies', path: '/movies', icon: <FaFilm className="w-5 h-5" />, badge: 'New' },
  { label: 'TV Shows', path: '/tv-shows', icon: <FaTv className="w-5 h-5" /> },
  { label: 'Organisation', path: '/organisation', icon: <FaFolderOpen className="w-5 h-5" /> },
  { label: 'Storage', path: '/storage', icon: <FaDatabase className="w-5 h-5" /> },
  { label: 'Queue', path: '/queue', icon: <FaList className="w-5 h-5" /> },
  { label: 'Plex Collections', path: '/plex/collections', icon: <FaLayerGroup className="w-5 h-5" /> },
  { label: 'Plex Playlists', path: '/plex/playlists', icon: <FaListUl className="w-5 h-5" /> },
  { label: 'System Health', path: '/system-health', icon: <FaServer className="w-5 h-5" /> },
  { label: 'Settings', path: '/settings', icon: <FaCog className="w-5 h-5" /> },
]

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export const Sidebar: React.FC<SidebarProps> = ({ isOpen: _isOpen = true, onClose }: SidebarProps) => {
  const location = useLocation()
  const sidebarOpen = useUIStore((state) => state.sidebarOpen)
  const setSidebarOpen = useUIStore((state) => state.setSidebarOpen)
  const [isCollapsed, setIsCollapsed] = useState(() => {
    const stored = localStorage.getItem('sidebarCollapsed')
    return stored ? JSON.parse(stored) : false
  })
  const [isMobile, setIsMobile] = useState(false)
  const [showTooltip, setShowTooltip] = useState<string | null>(null)

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 1024)
    }
    handleResize()
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', JSON.stringify(isCollapsed))
  }, [isCollapsed])

  const handleClose = () => {
    setSidebarOpen(false)
    onClose?.()
  }

  const isActive = (path: string) => {
    if (path === '/') {
      return location.pathname === '/'
    }
    return location.pathname === path || location.pathname.startsWith(path + '/')
  }

  const toggleCollapse = () => {
    setIsCollapsed(!isCollapsed)
  }

  const sidebarWidth = isCollapsed ? 'w-16' : 'w-64'

  return (
    <>
      {/* Mobile Backdrop */}
      {sidebarOpen && isMobile && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={handleClose}
          aria-hidden="true"
        />
      )}

      {/* Sidebar */}
      <aside
        className={`
          fixed top-16 left-0 h-[calc(100vh-4rem)] bg-card
          border-r border-edge
          transition-all duration-300 ease-in-out z-40
          ${sidebarWidth}
          ${isMobile 
            ? (sidebarOpen ? 'translate-x-0' : '-translate-x-full')
            : (isCollapsed ? 'lg:w-16' : 'lg:w-64')
          }
        `}
      >
        <div className="flex flex-col h-full">
          {/* Navigation */}
          <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
            {navItems.map((item) => {
              const active = isActive(item.path)
              const itemKey = item.path

              return (
                <div
                  key={item.path}
                  className="relative"
                  onMouseEnter={() => !isCollapsed && setShowTooltip(itemKey)}
                  onMouseLeave={() => setShowTooltip(null)}
                >
                  <Link
                    to={item.path}
                    onClick={handleClose}
                    className={`
                      flex items-center gap-3 px-3 py-2.5 rounded-lg
                      transition-all duration-150
                      ${active
                        ? 'bg-primary-50 dark:bg-primary-900/30 text-primary-600 dark:text-primary-400 font-medium'
                        : 'text-dim hover:bg-subtle'
                      }
                      ${isCollapsed ? 'justify-center' : ''}
                      focus:outline-none focus:ring-2 focus:ring-primary-500
                    `}
                    aria-current={active ? 'page' : undefined}
                  >
                    <span className={active ? 'text-primary-600 dark:text-primary-400' : 'text-hint'}>
                      {item.icon}
                    </span>
                    
                    {!isCollapsed && (
                      <>
                        <span className="flex-1">{item.label}</span>
                        {item.badge && (
                          <span className="px-2 py-0.5 text-xs font-medium bg-primary-100 dark:bg-primary-900 text-primary-600 dark:text-primary-300 rounded-full">
                            {item.badge}
                          </span>
                        )}
                      </>
                    )}

                    {/* Active indicator for collapsed state */}
                    {isCollapsed && active && (
                      <span className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-primary-600 dark:bg-primary-400 rounded-r" />
                    )}
                  </Link>

                  {/* Tooltip for collapsed state */}
                  {isCollapsed && showTooltip === itemKey && (
                    <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-3 py-1.5 bg-popover text-body border border-edge text-sm rounded-lg whitespace-nowrap z-50 animate-in fade-in duration-150 shadow-lg">
                      {item.label}
                    </div>
                  )}
                </div>
              )
            })}
          </nav>

          {/* Footer */}
          <div className={`p-3 border-t border-edge ${isCollapsed ? 'flex justify-center' : ''}`}>
            {/* Collapse Toggle (Desktop only) */}
            {!isMobile && (
              <button
                onClick={toggleCollapse}
                className={`
                  w-full flex items-center gap-3 px-3 py-2
                  text-dim
                  hover:bg-subtle
                  rounded-lg transition-colors duration-150
                  ${isCollapsed ? 'justify-center' : ''}
                `}
                aria-label={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              >
                {isCollapsed ? (
                  <FaChevronRight className="w-4 h-4" />
                ) : (
                  <>
                    <FaChevronLeft className="w-4 h-4" />
                    <span className="text-sm">Collapse</span>
                  </>
                )}
              </button>
            )}

            {/* Version Info */}
            {!isCollapsed && (
              <div className="flex items-center justify-center gap-2 pt-3 text-xs text-hint">
                <FaInfoCircle className="w-3.5 h-3.5" />
                <span>Metamaster v1.0.0</span>
              </div>
            )}
          </div>
        </div>
      </aside>
    </>
  )
}

export default Sidebar
