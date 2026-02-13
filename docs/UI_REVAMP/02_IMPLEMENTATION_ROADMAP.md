# Metamaster UI Revamp - Implementation Roadmap

## Overview

This document provides a detailed implementation roadmap for the Metamaster UI revamp, breaking down the work into manageable phases with specific deliverables and dependencies.

---

## Phase 0: Legacy Component Audit & Deprecation (Prerequisite)

**Status: ✅ COMPLETED**

**Critical: Must complete before Phase 1**

### Objectives
- Audit all existing components
- Create deprecation strategy
- Prevent new usage of deprecated components
- Plan removal timeline

### Deliverables
- [x] Audit all existing components and identify non-conforming ones
- [x] Create deprecation list with migration paths
- [x] Add deprecation warnings to legacy components
- [x] Document which new components replace which old ones
- [ ] Create linting rules to prevent new usage of deprecated components
- [x] Plan removal timeline (remove after Phase 3 completion)

### Components to Deprecate
- All custom styled components outside design system
- Components with hardcoded colors/spacing
- Legacy button styles not matching design system
- Non-standard card layouts
- Custom form inputs not using design system
- Any component with inline styles

### Key Principle
After Phase 0, **no new code should use deprecated components**. The design system becomes the single source of truth.

---

## Phase 1: Design System Foundation

**Status: ✅ COMPLETED**

### Objectives
- Establish modern color palette and design tokens
- Update Tailwind configuration
- Create CSS variables for theming
- Implement dark mode support

### Deliverables

#### 1.1 Update Tailwind Configuration
**File**: `frontend/tailwind.config.js` ✅
- [x] Replace primary color palette with modern indigo gradient
- [x] Add accent colors (success, warning, danger, info)
- [x] Update neutral colors for better contrast
- [x] Add dark mode color definitions
- [x] Extend spacing, border radius, and shadow utilities

#### 1.2 Create Design Tokens
**File**: `frontend/src/styles/design-tokens.css` ✅
- [x] CSS custom properties for colors
- [x] Typography scale variables
- [x] Spacing scale variables
- [x] Shadow definitions
- [x] Border radius utilities
- [x] Transition/animation timings

#### 1.3 Update Global Styles
**File**: `frontend/src/index.css` ✅
- [x] Import design tokens
- [x] Update base styles with new typography
- [x] Enhance scrollbar styling
- [x] Add dark mode support
- [x] Update focus states for accessibility

#### 1.4 Create Theme Provider
**File**: `frontend/src/context/ThemeContext.tsx` ✅
- [x] Theme context for light/dark mode
- [x] useTheme hook
- [x] Theme persistence to localStorage
- [x] System preference detection

### Dependencies
- None (foundational)

---

## Phase 2: Core Component Library

**Status: ✅ COMPLETED**

### Objectives
- Create/enhance fundamental UI components
- Establish consistent component patterns
- Ensure accessibility compliance
- Build reusable component library

### Deliverables

#### 2.1 Card Component
**File**: `frontend/src/components/common/Card/Card.tsx` ✅
- [x] Variants: default, elevated, outlined
- [x] Header, content, footer sections
- [x] Hover effects and transitions
- [x] Proper spacing and padding

#### 2.2 Button Component (Enhanced)
**File**: `frontend/src/components/common/Button/Button.tsx` ✅
- [x] Variants: primary, secondary, outline, ghost
- [x] Sizes: sm, md, lg
- [x] Icon support
- [x] Loading state with spinner
- [x] Disabled state
- [x] Focus states for accessibility

#### 2.3 Badge Component
**File**: `frontend/src/components/common/Badge/Badge.tsx` ✅
- [x] Variants: primary, success, warning, danger, info
- [x] Sizes: sm, md, lg
- [x] Icon support
- [x] Dismissible option

#### 2.4 Input Components
**Files**: ✅
- [x] `frontend/src/components/common/TextInput/TextInput.tsx`
- [x] `frontend/src/components/common/Select/Select.tsx`
- [x] `frontend/src/components/common/Checkbox/Checkbox.tsx`
- [x] `frontend/src/components/common/Toggle/Toggle.tsx`

#### 2.5 DataTable Component
**File**: `frontend/src/components/common/DataTable/DataTable.tsx` ✅
- [x] Sortable columns
- [x] Filterable rows
- [x] Pagination
- [x] Row selection
- [x] Responsive design
- [x] Loading states

