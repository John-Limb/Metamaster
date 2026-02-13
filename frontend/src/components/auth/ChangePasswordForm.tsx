import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { zodResolver } from '@hookform/resolvers/zod'
import { z } from 'zod'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/context/AuthContext'
import { TextInput } from '@/components/common/TextInput'
import { Button } from '@/components/common/Button'

/**
 * Zod schema for password change form validation
 * Matches backend password requirements
 */
const changePasswordSchema = z
  .object({
    current_password: z.string().min(1, 'Current password is required'),
    new_password: z
      .string()
      .min(8, 'Password must be at least 8 characters')
      .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
      .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
      .regex(/[0-9]/, 'Password must contain at least one number'),
    confirm_new_password: z.string(),
  })
  .refine((data) => data.new_password === data.confirm_new_password, {
    message: "Passwords don't match",
    path: ['confirm_new_password'],
  })
  .refine((data) => data.current_password !== data.new_password, {
    message: 'New password must be different from current password',
    path: ['new_password'],
  })

type ChangePasswordFormData = z.infer<typeof changePasswordSchema>

/**
 * Password strength indicator component
 */
const PasswordStrengthIndicator: React.FC<{ password: string }> = ({
  password,
}) => {
  const requirements = [
    { met: password.length >= 8, label: 'At least 8 characters' },
    { met: /[A-Z]/.test(password), label: 'One uppercase letter' },
    { met: /[a-z]/.test(password), label: 'One lowercase letter' },
    { met: /[0-9]/.test(password), label: 'One number' },
  ]

  const metCount = requirements.filter((r) => r.met).length
  const strengthLevel = metCount === 0 ? 0 : metCount

  const strengthColors = ['bg-secondary-200', 'bg-danger', 'bg-warning', 'bg-info', 'bg-success']
  const strengthLabels = ['', 'Weak', 'Fair', 'Good', 'Strong']

  if (!password) return null

  return (
    <div className="mt-2 space-y-2">
      <div className="flex gap-1">
        {[1, 2, 3, 4].map((level) => (
          <div
            key={level}
            className={`h-1 flex-1 rounded-full transition-colors ${
              level <= strengthLevel ? strengthColors[strengthLevel] : 'bg-secondary-200 dark:bg-secondary-700'
            }`}
          />
        ))}
      </div>
      {strengthLevel > 0 && (
        <p className="text-xs text-secondary-600 dark:text-secondary-400">
          Password strength: {strengthLabels[strengthLevel]}
        </p>
      )}
      <ul className="text-xs space-y-1">
        {requirements.map((req, index) => (
          <li
            key={index}
            className={`flex items-center gap-1.5 ${
              req.met ? 'text-success dark:text-success-400' : 'text-secondary-500 dark:text-secondary-400'
            }`}
          >
            {req.met ? (
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                  clipRule="evenodd"
                />
              </svg>
            ) : (
              <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                <circle cx="10" cy="10" r="3" />
              </svg>
            )}
            {req.label}
          </li>
        ))}
      </ul>
    </div>
  )
}

/**
 * Change password form component
 *
 * Features:
 * - Current password, new password, and confirm new password fields
 * - Zod validation matching backend requirements
 * - Password strength indicator
 * - Displays error messages from auth context
 * - Loading state during submission
 * - Redirect after successful password change
 */
