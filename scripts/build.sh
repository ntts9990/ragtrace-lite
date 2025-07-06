#!/bin/bash
# Build script for RAGTrace Lite Docker images

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building RAGTrace Lite Docker images...${NC}"

# Get version from pyproject.toml
VERSION=$(grep "^version" pyproject.toml | cut -d'"' -f2)
echo -e "${YELLOW}Version: ${VERSION}${NC}"

# Build production image
echo -e "\n${GREEN}Building production image...${NC}"
docker build -t ragtrace-lite:${VERSION} -t ragtrace-lite:latest .

# Build development image
echo -e "\n${GREEN}Building development image...${NC}"
docker build -f Dockerfile.dev -t ragtrace-lite:dev .

# Build with BuildKit for better caching
echo -e "\n${GREEN}Building with BuildKit...${NC}"
DOCKER_BUILDKIT=1 docker build \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --cache-from ragtrace-lite:latest \
    -t ragtrace-lite:${VERSION} \
    -t ragtrace-lite:latest .

# Tag for GitHub Container Registry
echo -e "\n${GREEN}Tagging for GitHub Container Registry...${NC}"
docker tag ragtrace-lite:${VERSION} ghcr.io/yourusername/ragtrace-lite:${VERSION}
docker tag ragtrace-lite:latest ghcr.io/yourusername/ragtrace-lite:latest

# Show image sizes
echo -e "\n${GREEN}Docker images built:${NC}"
docker images | grep ragtrace-lite

echo -e "\n${GREEN}Build complete!${NC}"