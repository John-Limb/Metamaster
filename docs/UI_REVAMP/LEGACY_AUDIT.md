# Phase 0: Legacy Component Audit & Deprecation Plan

**Status: ✅ COMPLETED** - Color scheme migration to indigo (`#6366f1`) has been performed.

**Audit Date:** 2026-02-11  
**Auditor:** Architecture Review  
**Target Design System:** Indigo (`#6366f1`) - per `01_DESIGN_SYSTEM.md`

---

## 1. Executive Summary

This audit examines all frontend components in the Metamaster codebase to identify design system conformance issues, hardcoded values, dummy data, and accessibility gaps. ~~The audit reveals a significant migration effort is required to transition from the current sky-blue (`#0ea5e9`) color scheme to the target indigo (`#6366f1`) design system.~~

**Update (2026-02-13):** The color scheme migration has been completed. The design system now uses indigo (`#6366f1`) as the primary color. All Tailwind configurations and CSS variables have been updated to reflect the new design system.

### Key Findings

| Category | Count | Priority |
|----------|-------|----------|
| Components to Replace | 0 | - |
| Components to Enhance | 47 | High |
| Components to Keep | 8 | Low |
| Components with Dummy Data | 5 | Critical |
| Files with Hardcoded Colors | 32 | High |
| Missing Accessibility Attributes | 24 | Medium |
| Inline Styles Found | 8 | Medium |

### Primary Issues Identified

1. **Color Scheme Mismatch**: Tailwind config and CSS variables use sky-blue (`#0ea5e9`) instead of target indigo (`#6366f1`)
2. **Hardcoded Tailwind Classes**: 32 files contain hardcoded `blue-*`, `sky-*`, or hex color values
3. **Dummy Data Present**: 5 files contain mock data that violates the "No Dummy Data" policy
4. **Accessibility Gaps**: Multiple components lack proper ARIA attributes
5. **Inconsistent Styling**: Non-standard button, input, and card implementations

---

## 2. Component Inventory

### 2.1 Common Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`ApiErrorBoundary.tsx`](frontend/src/components/common/ApiErrorBoundary.tsx) | Enhance | Uses `bg-blue-600`, `hover:bg-blue-700` (line 110) | Replace with indigo color tokens |
| [`Breadcrumb.tsx`](frontend/src/components/common/Breadcrumb.tsx) | Keep | Uses `text-primary-*` (line 39, 47) | Already uses design tokens |
| [`ConfirmDialog.tsx`](frontend/src/components/common/ConfirmDialog.tsx) | Enhance | Uses `bg-primary-600` (line 81) | Verify primary color mapping |
| [`ErrorBoundary.tsx`](frontend/src/components/common/ErrorBoundary.tsx) | Enhance | Uses `bg-primary-600` (line 63) | Verify primary color mapping |
| [`ErrorModal.tsx`](frontend/src/components/common/ErrorModal.tsx) | Enhance | Uses `bg-red-600` for retry (line 85) | Keep red for errors |
| [`LoadingSpinner.tsx`](frontend/src/components/common/LoadingSpinner.tsx) | Enhance | Uses `border-primary-200`, `border-t-primary-500` (line 25) | Verify color mapping |
| [`NotFound.tsx`](frontend/src/components/common/NotFound.tsx) | Enhance | Uses `bg-primary-600` (line 31) | Verify color mapping |
| [`Toast.tsx`](frontend/src/components/common/Toast.tsx) | Enhance | Uses `bg-blue-50` for info type (line 42) | Change to indigo-50 |

