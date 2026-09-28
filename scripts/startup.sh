#!/bin/bash
# Startup script to ensure database is properly configured

echo "Running startup tasks..."

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput

# Seed initial data
echo "Seeding initial data..."
python manage.py seed_data

echo "Startup tasks completed. Starting application..."

# Start the application
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -