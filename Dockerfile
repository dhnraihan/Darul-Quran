FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    libpq-dev \
    gettext \
    && apt-get clean

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run migrations
RUN python manage.py migrate --noinput

# Compile translations
RUN python manage.py compilemessages

# Create superuser (optional, for development)
# RUN echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin@amarquran.com', 'adminpass123')" | python manage.py shell

# Run the application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "amar_quran.wsgi:application"]