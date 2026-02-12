# Metamaster UI Revamp - Implementation Roadmap

## Overview

This document provides a detailed implementation roadmap for the Metamaster UI revamp, breaking down the work into manageable phases with specific deliverables and dependencies.

---

## Phase 0: Legacy Component Audit & Deprecation (Prerequisite)

**Critical: Must complete before Phase 1**

### Objectives
- Audit all existing components
- Create deprecation strategy
- Prevent new usage of deprecated components
- Plan removal timeline

### Deliverables
- [ ] Audit all existing components and identify non-conforming ones
- [ ] Create deprecation list with migration paths
- [ ] Add deprecation warnings to legacy components
- [ ] Document which new components replace which old ones
- [ ] Create linting rules to prevent new usage of deprecated components
- [ ] Plan removal timeline (remove after Phase 3 completion)

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

### Objectives
- Establish modern color palette and design tokens
- Update Tailwind configuration
- Create CSS variables for theming
- Implement dark mode support

### Deliverables

#### 1.1 Update Tailwind Configuration
**File**: `frontend/tailwind.config.js`
- Replace primary color palette with modern indigo gradient
- Add accent colors (success, warning, danger, info)
- Update neutral colors for better contrast
- Add dark mode color definitions
- Extend spacing, border radius, and shadow utilities

#### 1.2 Create Design Tokens
**File**: `frontend/src/styles/design-tokens.css`
- CSS custom properties for colors
- Typography scale variables
- Spacing scale variables
- Shadow definitions
- Border radius utilities
- Transition/animation timings

#### 1.3 Update Global Styles
**File**: `frontend/src/index.css`
- Import design tokens
- Update base styles with new typography
- Enhance scrollbar styling
- Add dark mode support
- Update focus states for accessibility

#### 1.4 Create Theme Provider
**File**: `frontend/src/context/ThemeContext.tsx`
- Theme context for light/dark mode
- useTheme hook
- Theme persistence to localStorage
- System preference detection

### Dependencies
- None (foundational)

---

## Phase 2: Core Component Library

### Objectives
- Create/enhance fundamental UI components
- Establish consistent component patterns
- Ensure accessibility compliance
- Build reusable component library

### Deliverables

#### 2.1 Card Component
**File**: `frontend/src/components/common/Card.tsx`
- Variants: default, elevated, outlined
- Header, content, footer sections
- Hover effects and transitions
- Proper spacing and padding

#### 2.2 Button Component (Enhanced)
**File**: `frontend/src/components/common/Button.tsx`
- Variants: primary, secondary, outline, ghost
- Sizes: sm, md, lg
- Icon support
- Loading state with spinner
- Disabled state
- Focus states for accessibility

#### 2.3 Badge Component
**File**: `frontend/src/components/common/Badge.tsx`
- Variants: primary, success, warning, danger, info
- Sizes: sm, md, lg
- Icon support
- Dismissible option

#### 2.4 Input Components
**Files**: 
- `frontend/src/components/common/TextInput.tsx`
- `frontend/src/components/common/Select.tsx`
- `frontend/src/components/common/Checkbox.tsx`
- `frontend/src/components/common/Toggle.tsx`

#### 2.5 DataTable Component
**File**: `frontend/src/components/common/DataTable.tsx`
- Sortable columns
- Filterable rows
- Pagination
- Row selection
- Responsive design
- Loading states

#### 2.6 Navigation Components
**Files**:
- `frontend/src/components/common/Breadcrumb.tsx` (enhance)
- `frontend/src/components/common/Tabs.tsx`
- `frontend/src/components/common/Pagination.tsx`

#### 2.7 Loading & Feedback Components
**Files**:
- `frontend/src/components/common/Skeleton.tsx`
- `frontend/src/components/common/ProgressBar.tsx`
- `frontend/src/components/common/Spinner.tsx` (enhance)

#### 2.8 Modal/Dialog (Enhanced)
**File**: `frontend/src/components/common/ConfirmDialog.tsx` (enhance)
- Improved animations
- Better backdrop blur
- Keyboard navigation
- Focus trap

### Dependencies
- Phase 1 (Design System Foundation)

---

## Phase 3: Layout Modernization

### Objectives
- Redesign header and sidebar
- Update main layout structure
- Implement modern navigation patterns
- Add breadcrumb navigation

### Deliverables

#### 3.1 Header Component (Redesign)
**File**: `frontend/src/components/layout/Header.tsx`
- Sticky positioning with subtle shadow
- Integrated search with autocomplete
- Notification bell with badge
- Settings quick access
- User profile dropdown
- Dark mode toggle
- Responsive hamburger menu
- Better spacing and alignment

#### 3.2 Sidebar Component (Redesign)
**File**: `frontend/src/components/layout/Sidebar.tsx`
- Collapsible sidebar (icon-only when collapsed)
- Active state with accent color
- Hover effects with smooth transitions
- Icons with labels
- Version info at bottom
- Smooth collapse/expand animation
- Better visual hierarchy

#### 3.3 MainLayout Component (Update)
**File**: `frontend/src/components/layout/MainLayout.tsx`
- Updated structure for new header/sidebar
- Proper spacing and padding
- Breadcrumb integration
- Better responsive behavior

#### 3.4 Breadcrumb Navigation
**File**: `frontend/src/components/common/Breadcrumb.tsx` (enhance)
- Proper styling
- Active state
- Navigation links
- Responsive behavior

#### 3.5 Footer Component (Optional Enhancement)
**File**: `frontend/src/components/layout/Footer.tsx`
- Modern styling
- Better spacing
- Links and information

