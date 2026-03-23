import React from 'react'

export interface SelectOption {
  value: string
  label: string
  disabled?: boolean
}

export interface SelectProps {
  label?: string
  options: SelectOption[]
  value?: string
  onChange?: (value: string) => void
  placeholder?: string
  error?: string
  disabled?: boolean
  required?: boolean
  className?: string
}

export const Select: React.FC<SelectProps> = ({
  label,
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  error,
  disabled = false,
  required = false,
  className = '',
}) => {
  const selectId = `select-${crypto.randomUUID()}`

  return (
    <div className={`w-full ${className}`}>
      {label && (
        <label
          htmlFor={selectId}
          className="block text-sm font-medium text-dim mb-1.5"
        >
          {label}
          {required && <span className="text-danger ml-1">*</span>}
        </label>
      )}
      <div className="relative">
        <select
          id={selectId}
          value={value}
          onChange={(e) => onChange?.(e.target.value)}
          disabled={disabled}
          required={required}
          className={`
            block w-full rounded-lg border appearance-none
            pr-10 pl-4 py-2.5 text-sm
            cursor-pointer
            transition-colors duration-150
            ${
              error
                ? 'border-danger focus:ring-danger focus:border-danger'
                : 'border-edge focus:ring-primary-500 focus:border-primary-500'
            }
            bg-card
            text-body
            focus:outline-none focus:ring-2
            disabled:bg-subtle disabled:cursor-not-allowed
          `}
        >
          <option value="" disabled>
            {placeholder}
          </option>
          {options.map((option) => (
            <option
              key={option.value}
              value={option.value}
              disabled={option.disabled}
            >
              {option.label}
            </option>
          ))}
        </select>
        <div className="absolute inset-y-0 right-0 flex items-center pr-3 pointer-events-none">
          <svg
            className="w-5 h-5 text-hint"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 9l-7 7-7-7"
            />
          </svg>
        </div>
      </div>
      {error && <p className="mt-1.5 text-sm text-danger">{error}</p>}
    </div>
  )
}
