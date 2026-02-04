# Media Management Web Tool - React UI Architecture

## Overview

This document provides comprehensive design specifications for the React-based frontend application for the media management web tool.

---

## 1. Frontend Technology Stack

### 1.1 Core Framework & Libraries

| Technology | Version | Purpose | Rationale |
|-----------|---------|---------|-----------|
| React | 18.x | UI framework | Modern, component-based, large ecosystem |
| TypeScript | 5.x | Type safety | Catch errors at compile time, better IDE support |
| Vite | 5.x | Build tool | Fast development, optimized production builds |
| React Router | 6.x | Routing | Client-side navigation, nested routes |
| TanStack Query | 5.x | Data fetching | Caching, synchronization, background updates |
| Zustand | 4.x | State management | Lightweight, simple API, minimal boilerplate |
| Axios | 1.x | HTTP client | Interceptors, request/response handling |
| Tailwind CSS | 3.x | Styling | Utility-first, responsive, customizable |
| Shadcn/ui | Latest | Component library | Accessible, customizable, Tailwind-based |
| React Hook Form | 7.x | Form handling | Performant, flexible, minimal re-renders |
| Zod | 3.x | Schema validation | Type-safe validation, TypeScript integration |

### 1.2 Development Tools

| Tool | Purpose |
|------|---------|
| ESLint | Code linting and quality |
| Prettier | Code formatting |
| Vitest | Unit testing |
| React Testing Library | Component testing |
| Storybook | Component documentation |
| Husky | Git hooks |

---

## 2. Project Structure

### 2.1 Directory Organization

```
frontend/
├── public/
│   ├── favicon.ico
│   └── manifest.json
│
├── src/
│   ├── main.tsx                    # Application entry point
│   ├── App.tsx                     # Root component
│   ├── index.css                   # Global styles
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── Header.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── NotFound.tsx
│   │   │
│   │   ├── layout/
│   │   │   ├── MainLayout.tsx
│   │   │   ├── AuthLayout.tsx
│   │   │   └── DashboardLayout.tsx
│   │   │
│   │   ├── movies/
│   │   │   ├── MovieList.tsx
│   │   │   ├── MovieCard.tsx
│   │   │   ├── MovieDetail.tsx
│   │   │   ├── MovieForm.tsx
│   │   │   ├── MovieSearch.tsx
│   │   │   └── MovieGrid.tsx
│   │   │
│   │   ├── tv-shows/
│   │   │   ├── TVShowList.tsx
│   │   │   ├── TVShowCard.tsx
│   │   │   ├── TVShowDetail.tsx
│   │   │   ├── SeasonList.tsx
│   │   │   ├── EpisodeList.tsx
│   │   │   └── TVShowForm.tsx
│   │   │
│   │   ├── search/
│   │   │   ├── SearchBar.tsx
│   │   │   ├── SearchResults.tsx
│   │   │   ├── AdvancedSearch.tsx
│   │   │   └── FilterPanel.tsx
│   │   │
│   │   ├── dashboard/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── StatCard.tsx
│   │   │   ├── RecentActivity.tsx
│   │   │   ├── LibraryStats.tsx
│   │   │   └── QuickActions.tsx
│   │   │
│   │   ├── files/
│   │   │   ├── FileQueue.tsx
│   │   │   ├── FileQueueItem.tsx
│   │   │   ├── FileUpload.tsx
│   │   │   └── FileDetails.tsx
│   │   │
│   │   └── settings/
│   │       ├── Settings.tsx
│   │       ├── GeneralSettings.tsx
│   │       ├── APISettings.tsx
│   │       ├── MonitoringSettings.tsx
│   │       └── CacheSettings.tsx
│   │
│   ├── pages/
│   │   ├── HomePage.tsx
│   │   ├── MoviesPage.tsx
│   │   ├── TVShowsPage.tsx
│   │   ├── SearchPage.tsx
│   │   ├── DashboardPage.tsx
│   │   ├── SettingsPage.tsx
│   │   ├── NotFoundPage.tsx
│   │   └── ErrorPage.tsx
│   │
│   ├── hooks/
│   │   ├── useMovies.ts
│   │   ├── useTVShows.ts
│   │   ├── useSearch.ts
│   │   ├── useFileQueue.ts
│   │   ├── useCache.ts
│   │   ├── useDebounce.ts
│   │   ├── usePagination.ts
│   │   └── useLocalStorage.ts
│   │
│   ├── services/
│   │   ├── api.ts                  # Axios instance and config
│   │   ├── movieService.ts         # Movie API calls
│   │   ├── tvShowService.ts        # TV show API calls
│   │   ├── searchService.ts        # Search API calls
│   │   ├── fileService.ts          # File management API calls
│   │   ├── cacheService.ts         # Cache management API calls
│   │   └── healthService.ts        # Health check API calls
│   │
│   ├── store/
│   │   ├── index.ts                # Zustand store setup
│   │   ├── movieStore.ts           # Movie state
│   │   ├── tvShowStore.ts          # TV show state
│   │   ├── searchStore.ts          # Search state
│   │   ├── uiStore.ts              # UI state (modals, notifications)
│   │   └── settingsStore.ts        # User settings
│   │
│   ├── types/
│   │   ├── index.ts                # Type exports
│   │   ├── movie.ts                # Movie types
│   │   ├── tvshow.ts               # TV show types
│   │   ├── file.ts                 # File types
│   │   ├── api.ts                  # API response types
│   │   └── common.ts               # Common types
│   │
│   ├── utils/
│   │   ├── formatters.ts           # Date, number formatting
│   │   ├── validators.ts           # Input validation
│   │   ├── constants.ts            # App constants
│   │   ├── helpers.ts              # Utility functions
│   │   └── errorHandler.ts         # Error handling
│   │
│   ├── config/
│   │   ├── api.config.ts           # API configuration
│   │   ├── theme.config.ts         # Theme configuration
│   │   └── constants.config.ts     # App constants
│   │
│   └── styles/
│       ├── globals.css
│       ├── variables.css
│       └── animations.css
│
├── tests/
│   ├── unit/
│   ├── integration/
│   └── e2e/
│
├── .env.example
├── .eslintrc.cjs
├── .prettierrc
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── package.json
└── README.md
```

