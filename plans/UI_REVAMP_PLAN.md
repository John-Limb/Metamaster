# Metamaster UI Revamp Plan

## Executive Summary

This document outlines a comprehensive modernization of the Metamaster user interface, inspired by industry-leading media management applications like Sonarr and Radarr. The revamp focuses on creating a modern, intuitive, and functional interface that improves user experience while maintaining the application's powerful capabilities.

## Critical Design Principles

### Design System as Single Source of Truth
- **All UI components must use the design system** - No custom styling outside the design system
- **Deprecate legacy components** - Remove all existing components that don't conform to the design system
- **Enforce consistency** - Every visual element must follow design tokens and component specifications
- **No exceptions** - All new features must use design system components exclusively

### Empty States & Configuration Status
- **No dummy data** - Never display placeholder/mock data in the UI
- **Clean slate approach** - Show "Nothing here, yet" messages for empty states
- **Configuration status bar** - Display a prominent status bar at the top of the UI showing:
  - Incomplete configurations
  - Required setup steps
  - Missing API keys or settings
  - Action items for the user
- **Progressive disclosure** - Hide features until properly configured
- **Clear guidance** - Provide links to configuration pages from status messages

---

## Current State Analysis

### Existing Architecture
- **Framework**: React 19 with TypeScript
- **Styling**: Tailwind CSS v4
- **State Management**: Zustand
- **UI Components**: Custom components + React Icons
- **Layout**: Traditional sidebar + main content area

### Current Strengths
✅ Clean component structure with proper separation of concerns
✅ Responsive design foundation with Tailwind CSS
✅ Comprehensive dashboard with stats and charts
✅ Modular feature architecture (Movies, TV Shows)
✅ Good accessibility foundations

### Areas for Modernization
❌ Basic color palette lacks visual hierarchy and modern aesthetics
❌ Sidebar navigation is functional but lacks visual polish
❌ Dashboard layout could be more dynamic and engaging
❌ Missing modern UI patterns (cards with hover effects, better spacing)
❌ Limited visual feedback and micro-interactions
❌ Movies and TV Shows modules are not fully implemented
❌ No dark mode support
❌ Limited use of modern design patterns (glass morphism, gradients, shadows)

---

## Design System Modernization

### 1. Color Palette Enhancement

#### Primary Colors (Modern Blue-Purple Gradient)
```
Primary-50:  #f0f4ff  (Lightest)
Primary-100: #e0e7ff
Primary-200: #c7d2fe
Primary-300: #a5b4fc
Primary-400: #818cf8
Primary-500: #6366f1  (Main - Modern Indigo)
Primary-600: #4f46e5  (Darker)
Primary-700: #4338ca
Primary-800: #3730a3
Primary-900: #312e81  (Darkest)
```

#### Accent Colors (Complementary)
- **Success**: `#10b981` (Emerald) - for positive actions
- **Warning**: `#f59e0b` (Amber) - for caution
- **Danger**: `#ef4444` (Red) - for destructive actions
- **Info**: `#3b82f6` (Blue) - for informational content

#### Neutral Colors (Enhanced)
- **Background**: `#ffffff` (Light mode), `#0f172a` (Dark mode)
- **Surface**: `#f8fafc` (Light), `#1e293b` (Dark)
- **Border**: `#e2e8f0` (Light), `#334155` (Dark)
- **Text**: `#1e293b` (Light), `#f1f5f9` (Dark)

### 2. Typography System

#### Font Stack
```
Font Family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
```

#### Type Scale
- **Display**: 48px / 56px (font-bold)
- **Heading 1**: 36px / 44px (font-bold)
- **Heading 2**: 28px / 36px (font-bold)
- **Heading 3**: 24px / 32px (font-semibold)
- **Body Large**: 18px / 28px (font-normal)
- **Body**: 16px / 24px (font-normal)
- **Body Small**: 14px / 20px (font-normal)
- **Caption**: 12px / 16px (font-medium)

### 3. Spacing System

```
xs: 4px
sm: 8px
md: 12px
lg: 16px
xl: 24px
2xl: 32px
3xl: 48px
4xl: 64px
```

### 4. Shadow & Elevation System

```
Subtle:    0 1px 2px 0 rgba(0, 0, 0, 0.05)
Small:     0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)
Medium:    0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)
Large:     0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)
XL:        0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)
```

### 5. Border Radius System

```
sm: 4px
md: 8px
lg: 12px
xl: 16px
2xl: 20px
full: 9999px
```

---

## Layout Architecture

### New Header Design
**Inspiration**: Sonarr/Radarr clean header with integrated search

```
┌─────────────────────────────────────────────────────────────────┐
│ ☰  [Logo] Metamaster    [Search Bar]    🔔 ⚙️ 👤 🌙           │
└─────────────────────────────────────────────────────────────────┘
```

