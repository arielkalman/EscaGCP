import { Link, useLocation } from 'react-router-dom';
import { 
  BarChart3, 
  Network, 
  AlertTriangle, 
  Settings,
  Shield,
  Database,
  GitBranch,
  Moon,
  Sun,
  Activity
} from 'lucide-react';
import { Button } from '../ui/button';
import { cn } from '../../lib/utils';
import { useTheme } from '../../context/ThemeContext';

const navigation = [
  {
    name: 'Dashboard',
    href: '/',
    icon: BarChart3,
  },
  {
    name: 'Graph',
    href: '/graph',
    icon: Network,
  },
  {
    name: 'Findings',
    href: '/findings',
    icon: AlertTriangle,
  },
  {
    name: 'Nodes',
    href: '/nodes',
    icon: Database,
  },
  {
    name: 'Edges',
    href: '/edges',
    icon: GitBranch,
  },
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
];

export function Header() {
  const { state, toggleTheme } = useTheme();
  const location = useLocation();

  return (
    <header className="bg-card border-b border-border">
      <div className="mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* Logo and Brand */}
          <div className="flex items-center">
            <Link 
              to="/" 
              className="flex items-center space-x-3 text-foreground hover:text-primary transition-colors"
            >
              <div className="flex items-center justify-center w-8 h-8 bg-primary rounded-lg">
                <Shield className="h-5 w-5 text-primary-foreground" />
              </div>
              <div>
                <div className="text-xl font-bold">GCPHound</div>
                <p className="text-xs text-muted-foreground">Security Dashboard</p>
              </div>
            </Link>
          </div>

          {/* Navigation */}
          <nav className="flex items-center space-x-1">
            {navigation.map((item) => {
              const isActive = location.pathname === item.href;
              const Icon = item.icon;
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={cn(
                    'flex items-center space-x-2 px-3 py-2 rounded-md text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-primary text-primary-foreground'
                      : 'text-muted-foreground hover:text-foreground hover:bg-accent'
                  )}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Right side actions */}
          <div className="flex items-center space-x-3">
            {/* Theme toggle */}
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleTheme}
              className="h-8 w-8 p-0"
              title={`Switch to ${state.actualTheme === 'light' ? 'dark' : 'light'} theme`}
            >
              {state.actualTheme === 'dark' ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
            
            {/* Status indicator */}
            <div className="flex items-center space-x-2">
              <div className="w-2 h-2 bg-green-800 rounded-full"></div>
              <span className="text-xs text-muted-foreground">Online</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  );
} 