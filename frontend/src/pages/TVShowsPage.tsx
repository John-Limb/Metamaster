import React, { useState } from 'react'
import { FaFilter, FaSort } from 'react-icons/fa'

export const TVShowsPage: React.FC = () => {
  const [shows] = useState([])
  const [sortBy, setSortBy] = useState('title')

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900 mb-2">TV Shows</h1>
        <p className="text-gray-600">Browse and manage your TV show collection</p>
      </div>

      {/* Filters and Sort */}
      <div className="bg-white rounded-lg shadow-md p-4 flex flex-col sm:flex-row gap-4">
        <div className="flex-1 flex gap-2">
          <button className="flex items-center gap-2 px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition">
            <FaFilter className="w-4 h-4" />
            Filters
          </button>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            <option value="title">Sort by Title</option>
            <option value="year">Sort by Year</option>
            <option value="rating">Sort by Rating</option>
            <option value="added">Sort by Added Date</option>
          </select>
        </div>
        <button className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition">
          <FaSort className="w-4 h-4" />
          View Options
        </button>
      </div>

      {/* TV Shows Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        {shows.length === 0 ? (
          <div className="col-span-full text-center py-12">
            <p className="text-gray-500 text-lg">No TV shows found</p>
            <p className="text-gray-400 text-sm mt-2">Start by uploading or scanning files</p>
          </div>
        ) : (
          shows.map((show: any) => (
            <div key={show.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition">
              <div className="aspect-video bg-gray-200" />
              <div className="p-4">
                <h3 className="font-semibold text-gray-900 truncate">{show.title}</h3>
                <p className="text-sm text-gray-600">
                  {show.seasons} seasons • {show.episodes} episodes
                </p>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  )
}
