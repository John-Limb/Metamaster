import React from 'react'

// ---------------------------------------------------------------------------
// RadioInput — standalone styled radio button primitive (no label)
// ---------------------------------------------------------------------------

export interface RadioInputProps {
  checked: boolean
  onChange: (value: string, e: React.ChangeEvent<HTMLInputElement>) => void
  value: string
  name?: string
  disabled?: boolean
  'aria-label'?: string
}

export const RadioInput: React.FC<RadioInputProps> = ({
  checked,
  onChange,
  value,
  name,
  disabled = false,
  'aria-label': ariaLabel,
}) => {
  return (
    <div className={`relative w-3.5 h-3.5 flex-shrink-0 group/rb ${disabled ? 'opacity-50' : ''}`}>
      <input
        type="radio"
        value={value}
        name={name}
        checked={checked}
        onChange={(e) => onChange(e.target.value, e)}
        disabled={disabled}
        aria-label={ariaLabel}
        className="absolute inset-0 opacity-0 w-full h-full m-0 cursor-pointer disabled:cursor-not-allowed"
      />
      <div
        className={`pointer-events-none w-full h-full rounded-full border transition-colors flex items-center justify-center ${
          checked
            ? 'bg-primary-500 border-primary-500 dark:bg-primary-400 dark:border-primary-400'
            : 'bg-card border-slate-300 dark:border-slate-600 group-hover/rb:border-primary-400 dark:group-hover/rb:border-primary-500'
        }`}
      >
        {checked && (
          <div className="w-1.5 h-1.5 rounded-full bg-white" />
        )}
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Radio — labelled radio button (for use in radio groups)
// ---------------------------------------------------------------------------

export interface RadioProps {
  id?: string
  label: string
  value: string
  name?: string
  checked?: boolean
  onChange?: (value: string, e?: React.ChangeEvent<HTMLInputElement>) => void
  disabled?: boolean
  className?: string
}

export const Radio: React.FC<RadioProps> = ({
  id,
  label,
  value,
  name,
  checked = false,
  onChange,
  disabled = false,
  className = '',
}) => {
  const radioId = id || `radio-${name ?? ''}-${value}`

  return (
    <div className={`flex items-center gap-3 ${className}`}>
      <RadioInput
        value={value}
        name={name}
        checked={checked}
        onChange={(val, e) => onChange?.(val, e)}
        disabled={disabled}
        aria-label={label}
      />
      <label
        htmlFor={radioId}
        className={`text-sm font-medium cursor-pointer select-none ${
          disabled
            ? 'text-slate-400 dark:text-slate-600'
            : 'text-slate-700 dark:text-slate-300'
        }`}
      >
        {label}
      </label>
    </div>
  )
}
