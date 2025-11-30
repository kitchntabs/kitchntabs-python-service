#!/usr/bin/env node
/**
 * Docker-based Cross-Compilation Build Script for kt_service
 * 
 * This script builds the Python service for multiple Linux architectures
 * using Docker with QEMU emulation. Works on macOS (Intel/Apple Silicon)
 * and Windows.
 * 
 * Prerequisites:
 *   - Docker Desktop installed and running
 *   - QEMU support enabled (usually automatic in Docker Desktop)
 * 
 * Usage:
 *   node build-docker.js [--arch=<arch>] [--config=<config>] [--all]
 * 
 * Arguments:
 *   --arch      Target architecture: x64, arm64, armv7l (default: all)
 *   --config    Config mode: ngrok, prod (default: prod)
 *   --all       Build for all architectures
 *   --clean     Remove Docker images after build
 */

const { execSync, spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

const SCRIPT_DIR = __dirname;
const DOCKER_DIR = path.join(SCRIPT_DIR, 'docker');
const OUTPUT_DIR = path.join(SCRIPT_DIR, 'kt_service_builds');

// Architecture configurations
const ARCH_CONFIG = {
  x64: {
    dockerfile: 'Dockerfile.linux-x64',
    platform: 'linux/amd64',
    outputSuffix: 'linux_x64'
  },
  arm64: {
    dockerfile: 'Dockerfile.linux-arm64',
    platform: 'linux/arm64',
    outputSuffix: 'linux_arm64'
  },
  armv7l: {
    dockerfile: 'Dockerfile.linux-armv7l',
    platform: 'linux/arm/v7',
    outputSuffix: 'linux_armv7l'
  },
  // Buster variants for older Raspberry Pi OS (GLIBC 2.28)
  'armv7l-buster': {
    dockerfile: 'Dockerfile.linux-armv7l-buster',
    platform: 'linux/arm/v7',
    outputSuffix: 'linux_armv7l_buster'
  }
};

// Config file mapping
const CONFIG_MAP = {
  ngrok: 'config.kitchntabs.ngrok.yaml',
  prod: 'config.kitchntabs.prod.yaml',
  production: 'config.kitchntabs.prod.yaml',
  dev: 'config.dev.yaml'
};

// Parse command line arguments
function parseArgs() {
  const args = {
    arch: null,
    config: 'prod',
    buildAll: false,
    cleanImages: false
  };

  process.argv.slice(2).forEach(arg => {
    if (arg.startsWith('--arch=')) {
      args.arch = arg.split('=')[1];
    } else if (arg.startsWith('--config=')) {
      args.config = arg.split('=')[1];
    } else if (arg === '--all') {
      args.buildAll = true;
    } else if (arg === '--clean') {
      args.cleanImages = true;
    } else if (arg === '--help') {
      console.log(`
Docker-based Cross-Compilation Build Script

Usage:
  node build-docker.js [options]

Options:
  --arch=<arch>     Target architecture: x64, arm64, armv7l
  --config=<mode>   Config mode: ngrok, prod (default: prod)
  --all             Build for all architectures
  --clean           Remove Docker images after build
  --help            Show this help message

Examples:
  node build-docker.js --arch=arm64 --config=ngrok
  node build-docker.js --all --config=prod
  node build-docker.js --arch=armv7l
      `);
      process.exit(0);
    }
  });

  return args;
}

// Check if Docker is running
function checkDocker() {
  console.log('🐳 Checking Docker...');
  try {
    execSync('docker info', { stdio: 'pipe' });
    console.log('✅ Docker is running');
    return true;
  } catch (error) {
    console.error('❌ Docker is not running. Please start Docker Desktop.');
    return false;
  }
}

// Setup QEMU for multi-architecture builds
function setupQemu() {
  console.log('🔧 Setting up QEMU for multi-arch builds...');
  
  try {
    // Check buildx
    execSync('docker buildx version', { stdio: 'pipe' });
  } catch (error) {
    console.error('❌ Docker buildx not available. Please update Docker Desktop.');
    return false;
  }

  try {
    // Check if builder exists
    execSync('docker buildx inspect kt-builder', { stdio: 'pipe' });
    execSync('docker buildx use kt-builder', { stdio: 'pipe' });
  } catch (error) {
    // Create builder
    console.log('Creating new buildx builder...');
    execSync('docker buildx create --name kt-builder --use --bootstrap', { stdio: 'inherit' });
  }

  // Register QEMU handlers
  try {
    execSync('docker run --rm --privileged multiarch/qemu-user-static --reset -p yes', { 
      stdio: 'pipe',
      timeout: 60000 
    });
  } catch (error) {
    // This might fail on some systems but that's okay
    console.log('⚠️  QEMU registration skipped (may already be configured)');
  }

  console.log('✅ QEMU setup complete');
  return true;
}

// Build for a specific architecture
async function buildArch(arch, configFile, cleanImages) {
  const config = ARCH_CONFIG[arch];
  if (!config) {
    console.error(`❌ Unknown architecture: ${arch}`);
    return false;
  }

  const outputName = `kt_service_${config.outputSuffix}`;
  const archOutputDir = path.join(OUTPUT_DIR, arch);

  console.log('');
  console.log('════════════════════════════════════════════════════════════');
  console.log(`🏗️  Building for ${arch} (${config.platform})`);
  console.log(`   Config: ${configFile}`);
  console.log('════════════════════════════════════════════════════════════');

  // Create output directory
  fs.mkdirSync(archOutputDir, { recursive: true });

  const startTime = Date.now();

  try {
    // Build Docker image
    console.log('📦 Building Docker image (this may take a while for ARM)...');
    
    const buildCmd = [
      'docker', 'buildx', 'build',
      '--platform', config.platform,
      '--build-arg', `CONFIG_FILE=${configFile}`,
      '--build-arg', `OUTPUT_NAME=${outputName}`,
      '-f', path.join(DOCKER_DIR, config.dockerfile),
      '-t', `kt-service-${arch}:latest`,
      '--load',
      SCRIPT_DIR
    ].join(' ');

    execSync(buildCmd, { 
      stdio: 'inherit',
      cwd: SCRIPT_DIR 
    });

    // Extract binaries
    console.log('📤 Extracting binaries...');
    
    // Create container
    const containerId = execSync(
      `docker create --platform ${config.platform} kt-service-${arch}:latest`,
      { encoding: 'utf8' }
    ).trim();

    // Services to extract
    const services = ['kt_service', 'print_service', 'tts_service'];
    
    // Copy all services from container
    for (const service of services) {
      try {
        execSync(`docker cp ${containerId}:/output/${service} ${archOutputDir}/${service}`);
        console.log(`   ✅ Extracted ${service}`);
      } catch (e) {
        console.log(`   ⚠️  ${service} not found in container (may be optional)`);
      }
    }
    
    // Remove container
    execSync(`docker rm ${containerId}`, { stdio: 'pipe' });

    // Copy config file
    fs.copyFileSync(
      path.join(SCRIPT_DIR, configFile),
      path.join(archOutputDir, 'config.yaml')
    );

    const duration = Math.round((Date.now() - startTime) / 1000);

    // Verify builds (reuse services array from above)
    let hasMainService = false;
    
    console.log('📋 Verifying build outputs...');
    for (const service of services) {
      const outputPath = path.join(archOutputDir, service);
      if (fs.existsSync(outputPath)) {
        const stats = fs.statSync(outputPath);
        const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
        console.log(`   ✅ ${service}: ${sizeMB} MB`);
        
        // Make executable
        if (process.platform !== 'win32') {
          fs.chmodSync(outputPath, '755');
        }
        
        if (service === 'kt_service') {
          hasMainService = true;
        }
      } else {
        console.log(`   ⚠️  ${service}: not found`);
      }
    }
    
    if (!hasMainService) {
      console.error('❌ Build failed - kt_service not found');
      return false;
    }
    
    console.log('✅ Build successful!');
    console.log(`   Duration: ${duration}s`);

    // Clean up image if requested
    if (cleanImages) {
      console.log('🧹 Cleaning up Docker image...');
      try {
        execSync(`docker rmi kt-service-${arch}:latest`, { stdio: 'pipe' });
      } catch (e) {
        // Ignore errors
      }
    }

    return true;
  } catch (error) {
    console.error(`❌ Build failed for ${arch}:`, error.message);
    return false;
  }
}

// Copy builds to kt_service directory with architecture-specific names
function organizeBuilds(architectures) {
  console.log('');
  console.log('📁 Organizing builds...');
  
  const ktServiceDir = path.join(SCRIPT_DIR, 'kt_service');
  fs.mkdirSync(ktServiceDir, { recursive: true });

  const services = ['kt_service', 'print_service', 'tts_service'];

  for (const arch of architectures) {
    console.log(`   ${arch}:`);
    for (const service of services) {
      const sourcePath = path.join(OUTPUT_DIR, arch, service);
      if (fs.existsSync(sourcePath)) {
        const destPath = path.join(ktServiceDir, `${service}_${arch}`);
        fs.copyFileSync(sourcePath, destPath);
        if (process.platform !== 'win32') {
          fs.chmodSync(destPath, '755');
        }
        console.log(`      ✅ ${service} → kt_service/${service}_${arch}`);
      }
    }
  }
}

// Main function
async function main() {
  console.log('');
  console.log('╔════════════════════════════════════════════════════════════╗');
  console.log('║     🐍 Python Service Cross-Compilation Build Script       ║');
  console.log('╚════════════════════════════════════════════════════════════╝');
  console.log('');

  const args = parseArgs();

  // Get config file
  const configFile = CONFIG_MAP[args.config] || CONFIG_MAP.prod;
  console.log('📋 Configuration:');
  console.log(`   Config Mode: ${args.config}`);
  console.log(`   Config File: ${configFile}`);
  console.log('');

  // Check config file exists
  if (!fs.existsSync(path.join(SCRIPT_DIR, configFile))) {
    console.error(`❌ Config file not found: ${configFile}`);
    process.exit(1);
  }

  // Check Docker
  if (!checkDocker()) {
    process.exit(1);
  }

  // Setup QEMU
  if (!setupQemu()) {
    process.exit(1);
  }

  // Determine architectures to build
  let architectures = [];
  if (args.buildAll) {
    architectures = ['x64', 'arm64', 'armv7l'];
  } else if (args.arch) {
    architectures = [args.arch];
  } else {
    architectures = ['x64', 'arm64', 'armv7l'];
  }

  console.log('');
  console.log(`🎯 Target architectures: ${architectures.join(', ')}`);

  // Create output directory
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });

  // Build each architecture
  const failed = [];
  for (const arch of architectures) {
    const success = await buildArch(arch, configFile, args.cleanImages);
    if (!success) {
      failed.push(arch);
    }
  }

  // Organize builds into kt_service directory
  const successful = architectures.filter(a => !failed.includes(a));
  if (successful.length > 0) {
    organizeBuilds(successful);
  }

  // Summary
  console.log('');
  console.log('════════════════════════════════════════════════════════════');
  console.log('                        BUILD SUMMARY');
  console.log('════════════════════════════════════════════════════════════');
  console.log('');
  console.log(`Output directory: ${OUTPUT_DIR}`);
  console.log('');

  if (failed.length === 0) {
    console.log('✅ All builds completed successfully!');
    console.log('');
    console.log('Built artifacts:');
    const services = ['kt_service', 'print_service', 'tts_service'];
    architectures.forEach(arch => {
      console.log(`   ${arch}:`);
      services.forEach(service => {
        const outputPath = path.join(OUTPUT_DIR, arch, service);
        if (fs.existsSync(outputPath)) {
          const stats = fs.statSync(outputPath);
          const sizeMB = (stats.size / (1024 * 1024)).toFixed(2);
          console.log(`      ${service}: ${sizeMB} MB`);
        }
      });
    });
  } else {
    console.error(`❌ Some builds failed: ${failed.join(', ')}`);
    process.exit(1);
  }

  console.log('');
  console.log('📝 Next steps:');
  console.log('   The binaries are in kt_service_builds/<arch>/');
  console.log('   Services: kt_service, print_service, tts_service');
  console.log('');
  console.log('   Run the Debian build:');
  console.log('   cd ../dash-frontend && pnpm release:electron:kitchntabs:debian:dev');
  console.log('');
}

// Run
main().catch(error => {
  console.error('Fatal error:', error);
  process.exit(1);
});
