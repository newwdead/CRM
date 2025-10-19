#!/bin/bash

# BizCard CRM - Database Restore Script
# Restores PostgreSQL database from a backup file

set -e

# Configuration
BACKUP_DIR="/home/ubuntu/fastapi-bizcard-crm-ready/backups"
DB_CONTAINER="bizcard-db"
DB_NAME="bizcard_crm"
DB_USER="postgres"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to log messages
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Check if backup file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 <backup_file>"
    echo ""
    echo "Available backups:"
    find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -type f -printf "%T@ %p\n" | sort -rn | head -10 | while read -r timestamp file; do
        size=$(du -h "$file" | cut -f1)
        date=$(date -d "@${timestamp%.*}" +"%Y-%m-%d %H:%M:%S")
        echo "  - $(basename "$file") ($size) - $date"
    done
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ] && [ ! -f "$BACKUP_DIR/$BACKUP_FILE" ]; then
    error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Use full path if only filename provided
if [ ! -f "$BACKUP_FILE" ]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

# Check if database container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    error "Database container $DB_CONTAINER is not running!"
    exit 1
fi

warning "⚠️  WARNING: This will OVERWRITE the current database!"
warning "Database: $DB_NAME"
warning "Backup file: $(basename $BACKUP_FILE)"
echo ""
read -p "Are you sure you want to continue? (type 'yes' to confirm): " -r
echo

if [[ ! $REPLY == "yes" ]]; then
    log "Restore cancelled."
    exit 0
fi

# Create a safety backup before restore
SAFETY_BACKUP="backup_${DB_NAME}_before_restore_$(date +"%Y%m%d_%H%M%S").sql.gz"
log "Creating safety backup: $SAFETY_BACKUP"
docker exec -t "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$SAFETY_BACKUP"

# Stop backend to prevent database access during restore
log "Stopping backend container..."
docker stop bizcard-backend 2>/dev/null || true

# Drop and recreate database
log "Dropping existing database..."
docker exec -t "$DB_CONTAINER" psql -U "$DB_USER" -c "DROP DATABASE IF EXISTS ${DB_NAME};"
log "Creating new database..."
docker exec -t "$DB_CONTAINER" psql -U "$DB_USER" -c "CREATE DATABASE ${DB_NAME};"

# Restore from backup
log "Restoring from backup..."
if gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" "$DB_NAME"; then
    log "Database restored successfully!"
else
    error "Restore failed!"
    log "Attempting to restore from safety backup..."
    gunzip -c "$BACKUP_DIR/$SAFETY_BACKUP" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" "$DB_NAME"
    exit 1
fi

# Restart backend
log "Starting backend container..."
docker start bizcard-backend

log "Restore completed successfully!"
log "Safety backup saved as: $SAFETY_BACKUP"

