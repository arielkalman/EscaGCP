import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Header } from './components/common/Header';
import { Dashboard } from './pages/Dashboard/Dashboard';
import { Graph } from './pages/Graph/Graph';
import { Findings } from './pages/Findings/Findings';
import { NodesPage } from './pages/Nodes/NodesPage';
import { EdgesPage } from './pages/Edges/EdgesPage';
import { Settings } from './pages/Settings/Settings';
import { AttackPathVisualization } from './pages/AttackPath/AttackPathVisualization';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { ThemeProvider } from './context/ThemeContext';
import { SettingsProvider } from './context/SettingsContext';
import { AppSettingsProvider } from './context/AppSettingsContext';

// Create a client for React Query
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      refetchOnWindowFocus: false,
      retry: 2,
    },
  },
});

function App() {
  return (
    <ThemeProvider>
      <AppSettingsProvider>
        <SettingsProvider>
          <QueryClientProvider client={queryClient}>
            <ErrorBoundary>
              <Router>
                <div className="min-h-screen bg-background text-foreground">
                  <Header />
                  <main className="flex-1">
                    <Routes>
                      <Route path="/" element={<Dashboard />} />
                      <Route path="/dashboard" element={<Navigate to="/" replace />} />
                      <Route path="/graph" element={<Graph />} />
                      <Route path="/findings" element={<Findings />} />
                      <Route path="/attack-path" element={<AttackPathVisualization />} />
                      <Route path="/nodes" element={<NodesPage />} />
                      <Route path="/edges" element={<EdgesPage />} />
                      <Route path="/settings" element={<Settings />} />
                      <Route path="*" element={<Navigate to="/" replace />} />
                    </Routes>
                  </main>
                </div>
              </Router>
            </ErrorBoundary>
          </QueryClientProvider>
        </SettingsProvider>
      </AppSettingsProvider>
    </ThemeProvider>
  );
}

export default App;
