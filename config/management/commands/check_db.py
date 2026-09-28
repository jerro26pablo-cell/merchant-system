from django.core.management.base import BaseCommand
from django.db import connection, DatabaseError
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Check database connectivity and configuration'

    def handle(self, *args, **kwargs):
        self.stdout.write('Checking database configuration and connectivity...')
        
        # Check all environment variables
        self.stdout.write('\n=== All Environment Variables ===')
        all_env = {k: v for k, v in os.environ.items() if 'DB' in k.upper() or 'DATABASE' in k.upper()}
        for key, value in sorted(all_env.items()):
            if 'PASSWORD' in key or 'SECRET' in key:
                self.stdout.write(f'{key}: {"*" * len(value)}')
            else:
                self.stdout.write(f'{key}: {value}')
        
        # Check specific DATABASE_URL
        self.stdout.write('\n=== DATABASE_URL Details ===')
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            self.stdout.write(f'DATABASE_URL: {"*" * (len(db_url) - 20)}{db_url[-20:]}')  # Show last 20 chars
            # Try to parse and show components
            try:
                import dj_database_url
                parsed = dj_database_url.parse(db_url)
                self.stdout.write(f'Parsed ENGINE: {parsed.get("ENGINE")}')
                self.stdout.write(f'Parsed NAME: {parsed.get("NAME")}')
                self.stdout.write(f'Parsed USER: {parsed.get("USER")}')
                self.stdout.write(f'Parsed HOST: {parsed.get("HOST")}')
                self.stdout.write(f'Parsed PORT: {parsed.get("PORT")}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error parsing DATABASE_URL: {e}'))
        else:
            self.stdout.write(self.style.ERROR('DATABASE_URL: NOT SET'))
        
        self.stdout.write(f'RENDER: {"SET" if "RENDER" in os.environ else "NOT SET"}')
        
        # Check Django database configuration
        self.stdout.write('\n=== Django Database Configuration ===')
        db_config = settings.DATABASES['default']
        self.stdout.write(f'ENGINE: {db_config["ENGINE"]}')
        self.stdout.write(f'NAME: {db_config["NAME"]}')
        self.stdout.write(f'USER: {db_config.get("USER", "NOT SET")}')
        self.stdout.write(f'HOST: {db_config.get("HOST", "NOT SET")}')
        self.stdout.write(f'PORT: {db_config.get("PORT", "NOT SET")}')
        
        # Test database connection
        self.stdout.write('\n=== Testing Database Connection ===')
        try:
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
                result = cursor.fetchone()
                if result and result[0] == 1:
                    self.stdout.write(self.style.SUCCESS('✓ Database connection successful'))
                else:
                    self.stdout.write(self.style.ERROR('✗ Database query returned unexpected result'))
        except DatabaseError as e:
            self.stdout.write(self.style.ERROR(f'✗ Database connection failed: {e}'))
            logger.error(f"Database connection error: {e}", exc_info=True)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Unexpected error: {e}'))
            logger.error(f"Unexpected database error: {e}", exc_info=True)
        
        # Check if tables exist
        self.stdout.write('\n=== Checking Database Tables ===')
        try:
            with connection.cursor() as cursor:
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name;
                """)
                tables = cursor.fetchall()
                if tables:
                    self.stdout.write(f'Found {len(tables)} tables:')
                    for table in tables:
                        self.stdout.write(f'  - {table[0]}')
                else:
                    self.stdout.write(self.style.WARNING('No tables found - run migrations'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error checking tables: {e}'))
        
        self.stdout.write('\n=== Database Check Complete ===')