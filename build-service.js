#!/usr/bin/env node
/**
 * Python Service Build Script
 * 
 * This script builds the kt_service Python application using PyInstaller.
 * It handles config file copying based on CUSTOM_MODE and platform detection.
 * 
 * Usage:
 *   node build-service.js [--custom-mode=<mode>] [--platform=<platform>]
 * 
 * Arguments:
 *   --custom-mode   The custom mode (e.g., kitchntabs.ngrok, kitchntabs.prod)
 *   --platform      Target platform (darwin, win32, linux)
 * 
 * Environment Variables:
 *   CUSTOM_MODE     Alternative to --custom-mode flag
 *   PLATFORM        Alternative to --platform flag
 */

const { execSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const PROJECT_DIR = __dirname;
const SRC_DIR = path.join(PROJECT_DIR, 'src');
const SERVICE_OUTPUT_DIR = path.join(PROJECT_DIR, 'kt_service');
const VENV_DIR = path.join(PROJECT_DIR, 'pw_env');

// Parse command line arguments
function parseArgs() {
  const args = {
    customMode: process.env.CUSTOM_MODE || null,
    platform: process.env.PLATFORM || process.platform,
  };

  process.argv.slice(2).forEach(arg => {
    if (arg.startsWith('--custom-mode=')) {
      args.customMode = arg.split('=')[1];
    } else if (arg.startsWith('--platform=')) {
      args.platform = arg.split('=')[1];
    }
  });

  return args;
}

// Map CUSTOM_MODE to config file name
function getConfigFileName(customMode, platform) {
  // Map common custom modes to their config files
  const configMap = {
    'kitchntabs.ngrok': 'config.kitchntabs.ngrok.yaml',
    'kitchntabs.production': 'config.kitchntabs.prod.yaml',
    'kitchntabs.prod': 'config.kitchntabs.prod.yaml',
    'pinoywok.ngrok': 'config.dev.yaml',
    'pinoywok.production': 'config.prod.yaml',
    'dev': platform === 'darwin' ? 'config.dev.mac.yaml' : 'config.dev.yaml',
    'prod': platform === 'darwin' ? 'config.prod.mac.yaml' : 'config.prod.yaml',
  };

  if (customMode && configMap[customMode]) {
    return configMap[customMode];
  }

  // Default based on platform
  return platform === 'darwin' ? 'config.prod.mac.yaml' : 'config.prod.yaml';
}

// Get the escpos package path based on platform
function getEscposPath(platform) {
  if (platform === 'win32') {
    return 'pw_env/Lib/site-packages/escpos/*.json';
  }
  return 'pw_env/lib/python3.9/site-packages/escpos/*.json';
}

// Get Python command based on platform
function getPythonCommand(platform) {
  if (platform === 'win32') {
    return 'python';
  }
  return 'python3.9';
}

// Check if virtual environment exists
function checkVenv() {
  if (!fs.existsSync(VENV_DIR)) {
    console.error('❌ Virtual environment not found at:', VENV_DIR);
    console.error('   Please create it first:');
    console.error('   python3.9 -m venv pw_env');
    console.error('   source ./pw_env/bin/activate');
    console.error('   pip install -r ./requirements.txt');
    process.exit(1);
  }
  console.log('✅ Virtual environment found');
}

// Copy config file to temporary config.yaml
function copyConfigFile(configFileName) {
  const sourcePath = path.join(PROJECT_DIR, configFileName);
  const destPath = path.join(PROJECT_DIR, 'config.yaml');

  if (!fs.existsSync(sourcePath)) {
    console.error(`❌ Config file not found: ${sourcePath}`);
    console.error('   Available config files:');
    fs.readdirSync(PROJECT_DIR)
      .filter(f => f.startsWith('config.') && f.endsWith('.yaml'))
      .forEach(f => console.error(`     - ${f}`));
    process.exit(1);
  }

  console.log(`📄 Copying ${configFileName} → config.yaml`);
  fs.copyFileSync(sourcePath, destPath);
  console.log('✅ Config file ready');

  return destPath;
}

// Clean up temporary config file
function cleanupConfigFile() {
  const tempConfigPath = path.join(PROJECT_DIR, 'config.yaml');
  if (fs.existsSync(tempConfigPath)) {
    fs.unlinkSync(tempConfigPath);
    console.log('🧹 Cleaned up temporary config.yaml');
  }
}

// Clean previous build artifacts
function cleanBuildArtifacts() {
  const dirsToClean = [
    path.join(PROJECT_DIR, 'build'),
    path.join(PROJECT_DIR, 'dist'),
    SERVICE_OUTPUT_DIR
  ];

  const filesToClean = [
    path.join(PROJECT_DIR, 'kt_service.spec')
  ];

  dirsToClean.forEach(dir => {
    if (fs.existsSync(dir)) {
      console.log(`🧹 Cleaning ${path.basename(dir)}/`);
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });

  // Don't delete spec file, it might have custom settings
  // filesToClean.forEach(file => {
  //   if (fs.existsSync(file)) {
  //     fs.unlinkSync(file);
  //   }
  // });
}

// Build the Python service
function buildService(args) {
  const { platform } = args;
  const escposPath = getEscposPath(platform);
  const pythonCmd = getPythonCommand(platform);

  // Determine if we should use --onefile
  const useOnefile = true; // Set to false for directory mode

  // Build PyInstaller command
  const pyinstallerArgs = [
    `${pythonCmd} -m PyInstaller`,
    './src/kt_service.py',
    useOnefile ? '--onefile' : '',
    `--distpath ./kt_service`,
    '--add-data "config.yaml:."',
    `--add-data "${escposPath}:escpos"`,
    '--collect-data escpos',
    '--noconfirm',
    '--clean'
  ].filter(Boolean).join(' ');

  console.log('🔧 Building Python service...');
  console.log(`   Command: ${pyinstallerArgs}`);

  try {
    // Activate venv and run pyinstaller
    let activateCmd;
    if (platform === 'win32') {
      activateCmd = `.\\pw_env\\Scripts\\activate.ps1 && ${pyinstallerArgs}`;
    } else {
      activateCmd = `source ./pw_env/bin/activate && ${pyinstallerArgs}`;
    }

    execSync(activateCmd, {
      cwd: PROJECT_DIR,
      stdio: 'inherit',
      shell: platform === 'win32' ? 'powershell.exe' : '/bin/bash'
    });

    console.log('✅ Python service built successfully!');
    return true;
  } catch (error) {
    console.error('❌ Build failed:', error.message);
    return false;
  }
}

// Verify build output
function verifyBuild(platform) {
  const executableName = platform === 'win32' ? 'kt_service.exe' : 'kt_service';
  const executablePath = path.join(SERVICE_OUTPUT_DIR, executableName);

  if (fs.existsSync(executablePath)) {
    const stats = fs.statSync(executablePath);
    const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
    console.log(`✅ Build verified: ${executablePath}`);
    console.log(`   Size: ${sizeMB} MB`);
    return true;
  } else {
    console.error('❌ Build verification failed: executable not found');
    console.error(`   Expected: ${executablePath}`);
    return false;
  }
}

// Copy the built service to dash-frontend for electron-builder
function copyToFrontend() {
  const frontendPythonServiceDir = path.join(PROJECT_DIR, '..', 'dash-frontend', 'python-service');
  
  if (!fs.existsSync(frontendPythonServiceDir)) {
    fs.mkdirSync(frontendPythonServiceDir, { recursive: true });
  }

  // Copy the entire kt_service directory
  const sourceDir = SERVICE_OUTPUT_DIR;
  
  if (fs.existsSync(sourceDir)) {
    console.log(`📦 Copying service to dash-frontend/python-service/`);
    
    // Copy all files from kt_service to python-service
    fs.readdirSync(sourceDir).forEach(file => {
      const srcFile = path.join(sourceDir, file);
      const destFile = path.join(frontendPythonServiceDir, file);
      fs.copyFileSync(srcFile, destFile);
    });
    
    console.log('✅ Service copied to frontend');
  }
}

// Main function
function main() {
  console.log('🐍 Python Service Build Script');
  console.log('================================\n');

  const args = parseArgs();
  console.log(`📋 Configuration:`);
  console.log(`   Custom Mode: ${args.customMode || 'default'}`);
  console.log(`   Platform: ${args.platform}`);
  console.log('');

  // Determine config file
  const configFileName = getConfigFileName(args.customMode, args.platform);
  console.log(`   Config File: ${configFileName}`);
  console.log('');

  // Pre-build checks
  checkVenv();

  // Clean previous builds
  cleanBuildArtifacts();

  // Copy config file
  const tempConfigPath = copyConfigFile(configFileName);

  let success = false;
  try {
    // Build the service
    success = buildService(args);

    if (success) {
      // Verify the build
      success = verifyBuild(args.platform);
    }

    if (success) {
      // Optionally copy to frontend
      // copyToFrontend();
    }
  } finally {
    // Clean up temp config file
    cleanupConfigFile();
  }

  if (success) {
    console.log('\n🎉 Build completed successfully!');
    console.log(`   Output: ${SERVICE_OUTPUT_DIR}`);
  } else {
    console.error('\n💥 Build failed!');
    process.exit(1);
  }
}

// Run
if (require.main === module) {
  main();
}

module.exports = {
  parseArgs,
  getConfigFileName,
  buildService,
  copyConfigFile,
  cleanupConfigFile
};
