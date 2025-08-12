#!/bin/bash

# Automated backup script for Amar Quran
# Run this script daily via cron

set -e

# Configuration
DB_NAME="amar_quran"
DB_USER="amar_quran_user"
BACKUP_DIR="/home/ubuntu/backups"
S3_BUCKET="amar-quran-backups"
RETENTION_DAYS=30
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
echo "Starting database backup..."
pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

# Media files backup
echo "Backing up media files..."
tar -czf "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" /home/ubuntu/amar_quran/media

# Upload to S3
echo "Uploading to S3..."
aws s3 cp "$BACKUP_DIR/db_$TIMESTAMP.sql.gz" "s3://$S3_BUCKET/database/"
aws s3 cp "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" "s3://$S3_BUCKET/media/"

# Clean old local backups
echo "Cleaning old backups..."
find $BACKUP_DIR -type f -mtime +$RETENTION_DAYS -delete

# Clean old S3 backups
aws s3 ls "s3://$S3_BUCKET/database/" | while read -r line; do
  createDate=$(echo $line | awk '{print $1" "$2}')
  createDate=$(date -d "$createDate" +%s)
  olderThan=$(date -d "$RETENTION_DAYS days ago" +%s)
  if [[ $createDate -lt $olderThan ]]; then
    fileName=$(echo $line | awk '{print $4}')
    if [[ $fileName != "" ]]; then
      aws s3 rm "s3://$S3_BUCKET/database/$fileName"
    fi
  fi
done

echo "Backup completed successfully!"

# Send notification
python3 <<EOF
import requests
from datetime import datetime

webhook_url = "YOUR_SLACK_WEBHOOK_URL"
message = {
    "text": f"Amar Quran backup completed successfully at {datetime.now()}"
}
requests.post(webhook_url, json=message)
EOF