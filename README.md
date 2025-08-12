# Amar Quran - Online Qur'an Learning Platform

A comprehensive Django-based platform for one-to-one live Qur'an, Hifz, Arabic, and Islamic studies courses.

## Features

- **User Management**: Student, Teacher, and Admin roles with custom user model
- **Course Management**: Multiple course types including Hifz, Qur'an recitation, Arabic, Aqeedah
- **Live Classes**: Integration with Teams, Zoom, Google Meet, and WhatsApp
- **Payment Processing**: SSLCommerz for Bangladesh, Stripe for international payments
- **Multi-language Support**: Bengali and English UI
- **Assessment System**: Multi-step assessment form for new students
- **Teacher Management**: Profile, ratings, reviews, and availability scheduling
- **Student Dashboard**: Track progress, upcoming classes, payments
- **Teacher Dashboard**: Manage schedule, students, earnings
- **Automated Notifications**: Email and WhatsApp reminders via Twilio

## Technology Stack

- **Backend**: Django 4.2+
- **Database**: PostgreSQL
- **Cache/Queue**: Redis + Celery
- **Frontend**: TailwindCSS (CDN)
- **Payment**: SSLCommerz, Stripe
- **Communications**: Twilio (WhatsApp), Microsoft Graph API (Teams)
- **Deployment**: Gunicorn + Nginx + Systemd

## Installation

### Prerequisites
- Python 
- PostgreSQL 
- Redis

### Local Development Setup

