import { type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

interface ProtectedRouteProps {
  /** Children to render if authenticated */
  children: ReactNode
  /** If true, requires user to change password before accessing this route */
  requirePasswordChange?: boolean
}

/**
 * Route guard component that checks authentication status
 *
 * Features:
 * - Checks authentication status using useAuth hook
 * - Shows loading spinner while checking auth status
 * - Redirects to login page if not authenticated
 * - Supports optional requirePasswordChange prop for forced password change flow
 * - Preserves the intended destination URL for post-login redirect
 */
export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requirePasswordChange = false,
}) => {
  const { isAuthenticated, isLoading, requiresPasswordChange } = useAuth()
  const location = useLocation()

  // Show loading spinner while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50 dark:bg-secondary-900">
        <LoadingSpinner size="lg" message="Checking authentication..." />
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    // Save the attempted URL for redirecting after login
    return <Navigate to="/login" state={{ from: location }} replace />
  }

  // If this route requires password change and user doesn't need to change password,
  // redirect to home (they've already changed it)
  if (requirePasswordChange && !requiresPasswordChange) {
    return <Navigate to="/" replace />
  }

  // If user needs to change password and this is not the password change route,
  // redirect to password change page
  if (requiresPasswordChange && !requirePasswordChange) {
    return <Navigate to="/change-password" state={{ from: location }} replace />
  }

  // User is authenticated and meets all requirements
  return <>{children}</>
}

export default ProtectedRoute