**Features**:
- Sticky header with subtle shadow
- Integrated search with autocomplete
- Notification bell with badge
- Settings quick access
- User profile dropdown
- Dark mode toggle
- Responsive hamburger menu on mobile

### New Sidebar Design
**Inspiration**: Modern collapsible sidebar with icons and labels

```
┌──────────────────┐
│ ☰ Navigation     │
├──────────────────┤
│ 🏠 Dashboard     │
│ 🎬 Movies        │
│ 📺 TV Shows      │
│ 📁 Files         │
│ 🔍 Search        │
│ ⚙️  Settings     │
├──────────────────┤
│ v1.0.0           │
└──────────────────┘
```

**Features**:
- Collapsible sidebar (icon-only when collapsed)
- Active state with accent color and subtle background
- Hover effects with smooth transitions
- Icons with labels for clarity
- Version info at bottom
- Smooth collapse/expand animation

### Main Content Area
- Full-width responsive grid
- Consistent padding and margins
- Breadcrumb navigation for context
- Page header with title and actions
- Content sections with clear visual separation

---

## Component Library Modernization

### Core Components to Update

#### 1. **Card Component** (New)
```typescript
// Modern card with hover effects and proper spacing
<Card variant="default" | "elevated" | "outlined">
  <CardHeader title="Title" subtitle="Subtitle" />
  <CardContent>Content</CardContent>
  <CardFooter>Actions</CardFooter>
</Card>
```

**Features**:
- Multiple variants (default, elevated, outlined)
- Hover elevation effect
- Smooth transitions
- Proper spacing and padding

#### 2. **Button Component** (Enhanced)
```typescript
<Button 
  variant="primary" | "secondary" | "outline" | "ghost"
  size="sm" | "md" | "lg"
  icon={<Icon />}
  loading={false}
  disabled={false}
>
  Click me
</Button>
```

**Features**:
- Multiple variants with proper contrast
- Loading state with spinner
- Icon support
- Proper focus states for accessibility
- Smooth hover and active states

#### 3. **Badge Component** (New)
```typescript
<Badge variant="primary" | "success" | "warning" | "danger">
  Label
</Badge>
```

#### 4. **Stat Card Component** (Enhanced)
```typescript
<StatCard
  title="Total Movies"
  value={456}
  trend={{ value: 12, direction: 'up' }}
  icon={<Icon />}
  color="primary"
/>
```

**Improvements**:
- Better visual hierarchy
- Improved trend indicator
- Hover effects
- Better spacing

#### 5. **Data Table Component** (New)
```typescript
<DataTable
  columns={columns}
  data={data}
  sortable={true}
  filterable={true}
  paginated={true}
/>
```

**Features**:
- Sortable columns
- Filterable rows
- Pagination
- Row selection
- Responsive design

#### 6. **Modal/Dialog Component** (Enhanced)
- Improved backdrop blur
- Better animations
- Proper focus management
- Keyboard navigation

#### 7. **Toast/Notification Component** (Enhanced)
- Position variants (top, bottom, corner)
- Auto-dismiss with progress bar
- Action buttons
- Icons for different types

#### 8. **Input Components** (Enhanced)
- Text input with icons
- Select dropdown with search
- Checkbox and radio buttons
- Toggle switch
- Date picker
- File upload with drag-and-drop

#### 9. **Navigation Components** (New)
- Breadcrumb with proper styling
- Tabs with underline indicator
- Pagination controls
- Stepper component

#### 10. **Loading States** (Enhanced)
- Skeleton loaders for cards
- Shimmer effects
- Progress bars
- Spinners with variants

---

## Feature Pages Design

### 1. Movies Page

#### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ Movies                                    [+ Add] [Filter]│
├─────────────────────────────────────────────────────────┤
│ [Search] [Sort: Title ▼] [View: Grid/List ▼]           │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ Poster   │ │ Poster   │ │ Poster   │ │ Poster   │   │
│ │ Title    │ │ Title    │ │ Title    │ │ Title    │   │
│ │ Year     │ │ Year     │ │ Year     │ │ Year     │   │
│ │ Rating   │ │ Rating   │ │ Rating   │ │ Rating   │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ Poster   │ │ Poster   │ │ Poster   │ │ Poster   │   │
│ │ Title    │ │ Title    │ │ Title    │ │ Title    │   │
│ │ Year     │ │ Year     │ │ Year     │ │ Year     │   │
│ │ Rating   │ │ Rating   │ │ Rating   │ │ Rating   │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│ < 1 2 3 4 5 >                                           │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Grid view with movie posters (4 columns on desktop, responsive)
- List view alternative
- Search and filter functionality
- Sort options (title, year, rating, date added)
- Movie cards with:
  - Poster image with hover overlay
  - Title and year
  - Rating/score
  - Quick actions (play, edit, delete)
  - Status badge (monitored, unmonitored)
