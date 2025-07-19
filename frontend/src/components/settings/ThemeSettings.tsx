import { Moon, Sun, Monitor } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../ui/card';
import { Label } from '../ui/label';
import { RadioGroup, RadioGroupItem } from '../ui/radio-group';
import { Switch } from '../ui/switch';
import { Separator } from '../ui/separator';
import { useTheme, type Theme } from '../../context/ThemeContext';

export function ThemeSettings() {
  const { state, setTheme } = useTheme();

  const handleThemeChange = (value: string) => {
    setTheme(value as Theme);
  };

  const getThemeDescription = () => {
    switch (state.theme) {
      case 'light':
        return 'Use light theme colors and styling';
      case 'dark':
        return 'Use dark theme colors and styling';
      case 'system':
        return `Follow system preference (currently ${state.systemTheme})`;
      default:
        return '';
    }
  };

  return (
    <div className="space-y-6">
      {/* Theme Selection */}
      <Card>
        <CardHeader>
          <CardTitle>Theme</CardTitle>
          <CardDescription>
            Choose how EscaGCP looks and feels
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-3">
            <Label htmlFor="theme-selection" className="text-sm font-medium">
              Color Scheme
            </Label>
            <RadioGroup
              value={state.theme}
              onValueChange={handleThemeChange}
              className="grid grid-cols-1 sm:grid-cols-3 gap-4"
            >
              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="light" id="light" />
                <div className="flex items-center space-x-3 flex-1">
                  <Sun className="h-4 w-4 text-yellow-500" />
                  <div>
                    <Label htmlFor="light" className="font-medium cursor-pointer">
                      Light
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Bright and clean
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="dark" id="dark" />
                <div className="flex items-center space-x-3 flex-1">
                  <Moon className="h-4 w-4 text-blue-500" />
                  <div>
                    <Label htmlFor="dark" className="font-medium cursor-pointer">
                      Dark
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Easy on the eyes
                    </p>
                  </div>
                </div>
              </div>

              <div className="flex items-center space-x-2 border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors">
                <RadioGroupItem value="system" id="system" />
                <div className="flex items-center space-x-3 flex-1">
                  <Monitor className="h-4 w-4 text-gray-500" />
                  <div>
                    <Label htmlFor="system" className="font-medium cursor-pointer">
                      System
                    </Label>
                    <p className="text-xs text-muted-foreground">
                      Use device setting
                    </p>
                  </div>
                </div>
              </div>
            </RadioGroup>
            
            <p className="text-sm text-muted-foreground">
              {getThemeDescription()}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Theme Preview */}
      <Card>
        <CardHeader>
          <CardTitle>Preview</CardTitle>
          <CardDescription>
            See how your selection looks with sample components
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Sample UI Elements */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 border border-border rounded-lg bg-card">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 rounded-full bg-primary"></div>
                <div>
                  <p className="font-medium text-foreground">Sample Dashboard Card</p>
                  <p className="text-sm text-muted-foreground">Secondary text content</p>
                </div>
              </div>
              <div className="flex space-x-2">
                <div className="px-2 py-1 text-xs rounded-full bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200">
                  Active
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between p-3 border border-border rounded-lg bg-muted/50">
              <span className="text-sm font-medium">Sample Setting</span>
              <Switch checked={true} disabled />
            </div>

            <div className="flex space-x-2">
              <div className="px-3 py-1 text-xs rounded-full bg-red-100 text-red-800 dark:bg-red-900 dark:text-red-200">
                Critical
              </div>
              <div className="px-3 py-1 text-xs rounded-full bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200">
                High
              </div>
              <div className="px-3 py-1 text-xs rounded-full bg-yellow-100 text-yellow-800 dark:bg-yellow-900 dark:text-yellow-200">
                Medium
              </div>
              <div className="px-3 py-1 text-xs rounded-full bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                Low
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Theme Options */}
      <Card>
        <CardHeader>
          <CardTitle>Advanced Options</CardTitle>
          <CardDescription>
            Additional theme and appearance settings
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="reduce-motion" className="font-medium">
                Reduce Motion
              </Label>
              <p className="text-sm text-muted-foreground">
                Minimize animations and transitions
              </p>
            </div>
            <Switch 
              id="reduce-motion" 
              disabled 
            />
          </div>

          <Separator />

          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <Label htmlFor="high-contrast" className="font-medium">
                High Contrast
              </Label>
              <p className="text-sm text-muted-foreground">
                Increase contrast for better readability
              </p>
            </div>
            <Switch 
              id="high-contrast" 
              disabled 
            />
          </div>

          <div className="text-xs text-muted-foreground mt-4 p-3 bg-muted/50 rounded-lg">
            <strong>Note:</strong> Advanced options are planned for future releases.
            Your feedback on theme preferences is welcome!
          </div>
        </CardContent>
      </Card>
    </div>
  );
} 