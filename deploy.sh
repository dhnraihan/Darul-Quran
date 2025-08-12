#!/bin/bash

# Amar Quran Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "Starting Amar Quran deployment..."

# Variables
PROJECT_DIR="/home/ubuntu/amar_quran"
VENV_DIR="$PROJECT_DIR/venv"
BACKUP_DIR="/home/ubuntu/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

# Backup database
echo "Backing up database..."
pg_dump amar_quran > "$BACKUP_DIR/amar_quran_$TIMESTAMP.sql"

# Backup media files
echo "Backing up media files..."
tar -czf "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" "$PROJECT_DIR/media"

# Pull latest code
echo "Pulling latest code from repository..."
cd $PROJECT_DIR
git pull origin main

# Activate virtual environment
echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput

# Compile translations
echo "Compiling translations..."
python manage.py compilemessages

# Restart services
echo "Restarting services..."
sudo systemctl restart amar_quran
sudo systemctl restart nginx
sudo supervisorctl restart all

# Run tests
echo "Running tests..."
python manage.py test --parallel

# Check service status
echo "Checking service status..."
sudo systemctl status amar_quran --no-pager
sudo supervisorctl status

echo "Deployment completed successfully!"

# Send notification (optional)
curl -X POST https://api.telegram.org/bot<YOUR_BOT_TOKEN>/sendMessage \
     -d chat_id=<YOUR_CHAT_ID> \
     -d text="Amar Quran deployment completed successfully at $(date)"