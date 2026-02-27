import React, { useEffect, useRef } from 'react'

// ---------------------------------------------------------------------------
// CheckboxInput — standalone styled checkbox primitive (no label)
// ---------------------------------------------------------------------------

export interface CheckboxInputProps {
  checked: boolean
  indeterminate?: boolean
  onChange: (checked: boolean, e: React.ChangeEvent<HTMLInputElement>) => void
  onClick?: (e: React.MouseEvent<HTMLInputElement>) => void
  disabled?: boolean
  'aria-label'?: string
}

export const CheckboxInput: React.FC<CheckboxInputProps> = ({
  checked,
  indeterminate = false,
  onChange,
  onClick,
  disabled = false,
  'aria-label': ariaLabel,
}) => {
  const ref = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (ref.current) ref.current.indeterminate = indeterminate
  }, [indeterminate])

  const active = checked || indeterminate

  return (
    <div className={`relative w-3.5 h-3.5 flex-shrink-0 group/cb ${disabled ? 'opacity-50' : ''}`}>
      <input
        ref={ref}
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange(e.target.checked, e)}
        onClick={onClick}
        disabled={disabled}
        aria-label={ariaLabel}
        className="absolute inset-0 opacity-0 w-full h-full m-0 cursor-pointer disabled:cursor-not-allowed"
      />
      <div
        className={`pointer-events-none w-full h-full rounded-sm border transition-colors flex items-center justify-center ${
          active
            ? 'bg-indigo-500 border-indigo-500 dark:bg-indigo-400 dark:border-indigo-400'
            : 'bg-white dark:bg-slate-800 border-slate-300 dark:border-slate-600 group-hover/cb:border-indigo-400 dark:group-hover/cb:border-indigo-500'
        }`}
      >
        {checked && !indeterminate && (
          <svg className="w-2 h-2 text-white" fill="none" stroke="currentColor" strokeWidth={3} viewBox="0 0 8 8">
            <polyline points="1,4 3.5,6.5 7,1.5" />
          </svg>
        )}
        {indeterminate && (
          <div className="w-2 h-px bg-white rounded-full" />
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Checkbox — labelled form checkbox
// ---------------------------------------------------------------------------

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
  const checkboxId = id || `checkbox-${crypto.randomUUID()}`

  return (
    <div className={`flex items-start gap-3 ${className}`}>
      <div className="flex items-center h-5 mt-0.5">
        <CheckboxInput
          checked={checked}
          onChange={(val, e) => onChange?.(val, e)}
          disabled={disabled}
          aria-label={label}
        />
      </div>
      <div className="text-sm">
        <label
          htmlFor={checkboxId}
          className={`font-medium cursor-pointer ${
            disabled
              ? 'text-slate-400 dark:text-slate-600'
              : 'text-slate-700 dark:text-slate-300'
          }`}
        >
          {label}
        </label>
        {error && <p className="mt-1 text-sm text-red-500 dark:text-red-400">{error}</p>}
      </div>
    </div>
  )
}
