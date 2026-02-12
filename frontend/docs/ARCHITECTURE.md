# Frontend Architecture

This document provides a comprehensive overview of the Metamaster frontend architecture, including project structure, component patterns, state management, and data flow.

## 📁 Project Structure Overview

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/           # Shared UI components (buttons, modals, etc.)
│   │   ├── dashboard/        # Dashboard-specific components
│   │   ├── features/          # Feature modules (movies, tvshows)
│   │   ├── file/             # File management components
│   │   ├── layout/           # Layout wrappers (Header, Sidebar, etc.)
│   │   ├── queue/           # Task queue components
│   │   ├── search/           # Search and filter components
│   │   └── settings/         # Settings pages
│   ├── hooks/                # Custom React hooks
│   ├── services/             # API service layer
│   ├── stores/               # Zustand state stores
│   ├── types/                # TypeScript definitions
│   ├── utils/                # Utility functions
│   ├── App.tsx               # Root component
│   └── main.tsx              # Entry point
├── .storybook/              # Storybook configuration
├── .github/                  # CI/CD workflows
└── docs/                     # Documentation
```

## 🧩 Component Hierarchy and Patterns

### Component Organization

Components are organized by scope and reusability:

1. **Common Components** (`src/components/common/`)
   - Highly reusable, dumb components
   - No direct dependencies on features
   - Examples: `Button`, `Modal`, `Toast`, `LoadingSpinner`

2. **Feature Components** (`src/components/features/`)
   - Complex, feature-specific components
   - May contain business logic
   - Examples: `MoviesModule`, `TvShowsModule`

3. **Domain Components** (`src/components/dashboard/`, `src/components/file/`)
   - Components specific to a domain
   - Composite components using common elements
   - Examples: `Dashboard`, `FileExplorer`, `QueuePanel`

### Component Patterns

#### Compound Components

Used for related components that share state:

```typescript
// Toast example
interface ToastProps extends ToastType {
  onClose: () => void;
}

export const Toast: React.FC<ToastProps> = ({ /* ... */ });
export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemoveToast });
```

#### Render Props

Used when flexibility in rendering is needed:

```typescript
interface ConfirmDialogProps {
  isOpen: boolean;
  renderContent?: (state: DialogState) => React.ReactNode;
}
```

#### Higher-Order Components (Legacy)

Some components may use HOC patterns for cross-cutting concerns.

## 📦 State Management Flow

### Zustand Store Architecture

```
┌─────────────────────────────────────────────────┐
│                 Application State               │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐            │
│  │   AppStore   │  │  MovieStore  │            │
│  │  (Global UI) │  │ (Movie Data) │            │
│  └──────────────┘  └──────────────┘            │
│  ┌──────────────┐  ┌──────────────┐            │
│  │   QueueStore │  │  SearchStore │            │
│  │ (Task Queue) │  │ (Search State)           │
│  └──────────────┘  └──────────────┘            │
└─────────────────────────────────────────────────┘
```

### Store Structure

```typescript
// Example store pattern
interface AppSlice {
  theme: 'light' | 'dark';
  sidebarOpen: boolean;
  setTheme: (theme: 'light' | 'dark') => void;
  toggleSidebar: () => void;
}

interface MovieSlice {
  movies: Movie[];
  loading: boolean;
  fetchMovies: () => Promise<void>;
}

// Combined store
type AppState = AppSlice & MovieSlice;
```

### Data Flow

1. **User Action** → Component
2. **Component** → Store Action
3. **Store** → State Update
4. **Store** → Component Re-render
5. **Component** → UI Update

## 🔌 API Integration Flow

### Service Layer Architecture

```
┌─────────────────────────────────────────────────┐
│                 Components                       │
│  (Dashboard, MoviesModule, etc.)                │
└───────────────────┬─────────────────────────────┘
                    │ method calls
                    ▼
┌─────────────────────────────────────────────────┐
│              Service Layer                      │
│  ┌─────────────┐  ┌─────────────┐              │
│  │ movieService│  │ tvShowService│              │
│  └─────────────┘  └─────────────┘              │
└───────────────────┬─────────────────────────────┘
                    │ axios requests
                    ▼
┌─────────────────────────────────────────────────┐
│              API Client (Axios)                 │
│  ┌─────────────────────────────────────────┐    │
│  │ Interceptors:                          │    │
│  │ - Request (auth, logging)              │    │
│  │ - Response (error handling, caching)   │    │
│  └─────────────────────────────────────────┘    │
└───────────────────┬─────────────────────────────┘
                    │ HTTP requests
                    ▼
