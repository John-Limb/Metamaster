import React, { useState } from 'react'
import { FaSearch } from 'react-icons/fa'

export const SearchPage: React.FC = () => {
  const [query, setQuery] = useState('')
  const [results] = useState([])

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    // Search logic will be implemented in Phase 4
  }

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Search</h1>
        <p className="text-gray-600">Find files, movies, and TV shows</p>
      </div>

      {/* Search Form */}
      <form onSubmit={handleSearch} className="bg-white rounded-lg shadow-md p-6">
        <div className="flex gap-2">
          <div className="flex-1 relative">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search files, movies, shows..."
              className="w-full px-4 py-3 pl-10 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <FaSearch className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition font-medium"
          >
            Search
          </button>
        </div>
      </form>

      {/* Advanced Filters */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Filters</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Type</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>All</option>
              <option>Files</option>
              <option>Movies</option>
              <option>TV Shows</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Date Range</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Any time</option>
              <option>Last 7 days</option>
              <option>Last 30 days</option>
              <option>Last year</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
            <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500">
              <option>Relevance</option>
              <option>Name</option>
              <option>Date Modified</option>
              <option>Size</option>
            </select>
          </div>
        </div>
      </div>

      {/* Search Results */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Results</h2>
        {results.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-gray-500 text-lg">
              {query ? 'No results found' : 'Enter a search query to get started'}
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {/* Results will be displayed here */}
          </div>
        )}
      </div>
    </div>
  )
}
