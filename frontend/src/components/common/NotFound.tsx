import React from 'react'
import { useNavigate } from 'react-router-dom'

interface NotFoundProps {
  title?: string
  message?: string
  showBackButton?: boolean
}

export const NotFound: React.FC<NotFoundProps> = ({
  title = 'Page Not Found',
  message = 'The page you are looking for does not exist.',
  showBackButton = true,
}) => {
  const navigate = useNavigate()

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="text-center px-4">
        <div className="mb-8">
          <svg className="mx-auto h-24 w-24 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <h1 className="text-6xl font-bold text-gray-900 mb-4">404</h1>
        <p className="text-2xl font-semibold text-gray-700 mb-4">{title}</p>
        <p className="text-gray-600 mb-8 max-w-md">{message}</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <button
            onClick={() => navigate('/')}
            className="bg-primary-600 text-white px-6 py-3 rounded-lg hover:bg-primary-700 transition font-medium"
          >
            Go Home
          </button>
          {showBackButton && (
            <button
              onClick={() => navigate(-1)}
              className="bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition font-medium"
            >
              Go Back
            </button>
          )}
        </div>
      </div>
    </div>
  )
}

// Default export for lazy loading
export default NotFound
