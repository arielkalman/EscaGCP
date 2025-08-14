import { createContext, useContext, useReducer, useEffect } from 'react';
import type { ReactNode } from 'react';

// Theme types
export type Theme = 'light' | 'dark' | 'system';

// State interface
interface ThemeState {
  theme: Theme;
  systemTheme: 'light' | 'dark';
  actualTheme: 'light' | 'dark'; // The resolved theme that's actually applied
}

// Action types
type ThemeAction =
  | { type: 'SET_THEME'; payload: Theme }
  | { type: 'SET_SYSTEM_THEME'; payload: 'light' | 'dark' };

// Initial state
const getInitialTheme = (): Theme => {
  if (typeof window === 'undefined') return 'system';
  const stored = localStorage.getItem('escagcp-theme');
  if (stored && ['light', 'dark', 'system'].includes(stored)) {
    return stored as Theme;
  }
  return 'system';
};

const getSystemTheme = (): 'light' | 'dark' => {
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
};

const resolveTheme = (theme: Theme, systemTheme: 'light' | 'dark'): 'light' | 'dark' => {
  return theme === 'system' ? systemTheme : theme;
};

const initialSystemTheme = getSystemTheme();
const initialTheme = getInitialTheme();

const initialState: ThemeState = {
  theme: initialTheme,
  systemTheme: initialSystemTheme,
  actualTheme: resolveTheme(initialTheme, initialSystemTheme),
};

// Reducer
function themeReducer(state: ThemeState, action: ThemeAction): ThemeState {
  switch (action.type) {
    case 'SET_THEME': {
      const newState = {
        ...state,
        theme: action.payload,
        actualTheme: resolveTheme(action.payload, state.systemTheme),
      };
      
      // Persist to localStorage
      localStorage.setItem('escagcp-theme', action.payload);
      
      return newState;
    }
    
    case 'SET_SYSTEM_THEME': {
      const newState = {
        ...state,
        systemTheme: action.payload,
        actualTheme: resolveTheme(state.theme, action.payload),
      };
      
      return newState;
    }
    
    default:
      return state;
  }
}

// Context interface
interface ThemeContextType {
  state: ThemeState;
  setTheme: (theme: Theme) => void;
  toggleTheme: () => void;
}

// Create context
const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

// Provider component
interface ThemeProviderProps {
  children: ReactNode;
}

export function ThemeProvider({ children }: ThemeProviderProps) {
  const [state, dispatch] = useReducer(themeReducer, initialState);

  // Listen for system theme changes
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    
    const handleChange = (e: MediaQueryListEvent) => {
      dispatch({ 
        type: 'SET_SYSTEM_THEME', 
        payload: e.matches ? 'dark' : 'light' 
      });
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Apply theme to document
  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove previous theme classes
    root.classList.remove('light', 'dark');
    
    // Add the current theme class
    root.classList.add(state.actualTheme);
  }, [state.actualTheme]);

  const contextValue: ThemeContextType = {
    state,
    setTheme: (theme: Theme) => dispatch({ type: 'SET_THEME', payload: theme }),
    toggleTheme: () => {
      const newTheme = state.actualTheme === 'light' ? 'dark' : 'light';
      dispatch({ type: 'SET_THEME', payload: newTheme });
    },
  };

  return (
    <ThemeContext.Provider value={contextValue}>
      {children}
    </ThemeContext.Provider>
  );
}

// Hook to use the context
export function useTheme() {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
} 