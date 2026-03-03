import React, { useState, useCallback, useRef, useEffect } from 'react'
import { useSearchStore } from '@/stores/searchStore'
import { LoadingSpinner } from '@/components/common'
import { debounce } from '@/utils/helpers'

interface SearchBarProps {
  placeholder?: string
  onSearch?: (query: string) => void
  showSuggestions?: boolean
  className?: string
  ariaLabel?: string
}

export function SearchBar({
  placeholder = 'Search files, movies, TV shows...',
  onSearch,
  showSuggestions = true,
  className = '',
  ariaLabel = 'Search',
}: SearchBarProps) {
  const [isFocused, setIsFocused] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  
  const {
    query,
    suggestions,
    isLoadingSuggestions,
    recentSearches,
    setQuery,
    fetchSuggestions,
    clearSuggestions,
    search,
    addRecentSearch,
  } = useSearchStore()

  const debouncedFetchSuggestionsRef = useRef(
    debounce((q: string) => {
      if (q.length >= 2) {
        fetchSuggestions(q)
      } else {
        clearSuggestions()
      }
    }, 300)
  )

  const handleInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const value = e.target.value
      setQuery(value)
      if (showSuggestions) {
        debouncedFetchSuggestionsRef.current(value)
      }
    },
    [setQuery, showSuggestions]
  )

  const handleSubmit = useCallback(
    (e: React.FormEvent) => {
      e.preventDefault()
      if (query.trim()) {
        addRecentSearch(query)
        search()
        onSearch?.(query)
        clearSuggestions()
        setIsFocused(false)
      }
    },
    [query, search, onSearch, addRecentSearch, clearSuggestions]
  )

  const handleFocus = useCallback(() => {
    setIsFocused(true)
    if (query.length >= 2 && showSuggestions) {
      fetchSuggestions(query)
    }
  }, [query, showSuggestions, fetchSuggestions])

  const handleBlur = useCallback(() => {
    // Delay to allow click on suggestions
    setTimeout(() => {
      setIsFocused(false)
      clearSuggestions()
    }, 200)
  }, [clearSuggestions])

  const handleSuggestionClick = useCallback(
    (suggestion: string) => {
      setQuery(suggestion)
      addRecentSearch(suggestion)
      search()
      onSearch?.(suggestion)
      clearSuggestions()
      setIsFocused(false)
    },
    [setQuery, addRecentSearch, search, onSearch, clearSuggestions]
  )

  const handleRecentSearchClick = useCallback(
    (recentQuery: string) => {
      setQuery(recentQuery)
      search()
      onSearch?.(recentQuery)
      setIsFocused(false)
    },
    [setQuery, search, onSearch]
  )

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearSuggestions()
        setIsFocused(false)
        inputRef.current?.blur()
      }
    },
    [clearSuggestions]
  )

  // Cleanup debounced function
  useEffect(() => {
    const fn = debouncedFetchSuggestionsRef.current
    return () => {
      fn.cancel()
    }
  }, [])

  return (
    <div className={`relative ${className}`}>
      <form onSubmit={handleSubmit} role="search" aria-label={ariaLabel}>
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <svg
              className="h-5 w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
          <input
            ref={inputRef}
            type="search"
            value={query}
            onChange={handleInputChange}
            onFocus={handleFocus}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            className="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 sm:text-sm transition-all duration-200"
            aria-autocomplete="list"
            aria-controls="search-results"
            aria-expanded={isFocused && suggestions.length > 0}
          />
          {isLoadingSuggestions && (
            <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
              <LoadingSpinner size="sm" />
            </div>
          )}
        </div>
      </form>

      {/* Suggestions Dropdown */}
      {isFocused && showSuggestions && (suggestions.length > 0 || recentSearches.length > 0) && (
        <div
          className="absolute z-10 mt-1 w-full bg-white shadow-lg rounded-md py-1 text-base ring-1 ring-black ring-opacity-5 overflow-auto max-h-60 focus:outline-none sm:text-sm"
          role="listbox"
          id="search-results"
        >
          {/* Suggestions */}
          {suggestions.length > 0 && (
            <div role="group" aria-label="Search suggestions">
              {suggestions.map((suggestion, index) => (
                <button
                  key={`${suggestion}-${index}`}
                  role="option"
                  onClick={() => handleSuggestionClick(suggestion)}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                >
                  <span className="flex items-center">
                    <svg
                      className="h-4 w-4 mr-2 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                      />
                    </svg>
                    {suggestion}
                  </span>
                </button>
              ))}
            </div>
          )}

          {/* Recent Searches */}
          {recentSearches.length > 0 && suggestions.length === 0 && (
            <div role="group" aria-label="Recent searches">
              <div className="px-4 py-2 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                Recent Searches
              </div>
              {recentSearches.slice(0, 5).map((recentQuery, index) => (
                <button
                  key={`recent-${index}`}
                  role="option"
                  onClick={() => handleRecentSearchClick(recentQuery)}
                  className="w-full text-left px-4 py-2 hover:bg-gray-100 focus:bg-gray-100 focus:outline-none"
                >
                  <span className="flex items-center">
                    <svg
                      className="h-4 w-4 mr-2 text-gray-400"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                      aria-hidden="true"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    {recentQuery}
                  </span>
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default SearchBar