1. Clone the repository:
```bash
git clone https://github.com/dhnraihan/amar_quran.git
cd amar_quran






10. API Integration Examples
integrations/teams.py

Python

"""
Microsoft Teams Integration
This module handles Teams meeting creation using Microsoft Graph API
"""

import requests
from msal import ConfidentialClientApplication
from django.conf import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class TeamsIntegration:
    """
    Microsoft Teams meeting integration using Graph API
    
    OAuth 2.0 Authentication Flow:
    1. Register app in Azure AD
    2. Get client credentials (ID, Secret, Tenant)
    3. Request access token using MSAL
    4. Use token to call Graph API
    """
    
    def __init__(self):
        self.client_id = settings.MICROSOFT_CLIENT_ID
        self.client_secret = settings.MICROSOFT_CLIENT_SECRET
        self.tenant_id = settings.MICROSOFT_TENANT_ID
        self.authority = f"https://login.microsoftonline.com/{self.tenant_id}"
        self.scope = ["https://graph.microsoft.com/.default"]
        
        # Initialize MSAL client
        self.app = ConfidentialClientApplication(
            self.client_id,
            authority=self.authority,
            client_credential=self.client_secret,
        )
    
    def get_access_token(self):
        """Get access token for Graph API"""
        result = self.app.acquire_token_silent(self.scope, account=None)
        
        if not result:
            result = self.app.acquire_token_for_client(scopes=self.scope)
        
        if "access_token" in result:
            return result["access_token"]
        else:
            logger.error(f"Token acquisition failed: {result.get('error')}")
            return None
    
    def create_meeting(self, subject, start_time, end_time, attendees):
        """
        Create a Teams meeting
        
        Args:
            subject: Meeting subject
            start_time: datetime object for start
            end_time: datetime object for end
            attendees: List of email addresses
        
        Returns:
            dict: Meeting details including join URL
        """
        token = self.get_access_token()
        if not token:
            return None
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Prepare meeting data
        meeting_data = {
            "subject": subject,
            "startDateTime": start_time.isoformat(),
            "endDateTime": end_time.isoformat(),
            "isOnlineMeeting": True,
            "onlineMeetingProvider": "teamsForBusiness",
            "attendees": [
                {
                    "emailAddress": {
                        "address": email
                    },
                    "type": "required"
                } for email in attendees
            ]
        }
        
        # Create calendar event with Teams meeting
        # This requires delegated permissions or application permissions with user context
        # For simplicity, using application permissions to create meetings
        
        url = "https://graph.microsoft.com/v1.0/users/{organizer}/events"
        
        try:
            response = requests.post(url, headers=headers, json=meeting_data)
            response.raise_for_status()
            
            meeting = response.json()
            
            return {
                'id': meeting.get('id'),
                'join_url': meeting.get('onlineMeeting', {}).get('joinUrl'),
                'subject': meeting.get('subject'),
                'start': meeting.get('start'),
                'end': meeting.get('end')
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create Teams meeting: {str(e)}")
            return None
    
    def update_meeting(self, meeting_id, updates):
        """Update existing Teams meeting"""
        token = self.get_access_token()
        if not token:
            return None
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        url = f"https://graph.microsoft.com/v1.0/me/events/{meeting_id}"
        
        try:
            response = requests.patch(url, headers=headers, json=updates)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to update Teams meeting: {str(e)}")
            return None
    
    def cancel_meeting(self, meeting_id, message="Meeting cancelled"):
        """Cancel a Teams meeting"""
        token = self.get_access_token()
        if not token:
            return False
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        # Cancel by updating the meeting status
        cancel_data = {
            "isCancelled": True,
            "responseStatus": {
                "response": "declined",
                "time": datetime.utcnow().isoformat()
            }
        }
        
        url = f"https://graph.microsoft.com/v1.0/me/events/{meeting_id}"
        
        try:
            response = requests.patch(url, headers=headers, json=cancel_data)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to cancel Teams meeting: {str(e)}")
            return False


# Example usage in views
def create_class_meeting(session):
    """
    Create Teams meeting for a class session
    """
    teams = TeamsIntegration()
    
    meeting = teams.create_meeting(
        subject=f"{session.course.title} - Class Session",
        start_time=datetime.combine(session.date, session.start_time),
        end_time=datetime.combine(session.date, session.end_time),
        attendees=[session.teacher.email, session.student.email]
    )
    
    if meeting:
        session.meeting_link = meeting['join_url']
        session.meeting_id = meeting['id']
        session.save()
        return True
    
    return False






11. Deployment Configuration
nginx.conf

nginx

server {
    listen 80;
    server_name amarquran.com www.amarquran.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name amarquran.com www.amarquran.com;
    
    ssl_certificate /etc/letsencrypt/live/amarquran.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/amarquran.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
    
    client_max_body_size 100M;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static/ {
        alias /home/ubuntu/amar_quran/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /home/ubuntu/amar_quran/media/;
        expires 7d;
        add_header Cache-Control "public";
    }
}

systemd service file (amar_quran.service)

ini

[Unit]
Description=Amar Quran Django Application
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/amar_quran
Environment="PATH=/home/ubuntu/amar_quran/venv/bin"
ExecStart=/home/ubuntu/amar_quran/venv/bin/gunicorn \
          --workers 3 \
          --bind 127.0.0.1:8000 \
          --timeout 120 \
          --access-logfile /var/log/amar_quran/access.log \
          --error-logfile /var/log/amar_quran/error.log \
          amar_quran.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target





    Create virtual environment:

Bash

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

    Install dependencies:

Bash

pip install -r requirements.txt

    Copy environment variables:

Bash

cp .env.example .env
# Edit .env with your configuration

    Setup database:

Bash

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

    Collect static files:

Bash

python manage.py collectstatic

    Load initial data (optional):

Bash

python manage.py loaddata initial_data.json

    Run development server:

Bash

python manage.py runserver

    Start Celery worker (in another terminal):

Bash

celery -A amar_quran worker -l info

    Start Celery beat (for scheduled tasks):

Bash

celery -A amar_quran beat -l info

Production Deployment
Server Setup (Ubuntu/Debian)

    Update system:

Bash

sudo apt update && sudo apt upgrade -y

    Install dependencies:

Bash

sudo apt install python3-pip python3-venv postgresql postgresql-contrib nginx redis-server supervisor

    Clone and setup project:

Bash

cd /home/ubuntu
git clone https://github.com/yourusername/amar_quran.git
cd amar_quran
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

    Configure PostgreSQL:

Bash

sudo -u postgres psql
CREATE DATABASE amar_quran;
CREATE USER amar_quran_user WITH PASSWORD 'your_password';
ALTER ROLE amar_quran_user SET client_encoding TO 'utf8';
ALTER ROLE amar_quran_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE amar_quran_user SET timezone TO 'Asia/Dhaka';
GRANT ALL PRIVILEGES ON DATABASE amar_quran TO amar_quran_user;
\q

    Configure environment:

Bash

cp .env.example .env
nano .env  # Update with production values

    Run migrations and collect static:

Bash

python manage.py migrate
python manage.py collectstatic --noinput

    Setup Gunicorn with systemd:

Bash

sudo cp deployment/amar_quran.service /etc/systemd/system/
sudo systemctl start amar_quran
sudo systemctl enable amar_quran

    Configure Nginx:

Bash

sudo cp deployment/nginx.conf /etc/nginx/sites-available/amar_quran
sudo ln -s /etc/nginx/sites-available/amar_quran /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

    Setup SSL with Certbot:

Bash

sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d amarquran.com -d www.amarquran.com

    Setup Celery with Supervisor:

Bash

sudo cp deployment/celery.conf /etc/supervisor/conf.d/
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all






















13. GitHub Actions CI/CD

### .github/workflows/django.yml
```yaml
name: Django CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_amar_quran
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 6379:6379
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Cache pip packages
      uses: actions/cache@v3
      with:
        path: ~/.cache/pip
        key: ${{ runner.os }}-pip-${{ hashFiles('requirements.txt') }}
        restore-keys: |
          ${{ runner.os }}-pip-
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_amar_quran
        REDIS_URL: redis://localhost:6379/0
        SECRET_KEY: test-secret-key
        DEBUG: True
      run: |
        python manage.py migrate
        python manage.py test
    
    - name: Generate coverage report
      run: |
        pip install coverage
        coverage run --source='.' manage.py test
        coverage xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: unittests
        name: codecov-umbrella

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' && github.event_name == 'push'
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.SSH_KEY }}
        script: |
          cd /home/ubuntu/amar_quran
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          python manage.py migrate
          python manage.py collectstatic --noinput
          sudo systemctl restart amar_quran
          sudo systemctl restart nginx