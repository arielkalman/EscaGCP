import { FullConfig } from '@playwright/test';
import { spawn } from 'child_process';

async function globalTeardown(config: FullConfig) {
  console.log('Starting global teardown...');
  
  try {
    // Force kill any remaining processes
    if (process.platform === 'win32') {
      // Windows - kill all node processes (more aggressive)
      spawn('taskkill', ['/F', '/IM', 'node.exe'], { stdio: 'ignore' });
      spawn('taskkill', ['/F', '/T', '/FI', 'IMAGENAME eq node.exe'], { stdio: 'ignore' });
    } else {
      // Unix-like systems
      spawn('pkill', ['-f', 'vite.*preview'], { stdio: 'ignore' });
      spawn('pkill', ['-f', 'playwright'], { stdio: 'ignore' });
      
      // More aggressive cleanup if needed
      spawn('fuser', ['-k', '4173/tcp'], { stdio: 'ignore' });
    }
    
    // Wait for cleanup to complete
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    console.log('Global teardown completed - all processes should be terminated');
  } catch (error) {
    console.warn('Error during teardown:', error.message);
  }
  
  // Force exit the process to ensure no hanging
  setTimeout(() => {
    console.log('Force exiting process...');
    process.exit(0);
  }, 1000);
}

export default globalTeardown; 