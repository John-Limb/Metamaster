/**
 * Movies Module - Routes for movies feature
 */

import { Routes, Route } from 'react-router-dom'
import MoviesPage from './MoviesPage/MoviesPage'
import MovieDetailPage from './MovieDetailPage/MovieDetailPage'

export default function MoviesModule() {
  return (
    <Routes>
      <Route path="/" element={<MoviesPage />} />
      <Route path="/:id" element={<MovieDetailPage />} />
    </Routes>
  )
}
