/**
 * TV Shows Module - Routes for TV shows feature
 */

import { Routes, Route } from 'react-router-dom'
import TVShowsPage from './TVShowsPage/TVShowsPage'
import TVShowDetailPage from './TVShowDetailPage/TVShowDetailPage'

export default function TvShowsModule() {
  return (
    <Routes>
      <Route path="/" element={<TVShowsPage />} />
      <Route path="/:id" element={<TVShowDetailPage />} />
    </Routes>
  )
}
