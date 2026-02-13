import { Suspense, lazy, useEffect } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { LoadingSpinner } from './components/common'
import { ProtectedRoute } from './components/auth/ProtectedRoute'

// Lazy load route components for code splitting
const Dashboard = lazy(() => import('./components/dashboard/Dashboard').then(m => ({ default: m.Dashboard })))
const NotFound = lazy(() => import('./components/common/NotFound'))

// Auth pages
const LoginPage = lazy(() => import('./pages/LoginPage'))
const RegisterPage = lazy(() => import('./pages/RegisterPage'))
const ChangePasswordPage = lazy(() => import('./pages/ChangePasswordPage'))

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
        {/* Public Auth Routes */}
        <Route
          path="/login"
          element={
            <RouteErrorBoundary>
              <LoginPage />
            </RouteErrorBoundary>
          }
        />
        <Route
          path="/register"
          element={
            <RouteErrorBoundary>
              <RegisterPage />
            </RouteErrorBoundary>
          }
        />

        {/* Protected Route for Password Change */}
        <Route
          path="/change-password"
          element={
            <ProtectedRoute requirePasswordChange>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />

        {/* Protected Main Layout Route */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <RouteErrorBoundary>
                <Dashboard />
              </RouteErrorBoundary>
            </ProtectedRoute>
          }
        />

        {/* Protected Feature Routes with Lazy Loading */}
        <Route
          path="/movies/*"
          element={
            <ProtectedRoute>
              <RouteErrorBoundary>
                <MoviesModule />
              </RouteErrorBoundary>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tv-shows/*"
          element={
            <ProtectedRoute>
              <RouteErrorBoundary>
                <TvShowsModule />
              </RouteErrorBoundary>
            </ProtectedRoute>
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
