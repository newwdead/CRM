#!/bin/bash

# BizCard CRM - Database Backup Script
# Automatically backs up PostgreSQL database with compression and rotation

set -e

# Configuration
BACKUP_DIR="/home/ubuntu/fastapi-bizcard-crm-ready/backups"
RETENTION_DAYS=${BACKUP_RETENTION_DAYS:-30}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
DB_CONTAINER="bizcard-db"
DB_NAME="bizcard_crm"
DB_USER="postgres"
BACKUP_FILE="backup_${DB_NAME}_${TIMESTAMP}.sql.gz"

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

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

# Check if database container is running
if ! docker ps | grep -q "$DB_CONTAINER"; then
    error "Database container $DB_CONTAINER is not running!"
    exit 1
fi

log "Starting database backup..."
log "Backup file: $BACKUP_FILE"

# Perform backup
if docker exec -t "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/$BACKUP_FILE"; then
    BACKUP_SIZE=$(du -h "$BACKUP_DIR/$BACKUP_FILE" | cut -f1)
    log "Backup completed successfully! Size: $BACKUP_SIZE"
else
    error "Backup failed!"
    exit 1
fi

# Verify backup file
if [ ! -s "$BACKUP_DIR/$BACKUP_FILE" ]; then
    error "Backup file is empty!"
    exit 1
fi

# Remove old backups (older than RETENTION_DAYS)
log "Cleaning up old backups (keeping last $RETENTION_DAYS days)..."
find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -type f -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -type f | wc -l)
log "Total backups: $BACKUP_COUNT"

# List 5 most recent backups
log "Recent backups:"
find "$BACKUP_DIR" -name "backup_${DB_NAME}_*.sql.gz" -type f -printf "%T@ %p\n" | sort -rn | head -5 | while read -r timestamp file; do
    size=$(du -h "$file" | cut -f1)
    date=$(date -d "@${timestamp%.*}" +"%Y-%m-%d %H:%M:%S")
    echo "  - $(basename "$file") ($size) - $date"
done

log "Backup process completed!"

# Optional: Send notification (uncomment and configure as needed)
# curl -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
#     -d "chat_id=${TELEGRAM_CHAT_ID}" \
#     -d "text=✅ Database backup completed: $BACKUP_FILE ($BACKUP_SIZE)"

