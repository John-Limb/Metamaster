import React from 'react'

export interface ToggleProps {
  label: string
  checked?: boolean
  onChange?: (checked: boolean) => void
  disabled?: boolean
  size?: 'sm' | 'md'
  className?: string
}

const sizeConfig = {
  sm: {
    track: 'w-8 h-4',
    thumb: 'w-3 h-3',
    translate: 'translate-x-4',
  },
  md: {
    track: 'w-11 h-6',
    thumb: 'w-5 h-5',
    translate: 'translate-x-5',
  },
}

export const Toggle: React.FC<ToggleProps> = ({
  label,
  checked = false,
  onChange,
  disabled = false,
  size = 'md',
  className = '',
}) => {
  const toggleId = `toggle-${crypto.randomUUID()}`
  const config = sizeConfig[size]

  return (
    <div className={`flex items-center ${className}`}>
      <button
        id={toggleId}
        type="button"
        role="switch"
        aria-checked={checked}
        onClick={() => onChange?.(!checked)}
        disabled={disabled}
        className={`
          relative inline-flex shrink-0 cursor-pointer
          rounded-full border-2 border-transparent
          transition-colors duration-200 ease-in-out
          focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 dark:focus:ring-offset-secondary-900
          ${disabled ? 'opacity-50 cursor-not-allowed' : ''}
          ${config.track}
          ${checked ? 'bg-primary-600' : 'bg-subtle'}
        `}
      >
        <span className="sr-only">{label}</span>
        <span
          aria-hidden="true"
          className={`
            pointer-events-none inline-block rounded-full
            bg-card shadow transform transition-transform duration-200 ease-in-out
            ${config.thumb}
            ${checked ? config.translate : 'translate-x-0'}
          `}
        />
      </button>
      <label
        htmlFor={toggleId}
        className={`ml-3 text-sm font-medium cursor-pointer ${
          disabled
            ? 'text-hint'
            : 'text-dim'
        }`}
      >
        {label}
      </label>
    </div>
  )
}
