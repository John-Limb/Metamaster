import React, { useState } from 'react'
import { FaUser, FaKey } from 'react-icons/fa'
import { useAuth } from '@/context/AuthContext'
import { authService, AuthApiError } from '@/services/authService'

interface ProfileSectionProps {
  icon: React.ReactNode
  title: string
  description: string
  children: React.ReactNode
}

const ProfileSection: React.FC<ProfileSectionProps> = ({ icon, title, description, children }) => (
  <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border-l-4 border-primary-600">
    <div className="flex items-start gap-4 mb-4">
      <div className="text-primary-600 text-2xl mt-1">{icon}</div>
      <div>
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">{title}</h3>
        <p className="text-gray-600 dark:text-gray-400 text-sm">{description}</p>
      </div>
    </div>
    <div className="mt-4">{children}</div>
  </div>
)

export const ProfilePage: React.FC = () => {
  const { user } = useAuth()

  // Email state
  const [email, setEmail] = useState(user?.email ?? '')
  const [emailSaved, setEmailSaved] = useState(false)
  const [emailError, setEmailError] = useState('')

  // Password state
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [passwordSaved, setPasswordSaved] = useState(false)
  const [passwordError, setPasswordError] = useState('')

  const handleSaveEmail = async () => {
    setEmailError('')
    setEmailSaved(false)
    try {
      await authService.updateProfile({ email })
      setEmailSaved(true)
      setTimeout(() => setEmailSaved(false), 3000)
    } catch (err) {
      if (err instanceof AuthApiError) {
        setEmailError(err.message)
      } else {
        setEmailError('Failed to update email.')
      }
    }
  }

  const handleChangePassword = async () => {
    setPasswordError('')
    setPasswordSaved(false)

    if (newPassword !== confirmPassword) {
      setPasswordError('New passwords do not match.')
      return
    }

    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters.')
      return
    }

    try {
      await authService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      })
      setPasswordSaved(true)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')
      setTimeout(() => setPasswordSaved(false), 3000)
    } catch (err) {
      if (err instanceof AuthApiError) {
        setPasswordError(err.message)
      } else {
        setPasswordError('Failed to change password.')
      }
    }
  }

  const inputClass =
    'w-full px-3 py-2 border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-700 text-gray-900 dark:text-white rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500'

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Profile</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Manage your account details
          {user && (
            <span className="ml-1">
              &mdash; signed in as <strong>{user.username}</strong>
            </span>
          )}
        </p>
      </div>

      {/* Email */}
      <ProfileSection
        icon={<FaUser />}
        title="Email Address"
        description="Update the email address associated with your account"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputClass}
              placeholder="you@example.com"
            />
            {emailError && (
              <p className="mt-1 text-xs text-red-600 dark:text-red-400">{emailError}</p>
            )}
            {emailSaved && (
              <p className="mt-1 text-xs text-green-600 dark:text-green-400">Email updated.</p>
            )}
          </div>
          <button
            onClick={handleSaveEmail}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium"
          >
            Save Email
          </button>
        </div>
      </ProfileSection>

      {/* Password */}
      <ProfileSection
        icon={<FaKey />}
        title="Change Password"
        description="Update your password to keep your account secure"
      >
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Current Password
            </label>
            <input
              type="password"
              value={currentPassword}
              onChange={(e) => setCurrentPassword(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              New Password
            </label>
            <input
              type="password"
              value={newPassword}
              onChange={(e) => setNewPassword(e.target.value)}
              className={inputClass}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              Confirm New Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              className={inputClass}
            />
          </div>
          {passwordError && (
            <p className="text-xs text-red-600 dark:text-red-400">{passwordError}</p>
          )}
          {passwordSaved && (
            <p className="text-xs text-green-600 dark:text-green-400">Password changed.</p>
          )}
          <button
            onClick={handleChangePassword}
            className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition text-sm font-medium"
          >
            Change Password
          </button>
        </div>
      </ProfileSection>
    </div>
  )
}
