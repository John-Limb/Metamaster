import { Navigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { RegisterForm } from '@/components/auth/RegisterForm'
import { LoadingSpinner } from '@/components/common/LoadingSpinner'

/**
 * Registration page component
 *
 * Features:
 * - Centers the registration form on the page
 * - Redirects authenticated users away from this page
 * - Shows branding and support information
 */
export const RegisterPage: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth()

  // Show loading spinner while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-secondary-50 dark:bg-secondary-900">
        <LoadingSpinner size="lg" message="Loading..." />
      </div>
    )
  }

  // Redirect to home if already authenticated
  if (isAuthenticated) {
    return <Navigate to="/" replace />
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
            Create your account
          </h1>
          <p className="mt-2 text-sm text-secondary-600 dark:text-secondary-400">
            Join Metamaster to manage your media library
          </p>
        </div>

        {/* Register Form */}
        <RegisterForm />

        {/* Terms and privacy */}
        <div className="mt-6 text-center text-xs text-secondary-500 dark:text-secondary-400">
          <p>
            By creating an account, you agree to our{' '}
            <a
              href="/terms"
              className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Terms of Service
            </a>{' '}
            and{' '}
            <a
              href="/privacy"
              className="text-indigo-600 hover:text-indigo-500 dark:text-indigo-400 dark:hover:text-indigo-300"
            >
              Privacy Policy
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default RegisterPage
