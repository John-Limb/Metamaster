/* eslint-disable react-refresh/only-export-components */
import React, { lazy, Suspense } from 'react'
import type { RouteObject } from 'react-router-dom'
import { MainLayout } from '@/components/layout'
import { LoadingSpinner, NotFound } from '@/components/common'

// Lazy load pages
const HomePage = lazy(() => import('@/pages/HomePage').then(m => ({ default: m.HomePage })))
const FilesPage = lazy(() => import('@/pages/FilesPage').then(m => ({ default: m.FilesPage })))
const SearchPage = lazy(() => import('@/pages/SearchPage').then(m => ({ default: m.SearchPage })))
const SettingsPage = lazy(() => import('@/pages/SettingsPage').then(m => ({ default: m.SettingsPage })))
const MoviesPage = lazy(() => import('@/components/features/movies/MoviesPage'))
const TVShowsPage = lazy(() => import('@/components/features/tvshows/TVShowsPage'))
const EnrichmentPage = lazy(() => import('@/pages/EnrichmentPage').then(m => ({ default: m.EnrichmentPage })))

// Loading fallback component
const PageLoader = () => (
  <div className="flex items-center justify-center min-h-screen">
    <LoadingSpinner size="lg" message="Loading page..." />
  </div>
)

// Wrapper component for pages with MainLayout
const withMainLayout = (Component: React.ComponentType) => (
  <MainLayout>
    <Suspense fallback={<PageLoader />}>
      <Component />
    </Suspense>
  </MainLayout>
)

export const routes: RouteObject[] = [
  {
    path: '/',
    element: withMainLayout(HomePage),
  },
  {
    path: '/files',
    element: withMainLayout(FilesPage),
  },
  {
    path: '/search',
    element: withMainLayout(SearchPage),
  },
  {
    path: '/settings',
    element: withMainLayout(SettingsPage),
  },
  {
    path: '/movies',
    element: withMainLayout(MoviesPage),
  },
  {
    path: '/tv-shows',
    element: withMainLayout(TVShowsPage),
  },
  {
    path: '/enrichment',
    element: withMainLayout(EnrichmentPage),
  },
  {
    path: '*',
    element: (
      <MainLayout showFooter={false}>
        <NotFound />
      </MainLayout>
    ),
  },
]