export const ChangePasswordForm: React.FC = () => {
  const navigate = useNavigate()
  const { changePassword, error, isLoading, clearError, requiresPasswordChange } = useAuth()
  const [showCurrentPassword, setShowCurrentPassword] = useState(false)
  const [showNewPassword, setShowNewPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [success, setSuccess] = useState(false)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors },
  } = useForm<ChangePasswordFormData>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: {
      current_password: '',
      new_password: '',
      confirm_new_password: '',
    },
  })

  const newPasswordValue = watch('new_password')

  const onSubmit = async (data: ChangePasswordFormData) => {
    try {
      clearError()
      await changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      })
      setSuccess(true)
      // Redirect after a short delay to show success message
      setTimeout(() => {
        navigate('/', { replace: true })
      }, 2000)
    } catch {
      // Error is handled by auth context
    }
  }

  // Show success message
  if (success) {
    return (
      <div className="w-full max-w-md mx-auto">
        <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-lg p-8">
          <div className="text-center">
            <div className="mx-auto flex items-center justify-center h-16 w-16 rounded-full bg-success-100 dark:bg-success-900/30 mb-4">
              <svg
                className="h-8 w-8 text-success"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M5 13l4 4L19 7"
                />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-secondary-900 dark:text-white mb-2">
              Password changed!
            </h1>
            <p className="text-secondary-600 dark:text-secondary-400">
              Your password has been successfully updated. Redirecting...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white dark:bg-secondary-800 rounded-xl shadow-lg p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-secondary-900 dark:text-white mb-2">
            Change your password
          </h1>
          {requiresPasswordChange ? (
            <p className="text-secondary-600 dark:text-secondary-400">
              You need to change your password before continuing
            </p>
          ) : (
            <p className="text-secondary-600 dark:text-secondary-400">
              Enter your current password and choose a new one
            </p>
          )}
        </div>

        <form onSubmit={handleSubmit(onSubmit)} noValidate>
          {/* Global error message from auth context */}
          {error && (
            <div
              className="mb-6 p-4 bg-danger-50 dark:bg-danger-900/20 border border-danger-200 dark:border-danger-800 rounded-lg"
              role="alert"
            >
              <div className="flex items-start">
                <svg
                  className="w-5 h-5 text-danger mt-0.5 mr-3 flex-shrink-0"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 20 20"
                  fill="currentColor"
                  aria-hidden="true"
                >
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                <p className="text-sm text-danger font-medium">{error}</p>
              </div>
            </div>
          )}

          <div className="space-y-5">
            <div className="relative">
              <TextInput
                label="Current password"
                placeholder="Enter your current password"
                type={showCurrentPassword ? 'text' : 'password'}
                autoComplete="current-password"
                required
                error={errors.current_password?.message}
                {...register('current_password')}
              />
              <button
                type="button"
                onClick={() => setShowCurrentPassword(!showCurrentPassword)}
                className="absolute right-3 top-[38px] text-secondary-400 hover:text-secondary-600 dark:hover:text-secondary-300 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                aria-label={showCurrentPassword ? 'Hide password' : 'Show password'}
              >
                {showCurrentPassword ? (
                  <svg
                    className="w-5 h-5"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z"
                      clipRule="evenodd"
                    />
                    <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
                  </svg>
                ) : (
                  <svg
                    className="w-5 h-5"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path
                      fillRule="evenodd"
                      d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            </div>

            <div>
              <div className="relative">
                <TextInput
                  label="New password"
                  placeholder="Enter your new password"
                  type={showNewPassword ? 'text' : 'password'}
                  autoComplete="new-password"
                  required
                  error={errors.new_password?.message}
                  {...register('new_password')}
                />
                <button
                  type="button"
                  onClick={() => setShowNewPassword(!showNewPassword)}
                  className="absolute right-3 top-[38px] text-secondary-400 hover:text-secondary-600 dark:hover:text-secondary-300 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                  aria-label={showNewPassword ? 'Hide password' : 'Show password'}
                >
                  {showNewPassword ? (
                    <svg
                      className="w-5 h-5"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path
                        fillRule="evenodd"
                        d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z"
                        clipRule="evenodd"
                      />
                      <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
                    </svg>
                  ) : (
                    <svg
                      className="w-5 h-5"
                      xmlns="http://www.w3.org/2000/svg"
                      viewBox="0 0 20 20"
                      fill="currentColor"
                      aria-hidden="true"
                    >
                      <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                      <path
                        fillRule="evenodd"
                        d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                        clipRule="evenodd"
                      />
                    </svg>
                  )}
                </button>
              </div>
              <PasswordStrengthIndicator password={newPasswordValue} />
            </div>

            <div className="relative">
              <TextInput
                label="Confirm new password"
                placeholder="Confirm your new password"
                type={showConfirmPassword ? 'text' : 'password'}
                autoComplete="new-password"
                required
                error={errors.confirm_new_password?.message}
                {...register('confirm_new_password')}
              />
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="absolute right-3 top-[38px] text-secondary-400 hover:text-secondary-600 dark:hover:text-secondary-300 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded"
                aria-label={showConfirmPassword ? 'Hide password' : 'Show password'}
              >
                {showConfirmPassword ? (
                  <svg
                    className="w-5 h-5"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path
                      fillRule="evenodd"
                      d="M3.707 2.293a1 1 0 00-1.414 1.414l14 14a1 1 0 001.414-1.414l-1.473-1.473A10.014 10.014 0 0019.542 10C18.268 5.943 14.478 3 10 3a9.958 9.958 0 00-4.512 1.074l-1.78-1.781zm4.261 4.26l1.514 1.515a2.003 2.003 0 012.45 2.45l1.514 1.514a4 4 0 00-5.478-5.478z"
                      clipRule="evenodd"
                    />
                    <path d="M12.454 16.697L9.75 13.992a4 4 0 01-3.742-3.741L2.335 6.578A9.98 9.98 0 00.458 10c1.274 4.057 5.065 7 9.542 7 .847 0 1.669-.105 2.454-.303z" />
                  </svg>
                ) : (
                  <svg
                    className="w-5 h-5"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 20 20"
                    fill="currentColor"
                    aria-hidden="true"
                  >
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z" />
                    <path
                      fillRule="evenodd"
                      d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </button>
            </div>
          </div>

          <div className="mt-6">
            <Button
              type="submit"
              variant="primary"
              size="lg"
              fullWidth
              loading={isLoading}
              disabled={isLoading}
            >
              Change password
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default ChangePasswordForm
