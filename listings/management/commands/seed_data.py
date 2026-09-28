from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from categories.models import Category, SizeSystem, SizeSpecification
from listings.models import Listing

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed initial data for the application'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding initial data...')
        
        # Create categories
        categories_data = [
            {'name': 'Electronics', 'slug': 'electronics', 'category_type': 'main', 'description': 'Electronic devices and accessories'},
            {'name': 'Clothing', 'slug': 'clothing', 'category_type': 'main', 'description': 'Clothing and apparel'},
            {'name': 'Home & Garden', 'slug': 'home-garden', 'category_type': 'main', 'description': 'Home and garden items'},
            {'name': 'Sports', 'slug': 'sports', 'category_type': 'main', 'description': 'Sports equipment and accessories'},
            {'name': 'Books', 'slug': 'books', 'category_type': 'main', 'description': 'Books and publications'},
        ]
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f'Created category: {category.name}')
            else:
                self.stdout.write(f'Category already exists: {category.name}')
        
        # Create size system for clothing
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
                spec, created = SizeSpecification.objects.get_or_create(
                    size_system=size_system,
                    size_value=size_data['size_value'],
                    defaults=size_data
                )
                if created:
                    self.stdout.write(f'Created size: {spec.display_name}')
        
        # Create a test user
        try:
            test_user = User.objects.create_user(
                email='test@example.com',
                username='testuser',
                password='testpass123'
            )
            test_user.status = 'active'
            test_user.email_verified = True
            test_user.save()
            self.stdout.write('Created test user: test@example.com')
        except Exception as e:
            self.stdout.write(f'Test user might already exist: {e}')
        
        self.stdout.write(self.style.SUCCESS('Data seeding completed successfully!'))