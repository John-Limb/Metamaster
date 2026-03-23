import React from 'react'
import { CheckboxInput } from '@/components/common'

interface IndeterminateCheckboxProps {
  keys: string[]
  selected: Set<string>
  onChange: () => void
  onClick?: (e: React.MouseEvent<HTMLInputElement>) => void
}

export function IndeterminateCheckbox({ keys, selected, onChange, onClick }: IndeterminateCheckboxProps) {
  const count = keys.filter((k) => selected.has(k)).length
  const checked = keys.length > 0 && count === keys.length
  const indeterminate = count > 0 && count < keys.length

  return (
    <CheckboxInput
      checked={checked}
      indeterminate={indeterminate}
      onChange={onChange}
      onClick={onClick}
    />
  )
}
