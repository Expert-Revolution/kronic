#!/bin/bash
# restore-kronic-db.sh
# Database restore script for Kronic PostgreSQL database

set -e

# Configuration from environment variables
DB_HOST="${KRONIC_DATABASE_HOST:-localhost}"
DB_PORT="${KRONIC_DATABASE_PORT:-5432}"
DB_NAME="${KRONIC_DATABASE_NAME:-kronic}"
DB_USER="${KRONIC_DATABASE_USER:-kronic}"

# Logging function
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Usage function
usage() {
    echo "Usage: $0 <backup_file>"
    echo "       $0 /path/to/kronic_backup_20231201_120000.sql.gz"
    echo ""
    echo "Environment variables:"
    echo "  KRONIC_DATABASE_HOST     - Database host (default: localhost)"
    echo "  KRONIC_DATABASE_PORT     - Database port (default: 5432)"
    echo "  KRONIC_DATABASE_NAME     - Database name (default: kronic)"
    echo "  KRONIC_DATABASE_USER     - Database user (default: kronic)"
    exit 1
}

# Check arguments
if [ $# -ne 1 ]; then
    usage
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    log "ERROR: Backup file not found: $BACKUP_FILE"
    exit 1
fi

log "Starting restore of Kronic database"
log "Database: $DB_HOST:$DB_PORT/$DB_NAME"
log "Backup file: $BACKUP_FILE"

# Check if PostgreSQL client is installed
if ! command -v psql &> /dev/null; then
    log "ERROR: psql not found. Please install PostgreSQL client tools."
    exit 1
fi

# Check if file is compressed
if [[ "$BACKUP_FILE" == *.gz ]]; then
    if ! command -v gunzip &> /dev/null; then
        log "ERROR: gunzip not found. Cannot decompress backup file."
        exit 1
    fi
    RESTORE_CMD="gunzip -c '$BACKUP_FILE' | psql -h '$DB_HOST' -p '$DB_PORT' -U '$DB_USER' -d '$DB_NAME'"
else
    RESTORE_CMD="psql -h '$DB_HOST' -p '$DB_PORT' -U '$DB_USER' -d '$DB_NAME' < '$BACKUP_FILE'"
fi

# Confirmation prompt
echo ""
echo "WARNING: This will overwrite the existing database '$DB_NAME' on $DB_HOST:$DB_PORT"
echo "Are you sure you want to continue? (yes/no)"
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    log "Restore cancelled by user"
    exit 0
fi

log "Starting database restore..."

# Perform restore
if [[ "$BACKUP_FILE" == *.gz ]]; then
    gunzip -c "$BACKUP_FILE" | psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME"
else
    psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" < "$BACKUP_FILE"
fi

if [ $? -eq 0 ]; then
    log "Database restore completed successfully"
    
    # Optional: Run migrations to ensure schema is up to date
    if [ -f "alembic.ini" ]; then
        log "Running database migrations to ensure schema is current"
        alembic upgrade head
        
        if [ $? -eq 0 ]; then
            log "Migrations completed successfully"
        else
            log "WARNING: Migrations failed. Database may need manual intervention."
        fi
    fi
    
    log "Restore process completed"
else
    log "ERROR: Database restore failed"
    exit 1
fi

# Optional: Send notification (uncomment and configure as needed)
# if command -v mail &> /dev/null; then
#     echo "Kronic database restore completed successfully at $(date)" | mail -s "Kronic Restore Success" admin@example.com
# fi