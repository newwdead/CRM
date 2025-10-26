#!/bin/bash
# Docker Cleanup Script - runs weekly to clean unused Docker resources

echo "Starting Docker cleanup..."

# Remove stopped containers
echo "Removing stopped containers..."
docker container prune -f

# Remove dangling images
echo "Removing dangling images..."
docker image prune -f

# Remove unused build cache (older than 7 days)
echo "Removing old build cache..."
docker builder prune -af --filter "until=168h"

# Remove unused volumes
echo "Removing unused volumes..."
docker volume prune -f

# Show disk usage after cleanup
echo ""
echo "Docker disk usage after cleanup:"
docker system df

echo ""
echo "Cleanup complete!"
