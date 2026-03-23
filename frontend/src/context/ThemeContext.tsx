/* eslint-disable react-refresh/only-export-components */
import { createContext, useCallback, useContext, useEffect, useState, useMemo, type ReactNode } from 'react';

type Theme = 'light' | 'dark' | 'system';
type ColourTheme = 'default' | 'matrix' | 'synthwave';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  resolvedTheme: 'light' | 'dark';
  colourTheme: ColourTheme;
  setColourTheme: (t: ColourTheme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window !== 'undefined') {
      const stored = localStorage.getItem('theme') as Theme | null;
      return stored || 'system';
    }
    return 'system';
  });

  const [systemIsDark, setSystemIsDark] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    return false;
  });

  const [colourTheme, setColourThemeState] = useState<ColourTheme>(() => {
    if (typeof window !== 'undefined') {
      const VALID_COLOUR_THEMES: ColourTheme[] = ['default', 'matrix', 'synthwave'];
      const raw = localStorage.getItem('colour-theme');
      const saved: ColourTheme =
        raw && (VALID_COLOUR_THEMES as string[]).includes(raw)
          ? (raw as ColourTheme)
          : 'default';
      // Set data-theme synchronously to avoid flash of wrong theme on reload
      document.documentElement.dataset.theme = saved;
      return saved;
    }
    return 'default';
  });

  const setColourTheme = useCallback((t: ColourTheme) => {
    setColourThemeState(t);
    localStorage.setItem('colour-theme', t);
  }, []);

  // Derive resolvedTheme without a separate setState call
  const resolvedTheme = useMemo<'light' | 'dark'>(() => {
    if (colourTheme !== 'default') return 'dark';
    if (theme === 'system') return systemIsDark ? 'dark' : 'light';
    return theme;
  }, [theme, systemIsDark, colourTheme]);

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove('light', 'dark');
    root.classList.add(resolvedTheme);
    root.dataset.theme = colourTheme;
    localStorage.setItem('theme', theme);
  }, [theme, resolvedTheme, colourTheme]);

  // Listen for system theme changes when in system mode and using default colour theme
  useEffect(() => {
    if (theme !== 'system' || colourTheme !== 'default') return;

    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');

    const handleChange = () => {
      setSystemIsDark(mediaQuery.matches);
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [theme, colourTheme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, resolvedTheme, colourTheme, setColourTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
}