---

## 3. Component Architecture

### 3.1 Component Hierarchy

```
App
├── MainLayout
│   ├── Header
│   │   ├── Logo
│   │   ├── SearchBar
│   │   └── UserMenu
│   ├── Sidebar
│   │   ├── Navigation
│   │   └── QuickLinks
│   ├── MainContent
│   │   ├── HomePage
│   │   ├── MoviesPage
│   │   │   ├── MovieList
│   │   │   │   └── MovieCard (multiple)
│   │   │   ├── FilterPanel
│   │   │   └── Pagination
│   │   ├── TVShowsPage
│   │   │   ├── TVShowList
│   │   │   │   └── TVShowCard (multiple)
│   │   │   ├── FilterPanel
│   │   │   └── Pagination
│   │   ├── SearchPage
│   │   │   ├── SearchBar
│   │   │   ├── AdvancedSearch
│   │   │   └── SearchResults
│   │   ├── DashboardPage
│   │   │   ├── StatCard (multiple)
│   │   │   ├── RecentActivity
│   │   │   ├── LibraryStats
│   │   │   └── QuickActions
│   │   ├── SettingsPage
│   │   │   ├── GeneralSettings
│   │   │   ├── APISettings
│   │   │   ├── MonitoringSettings
│   │   │   └── CacheSettings
│   │   └── MovieDetail/TVShowDetail
│   │       ├── MediaHeader
│   │       ├── MediaInfo
│   │       ├── FileList
│   │       └── RelatedMedia
│   └── Footer
└── Modals
    ├── ConfirmDialog
    ├── ErrorModal
    └── NotificationCenter
```

### 3.2 Component Types

**Presentational Components:**
- `MovieCard` - Displays movie information
- `TVShowCard` - Displays TV show information
- `StatCard` - Displays statistics
- `FileQueueItem` - Displays file queue entry

**Container Components:**
- `MovieList` - Fetches and displays movies
- `TVShowList` - Fetches and displays TV shows
- `SearchResults` - Handles search logic and display
- `Dashboard` - Aggregates dashboard data

**Layout Components:**
- `MainLayout` - Primary layout wrapper
- `DashboardLayout` - Dashboard-specific layout
- `AuthLayout` - Authentication pages layout

