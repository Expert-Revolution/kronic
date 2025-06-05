#!/bin/bash
# backup-kronic-db.sh
# Automated backup script for Kronic PostgreSQL database

set -e

# Configuration from environment variables
DB_HOST="${KRONIC_DATABASE_HOST:-localhost}"
DB_PORT="${KRONIC_DATABASE_PORT:-5432}"
DB_NAME="${KRONIC_DATABASE_NAME:-kronic}"
DB_USER="${KRONIC_DATABASE_USER:-kronic}"
BACKUP_DIR="${KRONIC_BACKUP_DIR:-/var/backups/kronic}"
RETENTION_DAYS="${KRONIC_BACKUP_RETENTION_DAYS:-30}"

# Create timestamp
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="kronic_backup_$DATE.sql"
COMPRESSED_FILE="$BACKUP_FILE.gz"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log "Starting backup of Kronic database"
log "Database: $DB_HOST:$DB_PORT/$DB_NAME"
log "Backup directory: $BACKUP_DIR"

# Check if PostgreSQL client is installed
if ! command -v pg_dump &> /dev/null; then
    log "ERROR: pg_dump not found. Please install PostgreSQL client tools."
    exit 1
fi

# Create backup
log "Creating database backup: $BACKUP_FILE"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
    --verbose --clean --no-owner --no-privileges \
    --file="$BACKUP_DIR/$BACKUP_FILE"

if [ $? -eq 0 ]; then
    log "Database backup created successfully"
    
    # Compress backup
    log "Compressing backup file"
    gzip "$BACKUP_DIR/$BACKUP_FILE"
    
    if [ $? -eq 0 ]; then
        log "Backup compressed successfully: $COMPRESSED_FILE"
        
        # Set appropriate permissions
        chmod 600 "$BACKUP_DIR/$COMPRESSED_FILE"
        
        # Calculate file size
        SIZE=$(du -h "$BACKUP_DIR/$COMPRESSED_FILE" | cut -f1)
        log "Backup size: $SIZE"
        
    else
        log "ERROR: Failed to compress backup file"
        exit 1
    fi
else
    log "ERROR: Database backup failed"
    exit 1
fi

# Clean up old backups
log "Cleaning up backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -name "kronic_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "kronic_backup_*.sql.gz" | wc -l)
log "Total backups in directory: $BACKUP_COUNT"

log "Backup process completed successfully"

# Optional: Send notification (uncomment and configure as needed)
# if command -v mail &> /dev/null; then
#     echo "Kronic database backup completed successfully at $(date)" | mail -s "Kronic Backup Success" admin@example.com
# fi