#### 2.6 Navigation Components
**Files**: ✅
- [x] `frontend/src/components/common/Breadcrumb.tsx` (enhanced)
- [x] `frontend/src/components/common/Tabs/Tabs.tsx`
- [x] `frontend/src/components/common/Pagination/Pagination.tsx`

#### 2.7 Loading & Feedback Components
**Files**: ✅
- [x] `frontend/src/components/common/Skeleton/Skeleton.tsx`
- [x] `frontend/src/components/common/ProgressBar/ProgressBar.tsx`
- [x] `frontend/src/components/common/LoadingSpinner.tsx` (enhanced)

#### 2.8 Modal/Dialog (Enhanced)
**File**: `frontend/src/components/common/ConfirmDialog.tsx` ✅
- [x] Improved animations
- [x] Better backdrop blur
- [x] Keyboard navigation
- [x] Focus trap

### Dependencies
- Phase 1 (Design System Foundation)

---

## Phase 3: Layout Modernization

**Status: ✅ COMPLETED**

### Objectives
- Redesign header and sidebar
- Update main layout structure
- Implement modern navigation patterns
- Add breadcrumb navigation

### Deliverables

#### 3.1 Header Component (Redesign)
**File**: `frontend/src/components/layout/Header/Header.tsx` ✅
- [x] Sticky positioning with subtle shadow
- [x] Integrated search with autocomplete
- [x] Notification bell with badge
- [x] Settings quick access
- [x] User profile dropdown
- [x] Dark mode toggle
- [x] Responsive hamburger menu
- [x] Better spacing and alignment

#### 3.2 Sidebar Component (Redesign)
**File**: `frontend/src/components/layout/Sidebar/Sidebar.tsx` ✅
- [x] Collapsible sidebar (icon-only when collapsed)
- [x] Active state with accent color
- [x] Hover effects with smooth transitions
- [x] Icons with labels
- [x] Version info at bottom
- [x] Smooth collapse/expand animation
- [x] Better visual hierarchy

#### 3.3 MainLayout Component (Update)
**File**: `frontend/src/components/layout/MainLayout/MainLayout.tsx` ✅
- [x] Updated structure for new header/sidebar
- [x] Proper spacing and padding
- [x] Breadcrumb integration
- [x] Better responsive behavior

#### 3.4 Breadcrumb Navigation
**File**: `frontend/src/components/common/Breadcrumb.tsx` ✅
- [x] Proper styling
- [x] Active state
- [x] Navigation links
- [x] Responsive behavior

#### 3.5 Footer Component (Optional Enhancement)
**File**: `frontend/src/components/layout/Footer.tsx` ✅
- [x] Modern styling
- [x] Better spacing
- [x] Links and information

### Dependencies
- Phase 1 (Design System Foundation)
- Phase 2 (Core Components)

### Post-Phase 3 Action
- [x] **Remove deprecated components** from codebase

---

## Phase 4: Configuration Status Bar & Empty States

**Status: ✅ COMPLETED** (Data Removal pending)

**Critical: Must implement before feature pages**

### Objectives
- Implement configuration status detection
- Create empty state components
- Remove all dummy data
- Guide users through setup

### Deliverables

#### 4.1 Configuration Status Bar
**File**: `frontend/src/components/configuration/ConfigurationStatusBar/ConfigurationStatusBar.tsx` ✅
- [x] Display at top of UI
- [x] Show incomplete configurations
- [x] List required setup steps
- [x] Display missing API keys/settings
- [x] Provide action links to configuration pages
- [x] Auto-hide when all configurations complete

#### 4.2 Configuration Detection Service
**File**: `frontend/src/services/configurationService.ts` ✅
- [x] Check API key configuration
- [x] Check database connection
- [x] Check file system paths
- [x] Check file monitoring status
- [x] Check metadata sources
- [x] Real-time status updates

#### 4.3 Empty State Components
**Files**: `frontend/src/components/common/EmptyState/` ✅
- [x] `frontend/src/components/common/EmptyState/EmptyState.tsx`
- [x] EmptyStateIcon component library

**Variants**:
- [x] No Data (Initial State)
- [x] No Results (Search/Filter)
- [x] Feature Disabled (Configuration Required)
- [x] Error State
- [x] Loading State