- Pagination or infinite scroll
- Add new movie button

#### Movie Detail Page
```
┌─────────────────────────────────────────────────────────┐
│ < Back                                                   │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐  Title                                     │
│ │ Poster   │  Year | Rating | Genre | Runtime          │
│ │          │  ─────────────────────────────────────    │
│ │          │  Description...                            │
│ │          │  ─────────────────────────────────────    │
│ │          │  [Edit] [Delete] [Monitor]                │
│ └──────────┘                                            │
├─────────────────────────────────────────────────────────┤
│ Files                                                    │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ filename.mkv  | 2.5 GB | 1080p | 2024-01-15       │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Metadata                                                 │
│ Director: ... | Cast: ... | IMDb: ...                  │
└─────────────────────────────────────────────────────────┘
```

### 2. TV Shows Page

#### Layout Structure
```
┌─────────────────────────────────────────────────────────┐
│ TV Shows                                  [+ Add] [Filter]│
├─────────────────────────────────────────────────────────┤
│ [Search] [Sort: Title ▼] [View: Grid/List ▼]           │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ Poster   │ │ Poster   │ │ Poster   │ │ Poster   │   │
│ │ Title    │ │ Title    │ │ Title    │ │ Title    │   │
│ │ Seasons  │ │ Seasons  │ │ Seasons  │ │ Seasons  │   │
│ │ Status   │ │ Status   │ │ Status   │ │ Status   │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
└─────────────────────────────────────────────────────────┘
```

**Features**:
- Similar to Movies but with season/episode information
- Show cards with:
  - Poster image
  - Title
  - Number of seasons
  - Status (Ongoing, Ended, Upcoming)
  - Next episode info
  - Quick actions