### 2.2 Dashboard Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`Dashboard.tsx`](frontend/src/components/dashboard/Dashboard.tsx) | **Remove Dummy Data** | Mock storage data (lines 91, 112-119), mock recent activities (lines 95-110), hardcoded colors `#3b82f6`, `#8b5cf6` (lines 50-51, 115-116) | Remove all dummy data, implement empty state |
| [`LibraryStats.tsx`](frontend/src/components/dashboard/LibraryStats.tsx) | Enhance | Hardcoded `text-blue-600`, `text-purple-600`, `text-green-600`, `text-yellow-600`, `text-red-600` (lines 26, 36, 46, 56, 66) | Use design system color tokens |
| [`QuickActions.tsx`](frontend/src/components/dashboard/QuickActions.tsx) | Enhance | Uses `bg-blue-50`, `hover:bg-blue-100`, `text-blue-700`, `bg-blue-100`, `focus:ring-blue-500` (lines 48-50, 56) | Replace with indigo tokens |
| [`RecentActivity.tsx`](frontend/src/components/dashboard/RecentActivity.tsx) | Enhance | Uses `text-blue-600` (line 84), `bg-blue-100`, `text-blue-600` (line 46) | Replace with indigo tokens |
| [`StatCard.tsx`](frontend/src/components/dashboard/StatCard.tsx) | Enhance | Uses `bg-blue-50`, `text-blue-600` (lines 17-18) | Replace with indigo tokens |
| [`StorageChart.tsx`](frontend/src/components/dashboard/StorageChart.tsx) | Enhance | Hardcoded colors in data array (lines 50-53): `#3b82f6`, `#8b5cf6`, `#10b981`, `#f59e0b` | Use design system accent colors |

### 2.3 Layout Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`DashboardLayout.tsx`](frontend/src/components/layout/DashboardLayout.tsx) | Keep | Uses `text-primary-*` consistently | Already uses design tokens |
| [`Footer.tsx`](frontend/src/components/layout/Footer.tsx) | Keep | Uses gray scale, no primary colors | Already compliant |
| [`Header.tsx`](frontend/src/components/layout/Header.tsx) | Enhance | Uses `bg-primary-600` (line 31) | Verify color mapping |
| [`MainLayout.tsx`](frontend/src/components/layout/MainLayout.tsx) | Keep | Uses `text-primary-*` | Already uses design tokens |
| [`Sidebar.tsx`](frontend/src/components/layout/Sidebar.tsx) | Enhance | Uses `bg-primary-50` (line 75) | Verify color mapping |

### 2.4 Feature Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`MoviesModule.tsx`](frontend/src/components/features/movies/MoviesModule.tsx) | Replace | Placeholder: "Movies Feature - To be implemented" | Implement new design per Phase 6 |
| [`TvShowsModule.tsx`](frontend/src/components/features/tvshows/TvShowsModule.tsx) | Replace | Placeholder: "TV Shows Feature - To be implemented" | Implement new design per Phase 6 |

### 2.5 File Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`FileCard.tsx`](frontend/src/components/file/FileCard.tsx) | Enhance | Uses `border-blue-500` (line 118), `bg-blue-50` (line 88) | Replace with indigo tokens |
| [`FileExplorer.tsx`](frontend/src/components/file/FileExplorer.tsx) | Enhance | Uses `bg-blue-100`, `text-blue-600` for view mode buttons (lines 115, 126, 137) | Replace with indigo tokens |
| [`BatchOperationModal.tsx`](frontend/src/components/file/BatchOperationModal.tsx) | Enhance | Uses `focus:ring-blue-500` (lines 125, 141), `bg-blue-600` (line 188) | Replace with indigo tokens |
| [`FileContextMenu.tsx`](frontend/src/components/file/FileContextMenu.tsx) | Keep | Uses red for delete action | Correct semantic color usage |
| [`FileDetailsPanel.tsx`](frontend/src/components/file/FileDetailsPanel.tsx) | Enhance | Uses `text-blue-500` for folder icon (line 38) | May use semantic color for folder |
| [`FileGrid.tsx`](frontend/src/components/file/FileGrid.tsx) | Enhance | Uses `border-b-2 border-blue-500` (line 27) | Replace with indigo tokens |
| [`FileInformationModal.tsx`](frontend/src/components/file/FileInformationModal.tsx) | Enhance | Uses `bg-gray-100` backgrounds (lines 56, 92-93, 98-99, 140) | Check dark mode contrast |
| [`FileList.tsx`](frontend/src/components/file/FileList.tsx) | Enhance | Uses `border-b-2 border-blue-500` (line 27) | Replace with indigo tokens |
| [`FilePreview.tsx`](frontend/src/components/file/FilePreview.tsx) | Keep | Uses semantic colors for file type icons | Already compliant |
| [`FileScanner.tsx`](frontend/src/components/file/FileScanner.tsx) | **Remove Dummy Data** | Simulated scan progress (lines 24-45), hardcoded progress updates | Replace with real API integration |
| [`FileTree.tsx`](frontend/src/components/file/FileTree.tsx) | Enhance | Uses `bg-blue-50` (line 48), `text-blue-500` (line 74) | Replace with indigo tokens |
| [`QuickAccessShortcuts.tsx`](frontend/src/components/file/QuickAccessShortcuts.tsx) | Enhance | Uses `bg-blue-100`, `text-blue-600` (line 30) | Replace with indigo tokens |

