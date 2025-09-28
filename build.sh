#!/bin/bash

# Build script for speedtest-mqtt
# Gets latest git tag, creates VERSION file, builds container

set -e

# Default registry and image name
REGISTRY=${REGISTRY:-"ghcr.io/sefininio"}
IMAGE_NAME=${IMAGE_NAME:-"speedtest-mqtt"}
FULL_IMAGE_NAME="$REGISTRY/$IMAGE_NAME"

echo "🏷️  Getting latest git tag..."

# Get the latest git tag
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "unknown")

echo "📝 Creating VERSION file with: $VERSION"

# Create/update VERSION file
echo "$VERSION" > VERSION

echo "🐳 Building Docker container..."

# Build the container with registry tags
docker build -t $FULL_IMAGE_NAME:$VERSION .
docker build -t $FULL_IMAGE_NAME:latest .

echo "✅ Build complete!"
echo "   Image: $FULL_IMAGE_NAME:$VERSION"
echo "   Image: $FULL_IMAGE_NAME:latest"
echo "   Version file: $(cat VERSION)"
echo ""
echo "🚀 To push to registry:"
echo "   docker push $FULL_IMAGE_NAME:$VERSION"
echo "   docker push $FULL_IMAGE_NAME:latest"