---

## 4. State Management

### 4.1 Zustand Store Structure

**Movie Store:**
```typescript
interface MovieStore {
  movies: Movie[];
  selectedMovie: Movie | null;
  loading: boolean;
  error: string | null;
  pagination: PaginationState;
  filters: MovieFilters;
  
  // Actions
  fetchMovies: (page: number, filters: MovieFilters) => Promise<void>;
  selectMovie: (id: number) => void;
  addMovie: (movie: Movie) => void;
  updateMovie: (id: number, movie: Partial<Movie>) => void;
  deleteMovie: (id: number) => void;
  setFilters: (filters: MovieFilters) => void;
}
```

**TV Show Store:**
```typescript
interface TVShowStore {
  tvShows: TVShow[];
  selectedShow: TVShow | null;
  selectedSeason: Season | null;
  loading: boolean;
  error: string | null;
  pagination: PaginationState;
  filters: TVShowFilters;
  
  // Actions
  fetchTVShows: (page: number, filters: TVShowFilters) => Promise<void>;
  selectShow: (id: number) => void;
  selectSeason: (seasonId: number) => void;
  addTVShow: (show: TVShow) => void;
  updateTVShow: (id: number, show: Partial<TVShow>) => void;
  deleteTVShow: (id: number) => void;
  setFilters: (filters: TVShowFilters) => void;
}
```

**UI Store:**
```typescript
interface UIStore {
  sidebarOpen: boolean;
  notifications: Notification[];
  modals: {
    confirmDialog: boolean;
    errorModal: boolean;
    editModal: boolean;
  };
  
  // Actions
  toggleSidebar: () => void;
  addNotification: (notification: Notification) => void;
  removeNotification: (id: string) => void;
  openModal: (modalName: string) => void;
  closeModal: (modalName: string) => void;
}
```

### 4.2 Data Fetching with TanStack Query

```typescript
// Example hook
export const useMovies = (page: number, filters: MovieFilters) => {
  return useQuery({
    queryKey: ['movies', page, filters],
    queryFn: () => movieService.getMovies(page, filters),
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000,    // 10 minutes
  });
};
```

---

## 5. Routing Structure

### 5.1 Route Configuration

```typescript
const routes = [
  {
    path: '/',
    element: <MainLayout />,
    children: [
      {
        index: true,
        element: <HomePage />,
      },
      {
        path: 'movies',
        element: <MoviesPage />,
      },
      {
        path: 'movies/:id',
        element: <MovieDetail />,
      },
      {
        path: 'tv-shows',
        element: <TVShowsPage />,
      },
      {
        path: 'tv-shows/:id',
        element: <TVShowDetail />,
      },
      {
        path: 'search',
        element: <SearchPage />,
      },
      {
        path: 'dashboard',
        element: <DashboardPage />,
      },
      {
        path: 'settings',
        element: <SettingsPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
];
```

---

## 6. API Integration

### 6.1 Axios Configuration

```typescript
// services/api.ts
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use((config) => {
  // Add auth token if available
  const token = localStorage.getItem('authToken');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle errors globally
    if (error.response?.status === 401) {
      // Handle unauthorized
    }
    return Promise.reject(error);
  }
);
```

### 6.2 Service Layer

```typescript
// services/movieService.ts
export const movieService = {
  getMovies: (page: number, filters: MovieFilters) =>
    api.get('/movies', { params: { page, ...filters } }),
  
  getMovieById: (id: number) =>
    api.get(`/movies/${id}`),
  
  createMovie: (data: CreateMovieRequest) =>
    api.post('/movies', data),
  
  updateMovie: (id: number, data: UpdateMovieRequest) =>
    api.put(`/movies/${id}`, data),
  
  deleteMovie: (id: number) =>
    api.delete(`/movies/${id}`),
  
  syncMetadata: (id: number) =>
    api.post(`/movies/${id}/sync-metadata`),
};
```

---

## 7. Key Features & Pages

### 7.1 Home Page

**Components:**
- Welcome banner
- Quick stats (total movies, TV shows, files)
- Recent additions
- Quick actions (add movie, add TV show, scan files)

**Features:**
- Overview of library
- Quick navigation
- Recent activity feed

### 7.2 Movies Page