#### TV Show Detail Page
```
┌─────────────────────────────────────────────────────────┐
│ < Back                                                   │
├─────────────────────────────────────────────────────────┤
│ ┌──────────┐  Title                                     │
│ │ Poster   │  Year | Status | Seasons | Episodes       │
│ │          │  ─────────────────────────────────────    │
│ │          │  Description...                            │
│ │          │  ─────────────────────────────────────    │
│ │          │  [Edit] [Delete] [Monitor]                │
│ └──────────┘                                            │
├─────────────────────────────────────────────────────────┤
│ Seasons                                                  │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ Season 1 (10 episodes) | 5 monitored | 3 missing   │ │
│ │ Season 2 (12 episodes) | 12 monitored | 0 missing  │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ Episodes (Season 1)                                      │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ E01 | Title | Air Date | Status | File            │ │
│ │ E02 | Title | Air Date | Status | File            │ │
│ └─────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### 3. Dashboard Page (Enhanced)

#### New Layout
```
┌─────────────────────────────────────────────────────────┐
│ Dashboard                                  [Refresh]     │
├─────────────────────────────────────────────────────────┤
│ Quick Stats (4 cards in a row)                          │
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│ │ Total    │ │ Indexed  │ │ Pending  │ │ Completed│   │
│ │ Files    │ │ Files    │ │ Tasks    │ │ Tasks    │   │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘   │
├─────────────────────────────────────────────────────────┤
│ Quick Actions (horizontal scrollable)                   │
│ [Scan Library] [Sync Metadata] [Add Files] [Settings]  │
├─────────────────────────────────────────────────────────┤
│ Library Overview (2 columns)                            │
│ ┌──────────────────────┐ ┌──────────────────────┐     │
│ │ Movies: 456          │ │ TV Shows: 89         │     │
│ │ Episodes: 2,341      │ │ Total Size: 500 GB   │     │
│ └──────────────────────┘ └──────────────────────┘     │
├─────────────────────────────────────────────────────────┤
│ Storage Distribution (2 columns)                        │
│ ┌──────────────────────┐ ┌──────────────────────┐     │
│ │ Pie Chart            │ │ Recent Activity      │     │
│ │ Movies: 250 GB       │ │ • Scan completed     │     │
│ │ TV Shows: 180 GB     │ │ • Metadata synced    │     │
│ │ Music: 50 GB         │ │ • New content added  │     │
│ │ Other: 20 GB         │ │                      │     │
│ └──────────────────────┘ └──────────────────────┘     │
└─────────────────────────────────────────────────────────┘
```

**Enhancements**:
- Better visual hierarchy
- Improved stat cards with better spacing
- Quick actions as horizontal scrollable buttons
- Enhanced charts with better colors
- Recent activity with timestamps
- Better responsive design

---

## Visual Enhancements

### 1. Micro-interactions
- Smooth button hover effects (scale + shadow)
- Card hover elevation
- Smooth transitions on all interactive elements
- Loading spinners with smooth animations
- Toast notifications with slide-in animations

### 2. Visual Feedback
- Proper focus states for keyboard navigation
- Loading states with skeleton screens
- Error states with clear messaging
- Success states with checkmarks
- Disabled states with reduced opacity

### 3. Dark Mode Support
- Complete dark mode color scheme
- Smooth theme transition
- Persistent theme preference
- Proper contrast ratios for accessibility

### 4. Responsive Design
- Mobile-first approach
- Breakpoints: 640px (sm), 768px (md), 1024px (lg), 1280px (xl)
- Touch-friendly interactive elements (min 44px)
- Optimized layouts for each breakpoint

---

## Implementation Phases

### Phase 0: Legacy Component Audit & Deprecation (Prerequisite)
**Critical: Must complete before Phase 1**

- [ ] Audit all existing components and identify non-conforming ones
- [ ] Create deprecation list with migration paths
- [ ] Add deprecation warnings to legacy components
- [ ] Document which new components replace which old ones
- [ ] Create linting rules to prevent new usage of deprecated components
- [ ] Plan removal timeline (remove after Phase 3 completion)

**Components to Deprecate**:
- All custom styled components outside design system
- Components with hardcoded colors/spacing
- Legacy button styles not matching design system
- Non-standard card layouts
- Custom form inputs not using design system
- Any component with inline styles

**Key Principle**: After Phase 0, **no new code should use deprecated components**. The design system becomes the single source of truth.

### Phase 1: Design System Foundation
- [ ] Update Tailwind configuration with new color palette
- [ ] Create design tokens CSS variables
- [ ] Update typography system
- [ ] Create spacing and shadow utilities
- [ ] Add dark mode support
- [ ] Create deprecation guidelines document
- [ ] Set up ESLint rules to enforce design system usage

### Phase 2: Core Components
- [ ] Create/update Card component
- [ ] Create/update Button component
- [ ] Create Badge component
- [ ] Create DataTable component
- [ ] Create Input components
- [ ] Create Navigation components

### Phase 3: Layout Modernization
- [ ] Redesign Header component
- [ ] Redesign Sidebar component
- [ ] Update MainLayout structure
- [ ] Add breadcrumb navigation
- [ ] Implement dark mode toggle
- [ ] **Remove deprecated components** (after Phase 3)

### Phase 4: Configuration Status Bar & Empty States
**Critical: Must implement before feature pages**

- [ ] Create ConfigurationStatusBar component
- [ ] Implement configuration status detection
- [ ] Create empty state components (Nothing here, yet)
- [ ] Remove all dummy/placeholder data from codebase
- [ ] Add configuration checks to all feature pages
- [ ] Create configuration guidance system

**Configuration Status Bar Features**:
- Display at top of UI
- Show incomplete configurations
- List required setup steps
- Display missing API keys/settings
- Provide action links to configuration pages
- Auto-hide when all configurations complete

### Phase 5: Dashboard Enhancement
- [ ] Update StatCard styling
- [ ] Enhance LibraryStats component
- [ ] Improve QuickActions layout
- [ ] Update StorageChart styling
- [ ] Enhance RecentActivity component
- [ ] Implement empty state for dashboard
- [ ] Remove dummy data from dashboard

### Phase 6: Feature Pages
- [ ] Create Movies listing page with empty state
- [ ] Create Movies detail page
- [ ] Create TV Shows listing page with empty state
- [ ] Create TV Shows detail page
- [ ] Add filtering and sorting
- [ ] Implement configuration checks

### Phase 7: Polish & Testing
- [ ] Add micro-interactions
- [ ] Implement loading states
- [ ] Add error handling UI
- [ ] Test responsive design
- [ ] Accessibility audit
- [ ] Performance optimization

---

## Key Design Principles

1. **Modern Aesthetics**: Clean, contemporary design with proper spacing and typography
2. **User-Centric**: Intuitive navigation and clear visual hierarchy
3. **Functional**: Every design decision serves a purpose
4. **Accessible**: WCAG 2.1 AA compliance
5. **Responsive**: Works seamlessly on all devices
6. **Performant**: Optimized animations and transitions
7. **Consistent**: Unified design language throughout
8. **Dark Mode Ready**: Full support for light and dark themes

---

## Success Metrics

- ✅ Modern, professional appearance
- ✅ Improved user engagement with better visual feedback
- ✅ Faster navigation with clearer information hierarchy
- ✅ Better mobile experience
- ✅ Accessibility compliance
- ✅ Consistent design language
- ✅ Smooth animations and transitions
- ✅ Dark mode support

---

## Next Steps

1. Review and approve this plan
2. Proceed with Phase 1 (Design System Foundation)
3. Implement components phase by phase
4. Test thoroughly at each phase
5. Gather user feedback and iterate