#### 4.4 Data Removal
- [ ] Remove all DUMMY_DATA constants
- [ ] Remove mock data from Dashboard
- [ ] Remove mock data from Movies page
- [ ] Remove mock data from TV Shows page
- [ ] Remove mock data from Files page
- [ ] Remove mock data from all components

#### 4.5 Configuration Checks
- [x] Add configuration checks to all feature pages
- [x] Create configuration guidance system
- [x] Implement progressive disclosure
- [x] Add links to configuration pages

### Dependencies
- Phase 1 (Design System Foundation)
- Phase 2 (Core Components)
- Phase 3 (Layout Modernization)

---

## Phase 5: Dashboard Enhancement

**Status: ✅ COMPLETED**

### Objectives
- Modernize dashboard appearance
- Improve visual hierarchy
- Enhance user engagement
- Better information presentation

### Deliverables

#### 5.1 StatCard Component (Enhance)
**File**: `frontend/src/components/dashboard/StatCard/StatCard.tsx` ✅
- [x] Better visual design
- [x] Improved trend indicators
- [x] Hover effects
- [x] Better spacing
- [x] Dark mode support

#### 5.2 LibraryStats Component (Enhance)
**File**: `frontend/src/components/dashboard/LibraryStats/LibraryStats.tsx` ✅
- [x] Modern card design
- [x] Better layout
- [x] Improved icons
- [x] Better spacing

#### 5.3 QuickActions Component (Redesign)
**File**: `frontend/src/components/dashboard/QuickActions/QuickActions.tsx` ✅
- [x] Horizontal scrollable layout
- [x] Better button styling
- [x] Icons and labels
- [x] Responsive design

#### 5.4 StorageChart Component (Enhance)
**File**: `frontend/src/components/dashboard/StorageChart/StorageChart.tsx` ✅
- [x] Modern chart styling
- [x] Better colors
- [x] Improved legend
- [x] Responsive design

#### 5.5 RecentActivity Component (Enhance)
**File**: `frontend/src/components/dashboard/RecentActivity/RecentActivity.tsx` ✅
- [x] Better timeline styling
- [x] Improved icons
- [x] Better spacing
- [x] Timestamps

#### 5.6 Dashboard Layout (Reorganize)
**File**: `frontend/src/components/dashboard/Dashboard/Dashboard.tsx` ✅
- [x] Better section organization
- [x] Improved responsive grid
- [x] Better spacing
- [x] Enhanced visual hierarchy
- [x] Implement empty state
- [ ] Remove dummy data (pending)

### Dependencies
- Phase 1 (Design System Foundation)
- Phase 2 (Core Components)
- Phase 3 (Layout Modernization)
- Phase 4 (Configuration Status Bar & Empty States)

---

## Phase 6: Feature Pages Implementation

**Status: ✅ COMPLETED**

### Objectives
- Implement Movies listing and detail pages
- Implement TV Shows listing and detail pages
- Add filtering and sorting
- Create modern content browsing experience

### Deliverables

#### 6.1 Movies Listing Page
**File**: `frontend/src/components/features/movies/MoviesPage/MoviesPage.tsx` ✅
- [x] Grid/list view toggle
- [x] Search functionality
- [x] Filter panel
- [x] Sort options
- [x] Pagination
- [x] Movie cards with hover effects
- [x] Empty state implementation

#### 6.2 Movie Card Component
**File**: `frontend/src/components/features/movies/MovieCard/MovieCard.tsx` ✅
- [x] Poster image with hover overlay
- [x] Title and year
- [x] Rating/score
- [x] Quick actions
- [x] Status badge
- [x] Responsive design

#### 6.3 Movies Detail Page
**File**: `frontend/src/components/features/movies/MovieDetailPage/MovieDetailPage.tsx` ✅
- [x] Movie information
- [x] Poster and metadata
- [x] File information
- [x] Edit/delete actions
- [x] Related content
- [x] Breadcrumb navigation

#### 6.4 TV Shows Listing Page
**File**: `frontend/src/components/features/tvshows/TVShowsPage/TVShowsPage.tsx` ✅
- [x] Grid/list view toggle
- [x] Search functionality
- [x] Filter panel
- [x] Sort options
- [x] Pagination
- [x] Show cards with hover effects
- [x] Empty state implementation

