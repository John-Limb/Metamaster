# Metamaster UI Revamp - Empty States & Configuration Status

## Overview

This document defines the empty state strategy and configuration status system for Metamaster. The application should never display dummy data. Instead, it should show clean, helpful empty states and a prominent configuration status bar that guides users through setup.

---

## Configuration Status Bar

### Purpose
Display incomplete configurations and required setup steps at the top of the UI, guiding users through the setup process.

### Location
- Fixed at the top of the main content area (below header)
- Visible on all pages
- Auto-hides when all configurations are complete

### Design

```
┌─────────────────────────────────────────────────────────────────┐
│ ⚠️  Setup Required: 3 items need configuration                  │
│ • API Key not configured (Configure)                            │
│ • Database connection pending (Setup)                           │
│ • File monitoring disabled (Enable)                             │
│ [Dismiss] [Configure All]                                       │
└─────────────────────────────────────────────────────────────────┘
```

### Configuration Items to Track

#### Critical (Error)
- [ ] API Key configured - Explain to user how to add to docker env file
- [ ] Database connection established - Explain to user how to add to docker env file
- [ ] File system paths configured - Explain to user how to add to docker env file

#### Important (Warning)
- [ ] File monitoring enabled
- [ ] Metadata sources configured
- [ ] Storage location accessible

#### Optional (Info)
- [ ] Dark mode preference set
- [ ] Notification settings configured
- [ ] Advanced options configured

### Behavior

1. **On App Load**:
   - Check all configuration items
   - Display status bar if any items incomplete
   - Show count of incomplete items

2. **On Configuration Change**:
   - Update status bar in real-time
   - Remove item from list when configured
   - Auto-hide when all items complete

3. **User Dismissal**:
   - Allow dismissing individual items
   - Store dismissal preference in localStorage
   - Re-show if configuration becomes invalid

4. **Navigation**:
   - Clicking action links navigates to settings
   - Pre-fill settings form with relevant section
   - Show success message after configuration

---

## Empty States

### General Empty State Component

```typescript
interface EmptyStateProps {
  icon: React.ReactNode
  title: string
  description: string
  action?: {
    label: string
    onClick: () => void
  }
  illustration?: React.ReactNode
}

<EmptyState
  icon={<FilmIcon />}
  title="No Movies Yet"
  description="Start by adding your first movie to the library"
  action={{
    label: "Add Movie",
    onClick: () => navigate('/movies/add')
  }}
/>
```

### Empty State Variants

#### 1. No Data (Initial State)
**When**: Feature has no data and user hasn't started using it

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    🎬                                   │
│                                                         │
│              Nothing here, yet                          │
│                                                         │
│  Start by adding your first movie to the library       │
│                                                         │
│              [+ Add Movie]                              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 2. No Results (Search/Filter)
**When**: Search or filter returns no results

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    🔍                                   │
│                                                         │
│              No results found                           │
│                                                         │
│  Try adjusting your search or filter criteria          │
│                                                         │
│              [Clear Filters]                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 3. Feature Disabled (Configuration Required)
**When**: Feature requires configuration before use

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    ⚙️                                   │
│                                                         │
│              Feature Not Configured                     │
│                                                         │
│  This feature requires setup before you can use it     │
│                                                         │
│              [Configure Now]                            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 4. Error State
**When**: An error occurred loading data

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    ❌                                   │
│                                                         │
│              Something went wrong                       │
│                                                         │
│  Failed to load movies. Please try again.              │
│                                                         │
│              [Retry]  [Report Issue]                    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

#### 5. Loading State
**When**: Data is being fetched

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│                    ⏳                                   │
│                                                         │
│              Loading movies...                          │
│                                                         │
│              [████████░░] 80%                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Empty States by Feature

#### Dashboard
- **Initial**: Show configuration status bar + empty stat cards with "Configure" links
- **After Config**: Show actual data or "No activity yet" message
- **Never**: Show dummy stats or placeholder data

#### Movies Page
- **Initial**: "Nothing here, yet" with "Add Movie" button
- **After Search**: "No movies found" with filter reset option
- **After Filter**: "No movies match your criteria" with filter reset option
- **Error**: "Failed to load movies" with retry button

#### TV Shows Page
- **Initial**: "Nothing here, yet" with "Add Show" button
- **After Search**: "No shows found" with filter reset option
- **After Filter**: "No shows match your criteria" with filter reset option
- **Error**: "Failed to load shows" with retry button

