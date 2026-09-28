#!/bin/bash
# Startup script to ensure database is properly configured

set -e  # Exit on any error

echo "=== Starting Django Application ==="
echo "Running startup tasks..."

# Check database configuration
echo "Checking database configuration..."
python manage.py check_db || {
    echo "WARNING: Database check failed, but continuing..."
}

# Run migrations
echo "Running database migrations..."
python manage.py migrate --noinput || {
    echo "ERROR: Migrations failed!"
    exit 1
}

# Seed initial data
echo "Seeding initial data..."
python manage.py seed_data || {
    echo "WARNING: Data seeding failed, but continuing..."
}

echo "Startup tasks completed successfully."
echo "=== Starting Gunicorn Server ==="

# Start the application
exec gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120 --access-logfile - --error-logfile -