**Components:**
- Search bar
- Filter panel (genre, year, rating)
- Movie grid/list view toggle
- Movie cards with poster, title, rating
- Pagination

**Features:**
- Browse all movies
- Filter and search
- Sort by title, year, rating, date added
- View movie details
- Edit movie metadata
- Delete movie

### 7.3 TV Shows Page

**Components:**
- Search bar
- Filter panel (genre, status)
- TV show grid/list view toggle
- TV show cards
- Pagination

**Features:**
- Browse all TV shows
- Filter and search
- View seasons and episodes
- Edit TV show metadata
- Delete TV show

### 7.4 Movie/TV Show Detail Page

**Components:**
- Media header (poster, title, rating)
- Media information (plot, genres, runtime, etc.)
- File list with technical details
- Related media recommendations
- Action buttons (edit, delete, sync metadata)

**Features:**
- View complete media information
- View associated files
- Edit metadata
- Sync with external APIs
- View file technical details

### 7.5 Search Page

**Components:**
- Search bar with autocomplete
- Advanced search filters
- Search results (movies and TV shows)
- Result count and relevance

**Features:**
- Global search across movies and TV shows
- Advanced filtering
- Autocomplete suggestions
- Result highlighting

### 7.6 Dashboard Page

**Components:**
- Library statistics (total items, storage used)
- File queue status
- Recent activity
- System health
- Quick actions

**Features:**
- Overview of system status
- File processing queue
- Recent additions
- System statistics

### 7.7 Settings Page

**Components:**
- General settings (theme, language)
- API settings (OMDB, TVDB keys)
- Monitoring settings (watch paths, patterns)
- Cache settings (clear cache, cache stats)

**Features:**
- Configure application settings
- Manage API keys
- Configure file monitoring
- Manage cache

---

## 8. UI/UX Design Patterns

### 8.1 Design System

**Color Palette:**
- Primary: #3B82F6 (Blue)
- Secondary: #8B5CF6 (Purple)
- Success: #10B981 (Green)
- Warning: #F59E0B (Amber)
- Error: #EF4444 (Red)
- Neutral: #6B7280 (Gray)

**Typography:**
- Heading 1: 32px, Bold
- Heading 2: 24px, Bold
- Heading 3: 20px, Bold
- Body: 16px, Regular
- Small: 14px, Regular
- Caption: 12px, Regular

**Spacing:**
- xs: 4px
- sm: 8px
- md: 16px
- lg: 24px
- xl: 32px
- 2xl: 48px

### 8.2 Common Patterns

**Loading States:**
- Skeleton loaders for content
- Spinner for actions
- Progress bar for file uploads

**Error Handling:**
- Toast notifications for errors
- Error boundaries for component failures
- Fallback UI for failed requests

**Empty States:**
- Helpful message when no data
- Call-to-action to add content
- Illustration or icon

**Confirmation Dialogs:**
- Confirm destructive actions
- Clear action and consequence
- Cancel and confirm buttons

### 8.3 Responsive Design

**Breakpoints:**
- Mobile: < 640px
- Tablet: 640px - 1024px
- Desktop: > 1024px

**Mobile Optimizations:**
- Collapsible sidebar
- Touch-friendly buttons (min 44px)
- Simplified navigation
- Stack layout vertically

---

## 9. Form Handling

### 9.1 Form Validation

```typescript
// Using Zod for schema validation
const movieFormSchema = z.object({
  title: z.string().min(1, 'Title is required'),
  year: z.number().min(1900).max(new Date().getFullYear()),
  plot: z.string().optional(),
  rating: z.number().min(0).max(10).optional(),
  runtime: z.number().positive().optional(),
  genres: z.array(z.string()).optional(),
});

type MovieFormData = z.infer<typeof movieFormSchema>;
```

### 9.2 Form Components

**Movie Form:**
- Title input
- Year input
- Plot textarea
- Rating input
- Runtime input
- Genre multi-select
- Submit button

**TV Show Form:**
- Title input
- Plot textarea
- Rating input
- Status select
- Genres multi-select
- Submit button

---

## 10. Performance Optimization

### 10.1 Code Splitting

```typescript
// Lazy load pages
const HomePage = lazy(() => import('./pages/HomePage'));
const MoviesPage = lazy(() => import('./pages/MoviesPage'));
const TVShowsPage = lazy(() => import('./pages/TVShowsPage'));
```