#### 6.5 TV Show Card Component
**File**: `frontend/src/components/features/tvshows/TVShowCard/TVShowCard.tsx` ✅
- [x] Poster image with hover overlay
- [x] Title and seasons
- [x] Status badge
- [x] Next episode info
- [x] Quick actions
- [x] Responsive design

#### 6.6 TV Show Detail Page
**File**: `frontend/src/components/features/tvshows/TVShowDetailPage/TVShowDetailPage.tsx` ✅
- [x] Show information
- [x] Poster and metadata
- [x] Seasons and episodes
- [x] Episode list with status
- [x] Edit/delete actions
- [x] Breadcrumb navigation

#### 6.7 Filter Panel Component
**File**: `frontend/src/components/features/filter/FilterPanel.tsx` ✅
- [x] Collapsible filters
- [x] Multiple filter types
- [x] Apply/reset buttons
- [x] Responsive design

#### 6.8 Sort Component
**File**: `frontend/src/components/features/sort/SortDropdown.tsx` ✅
- [x] Sort options
- [x] Ascending/descending toggle
- [x] Responsive design

### Dependencies
- Phase 1 (Design System Foundation)
- Phase 2 (Core Components)
- Phase 3 (Layout Modernization)
- Phase 4 (Configuration Status Bar & Empty States)
- Phase 5 (Dashboard Enhancement)

---

## Phase 7: Polish & Optimization

### Objectives
- Add micro-interactions
- Implement loading states
- Add error handling UI
- Test and optimize
- Accessibility audit
- Performance optimization

### Deliverables

#### 7.1 Micro-interactions
- Button hover effects (scale + shadow)
- Card hover elevation
- Smooth transitions
- Loading spinners
- Toast animations

#### 7.2 Loading States
- Skeleton screens for cards
- Shimmer effects
- Progress bars
- Loading spinners

#### 7.3 Error Handling
- Error messages
- Error boundaries
- Retry mechanisms
- User-friendly error states

#### 7.4 Accessibility Audit
- WCAG 2.1 AA compliance
- Keyboard navigation
- Screen reader testing
- Color contrast verification
- Focus management

#### 7.5 Performance Optimization
- Code splitting
- Lazy loading
- Image optimization
- Bundle size analysis
- Lighthouse optimization

#### 7.6 Testing
- Unit tests for components
- Integration tests
- E2E tests
- Visual regression tests
- Accessibility tests

### Dependencies
- All previous phases

---

## Implementation Timeline

```
Phase 0: Legacy Component Audit & Deprecation
├─ Week 1: Audit, deprecation list, linting rules

Phase 1: Design System Foundation
├─ Week 1-2: Tailwind config, design tokens, global styles, theme provider

Phase 2: Core Component Library
├─ Week 2-3: Card, Button, Badge, Input, DataTable, Navigation components

Phase 3: Layout Modernization
├─ Week 3-4: Header, Sidebar, MainLayout, Breadcrumb, Footer
└─ Week 4: Remove deprecated components

Phase 4: Configuration Status Bar & Empty States
├─ Week 4-5: Status bar, configuration detection, empty states, data removal

Phase 5: Dashboard Enhancement
├─ Week 5-6: StatCard, LibraryStats, QuickActions, StorageChart, RecentActivity

Phase 6: Feature Pages Implementation
├─ Week 6-7: Movies pages, TV Shows pages, Filter, Sort components

Phase 7: Polish & Optimization
├─ Week 7-8: Micro-interactions, loading states, error handling
├─ Week 8-9: Accessibility audit, performance optimization
└─ Week 9: Testing and QA
```

---

## Success Criteria

- ✅ Modern, professional appearance matching Sonarr/Radarr inspiration
- ✅ All components have proper dark mode support
- ✅ Responsive design works on all breakpoints
- ✅ WCAG 2.1 AA accessibility compliance
- ✅ Smooth animations and transitions
- ✅ All components have Storybook stories
- ✅ Unit test coverage > 80%
- ✅ Lighthouse score > 90
- ✅ No console errors or warnings
- ✅ Performance metrics meet targets
- ✅ No dummy data displayed anywhere
- ✅ Configuration status bar functional
- ✅ All empty states properly implemented
- ✅ Design system as single source of truth
