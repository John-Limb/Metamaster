import { Suspense, lazy } from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { LoadingSpinner } from './components/common'
import { ProtectedRoute } from './components/auth/ProtectedRoute'
import { MainLayout } from './components/layout'

// Lazy load pages
const Dashboard = lazy(() => import('./components/dashboard/Dashboard').then(m => ({ default: m.Dashboard })))
const NotFound = lazy(() => import('./components/common/NotFound'))

// Auth pages
const LoginPage = lazy(() => import('./pages/LoginPage'))
const ChangePasswordPage = lazy(() => import('./pages/ChangePasswordPage'))

// Feature modules
const MoviesModule = lazy(() => import('./components/features/movies/MoviesModule'))
const TvShowsModule = lazy(() => import('./components/features/tvshows/TvShowsModule'))
const FilesPage = lazy(() => import('./pages/FilesPage').then(m => ({ default: m.FilesPage })))
const SettingsPage = lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const ProfilePage = lazy(() => import('./pages/ProfilePage').then(m => ({ default: m.ProfilePage })))
const EnrichmentPage = lazy(() => import('./pages/EnrichmentPage').then(m => ({ default: m.EnrichmentPage })))
const StoragePage = lazy(() => import('./pages/StoragePage').then(m => ({ default: m.StoragePage })))
const OrganisationPage = lazy(() => import('./pages/OrganisationPage').then(m => ({ default: m.OrganisationPage })))
const QueuePage = lazy(() => import('./pages/QueuePage').then(m => ({ default: m.QueuePage })))
const SystemHealthPage = lazy(() => import('./pages/SystemHealthPage').then(m => ({ default: m.SystemHealthPage })))
const PlexCollectionsPage = lazy(() => import('./pages/PlexCollectionsPage').then(m => ({ default: m.PlexCollectionsPage })))

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" />
  </div>
)

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Auth Routes (no layout) */}
        <Route
          path="/login"
          element={
            <Suspense fallback={<LoadingFallback />}>
              <LoginPage />
            </Suspense>
          }
        />
        {/* Protected Route for Password Change (no layout) */}
        <Route
          path="/change-password"
          element={
            <ProtectedRoute requirePasswordChange>
              <ChangePasswordPage />
            </ProtectedRoute>
          }
        />

        {/* All protected routes wrapped in MainLayout */}
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <Dashboard />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/files"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <FilesPage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/movies/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <MoviesModule />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/tv-shows/*"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <TvShowsModule />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/settings"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <SettingsPage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/profile"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <ProfilePage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/enrichment"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <EnrichmentPage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/storage"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <StoragePage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/organisation"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <OrganisationPage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/queue"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <QueuePage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/system-health"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <SystemHealthPage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        <Route
          path="/plex/collections"
          element={
            <ProtectedRoute>
              <MainLayout>
                <Suspense fallback={<LoadingFallback />}>
                  <PlexCollectionsPage />
                </Suspense>
              </MainLayout>
            </ProtectedRoute>
          }
        />

        {/* Redirects for legacy/dead routes */}
        <Route path="/dashboard" element={<Navigate to="/" replace />} />
        <Route path="/activity" element={<Navigate to="/" replace />} />
        <Route path="/search" element={<Navigate to="/" replace />} />

        {/* 404 Not Found */}
        <Route
          path="*"
          element={
            <MainLayout showFooter={false}>
              <Suspense fallback={<LoadingFallback />}>
                <NotFound />
              </Suspense>
            </MainLayout>
          }
        />
      </Routes>
    </BrowserRouter>
  )
}

export default App