┌─────────────────────────────────────────────────┐
│              Backend API                        │
│              (FastAPI)                          │
└─────────────────────────────────────────────────┘
```

### API Service Pattern

```typescript
// service example
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  timeout: 30000,
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    handleApiError(error);
    return Promise.reject(error);
  }
);
```

### Error Handling

Errors are handled through a centralized error boundary and notification system:

1. **ApiErrorBoundary** - Catches API errors in component tree
2. **errorNotificationManager** - Displays errors to users
3. **Toast** - Provides feedback

```typescript
// Error types
interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
```

## 🛤️ Routing Structure

### Route Hierarchy

```
/
├── /                      # Dashboard
├── /movies                # Movies list
│   ├── /:id              # Movie details
├── /tvshows              # TV Shows list
│   ├── /:id              # TV Show details
├── /files                # File explorer
│   ├── /:path*           # Nested paths
├── /queue                # Task queue
├── /settings             # Settings pages
│   ├── /general
│   ├── /api
│   ├── /cache
│   └── /monitoring
└── *                     # 404 Not Found
```

### Route Configuration

```typescript
// Routes are defined using react-router-dom
const routes = [
  { path: '/', element: <Dashboard /> },
  { path: '/movies', element: <MoviesModule /> },
  { path: '/tvshows', element: <TvShowsModule /> },
  { path: '/files', element: <FileExplorer /> },
  { path: '/queue', element: <QueuePanel /> },
  { path: '/settings/*', element: <Settings /> },
];
```

### Layout Structure

```
┌─────────────────────────────────────────────────┐
│  DashboardLayout                                │
│  ┌───────────────────────────────────────────┐  │
│  │ Header (Logo, Search, User Menu)          │  │
│  ├───────────────────────────────────────────┤  │
│  │ Sidebar (Navigation) │ Main Content      │  │
│  │                       │                   │  │
│  │  • Dashboard         │   <Route />        │  │
│  │  • Movies             │                   │  │
│  │  • TV Shows           │                   │  │
│  │  • Files              │                   │  │
│  │  • Queue              │                   │  │
│  │  • Settings           │                   │  │
│  └───────────────────────────────────────────┘  │
│  ┌───────────────────────────────────────────┐  │
│  │ Footer (Version, Status)                  │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

## 🎨 Styling Architecture

### Tailwind CSS

The project uses Tailwind CSS for styling:

```typescript
// tailwind.config.js
export default {
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          // ... more colors
          600: '#0284c7',
          // ... more colors
        },
      },
    },
  },
};
```

### CSS Custom Properties

Used for theming:

```css
:root {
  --color-primary: #0284c7;
  --color-secondary: #64748b;
  --border-radius: 0.5rem;
}
```

## 🔒 Security Architecture

### Authentication Flow

1. User logs in via backend
2. JWT token stored in localStorage or httpOnly cookie
3. Token included in API requests via Authorization header
4. Token refresh handled by axios interceptor

### Security Features

- **XSS Prevention** - Input sanitization, Content Security Policy
- **CSRF Protection** - Anti-CSRF tokens
- **Error Message Sanitization** - No sensitive data in error messages
- **Input Validation** - Zod schemas for all inputs

## 📊 Performance Optimizations

### Code Splitting

```typescript
// Lazy load routes
const MoviesModule = lazy(() => import('@/components/features/movies/MoviesModule'));
const TvShowsModule = lazy(() => import('@/components/features/tvshows/TvShowsModule'));
```

### Virtualization

Used for large lists (react-virtual):

```typescript
import { useVirtualizer } from 'react-virtual';

const rowVirtualizer = useVirtualizer({
  count: items.length,
  getScrollElement: () => parentRef.current,
  estimateSize: () => 50,
});
```

### Memoization

- `useMemo` for expensive computations
- `useCallback` for event handlers
- `React.memo` for component optimization

## 🧪 Testing Strategy

### Test Pyramid

```
        ┌───────────┐
        │   E2E     │  ← Playwright (critical user paths)
        └───────────┘
   ┌────────────┴────────────┐
   │    Integration Tests     │  ← Vitest (component tests)
   └────────────┬────────────┘
   ┌───────────┴───────────┐
   │     Unit Tests        │  ← Vitest (utils, hooks)
   └───────────────────────┘
```

### Test Files

- `*.test.ts` - Unit tests
- `*.test.tsx` - Component tests
- `*.e2e.test.ts` - E2E tests

## 📈 Bundle Analysis

Bundle size is monitored using rollup-plugin-visualizer:

```bash
npm run build:analyze
```

Output: `dist/stats.html` - Visual bundle analysis

## 🔧 Development Workflow

### Code Quality

1. **ESLint** - TypeScript and React best practices
2. **Prettier** - Consistent code formatting
3. **Husky** - Pre-commit hooks
4. **lint-staged** - Staged file linting

### Git Workflow

1. Create feature branch from `develop`
2. Implement changes
3. Add tests
4. Run lint and tests
5. Create PR for review
6. Merge after approval

## 📝 Documentation Generation

### Storybook

Components are documented with Storybook:

```bash
npm run storybook      # Development
npm run build-storybook # Production build
```

### TypeDoc

API documentation generated from TypeScript types:

```bash
npx typedoc --out docs/api src/types/
```

## 🚀 Deployment Pipeline

### CI/CD Flow

```
Push Code → Lint → Test → Build → Deploy
                 ↓
         Storybook Build → GitHub Pages
```

### Environment Matrix

| Environment | Branch | URL |
|------------|--------|-----|
| Development | `develop` | `dev.example.com` |
| Staging | `release/*` | `staging.example.com` |
| Production | `main` | `example.com` |

## 📚 Related Documentation

- [API Reference](../docs/API_REFERENCE.md)
- [User Guide](USER_GUIDE.md)
- [Deployment Guide](../docs/DEPLOYMENT.md)
- [Troubleshooting](../docs/USER_TROUBLESHOOTING.md)
