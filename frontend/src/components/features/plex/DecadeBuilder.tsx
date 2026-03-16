import React from 'react'

const DECADES = [1960, 1970, 1980, 1990, 2000, 2010, 2020]

interface DecadeBuilderProps {
  selected: number | null
  onSelect: (decade: number) => void
}

export function DecadeBuilder({ selected, onSelect }: DecadeBuilderProps) {
  return (
    <div className="rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-900 p-4">
      <p className="text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wide mb-3">
        Choose one decade
      </p>
      <div className="grid grid-cols-4 gap-2">
        {DECADES.map((decade) => (
          <button
            key={decade}
            type="button"
            onClick={() => onSelect(decade)}
            className={`rounded-lg py-2.5 text-sm font-medium text-center transition-colors ${
              selected === decade
                ? 'bg-indigo-600 text-white border-2 border-indigo-600'
                : 'bg-white dark:bg-slate-800 text-slate-600 dark:text-slate-300 border border-slate-200 dark:border-slate-700 hover:border-indigo-400 dark:hover:border-indigo-500'
            }`}
          >
            {decade}s
          </button>
        ))}
        <button
          type="button"
          disabled
          className="rounded-lg py-2.5 text-sm text-center text-slate-300 dark:text-slate-600 border border-dashed border-slate-200 dark:border-slate-700 cursor-not-allowed"
        >
          2030s
        </button>
      </div>
      <p className="text-xs text-slate-400 dark:text-slate-500 mt-3">
        One decade per collection · Movies only
      </p>
    </div>
  )
}

export default DecadeBuilder
