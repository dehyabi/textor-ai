# Use an official Python runtime as a parent image
FROM python:3.10.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput

# Run as non-root user
RUN useradd -m myuser
USER myuser

# Command to run the application
CMD gunicorn speech_to_text_api.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 60 --max-requests 1200 --max-requests-jitter 100 --log-file -
