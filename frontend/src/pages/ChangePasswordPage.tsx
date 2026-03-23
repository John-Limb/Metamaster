import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { ChangePasswordForm } from '@/components/auth/ChangePasswordForm'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

/**
 * Change password page component
 *
 * Features:
 * - Centers the change password form on the page
 * - Shows explanatory text about required password change
 * - Only accessible to authenticated users who need to change their password
 * - Redirects users who don't need to change their password
 */
export const ChangePasswordPage: React.FC = () => {
  const { isAuthenticated, isLoading, requiresPasswordChange } = useAuth()

  // Show loading spinner while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-page">
        <LoadingSpinner size="lg" message="Loading..." />
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  // Redirect to home if user doesn't need to change password
  // (they've already changed it or never needed to)
  if (!requiresPasswordChange) {
    return <Navigate to="/" replace />
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-page px-4 py-12 sm:px-6 lg:px-8">
      <div className="w-full max-w-md">
        {/* Logo/Brand */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-indigo-600 shadow-lg mb-4">
            <span className="text-3xl font-bold text-white">M</span>
          </div>
          <h1 className="text-3xl font-bold text-body">
            Change Password
          </h1>
          <p className="mt-2 text-sm text-dim">
            Update your password to continue
          </p>
        </div>

        {/* Info banner */}
        <div className="mb-6 p-4 bg-warning-50 dark:bg-warning-900/20 border border-warning-200 dark:border-warning-800 rounded-lg">
          <div className="flex items-start">
            <svg
              className="w-5 h-5 text-warning mt-0.5 mr-3 flex-shrink-0"
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 20 20"
              fill="currentColor"
              aria-hidden="true"
            >
              <path
                fillRule="evenodd"
                d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            <div>
              <p className="text-sm font-medium text-warning-800 dark:text-warning-200">
                Password change required
              </p>
              <p className="mt-1 text-sm text-warning-700 dark:text-warning-300">
                For security reasons, you must change your password before continuing to use your account.
              </p>
            </div>
          </div>
        </div>

        {/* Change Password Form */}
        <ChangePasswordForm />
      </div>
    </div>
  )
}

export default ChangePasswordPage
