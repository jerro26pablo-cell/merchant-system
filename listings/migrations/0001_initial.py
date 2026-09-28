# Generated migration for listings app
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('categories', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Listing',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=250, unique=True)),
                ('description', models.TextField()),
                ('listing_type', models.CharField(choices=[('auction', 'Auction'), ('buy_now', 'Buy Now'), ('both', 'Both (Auction + Buy Now)')], default='buy_now', max_length=20)),
                ('status', models.CharField(choices=[('draft', 'Draft'), ('active', 'Active'), ('ended', 'Ended'), ('sold', 'Sold'), ('cancelled', 'Cancelled'), ('relisted', 'Relisted')], default='draft', max_length=20)),
                ('condition', models.CharField(choices=[('new', 'New'), ('like_new', 'Like New'), ('good', 'Good'), ('fair', 'Fair'), ('for_parts', 'For Parts')], default='good', max_length=20)),
                ('quantity', models.IntegerField(default=1, help_text='Total original quantity')),
                ('available_stock', models.IntegerField(default=0, help_text='Available for buy-now purchases')),
                ('auction_quantity', models.IntegerField(default=0, help_text='Quantity allocated to auction')),
                ('quantity_sold', models.IntegerField(default=0, help_text='Total quantity sold')),
                ('starting_bid', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('current_bid', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('buy_now_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('reserve_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('display_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('minimum_increment', models.DecimalField(decimal_places=2, default=1.0, max_digits=10)),
                ('auction_start', models.DateTimeField(blank=True, null=True)),
                ('auction_end', models.DateTimeField(blank=True, null=True)),
                ('anti_snipe_seconds', models.IntegerField(default=300, help_text='Seconds to extend if bid placed near end')),
                ('auto_relist', models.BooleanField(default=False)),
                ('view_count', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='listings', to='categories.category')),
                ('inventory_source', models.ForeignKey(blank=True, help_text='Original buy-now listing if this is an auction created from inventory', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='auction_conversions', to='listings.listing')),
                ('original_listing', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='relistings', to='listings.listing')),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='listings', to=settings.AUTH_USER_MODEL)),
                ('size', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='listings', to='categories.sizespecification')),
            ],
            options={
                'verbose_name': 'Listing',
                'verbose_name_plural': 'Listings',
                'db_table': 'listings',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['status', 'listing_type'], name='listings_status_type_idx'),
                    models.Index(fields=['category'], name='listings_category_idx'),
                    models.Index(fields=['seller'], name='listings_seller_idx'),
                    models.Index(fields=['slug'], name='listings_slug_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='ListingImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', models.ImageField(upload_to='listings/')),
                ('alt_text', models.CharField(blank=True, max_length=200)),
                ('is_primary', models.BooleanField(default=False)),
                ('sort_order', models.IntegerField(default=0)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='images', to='listings.listing')),
            ],
            options={
                'verbose_name': 'Listing Image',
                'verbose_name_plural': 'Listing Images',
                'db_table': 'listing_images',
                'ordering': ['sort_order'],
            },
        ),
        migrations.CreateModel(
            name='ListingAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=500)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='categories.categoryattribute')),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='listings.listing')),
            ],
            options={
                'verbose_name': 'Listing Attribute',
                'verbose_name_plural': 'Listing Attributes',
                'db_table': 'listing_attributes',
                'unique_together': {('listing', 'attribute')},
            },
        ),
        migrations.CreateModel(
            name='ListingView',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('viewed_at', models.DateTimeField(auto_now_add=True)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='views', to='listings.listing')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Listing View',
                'verbose_name_plural': 'Listing Views',
                'db_table': 'listing_views',
                'ordering': ['-viewed_at'],
            },
        ),
        migrations.CreateModel(
            name='InventoryLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('change_type', models.CharField(choices=[('restock', 'Restock'), ('sale', 'Sale'), ('adjustment', 'Adjustment'), ('return', 'Return'), ('relist', 'Relist'), ('auction_conversion', 'Auction Conversion')], max_length=30)),
                ('quantity_before', models.IntegerField()),
                ('quantity_after', models.IntegerField()),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inventory_logs', to='listings.listing')),
            ],
            options={
                'verbose_name': 'Inventory Log',
                'verbose_name_plural': 'Inventory Logs',
                'db_table': 'inventory_logs',
                'ordering': ['-created_at'],
            },
        ),
    ]
