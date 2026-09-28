#!/usr/bin/env python
"""
Startup script to ensure database is properly configured before starting the application
"""
import os
import sys
import subprocess
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(command, description):
    """Run a command and log the result"""
    logger.info(f"Running: {description}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"✓ {description} completed successfully")
        if result.stdout:
            logger.info(f"Output: {result.stdout[:500]}")  # Log first 500 chars
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"✗ {description} failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"Stdout: {e.stdout}")
        if e.stderr:
            logger.error(f"Stderr: {e.stderr}")
        return False

def main():
    logger.info("=== Starting Django Application ===")
    logger.info("Running startup tasks...")
    
    # Run migrations (critical)
    if not run_command("python manage.py migrate --noinput", "Database migrations"):
        logger.error("CRITICAL: Migrations failed, cannot start application")
        sys.exit(1)
    
    # Seed initial data (optional)
    if not run_command("python manage.py seed_data", "Initial data seeding"):
        logger.warning("Data seeding failed, but continuing...")
    
    logger.info("Startup tasks completed successfully")
    logger.info("=== Starting Gunicorn Server ===")
    
    # Start the application
    port = os.environ.get('PORT', '8000')
    gunicorn_cmd = f"gunicorn config.wsgi:application --bind 0.0.0.0:{port} --workers 2 --timeout 120 --access-logfile - --error-logfile -"
    
    logger.info(f"Starting gunicorn on port {port}")
    os.execvp("gunicorn", gunicorn_cmd.split())

if __name__ == "__main__":
    main()