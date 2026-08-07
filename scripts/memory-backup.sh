#!/bin/bash
# Weekly memory backup script
# Creates a zip backup of the memory directory

MEMORY_DIR="$HOME/.openclaw/workspace/memory"
BACKUP_DIR="$MEMORY_DIR/backups"
TIMESTAMP=$(date +%Y-%m-%d_%H%M)
LOG_FILE="$BACKUP_DIR/cron-log.md"

# Create backup filename
BACKUP_NAME="memory-$TIMESTAMP.zip"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Get file count and size before backup
FILE_COUNT=$(find "$MEMORY_DIR" -type f ! -path "$BACKUP_DIR/*" | wc -l)
DIR_SIZE=$(du -sh "$MEMORY_DIR" | cut -f1)

# Create the backup
cd "$MEMORY_DIR"
zip -r "$BACKUP_PATH" . -x "backups/*" "backups/root-files/*" "cron-log.md" -9 -q

# Check if backup succeeded
if [ -f "$BACKUP_PATH" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_PATH" | cut -f1)
    RESULT="✅ SUCCESS"
    
    # Clean old backups (keep last 8)
    ls -1t "$BACKUP_DIR"/memory-*.zip | tail -n +9 | xargs -r rm 2>/dev/null
    
    MSG="$RESULT | $TIMESTAMP | Files: $FILE_COUNT | Memory: $DIR_SIZE | Backup: $BACKUP_SIZE"
else
    RESULT="❌ FAILED"
    MSG="$RESULT | $TIMESTAMP | Backup creation failed"
fi

# Append to log
echo "| $MSG |" >> "$LOG_FILE"

# Output for cron capture
echo "$MSG"
