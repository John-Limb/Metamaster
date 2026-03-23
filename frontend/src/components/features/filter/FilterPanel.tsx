import React from 'react'
import { Button, Checkbox } from '../../common'
import './FilterPanel.css'

export interface FilterOption {
  value: string
  label: string
  count?: number
}

export interface FilterSection {
  id: string
  label: string
  options: FilterOption[]
  multiSelect?: boolean
}

export interface FilterPanelProps {
  sections: FilterSection[]
  selectedFilters: Record<string, string[]>
  onFilterChange: (sectionId: string, values: string[]) => void
  onClearAll: () => void
  isOpen: boolean
  onToggle: () => void
}

export const FilterPanel: React.FC<FilterPanelProps> = ({
  sections,
  selectedFilters,
  onFilterChange,
  onClearAll,
  isOpen,
  onToggle,
}: FilterPanelProps) => {
  const handleCheckboxChange = (sectionId: string, optionValue: string, checked: boolean) => {
    const currentValues = selectedFilters[sectionId] || []
    if (checked) {
      onFilterChange(sectionId, [...currentValues, optionValue])
    } else {
      onFilterChange(sectionId, currentValues.filter((v) => v !== optionValue))
    }
  }

  const hasActiveFilters = Object.values(selectedFilters).some((arr) => arr.length > 0)

  return (
    <div className="filter-panel">
      <div className="filter-panel__header">
        <Button variant="secondary" size="sm" onClick={onToggle} aria-expanded={isOpen}>
          <svg
            className="filter-panel__icon"
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
            <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3" />
          </svg>
          Filters
          {hasActiveFilters && (
            <span className="filter-panel__badge">
              {Object.values(selectedFilters).flat().length}
            </span>
          )}
        </Button>
        {hasActiveFilters && (
          <Button variant="ghost" size="sm" onClick={onClearAll}>
            Clear all
          </Button>
        )}
      </div>

      {isOpen && (
        <div className="filter-panel__content" role="region" aria-label="Filter options">
          {sections.map((section) => (
            <div key={section.id} className="filter-panel__section">
              <h4 className="filter-panel__section-title">{section.label}</h4>
              <div className="filter-panel__options">
                {section.options.map((option) => {
                  const isChecked = (selectedFilters[section.id] || []).includes(option.value)
                  return (
                    <label
                      key={option.value}
                      className="filter-panel__option"
                      htmlFor={`filter-${section.id}-${option.value}`}
                    >
                      <Checkbox
                        id={`filter-${section.id}-${option.value}`}
                        label={option.label}
                        checked={isChecked}
                        onChange={(checked) => handleCheckboxChange(section.id, option.value, checked)}
                      />
                      <span className="filter-panel__option-label">{option.label}</span>
                      {option.count !== undefined && (
                        <span className="filter-panel__option-count">{option.count}</span>
                      )}
                    </label>
                  )
                })}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