### 2.6 Queue Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`QueueItem.tsx`](frontend/src/components/queue/QueueItem.tsx) | Enhance | Uses `bg-blue-100` for processing status (lines 97-98) | Change to indigo-100 |
| [`QueuePanel.tsx`](frontend/src/components/queue/QueuePanel.tsx) | Enhance | Uses `text-blue-600` (lines 91, 110, 121), `focus:ring-blue-500` (line 108) | Replace with indigo tokens |
| [`QueueStats.tsx`](frontend/src/components/queue/QueueStats.tsx) | Enhance | Uses `bg-blue-100`, `text-blue-800` (lines 64, 98) | Change to indigo tokens |
| [`TaskProgress.tsx`](frontend/src/components/queue/TaskProgress.tsx) | Enhance | Uses `bg-blue-500` for processing status (line 12) | Change to indigo-500 |

### 2.7 Search Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`SearchBar.tsx`](frontend/src/components/search/SearchBar.tsx) | Enhance | Uses `focus:ring-blue-500`, `focus:border-blue-500` (line 155) | Replace with indigo tokens |
| [`FilterPanel.tsx`](frontend/src/components/search/FilterPanel.tsx) | Enhance | Uses `focus:ring-blue-500`, `focus:border-blue-500` (lines 153, 174, 203, 229, 248, 264, 310), `bg-blue-100` (line 282) | Replace with indigo tokens |
| [`AdvancedSearch.tsx`](frontend/src/components/search/AdvancedSearch.tsx) | Enhance | Uses `bg-blue-50`, `border-blue-200`, `text-blue-700` (lines 55, 56, 74-76, 120) | Replace with indigo tokens |
| [`SavedSearches.tsx`](frontend/src/components/search/SavedSearches.tsx) | Enhance | Uses `text-blue-600` (line 80), `focus:ring-blue-500` (line 78) | Replace with indigo tokens |

### 2.8 Settings Components

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`GeneralSettings.tsx`](frontend/src/components/settings/GeneralSettings.tsx) | Enhance | Uses `focus:ring-blue-500`, `focus:border-blue-500` (lines 83, 103, 125-127, 155, 173-175, 200-202), `bg-blue-600` (lines 126, 174, 201) | Replace with indigo tokens |
| [`APISettings.tsx`](frontend/src/components/settings/APISettings.tsx) | Enhance | Uses `focus:ring-blue-500`, `focus:border-blue-500` (lines 109, 115, 139, 158, 178), `bg-blue-600` (line 115) | Replace with indigo tokens |
| [`CacheSettings.tsx`](frontend/src/components/settings/CacheSettings.tsx) | Enhance | Uses `focus:ring-blue-500`, `focus:border-blue-500` (lines 89-90, 119, 137-138, 145-147, 167, 187), `bg-blue-600` (lines 90, 138, 145) | Replace with indigo tokens |
| [`MonitoringSettings.tsx`](frontend/src/components/settings/MonitoringSettings.tsx) | Enhance | Uses `focus:ring-blue-500`, `focus:border-blue-500` (lines 50-51, 78, 104-105, 130, 152-153), `bg-blue-600` (lines 51, 78, 105, 153) | Replace with indigo tokens |

### 2.9 Page Files

