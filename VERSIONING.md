# Version Management

This project uses git tags for version management. The build script gets the latest git tag and creates a VERSION file that gets copied into the container.

## How it works

1. **Git tag** - Create a version tag in git
2. **Build script** - `build.sh` gets the latest git tag and creates/updates the `VERSION` file
3. **Docker build** - The Dockerfile copies the `VERSION` file into `/app/VERSION`
4. **Container startup** - The Python script reads the version file and displays it

## Building a new version

```bash
# Commit your changes
git add .
git commit -m "Release v1.2.3"

# Push changes
git push

# Tag the current commit with a new version
git tag -a v1.2.3 -m "support versioning"

# Push the tag
git push --tags

# Run the build script (automatically gets tag and builds container)
./build.sh
```

The build script will:
- Get the latest git tag using `git describe --tags --always --dirty`
- Create/update the `VERSION` file with the tag
- Build the Docker container with version tags

## Version display

When the container starts, you'll see:
```
🚀 Speedtest MQTT HA - Version: v1.2.3
```

## Manual version override

You can manually edit the `VERSION` file before building if needed:
```bash
echo "custom-version" > VERSION
docker build -t speedtest-mqtt .
```

## Notes

- Version is determined at build time, not runtime
- The `VERSION` file is created by the build script
- Falls back to commit hash if no tags exist
- Falls back to 'unknown' if git is not available
