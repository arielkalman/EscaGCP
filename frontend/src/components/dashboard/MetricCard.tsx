import React from 'react';
import { LucideIcon } from 'lucide-react';
import { Card, CardContent } from '../ui/card';
import { Badge } from '../ui/badge';
import { cn } from '../../lib/utils';

interface MetricCardProps {
  title: string;
  value: number | string;
  icon: LucideIcon;
  description?: string;
  trend?: {
    value: number;
    direction: 'up' | 'down' | 'stable';
    label?: string;
  };
  variant?: 'default' | 'success' | 'warning' | 'destructive';
  onClick?: () => void;
  className?: string;
  loading?: boolean;
}

export function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  variant = 'default',
  onClick,
  className,
  loading = false
}: MetricCardProps) {
  const variantStyles = {
    default: {
      iconBg: 'bg-gradient-to-br from-blue-50 to-blue-100',
      iconColor: 'text-blue-600',
      borderColor: 'border-blue-200/50',
    },
    success: {
      iconBg: 'bg-gradient-to-br from-emerald-50 to-emerald-100',
      iconColor: 'text-emerald-700',
      borderColor: 'border-emerald-200/50',
    },
    warning: {
      iconBg: 'bg-gradient-to-br from-orange-50 to-orange-100',
      iconColor: 'text-orange-600',
      borderColor: 'border-orange-200/50',
    },
    destructive: {
      iconBg: 'bg-gradient-to-br from-red-50 to-red-100',
      iconColor: 'text-red-600',
      borderColor: 'border-red-200/50',
    },
  };

  const currentVariant = variantStyles[variant];

  const getTrendColor = (direction: string) => {
    switch (direction) {
      case 'up':
        return 'text-red-600';
      case 'down':
        return 'text-emerald-700';
      default:
        return 'text-gray-600';
    }
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'up':
        return '↗';
      case 'down':
        return '↙';
      default:
        return '→';
    }
  };

  if (loading) {
    return (
      <Card className={cn("animate-pulse", className)}>
        <CardContent className="p-6">
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="w-12 h-12 bg-gray-200 rounded-xl"></div>
              <div className="w-16 h-6 bg-gray-200 rounded"></div>
            </div>
            <div className="space-y-2">
              <div className="w-24 h-4 bg-gray-200 rounded"></div>
              <div className="w-16 h-8 bg-gray-200 rounded"></div>
            </div>
            <div className="w-full h-3 bg-gray-200 rounded"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card 
      className={cn(
        "group relative overflow-hidden transition-all duration-300 hover:shadow-lg hover:-translate-y-1 border-0 shadow-md cursor-pointer",
        currentVariant.borderColor,
        onClick && "hover:shadow-xl",
        className
      )}
      onClick={onClick}
    >
      {/* Subtle gradient overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-white/50 to-transparent pointer-events-none" />
      
      <CardContent className="relative p-6">
        <div className="space-y-4">
          {/* Header with Icon and Badge */}
          <div className="flex items-center justify-between">
            <div 
              className={cn(
                "p-3 rounded-xl shadow-sm group-hover:scale-110 transition-transform duration-300",
                currentVariant.iconBg
              )}
            >
              <Icon className={cn("h-6 w-6", currentVariant.iconColor)} />
            </div>
            
            {variant !== 'default' && (
              <Badge 
                variant={variant === 'destructive' ? 'destructive' : variant === 'warning' ? 'warning' : 'success'}
                className="animate-pulse"
              >
                {variant === 'destructive' ? 'Alert' : variant === 'warning' ? 'Watch' : 'Good'}
              </Badge>
            )}
          </div>

          {/* Main Metric */}
          <div className="space-y-1">
            <p className="text-sm font-medium text-muted-foreground">
              {title}
            </p>
            <p className="text-3xl font-bold text-foreground group-hover:scale-105 transition-transform duration-300">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </p>
          </div>

          {/* Trend Indicator */}
          {trend && (
            <div className="flex items-center justify-between">
              <div className={cn(
                "flex items-center space-x-1 text-xs font-medium",
                getTrendColor(trend.direction)
              )}>
                <span className="text-sm">{getTrendIcon(trend.direction)}</span>
                <span>{Math.abs(trend.value)}%</span>
              </div>
              <span className="text-xs text-muted-foreground">
                {trend.label || 'vs last period'}
              </span>
            </div>
          )}

          {/* Description */}
          {description && (
            <p className="text-xs text-muted-foreground leading-relaxed">
              {description}
            </p>
          )}

          {/* Hover state indicator */}
          {onClick && (
            <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-to-r from-purple-500 to-blue-500 transform scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
          )}
        </div>
      </CardContent>
    </Card>
  );
} 