import { chromium, FullConfig } from '@playwright/test';
import { spawn } from 'child_process';

async function globalSetup(config: FullConfig) {
  console.log('Starting global setup...');
  
  // Ensure clean slate by killing any existing processes on the port
  try {
    // Kill any process using port 4173 (for cross-platform compatibility)
    if (process.platform === 'win32') {
      spawn('taskkill', ['/F', '/IM', 'node.exe'], { stdio: 'ignore' });
    } else {
      spawn('pkill', ['-f', 'vite.*preview'], { stdio: 'ignore' });
    }
    
    // Wait a moment for cleanup
    await new Promise(resolve => setTimeout(resolve, 1000));
  } catch (error) {
    // Ignore errors during cleanup
  }

  console.log('Global setup completed');
}

export default globalSetup; 