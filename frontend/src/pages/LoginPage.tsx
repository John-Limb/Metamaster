import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { LoginForm } from '@/components/auth/LoginForm'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

/**
 * Login page component
 *
 * Features:
 * - Centers the login form on the page
 * - Redirects authenticated users away from this page
 * - Preserves the intended destination for post-login redirect
 */
export const LoginPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  // Show loading spinner while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50 dark:bg-secondary-900">
        <LoadingSpinner size="lg" message="Loading..." />
      </div>
    )
  }

  // Redirect to home if already authenticated
  // Preserve the "from" location if it exists (e.g., from ProtectedRoute)
  if (isAuthenticated) {
    const from = (location.state as { from?: { pathname: string } })?.from?.pathname || '/'
    return <Navigate to={from} replace />
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-secondary-50 dark:bg-secondary-900 px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 shadow-lg mb-4">
            <span className="text-3xl font-bold text-white">M</span>
          </div>
          <h1 className="text-3xl font-bold text-secondary-900 dark:text-white">
            Metamaster
          </h1>
          <p className="mt-2 text-sm text-secondary-600 dark:text-secondary-400">
            Media metadata management system
          </p>
        </div>

        {/* Login Form */}
        <LoginForm />

        {/* Additional help links */}
        <div className="mt-6 text-center text-sm text-secondary-600 dark:text-secondary-400">
          <p>
            Need help?{' '}
            <a
              href="mailto:support@metamaster.local"
              className="font-medium text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Contact support
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default LoginPage
