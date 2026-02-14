import React from 'react'

interface FooterProps {
  className?: string
}

export const Footer: React.FC<FooterProps> = ({ className = '' }) => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className={`border-t border-gray-200 dark:border-gray-800 py-6 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-gray-500 dark:text-gray-400">
          &copy; {currentYear} Metamaster. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
