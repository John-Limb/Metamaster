/**
 * Sentry Error Tracking Integration (Stub Implementation)
 * 
 * This module configures Sentry for error tracking and performance monitoring.
 * Only enabled when VITE_ENABLE_ERROR_TRACKING=true and VITE_SENTRY_DSN is set.
 * 
 * Note: This is a stub implementation when Sentry packages are not installed.
 * Install @sentry/react and @sentry/browser for full functionality.
 */

// Types for the Sentry API
interface SentryConfig {
  dsn: string;
  environment: string;
  release: string;
  tracesSampleRate: number;
  replaysOnErrorSampleRate: number;
  replaysSessionSampleRate: number;
}

interface Transaction {
  finish(): void;
}

// Get configuration from environment
const getSentryConfig = (): SentryConfig | null => {
  const dsn = import.meta.env.VITE_SENTRY_DSN;
  
  if (!dsn || !import.meta.env.VITE_ENABLE_ERROR_TRACKING) {
    return null;
  }

  return {
    dsn,
    environment: import.meta.env.VITE_ENVIRONMENT || 'development',
    release: import.meta.env.VITE_APP_VERSION || 'unknown',
    tracesSampleRate: 1.0,
    replaysOnErrorSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
  };
};

// Initialize Sentry
export const initializeSentry = (): void => {
  const config = getSentryConfig();
  
  if (!config) {
    console.log('[Sentry] Error tracking disabled');
    return;
  }

  console.log('[Sentry] Initialized with config:', {
    environment: config.environment,
    release: config.release,
  });
};

// Error boundary component
export const SentryErrorBoundary = ({ children }: { children: React.ReactNode }) => {
  return children;
};

// Capture exception with context
export const captureException = (
  error: Error,
  context?: Record<string, unknown>
): string | undefined => {
  const config = getSentryConfig();
  
  if (!config) {
    console.error('[Sentry] Disabled - Error:', error);
    return undefined;
  }

  console.error('[Sentry] Error:', error, context);
  return 'mock-event-id';
};

// Capture message with level
export const captureMessage = (
  message: string,
  level: 'info' | 'warning' | 'error' = 'info'
): string | undefined => {
  const config = getSentryConfig();
  
  if (!config) {
    console.log(`[Sentry] ${level}:`, message);
    return undefined;
  }

  console.log(`[Sentry] ${level}:`, message);
  return 'mock-message-id';
};

// Set user context
export const setUserContext = (
  user: { id: string; email?: string; username?: string } | null
): void => {
  const config = getSentryConfig();
  
  if (!config) {
    return;
  }

  console.log('[Sentry] Set user context:', user);
};

// Add breadcrumb
export const addBreadcrumb = (
  category: string,
  message: string,
  data?: Record<string, unknown>
): void => {
  const config = getSentryConfig();
  
  if (!config) {
    return;
  }

  console.log('[Sentry] Breadcrumb:', { category, message, data });
};

// Performance monitoring
export const startTransaction = (
  name: string,
  op: string
): Transaction | undefined => {
  const config = getSentryConfig();
  
  if (!config) {
    return undefined;
  }

  console.log('[Sentry] Start transaction:', name, op);
  return { finish: () => console.log('[Sentry] Finish transaction:', name) };
};

// Initialize on import
initializeSentry();
