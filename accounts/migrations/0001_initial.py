# Generated migration for accounts app
from django.conf import settings
from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, help_text='Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.', max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('first_name', models.CharField(blank=True, max_length=150, verbose_name='first name')),
                ('last_name', models.CharField(blank=True, max_length=150, verbose_name='last name')),
                ('is_staff', models.BooleanField(default=False, help_text='Designates whether the user can log into this admin site.', verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='active')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('email', models.EmailField(max_length=254, unique=True, verbose_name='email address')),
                ('seller_enabled', models.BooleanField(default=False, help_text='Whether user has enabled seller mode')),
                ('status', models.CharField(choices=[('active', 'Active'), ('suspended', 'Suspended'), ('pending', 'Pending')], default='pending', max_length=20)),
                ('email_verified', models.BooleanField(default=False)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('province', models.CharField(blank=True, help_text='Province', max_length=100)),
                ('municipality', models.CharField(blank=True, help_text='Municipality/City', max_length=100)),
                ('address', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
                'db_table': 'users',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SellerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('business_name', models.CharField(blank=True, max_length=200)),
                ('business_address', models.TextField(blank=True)),
                ('business_description', models.TextField(blank=True)),
                ('verification_status', models.CharField(choices=[('pending', 'Pending'), ('verified', 'Verified'), ('rejected', 'Rejected')], default='pending', max_length=20)),
                ('rating', models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ('total_sales', models.IntegerField(default=0)),
                ('total_reviews', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='seller_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Seller Profile',
                'verbose_name_plural': 'Seller Profiles',
                'db_table': 'seller_profiles',
            },
        ),
        migrations.CreateModel(
            name='BuyerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('shipping_address', models.TextField(blank=True)),
                ('billing_address', models.TextField(blank=True)),
                ('total_purchases', models.IntegerField(default=0)),
                ('total_spent', models.DecimalField(decimal_places=2, default=0.0, max_digits=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='buyer_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Buyer Profile',
                'verbose_name_plural': 'Buyer Profiles',
                'db_table': 'buyer_profiles',
            },
        ),
        migrations.CreateModel(
            name='RiderProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_type', models.CharField(blank=True, max_length=50)),
                ('vehicle_plate', models.CharField(blank=True, max_length=20)),
                ('availability_status', models.CharField(choices=[('available', 'Available'), ('busy', 'Busy'), ('offline', 'Offline')], default='offline', max_length=20)),
                ('rating', models.DecimalField(decimal_places=2, default=0.0, max_digits=3)),
                ('total_deliveries', models.IntegerField(default=0)),
                ('current_location_lat', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('current_location_lng', models.DecimalField(blank=True, decimal_places=6, max_digits=9, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='rider_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Rider Profile',
                'verbose_name_plural': 'Rider Profiles',
                'db_table': 'rider_profiles',
            },
        ),
    ]
