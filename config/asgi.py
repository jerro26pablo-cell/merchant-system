import os
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Disable lifespan protocol for now since we're not using WebSockets
application = get_asgi_application()
