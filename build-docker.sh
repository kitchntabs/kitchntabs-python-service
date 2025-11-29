#!/bin/bash
#
# Docker-based Cross-Compilation Build Script for kt_service
#
# This script builds the Python service for multiple Linux architectures
# using Docker with QEMU emulation. Works on macOS (Intel/Apple Silicon)
# and Windows (via WSL2 or Git Bash).
#
# Prerequisites:
#   - Docker Desktop with "Use Rosetta for x86/amd64 emulation" disabled
#   - QEMU support enabled in Docker (usually automatic)
#
# Usage:
#   ./build-docker.sh [--arch=<arch>] [--config=<config>] [--all]
#
# Arguments:
#   --arch      Target architecture: x64, arm64, armv7l (default: all)
#   --config    Config mode: ngrok, prod (default: prod)
#   --all       Build for all architectures
#   --clean     Remove Docker images after build
#
# Examples:
#   ./build-docker.sh --arch=arm64 --config=ngrok
#   ./build-docker.sh --all --config=prod
#   ./build-docker.sh --arch=armv7l
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DOCKER_DIR="${SCRIPT_DIR}/docker"
OUTPUT_DIR="${SCRIPT_DIR}/kt_service_builds"

# Default values
ARCH=""
CONFIG="prod"
BUILD_ALL=false
CLEAN_IMAGES=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --arch=*)
            ARCH="${arg#*=}"
            ;;
        --config=*)
            CONFIG="${arg#*=}"
            ;;
        --all)
            BUILD_ALL=true
            ;;
        --clean)
            CLEAN_IMAGES=true
            ;;
        --help)
            head -40 "$0" | tail -35
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            exit 1
            ;;
    esac
done

# Map config to config file
get_config_file() {
    case $1 in
        ngrok)
            echo "config.kitchntabs.ngrok.yaml"
            ;;
        prod|production)
            echo "config.kitchntabs.prod.yaml"
            ;;
        dev)
            echo "config.dev.yaml"
            ;;
        *)
            echo "config.kitchntabs.prod.yaml"
            ;;
    esac
}

# Check Docker is running
check_docker() {
    echo -e "${BLUE}🐳 Checking Docker...${NC}"
    if ! docker info > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker is not running. Please start Docker Desktop.${NC}"
        exit 1
    fi
    echo -e "${GREEN}✅ Docker is running${NC}"
}

# Setup QEMU for multi-architecture builds
setup_qemu() {
    echo -e "${BLUE}🔧 Setting up QEMU for multi-arch builds...${NC}"
    
    # Check if buildx is available
    if ! docker buildx version > /dev/null 2>&1; then
        echo -e "${RED}❌ Docker buildx not available. Please update Docker Desktop.${NC}"
        exit 1
    fi
    
    # Create and use a new builder instance with multi-arch support
    if ! docker buildx inspect kt-builder > /dev/null 2>&1; then
        echo -e "${YELLOW}Creating new buildx builder...${NC}"
        docker buildx create --name kt-builder --use --bootstrap
    else
        docker buildx use kt-builder
    fi
    
    # Register QEMU handlers (needed for cross-compilation)
    docker run --rm --privileged multiarch/qemu-user-static --reset -p yes 2>/dev/null || true
    
    echo -e "${GREEN}✅ QEMU setup complete${NC}"
}

