import React, { createContext, useContext, useState, useCallback } from 'react';

export interface AppSettings {
  showGhostUsers: boolean;
  autoRefresh: boolean;
  refreshInterval: number;
  theme: 'light' | 'dark' | 'system';
}

interface AppSettingsContextType {
  settings: AppSettings;
  updateSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => void;
  toggleGhostUsers: () => void;
}

const defaultSettings: AppSettings = {
  showGhostUsers: false, // Hide ghost users by default
  autoRefresh: false,
  refreshInterval: 30000, // 30 seconds
  theme: 'system'
};

const AppSettingsContext = createContext<AppSettingsContextType | undefined>(undefined);

export function AppSettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(() => {
    // Try to load settings from localStorage
    try {
      const savedSettings = localStorage.getItem('gcphound-settings');
      if (savedSettings) {
        return { ...defaultSettings, ...JSON.parse(savedSettings) };
      }
    } catch (error) {
      console.warn('Failed to load settings from localStorage:', error);
    }
    return defaultSettings;
  });

  const updateSetting = useCallback(<K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => {
      const newSettings = { ...prev, [key]: value };
      
      // Save to localStorage
      try {
        localStorage.setItem('gcphound-settings', JSON.stringify(newSettings));
      } catch (error) {
        console.warn('Failed to save settings to localStorage:', error);
      }
      
      return newSettings;
    });
  }, []);

  const toggleGhostUsers = useCallback(() => {
    updateSetting('showGhostUsers', !settings.showGhostUsers);
  }, [settings.showGhostUsers, updateSetting]);

  return (
    <AppSettingsContext.Provider value={{ settings, updateSetting, toggleGhostUsers }}>
      {children}
    </AppSettingsContext.Provider>
  );
}

export function useAppSettings() {
  const context = useContext(AppSettingsContext);
  if (context === undefined) {
    throw new Error('useAppSettings must be used within an AppSettingsProvider');
  }
  return context;
} 