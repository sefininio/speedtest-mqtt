#!/bin/bash

# Build script for speedtest-mqtt
# Gets latest git tag, creates VERSION file, builds container

set -e

echo "🏷️  Getting latest git tag..."

# Get the latest git tag
VERSION=$(git describe --tags --always --dirty 2>/dev/null || echo "unknown")

echo "📝 Creating VERSION file with: $VERSION"

# Create/update VERSION file
echo "$VERSION" > VERSION

echo "🐳 Building Docker container..."

# Build the container
docker build -t speedtest-mqtt:$VERSION -t speedtest-mqtt:latest .

echo "✅ Build complete!"
echo "   Image: speedtest-mqtt:$VERSION"
echo "   Image: speedtest-mqtt:latest"
echo "   Version file: $(cat VERSION)"