# Build for a specific architecture
build_arch() {
    local arch=$1
    local config_file=$2
    local dockerfile=""
    local platform=""
    
    case $arch in
        x64)
            dockerfile="Dockerfile.linux-x64"
            platform="linux/amd64"
            ;;
        arm64)
            dockerfile="Dockerfile.linux-arm64"
            platform="linux/arm64"
            ;;
        armv7l)
            dockerfile="Dockerfile.linux-armv7l"
            platform="linux/arm/v7"
            ;;
        *)
            echo -e "${RED}❌ Unknown architecture: $arch${NC}"
            return 1
            ;;
    esac
    
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}🏗️  Building for ${YELLOW}${arch}${BLUE} (${platform})${NC}"
    echo -e "${BLUE}   Config: ${config_file}${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    
    # Create output directory
    mkdir -p "${OUTPUT_DIR}/${arch}"
    
    # Build the Docker image
    echo -e "${YELLOW}📦 Building Docker image (this may take a while for ARM)...${NC}"
    
    local start_time=$(date +%s)
    
    docker buildx build \
        --platform "${platform}" \
        --build-arg CONFIG_FILE="${config_file}" \
        -f "${DOCKER_DIR}/${dockerfile}" \
        -t "kt-service-${arch}:latest" \
        --load \
        "${SCRIPT_DIR}"
    
    # Extract all built binaries
    echo -e "${YELLOW}📤 Extracting binaries...${NC}"
    
    # Create a container and copy the output
    local container_id=$(docker create --platform "${platform}" "kt-service-${arch}:latest")
    
    # Extract all 3 services
    docker cp "${container_id}:/output/kt_service" "${OUTPUT_DIR}/${arch}/kt_service" 2>/dev/null || echo "Warning: kt_service not found"
    docker cp "${container_id}:/output/print_service" "${OUTPUT_DIR}/${arch}/print_service" 2>/dev/null || echo "Warning: print_service not found"
    docker cp "${container_id}:/output/tts_service" "${OUTPUT_DIR}/${arch}/tts_service" 2>/dev/null || echo "Warning: tts_service not found"
    
    docker rm "${container_id}"
    
    # Also copy config file
    cp "${SCRIPT_DIR}/${config_file}" "${OUTPUT_DIR}/${arch}/config.yaml"
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    # Verify the build
    if [ -f "${OUTPUT_DIR}/${arch}/kt_service" ]; then
        echo -e "${GREEN}✅ Build successful!${NC}"
        echo -e "   Output directory: ${OUTPUT_DIR}/${arch}/"
        echo -e "   Duration: ${duration}s"
        echo ""
        echo "Built services:"
        ls -lah "${OUTPUT_DIR}/${arch}/"
        echo ""
        # Show file info for kt_service
        echo "Binary info (kt_service):"
        file "${OUTPUT_DIR}/${arch}/kt_service" 2>/dev/null || true
    else
        echo -e "${RED}❌ Build failed - kt_service not found${NC}"
        return 1
    fi
    
    # Clean up image if requested
    if [ "$CLEAN_IMAGES" = true ]; then
        echo -e "${YELLOW}🧹 Cleaning up Docker image...${NC}"
        docker rmi "kt-service-${arch}:latest" 2>/dev/null || true
    fi
}

# Main execution
main() {
    echo ""
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║     🐍 Python Service Cross-Compilation Build Script       ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    
    # Get config file
    local config_file=$(get_config_file "$CONFIG")
    echo -e "${BLUE}📋 Configuration:${NC}"
    echo -e "   Config Mode: ${CONFIG}"
    echo -e "   Config File: ${config_file}"
    echo ""
    
    # Check config file exists
    if [ ! -f "${SCRIPT_DIR}/${config_file}" ]; then
        echo -e "${RED}❌ Config file not found: ${config_file}${NC}"
        exit 1
    fi
    
    # Check Docker
    check_docker
    
    # Setup QEMU
    setup_qemu
    
    # Determine which architectures to build
    local architectures=()
    
    if [ "$BUILD_ALL" = true ]; then
        architectures=("x64" "arm64" "armv7l")
    elif [ -n "$ARCH" ]; then
        architectures=("$ARCH")
    else
        # Default to all
        architectures=("x64" "arm64" "armv7l")
    fi
    
    echo ""
    echo -e "${BLUE}🎯 Target architectures: ${architectures[*]}${NC}"
    
    # Create output directory
    mkdir -p "$OUTPUT_DIR"
    
    # Build each architecture
    local failed=()
    for arch in "${architectures[@]}"; do
        if ! build_arch "$arch" "$config_file"; then
            failed+=("$arch")
        fi
    done
    
    # Summary
    echo ""
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}                        BUILD SUMMARY${NC}"
    echo -e "${BLUE}════════════════════════════════════════════════════════════${NC}"
    echo ""
    echo -e "Output directory: ${OUTPUT_DIR}"
    echo ""
    
    if [ ${#failed[@]} -eq 0 ]; then
        echo -e "${GREEN}✅ All builds completed successfully!${NC}"
        echo ""
        echo "Built artifacts:"
        ls -la "${OUTPUT_DIR}"/*/ 2>/dev/null || true
    else
        echo -e "${RED}❌ Some builds failed: ${failed[*]}${NC}"
        exit 1
    fi
    
    echo ""
    echo -e "${YELLOW}📝 Next steps:${NC}"
    echo "   Copy the appropriate binary to your dash-python-service/kt_service/ folder"
    echo "   or update electron-builder.config.js to include architecture-specific binaries."
    echo ""
}

# Run
main
