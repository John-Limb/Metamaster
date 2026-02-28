/**
 * Auth components barrel export
 *
 * Provides exports for all authentication-related components:
 * - LoginForm: User login form with validation
 * - ChangePasswordForm: Password change form for forced password change flow
 * - ProtectedRoute: Route guard component for authentication
 */

export { LoginForm } from './LoginForm'
export { ChangePasswordForm } from './ChangePasswordForm'
export { ProtectedRoute } from './ProtectedRoute'

// Default exports for convenience
export { default as LoginFormDefault } from './LoginForm'
export { default as ChangePasswordFormDefault } from './ChangePasswordForm'
export { default as ProtectedRouteDefault } from './ProtectedRoute'