| Component | Category | Issues Found | Migration Action |
|-----------|----------|--------------|-------------------|
| [`DashboardPage.tsx`](frontend/src/pages/DashboardPage.tsx) | **Remove Dummy Data** | Hardcoded "0" values (lines 38, 44, 50, 56) | Remove dummy data, show empty state |
| [`FilesPage.tsx`](frontend/src/pages/FilesPage.tsx) | Keep | Uses components from file module | Component migration will fix |
| [`HomePage.tsx`](frontend/src/pages/HomePage.tsx) | **Remove Dummy Data** | Hardcoded "0" values in quick stats (lines 88, 92, 96), gradient `from-primary-50 to-blue-50` (line 84) | Remove dummy data, fix gradient |
| [`MoviesPage.tsx`](frontend/src/pages/MoviesPage.tsx) | Keep | Uses empty state pattern | Already compliant |
| [`SearchPage.tsx`](frontend/src/pages/SearchPage.tsx) | Keep | Uses empty state pattern | Already compliant |
| [`SettingsPage.tsx`](frontend/src/pages/SettingsPage.tsx) | Enhance | Inline StatCard component (lines 11-22) | Extract to shared component |
| [`TVShowsPage.tsx`](frontend/src/pages/TVShowsPage.tsx) | Keep | Uses empty state pattern | Already compliant |

### 2.10 Configuration & Styles Files

| File | Category | Issues Found | Migration Action |
|------|----------|--------------|------------------|
| [`tailwind.config.js`](frontend/tailwind.config.js) | **Replace** | Primary colors set to sky-blue `#0ea5e9` (lines 10-21) | Complete rewrite with indigo palette |
| [`variables.css`](frontend/src/styles/variables.css) | **Replace** | CSS variables use sky-blue `#0ea5e9` (lines 5-14) | Complete rewrite with indigo palette |
| [`animations.css`](frontend/src/styles/animations.css) | Keep | Animation utilities, no color dependencies | Already compliant |
| [`globals.css`](frontend/src/styles/globals.css) | Enhance | Hardcoded `#0284c7` link color (line 42), `#0ea5e9` focus shadow (line 71) | Replace with indigo tokens |
| [`App.tsx`](frontend/src/App.tsx) | Keep | No color styling | Already compliant |
| [`App.css`](frontend/src/App.css) | Remove | Contains unused Vite default styles (lines 1-42) | Delete or clean up |
| [`index.css`](frontend/src/index.css) | Keep | Imports variables and animations | Already compliant |

---

## 3. Dummy Data Inventory

### 3.1 Critical Issues - Must Remove

| File | Line(s) | Dummy Data Description | Action |
|------|---------|----------------------|--------|
| [`Dashboard.tsx`](frontend/src/components/dashboard/Dashboard.tsx) | 91 | `totalSize: (movieResponse.items.length + tvResponse.items.length) * 25 * 1024 * 1024 * 1024` - Mock storage calculation | Replace with real API data |
| [`Dashboard.tsx`](frontend/src/components/dashboard/Dashboard.tsx) | 112-119 | Mock storage data array with hardcoded colors and values | Implement real storage API |
| [`Dashboard.tsx`](frontend/src/components/dashboard/Dashboard.tsx) | 95-110 | Mock recent activities with placeholder data | Implement real activity API |
| [`DashboardPage.tsx`](frontend/src/pages/DashboardPage.tsx) | 38, 44, 50, 56 | Hardcoded "0" values for stats | Remove, show empty state |
| [`HomePage.tsx`](frontend/src/pages/HomePage.tsx) | 88, 92, 96 | Hardcoded "0" values for quick stats | Remove, show empty state |
| [`FileScanner.tsx`](frontend/src/components/file/FileScanner.tsx) | 24-45 | Simulated scan progress with random increments | Connect to real file scanner API |

### 3.2 Implementation Guidance

Per the "No Dummy Data" policy from `README.md`:
- All empty states should display: "Nothing here, yet"
- Show configuration status bar when data unavailable
- Implement progressive disclosure for unconfigured features
- Always show