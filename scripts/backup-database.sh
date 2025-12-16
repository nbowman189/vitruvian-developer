#!/bin/bash
# Automated PostgreSQL backup script with rotation
# Run daily via cron: 0 2 * * * /path/to/backup-database.sh

set -e  # Exit on error

# Configuration
BACKUP_DIR="/home/nathan/backups/primary-assistant"
BACKUP_RETENTION_DAYS=30  # Keep backups for 30 days
PROJECT_DIR="/home/nathan/vitruvian-developer"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="primary_assistant_backup_${DATE}.sql.gz"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

log_info "======================================"
log_info "PostgreSQL Backup - $(date)"
log_info "======================================"

# Change to project directory
cd "$PROJECT_DIR"

# Check if containers are running
if ! docker-compose ps | grep -q "Up"; then
    log_error "Docker containers are not running!"
    exit 1
fi

log_info "Creating database backup..."

# Create backup using pg_dump via docker-compose
docker-compose exec -T db pg_dump -U postgres -d primary_assistant | gzip > "${BACKUP_DIR}/${BACKUP_FILE}"

# Check if backup was successful
if [ $? -eq 0 ] && [ -f "${BACKUP_DIR}/${BACKUP_FILE}" ]; then
    BACKUP_SIZE=$(du -h "${BACKUP_DIR}/${BACKUP_FILE}" | cut -f1)
    log_info "Backup created successfully: ${BACKUP_FILE} (${BACKUP_SIZE})"
else
    log_error "Backup failed!"
    exit 1
fi

# Verify backup integrity
log_info "Verifying backup integrity..."
if gunzip -t "${BACKUP_DIR}/${BACKUP_FILE}"; then
    log_info "Backup integrity verified"
else
    log_error "Backup file is corrupted!"
    exit 1
fi

# Rotate old backups
log_info "Rotating old backups (keeping last ${BACKUP_RETENTION_DAYS} days)..."
find "$BACKUP_DIR" -name "primary_assistant_backup_*.sql.gz" -type f -mtime +${BACKUP_RETENTION_DAYS} -delete

# Count remaining backups
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "primary_assistant_backup_*.sql.gz" -type f | wc -l)
log_info "Current backup count: ${BACKUP_COUNT}"

# List recent backups
log_info "Recent backups:"
ls -lh "$BACKUP_DIR" | tail -5

# Calculate total backup size
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log_info "Total backup size: ${TOTAL_SIZE}"

log_info "======================================"
log_info "Backup complete!"
log_info "======================================"

# Optional: Send notification (uncomment and configure)
# curl -X POST -H 'Content-type: application/json' \
#   --data "{\"text\":\"Database backup completed: ${BACKUP_FILE}\"}" \
#   YOUR_WEBHOOK_URL

exit 0
