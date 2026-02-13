import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { ThemeProvider } from './context/ThemeContext.tsx'
import { AuthProvider } from './context/AuthContext.tsx'
import { ErrorBoundary } from './components/common/ErrorBoundary.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ThemeProvider>
      <AuthProvider>
        <ErrorBoundary>
          <main id="main-content" tabIndex={-1}>
            <App />
          </main>
        </ErrorBoundary>
      </AuthProvider>
    </ThemeProvider>
  </StrictMode>,
)
