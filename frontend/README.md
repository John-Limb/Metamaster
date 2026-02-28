# Metamaster Frontend

A modern React-based media library management frontend for organizing and managing your movie and TV show collection.

## 🚀 Quick Start

### Prerequisites

- Node.js >= 18.0.0
- npm or yarn
- Backend API running (see root [README.md](../README.md))

### Installation

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Start development server
npm run dev
```

The application will be available at `http://localhost:5173`

### Environment Variables

Create a `.env` file based on `.env.example`:

| Variable | Description | Default |
|----------|-------------|---------|
| `VITE_API_URL` | Backend API base URL | `http://localhost:8000/api/v1` |
| `VITE_APP_NAME` | Application name | `Metamaster` |
| `VITE_ENABLE_LOGGING` | Enable console logging | `true` |

## 📁 Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Reusable UI components
│   │   ├── dashboard/      # Dashboard widgets and views
│   │   ├── features/        # Feature-specific modules
│   │   ├── file/            # File management components
│   │   ├── layout/          # Layout components
│   │   ├── queue/           # Task queue components
│   │   ├── search/          # Search components
│   │   └── settings/        # Settings components
│   ├── hooks/               # Custom React hooks
│   ├── services/            # API service layer
│   ├── stores/              # Zustand state stores
│   ├── types/               # TypeScript type definitions
│   ├── utils/               # Utility functions
│   ├── App.tsx              # Main application component
│   └── main.tsx             # Application entry point
├── .github/                 # GitHub workflows
└── docs/                   # Documentation files
```

## 🧩 Component Documentation

### Common Components

Located in [`src/components/common/`](src/components/common/), these are reusable UI components used throughout the application:

- **ApiErrorBoundary** - Error boundary for API-related errors
- **Breadcrumb** - Navigation breadcrumb component
- **ConfirmDialog** - Confirmation modal dialog
- **ErrorBoundary** - General error boundary
- **ErrorModal** - Error display modal
- **LoadingSpinner** - Loading indicator
- **NotFound** - 404 page component
- **Toast** - Toast notification component

### Dashboard Components

Located in [`src/components/dashboard/`](src/components/dashboard/):

- **Dashboard** - Main dashboard view
- **LibraryStats** - Library statistics display
- **QuickActions** - Quick action buttons
- **RecentActivity** - Activity feed
- **StatCard** - Statistical data card
- **StorageChart** - Storage usage visualization

### File Components

Located in [`src/components/file/`](src/components/file/):

- **FileCard** - File preview card
- **FileExplorer** - File browser
- **FileGrid** - Grid view of files
- **FileList** - List view of files
- **FileTree** - Tree view navigation
- **BatchOperationModal** - Batch operations dialog

## 🔌 API Integration

### Service Layer

API services are located in [`src/services/`](src/services/). Each feature has its own service module:

```typescript
// Example: Fetching movies
import { movieService } from '@/services/movieService';

const fetchMovies = async () => {
  try {
    const response = await movieService.getMovies();
    return response.data;
  } catch (error) {
    console.error('Failed to fetch movies:', error);
    throw error;
  }
};
```

### Error Handling

The application uses a centralized error handling pattern with `ApiError` types:

```typescript
import type { ApiError } from '@/types';

interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}
```

Use the `errorNotificationManager` utility for displaying errors to users:

```typescript
import { errorNotificationManager } from '@/utils/errorNotification';

errorNotificationManager.showError(error, 'ComponentName');
```

### Response Types

All API responses follow a consistent format:

```typescript
interface ApiResponse<T> {
  data: T;
  message?: string;
  status: number;
}
```

## 📦 State Management

### Zustand Stores

State management is handled using Zustand. Stores are located in [`src/stores/`](src/stores/).

```typescript
import { create } from 'zustand';

interface AppState {
  isLoading: boolean;
  theme: 'light' | 'dark';
  setTheme: (theme: 'light' | 'dark') => void;
}

export const useAppStore = create<AppState>((set) => ({
  isLoading: false,
  theme: 'light',
  setTheme: (theme) => set({ theme }),
}));
```

### Store Patterns

1. **Slices Pattern** - For complex state, split into smaller slices
2. **Async Actions** - Handle async operations within stores
3. **Selectors** - Memoize selectors for performance

```typescript
// Store slice example
interface MovieSlice {
  movies: Movie[];
  setMovies: (movies: Movie[]) => void;
}

const createMovieSlice = (set) => ({
  movies: [],
  setMovies: (movies) => set({ movies }),
});
```

## 🧪 Testing

### Unit Tests (Vitest)

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Watch mode
npm run test:watch

# UI mode
npm run test:ui
```

### E2E Tests (Playwright)

```bash
# Run E2E tests
npm run test:e2e

# Open Playwright UI
npm run test:e2e:ui

# View test reports
npm run test:e2e:report
```

### Security Tests

```bash
# Run security tests
npm run test:security
```

### Performance Tests

```bash
# Run performance tests
npm run test:performance
```

### Coverage Reports

Coverage reports are generated in `coverage/` directory. Key metrics:

- **Statements**: 80% minimum
- **Branches**: 80% minimum
- **Functions**: 80% minimum
- **Lines**: 80% minimum

## 🛠️ Development

### Code Style

- **ESLint** - TypeScript and React linting
- **Prettier** - Code formatting
- **Husky** - Pre-commit hooks

```bash
# Lint code
npm run lint

# Auto-fix lint issues
npm run lint:fix

# Format code
npm run format
```

### Build

```bash
# Build for production
npm run build

# Build with bundle analysis
npm run build:analyze

# Preview production build
npm run preview
```

### Docker

```dockerfile
# Build image
docker build -t metamaster-frontend .

# Run container
docker run -p 80:80 metamaster-frontend
```

## 🚀 Deployment

### Build for Production

```bash
npm run build
```

### Preview Production Build

```bash
npm run preview
```

### Docker Deployment

```bash
# Build and tag
docker build -t metamaster-frontend:latest .

# Run with environment
docker run -e VITE_API_URL=http://api:8000 metamaster-frontend
```

## 🧩 Troubleshooting

### Common Issues

#### 1. **API not reachable**

```
Error: Network Error / CORS Error
```

**Solution:**
- Verify backend is running
- Check `VITE_API_URL` environment variable
- Verify CORS settings on backend

#### 2. **Dependencies not installing**

```
Error: package.json not found / Invalid package name
```

**Solution:**
- Ensure you're in the `frontend/` directory
- Clear npm cache: `npm cache clean --force`
- Delete `node_modules/` and reinstall: `rm -rf node_modules && npm install`

#### 3. **TypeScript errors**

```
Error: TypeScript: No matching variant
```

**Solution:**
- Run `npm run lint:fix` to auto-fix common issues
- Restart TypeScript server in your IDE
- Check `tsconfig.json` configuration

#### 4. **Tests failing**

```
Error: Test failed
```

**Solution:**
- Check if backend services are running (for integration tests)
- Verify test environment variables
- Run `npm run test:ui` for visual debugging

### Getting Help

- Check existing [issues](../.github/ISSUE_TEMPLATE/)
- Review [API documentation](../docs/API_REFERENCE.md)
- Consult the [troubleshooting guide](../docs/USER_TROUBLESHOOTING.md)

## 📄 License

See the root [LICENSE](../LICENSE) file for license information.
