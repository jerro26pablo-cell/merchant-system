from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from categories.models import Category, SizeSystem, SizeSpecification
from listings.models import Listing
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Seed initial data for the application'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial data...')
        
        try:
            # Create categories
            categories_data = [
                {'name': 'Electronics', 'slug': 'electronics', 'category_type': 'main', 'description': 'Electronic devices and accessories'},
                {'name': 'Clothing', 'slug': 'clothing', 'category_type': 'main', 'description': 'Clothing and apparel'},
                {'name': 'Home & Garden', 'slug': 'home-garden', 'category_type': 'main', 'description': 'Home and garden items'},
                {'name': 'Sports', 'slug': 'sports', 'category_type': 'main', 'description': 'Sports equipment and accessories'},
                {'name': 'Books', 'slug': 'books', 'category_type': 'main', 'description': 'Books and publications'},
            ]
            
            for cat_data in categories_data:
                try:
                    category, created = Category.objects.get_or_create(
                        slug=cat_data['slug'],
                        defaults=cat_data
                    )
                    if created:
                        self.stdout.write(f'Created category: {category.name}')
                    else:
                        self.stdout.write(f'Category already exists: {category.name}')
                except Exception as e:
                    logger.error(f"Error creating category {cat_data['name']}: {e}")
                    self.stdout.write(f"Error creating category {cat_data['name']}: {e}")
            
            # Create size system for clothing
            try:
                size_system, created = SizeSystem.objects.get_or_create(
                    name='Clothing Sizes',
                    system_type='alpha',
                    defaults={'name': 'Clothing Sizes', 'system_type': 'alpha'}
                )
                if created:
                    self.stdout.write('Created size system: Clothing Sizes')
                    
                    # Create size specifications
                    sizes = [
                        {'size_value': 'S', 'display_name': 'Small'},
                        {'size_value': 'M', 'display_name': 'Medium'},
                        {'size_value': 'L', 'display_name': 'Large'},
                        {'size_value': 'XL', 'display_name': 'Extra Large'},
                    ]
                    for size_data in sizes:
                        try:
                            spec, created = SizeSpecification.objects.get_or_create(
                                size_system=size_system,
                                size_value=size_data['size_value'],
                                defaults=size_data
                            )
                            if created:
                                self.stdout.write(f'Created size: {spec.display_name}')
                        except Exception as e:
                            logger.error(f"Error creating size {size_data['display_name']}: {e}")
            except Exception as e:
                logger.error(f"Error creating size system: {e}")
                self.stdout.write(f"Error creating size system: {e}")
            
            # Create a test user
            try:
                test_user, created = User.objects.get_or_create(
                    email='test@example.com',
                    defaults={
                        'username': 'testuser',
                        'status': 'active',
                        'email_verified': True,
                    }
                )
                if created:
                    test_user.set_password('testpass123')
                    test_user.save()
                    self.stdout.write('Created test user: test@example.com')
                else:
                    self.stdout.write('Test user already exists: test@example.com')
            except Exception as e:
                logger.error(f"Error creating test user: {e}")
                self.stdout.write(f"Error creating test user: {e}")
            
            self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))
        except Exception as e:
            logger.error(f"Fatal error in seed_data: {e}")
            self.stdout.write(self.style.ERROR(f'Fatal error in seed_data: {e}'))