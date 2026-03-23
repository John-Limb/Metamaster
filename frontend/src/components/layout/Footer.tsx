import React from 'react'

interface FooterProps {
  className?: string
}

export const Footer: React.FC<FooterProps> = ({ className = '' }: FooterProps) => {
  const currentYear = new Date().getFullYear()

  return (
    <footer className={`border-t border-edge py-6 ${className}`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-hint">
          &copy; {currentYear} Metamaster. All rights reserved.
        </p>
      </div>
    </footer>
  )
}
