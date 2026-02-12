import React, { useState, useRef, useEffect } from 'react'
import './SortDropdown.css'

export interface SortOption {
  value: string
  label: string
  direction?: string
}

export interface SortDropdownProps {
  options: SortOption[]
  value: string
  onChange: (value: string) => void
}

export const SortDropdown: React.FC<SortDropdownProps> = ({ options, value, onChange }) => {
  const [isOpen, setIsOpen] = useState(false)
  const dropdownRef = useRef<HTMLDivElement>(null)

  const selectedOption = options.find((opt) => opt.value === value)

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleSelect = (optionValue: string) => {
    onChange(optionValue)
    setIsOpen(false)
  }

  const getDirectionIcon = (option: SortOption) => {
    if (option.value === value && option.direction) {
      return (
        <svg
          className="sort-dropdown__direction-icon"
          xmlns="http://www.w3.org/2000/svg"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          {option.direction === 'asc' ? (
            <path d="M12 5v14M5 12l7 7 7-7" />
          ) : (
            <path d="M12 19V5M5 12l7-7 7 7" />
          )}
        </svg>
      )
    }
    return null
  }

  return (
    <div className="sort-dropdown" ref={dropdownRef}>
      <button
        className="sort-dropdown__trigger"
        onClick={() => setIsOpen(!isOpen)}
        aria-expanded={isOpen}
        aria-haspopup="listbox"
      >
        <svg
          className="sort-dropdown__icon"
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M3 6h18M3 12h18M3 18h18" />
        </svg>
        <span className="sort-dropdown__label">Sort by:</span>
        <span className="sort-dropdown__value">{selectedOption?.label || 'Select'}</span>
        <svg
          className={`sort-dropdown__arrow ${isOpen ? 'sort-dropdown__arrow--open' : ''}`}
          xmlns="http://www.w3.org/2000/svg"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M6 9l6 6 6-6" />
        </svg>
      </button>

      {isOpen && (
        <ul className="sort-dropdown__menu" role="listbox">
          {options.map((option) => (
            <li
              key={option.value}
              className={`sort-dropdown__option ${option.value === value ? 'sort-dropdown__option--selected' : ''}`}
              onClick={() => handleSelect(option.value)}
              role="option"
              aria-selected={option.value === value}
            >
              <span className="sort-dropdown__option-label">{option.label}</span>
              {getDirectionIcon(option)}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
