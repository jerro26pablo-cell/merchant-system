import os
import sys
from pathlib import Path

# Add the project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Import Django and setup
import django
django.setup()

# Run migrations before starting the server
if __name__ == '__main__':
    from django.core.management import execute_from_command_line
    
    # First, run migrations
    print("Running migrations...")
    execute_from_command_line(['manage.py', 'migrate', '--noinput'])
    
    # Then, collect static files
    print("Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    # Finally, start the server
    import uvicorn
    from config.asgi import application
    
    port = int(os.environ.get('PORT', 8000))
    print(f"Starting uvicorn on port {port}...")
    uvicorn.run(application, host='0.0.0.0', port=port, log_level='info')
