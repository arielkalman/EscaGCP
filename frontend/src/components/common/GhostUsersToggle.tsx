import React from 'react';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { 
  Eye, 
  EyeOff, 
  Users, 
  UserX,
  Info
} from 'lucide-react';
import { useAppSettings } from '../../context/AppSettingsContext';
import { 
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '../ui/tooltip';

interface GhostUsersToggleProps {
  ghostUserStats?: {
    totalGhostNodes: number;
    ghostUsers: number;
    ghostServiceAccounts: number;
    edgesWithGhostUsers: number;
  };
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showStats?: boolean;
}

export function GhostUsersToggle({ 
  ghostUserStats, 
  className = "",
  size = 'md',
  showLabel = true,
  showStats = true
}: GhostUsersToggleProps) {
  const { settings, toggleGhostUsers } = useAppSettings();
  
  const hasGhostUsers = ghostUserStats && ghostUserStats.totalGhostNodes > 0;
  
  const sizeClasses = {
    sm: 'h-8 px-3 text-xs',
    md: 'h-9 px-4 text-sm',
    lg: 'h-10 px-6 text-base'
  };
  
  const iconSizes = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5'
  };

  // Map our size to Button component size
  const buttonSize = size === 'md' ? 'default' : size;

  const tooltipContent = (
    <div className="space-y-2">
      <div className="font-medium">
        {settings.showGhostUsers ? 'Hide Ghost Users' : 'Show Ghost Users'}
      </div>
      <div className="text-xs space-y-1">
        <p>Ghost users are deleted or inactive accounts that may still have residual permissions.</p>
        {ghostUserStats && ghostUserStats.totalGhostNodes > 0 && showStats && (
          <div className="mt-2 pt-2 border-t border-gray-600 space-y-1">
            <div>Total: {ghostUserStats.totalGhostNodes}</div>
            <div>Users: {ghostUserStats.ghostUsers}</div>
            <div>Service Accounts: {ghostUserStats.ghostServiceAccounts}</div>
            {ghostUserStats.edgesWithGhostUsers > 0 && (
              <div>Edges with ghosts: {ghostUserStats.edgesWithGhostUsers}</div>
            )}
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="outline"
              size={buttonSize}
              onClick={toggleGhostUsers}
              className={`flex items-center space-x-2 ${sizeClasses[size]}`}
              aria-label={settings.showGhostUsers ? 'Hide ghost users' : 'Show ghost users'}
            >
              {settings.showGhostUsers ? (
                <Eye className={iconSizes[size]} />
              ) : (
                <EyeOff className={iconSizes[size]} />
              )}
              {showLabel && (
                <span className="text-sm">
                  {settings.showGhostUsers ? 'Hide' : 'Show'} Ghost Users
                </span>
              )}
              {ghostUserStats && ghostUserStats.totalGhostNodes > 0 && showStats && (
                <span className="text-xs bg-muted px-1.5 py-0.5 rounded">
                  {ghostUserStats.totalGhostNodes}
                </span>
              )}
            </Button>
          </TooltipTrigger>
          <TooltipContent side="bottom" className="max-w-xs">
            {tooltipContent}
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
      
      {showStats && hasGhostUsers && (
        <div className="flex items-center space-x-2">
          <Badge variant="outline" className="text-xs flex items-center space-x-1">
            <UserX className="h-3 w-3" />
            <span>{ghostUserStats.totalGhostNodes} ghost</span>
          </Badge>
          
          {!settings.showGhostUsers && (
            <Badge variant="secondary" className="text-xs">
              Hidden
            </Badge>
          )}
        </div>
      )}
    </div>
  );
} 