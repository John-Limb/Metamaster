import { Suspense, lazy, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LoadingSpinner } from './components/common'

// Lazy load route components for code splitting
const Dashboard = lazy(() => import('./components/dashboard/Dashboard').then(m => ({ default: m.Dashboard })))
const NotFound = lazy(() => import('./components/common/NotFound'))

// Feature modules (to be implemented)
const MoviesModule = lazy(() => import('./components/features/movies/MoviesModule'))
const TvShowsModule = lazy(() => import('./components/features/tvshows/TvShowsModule'))

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" />
  </div>
)

// Error boundary for lazy loaded routes
const RouteErrorBoundary = ({ children }: { children: React.ReactNode }) => {
  return (
    <Suspense fallback={<LoadingFallback />}>
      {children}
    </Suspense>
  )
}

function App() {
  // Add global click handler for debugging
  useEffect(() => {
    const handleGlobalClick = (e: MouseEvent) => {
      const target = e.target as HTMLElement
      if (target.tagName === 'BUTTON') {
        console.log('Global: Button clicked', {
          text: target.textContent,
          className: target.className,
          id: target.id,
        })
      }
    }
    document.addEventListener('click', handleGlobalClick, true)
    return () => document.removeEventListener('click', handleGlobalClick, true)
  }, [])

  return (
    <BrowserRouter>
      <Routes>
        {/* Main Layout Route */}
        <Route
          path="/"
          element={
            <RouteErrorBoundary>
              <Dashboard />
            </RouteErrorBoundary>
          }
        />

        {/* Feature Routes with Lazy Loading */}
        <Route
          path="/movies/*"
          element={
            <RouteErrorBoundary>
              <MoviesModule />
            </RouteErrorBoundary>
          }
        />

        <Route
          path="/tv-shows/*"
          element={
            <RouteErrorBoundary>
              <TvShowsModule />
            </RouteErrorBoundary>
          }
        />

        {/* 404 Not Found */}
        <Route
          path="*"
          element={
            <RouteErrorBoundary>
              <NotFound />
            </RouteErrorBoundary>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
