import os
import sys
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

# Ensure media directory exists
from config.settings import MEDIA_ROOT
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)

# Export ASGI app for uvicorn (matching your flower shop pattern)
from config.asgi import application as app