#### Files Page
- **Initial**: "Nothing here, yet" with "Configure file monitoring" link
- **Monitoring Disabled**: "File monitoring is disabled" with "Enable" button
- **No Files Found**: "No files found in configured paths"
- **Error**: "Failed to scan files" with retry button

#### Settings Page
- **Incomplete**: Show configuration status bar with missing items
- **Complete**: Show "All configured" message
- **Errors**: Show validation errors with fix suggestions

---

## Data Loading Strategy

### Never Use Dummy Data
- ❌ Don't load fake data on app start
- ❌ Don't show placeholder movies/shows
- ❌ Don't display mock statistics
- ❌ Don't use Lorem Ipsum text

### Always Check Configuration First
```typescript
// Good: Check configuration before loading data
const MoviesPage = () => {
  const config = useConfigStore()
  
  if (!config.isConfigured) {
    return <EmptyState 
      title="Configuration Required"
      action={{ label: "Configure", onClick: () => navigate('/settings') }}
    />
  }
  
  return <MoviesList />
}

// Bad: Load dummy data regardless of configuration
const MoviesPage = () => {
  const [movies, setMovies] = useState(DUMMY_MOVIES)
  // ...
}
```

### Loading Flow

```
1. Check if feature is configured
   ├─ No → Show "Configure" empty state
   └─ Yes → Continue to step 2

2. Fetch data from API
   ├─ Loading → Show loading state with progress
   ├─ Error → Show error state with retry
   └─ Success → Continue to step 3

3. Check if data is empty
   ├─ Empty → Show "Nothing here, yet" empty state
   └─ Has Data → Display data
```

---

## Implementation Checklist

### Configuration Status Bar
- [x] Create ConfigurationStatusBar component
- [x] Create configuration detection service
- [x] Implement localStorage persistence for dismissals
- [x] Add configuration checks to all pages
- [x] Create settings navigation links
- [x] Add real-time status updates

### Empty States
- [x] Create EmptyState component
- [x] Create EmptyStateIcon component library
- [x] Implement empty state for each feature
- [x] Add loading state with progress
- [x] Add error state with retry
- [x] Add search/filter empty state

### Data Removal
- [ ] Remove all DUMMY_DATA constants
- [ ] Remove mock data from Dashboard
- [ ] Remove mock data from Movies page
- [ ] Remove mock data from TV Shows page
- [ ] Remove mock data from Files page
- [ ] Remove mock data from all components

### Configuration Detection
- [x] Create useConfiguration hook
- [x] Implement API key check
- [x] Implement database connection check
- [x] Implement file path check
- [x] Implement file monitoring check
- [x] Implement metadata source check

---

## User Experience Flow

### First Time User
1. App loads
2. Configuration status bar shows "3 items need configuration"
3. User clicks "Configure All"
4. Navigates to settings page
5. Completes configuration
6. Returns to dashboard
7. Status bar auto-hides
8. Dashboard shows "Nothing here, yet" for each section
9. User can now add content

### Returning User (Configured)
1. App loads
2. Configuration status bar hidden (all configured)
3. Dashboard shows actual data
4. User can browse, search, filter
5. Empty states only appear for search/filter with no results

### User Disables Feature
1. User disables file monitoring in settings
2. Configuration status bar reappears
3. Shows "File monitoring disabled" warning
4. Files page shows "Feature disabled" empty state
5. User can re-enable from settings

---

## Accessibility Considerations

### Empty States
- Use semantic HTML (section, article, etc.)
- Provide descriptive alt text for icons
- Ensure sufficient color contrast
- Make action buttons keyboard accessible
- Announce empty state to screen readers

### Configuration Status Bar
- Use ARIA live region for updates
- Provide clear focus management
- Ensure keyboard navigation
- Use semantic HTML for structure
- Provide skip link to main content

### Loading States
- Use ARIA busy attribute
- Announce loading progress
- Provide cancel option if applicable
- Use semantic loading indicators

---

## Success Criteria

✅ No dummy data displayed anywhere in the UI
✅ Configuration status bar visible and functional
✅ All empty states properly implemented
✅ Configuration checks working correctly
✅ User can complete setup from status bar
✅ Features properly disabled until configured
✅ Smooth transitions between states
✅ Accessibility compliance maintained
