import React from 'react'

export interface CheckboxProps {
  id?: string
  label: string
  checked?: boolean
  onChange?: (checked: boolean, e?: React.ChangeEvent<HTMLInputElement>) => void
  disabled?: boolean
  error?: string
  className?: string
}

export const Checkbox: React.FC<CheckboxProps> = ({
  id,
  label,
  checked = false,
  onChange,
  disabled = false,
  error,
  className = '',
}) => {
  const checkboxId = id || `checkbox-${Math.random().toString(36).substring(2, 9)}`

  return (
    <div className={`flex items-start ${className}`}>
      <div className="flex items-center h-5">
        <input
          id={checkboxId}
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange?.(e.target.checked, e)}
          disabled={disabled}
          className={`
            w-4 h-4 rounded border-secondary-300
            text-primary-600 focus:ring-primary-500
            cursor-pointer
            transition-colors duration-150
            ${
              error
                ? 'border-danger focus:ring-danger'
                : 'dark:border-secondary-600'
            }
            disabled:opacity-50 disabled:cursor-not-allowed
          `}
        />
      </div>
      <div className="ml-3 text-sm">
        <label
          htmlFor={checkboxId}
          className={`font-medium cursor-pointer ${
            disabled
              ? 'text-secondary-400 dark:text-secondary-600'
              : 'text-secondary-700 dark:text-secondary-300'
          }`}
        >
          {label}
        </label>
        {error && <p className="mt-1 text-sm text-danger">{error}</p>}
      </div>
    </div>
  )
}
