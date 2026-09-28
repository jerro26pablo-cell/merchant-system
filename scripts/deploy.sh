#!/bin/bash
# Render Deployment Script
# This script ensures proper Django deployment on Render

echo "Starting Django deployment on Render..."

# Install dependencies
pip install -r requirements.txt

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate --noinput

echo "Deployment completed successfully!"
