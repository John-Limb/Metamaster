import React, { useId } from 'react'

export interface TextInputProps {
  label?: string
  placeholder?: string
  error?: string
  errorId?: string
  helperText?: string
  helperTextId?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  disabled?: boolean
  required?: boolean
  value?: string
  onChange?: (e: React.ChangeEvent<HTMLInputElement>) => void
  onBlur?: (e: React.FocusEvent<HTMLInputElement>) => void
  className?: string
  type?: 'text' | 'email' | 'password' | 'number' | 'search' | 'tel' | 'url'
  name?: string
  autoComplete?: string
  id?: string
  ariaDescribedBy?: string
  inputMode?: 'none' | 'text' | 'decimal' | 'numeric' | 'tel' | 'search' | 'email' | 'url'
  pattern?: string
}

export const TextInput = React.forwardRef<HTMLInputElement, TextInputProps>(
  (
    {
      label,
      placeholder,
      error,
      errorId,
      helperText,
      helperTextId,
      leftIcon,
      rightIcon,
      disabled = false,
      required = false,
      value,
      onChange,
      onBlur,
      className = '',
      type = 'text',
      name,
      autoComplete,
      id,
      ariaDescribedBy,
      inputMode,
      pattern,
    },
    ref
  ) => {
    const generatedId = useId()
    const inputId = id || generatedId
    const errorMessageId = errorId || `error-${inputId}`
    const helperTextIdVal = helperTextId || `helper-${inputId}`

    const describedByIds = [
      ariaDescribedBy,
      error ? errorMessageId : null,
      helperText ? helperTextIdVal : null,
    ]
      .filter(Boolean)
      .join(' ') || undefined

    return (
      <div className={`w-full ${className}`}>
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-secondary-700 dark:text-secondary-300 mb-1.5"
          >
            {label}
            {required && (
              <span className="text-danger ml-1" aria-hidden="true">
                *
              </span>
            )}
            {required && (
              <span className="sr-only">(required)</span>
            )}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div
              className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-secondary-400"
              aria-hidden="true"
            >
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            type={type}
            placeholder={placeholder}
            value={value}
            onChange={onChange}
            onBlur={onBlur}
            disabled={disabled}
            required={required}
            name={name}
            autoComplete={autoComplete}
            inputMode={inputMode}
            pattern={pattern}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={describedByIds}
            aria-required={required}
            className={`
              block w-full rounded-lg border transition-all duration-150
              ${leftIcon ? 'pl-10' : 'pl-4'}
              ${rightIcon ? 'pr-10' : 'pr-4'}
              py-2.5 text-sm min-h-[44px]
              ${
                error
                  ? 'border-danger focus:ring-danger focus:border-danger bg-danger-50 dark:bg-danger-900/10'
                  : 'border-secondary-300 dark:border-secondary-600 focus:ring-primary-500 focus:border-primary-500'
              }
              bg-white dark:bg-secondary-800
              text-secondary-900 dark:text-white
              placeholder-secondary-400 dark:placeholder-secondary-500
              focus:outline-none focus:ring-2
              disabled:bg-secondary-50 dark:disabled:bg-secondary-900 disabled:cursor-not-allowed
              disabled:opacity-60
            `}
          />
          {rightIcon && (
            <div
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-secondary-400"
              aria-hidden="true"
            >
              {rightIcon}
            </div>
          )}
          {error && (
            <div className="absolute inset-y-0 right-0 pr-10 flex items-center pointer-events-none">
              <svg
                className="h-5 w-5 text-danger"
                xmlns="http://www.w3.org/2000/svg"
                viewBox="0 0 20 20"
                fill="currentColor"
                aria-hidden="true"
              >
                <path
                  fillRule="evenodd"
                  d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
          )}
        </div>
        {(error || helperText) && (
          <p
            id={error ? errorMessageId : helperTextIdVal}
            className={`mt-1.5 text-sm ${
              error ? 'text-danger' : 'text-secondary-500 dark:text-secondary-400'
            }`}
            role={error ? 'alert' : undefined}
          >
            {error || helperText}
          </p>
        )}
      </div>
    )
  }
)

TextInput.displayName = 'TextInput'

export default TextInput