### 10.2 Image Optimization

- Use Next.js Image component or similar
- Lazy load images
- Responsive image sizes
- WebP format with fallback

### 10.3 Caching Strategy

- TanStack Query for API response caching
- LocalStorage for user preferences
- Service Worker for offline support (optional)

### 10.4 Bundle Optimization

- Tree shaking
- Minification
- Code splitting
- Lazy loading

---

## 11. Testing Strategy

### 11.1 Unit Tests

```typescript
// Example test
describe('MovieCard', () => {
  it('renders movie information', () => {
    const movie = { id: 1, title: 'Test', year: 2024 };
    render(<MovieCard movie={movie} />);
    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});
```

### 11.2 Integration Tests

- Test component interactions
- Test API integration
- Test state management

### 11.3 E2E Tests

- Test complete user workflows
- Test navigation
- Test form submissions

---

## 12. Accessibility

### 12.1 WCAG Compliance

- Semantic HTML
- ARIA labels
- Keyboard navigation
- Color contrast
- Focus management

### 12.2 Accessibility Features

- Screen reader support
- Keyboard shortcuts
- High contrast mode
- Text size adjustment

---

## 13. Docker Configuration for Frontend

### 13.1 Dockerfile

```dockerfile
# Build stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist
EXPOSE 3000
CMD ["serve", "-s", "dist", "-l", "3000"]
```

### 13.2 Docker Compose Integration

```yaml
frontend:
  build:
    context: ./frontend
    dockerfile: Dockerfile
  container_name: media-management-frontend
  ports:
    - "3000:3000"
  environment:
    - VITE_API_URL=http://app:8000/api
  depends_on:
    - app
  networks:
    - media-network
```

---

## 14. Environment Configuration

### 14.1 Environment Variables

```env
# .env.example
VITE_API_URL=http://localhost:8000/api
VITE_APP_NAME=Media Management
VITE_APP_VERSION=1.0.0
VITE_LOG_LEVEL=info
```

---

## 15. Development Workflow

### 15.1 Development Server

```bash
npm run dev
```

### 15.2 Build for Production

```bash
npm run build
```

### 15.3 Preview Production Build

```bash
npm run preview
```

### 15.4 Linting and Formatting

```bash
npm run lint
npm run format
```

---

## 16. Browser Support

- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile browsers: Latest versions

---

## 17. Security Considerations

### 17.1 Frontend Security

- XSS prevention (React escapes by default)
- CSRF protection (token in headers)
- Secure storage of sensitive data
- Content Security Policy headers

### 17.2 API Communication

- HTTPS only in production
- Secure cookie handling
- Request/response validation
- Error message sanitization

---

## 18. Monitoring & Analytics

### 18.1 Error Tracking

- Sentry integration for error reporting
- User session tracking
- Performance monitoring

### 18.2 Analytics

- Page view tracking
- User interaction tracking
- Feature usage analytics

---

## 19. Future Enhancements

### 19.1 Potential Features

- Dark mode toggle
- User authentication
- Multi-user support
- Watchlist functionality
- Rating and reviews
- Social sharing
- Advanced recommendations
- Mobile app (React Native)

### 19.2 Performance Improvements

- Virtual scrolling for large lists
- Infinite scroll pagination
- Progressive image loading
- Service Worker caching

---

## 20. Project Dependencies

### 20.1 Core Dependencies

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "@tanstack/react-query": "^5.28.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.48.0",
    "zod": "^3.22.0",
    "@hookform/resolvers": "^3.3.0"
  },
  "devDependencies": {
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.3.0",
    "postcss": "^8.4.0",
    "autoprefixer": "^10.4.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0"
  }
}
```

---

## Conclusion

This React UI architecture provides a modern, scalable foundation for the media management web tool frontend. The design emphasizes:

- **Component Reusability:** Well-organized, modular components
- **State Management:** Simple, efficient state handling with Zustand
- **Performance:** Optimized data fetching and rendering
- **User Experience:** Intuitive navigation and responsive design
- **Maintainability:** Clear structure and TypeScript type safety
- **Accessibility:** WCAG compliance and inclusive design

The architecture is ready for implementation and can scale to support additional features and users.