### Dependencies
- Phase 1 (Design System Foundation)
- Phase 2 (Core Components)

### Post-Phase 3 Action
- **Remove deprecated components** from codebase

---

## Phase 4: Configuration Status Bar & Empty States

**Critical: Must implement before feature pages**

### Objectives
- Implement configuration status detection
- Create empty state components
- Remove all dummy data
- Guide users through setup

### Deliverables

#### 4.1 Configuration Status Bar
**File**: `frontend/src/components/common/ConfigurationStatusBar.tsx`
- Display at top of UI
- Show incomplete configurations
- List required setup steps
- Display missing API keys/settings
- Provide action links to configuration pages
- Auto-hide when all configurations complete

#### 4.2 Configuration Detection Service
**File**: `frontend/src/services/configurationService.ts`
- Check API key configuration
- Check database connection
- Check file system paths
- Check file monitoring status
- Check metadata sources
- Real-time status updates

#### 4.3 Empty State Components
**Files**:
- `frontend/src/components/common/EmptyState.tsx`
- `frontend/src/components/common/EmptyStateIcon.tsx`

**Variants**:
- No Data (Initial State)
- No Results (Search/Filter)
- Feature Disabled (Configuration Required)
- Error State
- Loading State

#### 4.4 Data Removal
- [ ] Remove all DUMMY_DATA constants
- [ ] Remove mock data from Dashboard
- [ ] Remove mock data from Movies page
- [ ] Remove mock data from TV Shows page
- [ ] Remove mock data from Files page
- [ ] Remove mock data from all components

#### 4.5 Configuration Checks
- [ ] Add configuration checks to all feature pages
- [ ] Create configuration guidance system
- [ ] Implement progressive disclosure
- [ ] Add links to configuration pages

### Dependencies
- Phase 1 (Design System Foundation)
- Phase 2 (Core Components)
- Phase 3 (Layout Modernization)

---

## Phase 5: Dashboard Enhancement

### Objectives
- Modernize dashboard appearance
- Improve visual hierarchy
- Enhance user engagement
- Better information presentation

### Deliverables

#### 5.1 StatCard Component (Enhance)
**File**: `frontend/src/components/dashboard/StatCard.tsx`
- Better visual design
- Improved trend indicators
- Hover effects
- Better spacing
- Dark mode support

#### 5.2 LibraryStats Component (Enhance)
**File**: `frontend/src/components/dashboard/LibraryStats.tsx`
- Modern card design
- Better layout
- Improved icons
- Better spacing

#### 5.3 QuickActions Component (Redesign)
**File**: `frontend/src/components/dashboard/QuickActions.tsx`
- Horizontal scrollable layout
- Better button styling
- Icons and labels
- Responsive design

#### 5.4 StorageChart Component (Enhance)
**File**: `frontend/src/components/dashboard/StorageChart.tsx`
- Modern chart styling
- Better colors
- Improved legend
- Responsive design

#### 5.5 RecentActivity Component (Enhance)
**File**: `frontend/src/components/dashboard/RecentActivity.tsx`
- Better timeline styling
- Improved icons
- Better spacing
- Timestamps

#### 5.6 Dashboard Layout (Reorganize)
**File**: `frontend/src/components/dashboard/Dashboard.tsx`
- Better section organization
- Improved responsive grid
- Better spacing
- Enhanced visual hierarchy
- Implement empty state
- Remove dummy data

### Dependencies
- Phase 1 (Design System Foundation)
- Phase 2 (Core Components)
- Phase 3 (Layout Modernization)
- Phase 4 (Configuration Status Bar & Empty States)

---

## Phase 6: Feature Pages Implementation

### Objectives
- Implement Movies listing and detail pages
- Implement TV Shows listing and detail pages
- Add filtering and sorting
- Create modern content browsing experience

### Deliverables

#### 6.1 Movies Listing Page
**File**: `frontend/src/pages/MoviesPage.tsx`
- Grid/list view toggle
- Search functionality
- Filter panel
- Sort options
- Pagination
- Movie cards with hover effects
- Empty state implementation

#### 6.2 Movie Card Component
**File**: `frontend/src/components/features/movies/MovieCard.tsx`
- Poster image with hover overlay
- Title and year
- Rating/score
- Quick actions
- Status badge
- Responsive design

#### 6.3 Movies Detail Page
**File**: `frontend/src/pages/MovieDetailPage.tsx`
- Movie information
- Poster and metadata
- File information
- Edit/delete actions
- Related content
- Breadcrumb navigation

#### 6.4 TV Shows Listing Page
**File**: `frontend/src/pages/TVShowsPage.tsx`
- Grid/list view toggle
- Search functionality
- Filter panel
- Sort options
- Pagination
- Show cards with hover effects
- Empty state implementation

#### 6.5 TV Show Card Component
**File**: `frontend/src/components/features/tvshows/TVShowCard.tsx`
- Poster image with hover overlay
- Title and seasons
- Status badge
- Next episode info
- Quick actions
- Responsive design

#### 6.6 TV Show Detail Page
**File**: `frontend/src/pages/TVShowDetailPage.tsx`
- Show information
- Poster and metadata
- Seasons and episodes
- Episode list with status
- Edit/delete actions
- Breadcrumb navigation

#### 6.7 Filter Panel Component
**File**: `frontend/src/components/common/FilterPanel.tsx`
- Collapsible filters
- Multiple filter types
- Apply/reset buttons
- Responsive design

#### 6.8 Sort Component
**File**: `frontend/src/components/common/SortDropdown.tsx`
- Sort options
- Ascending/descending toggle
- Responsive design

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
