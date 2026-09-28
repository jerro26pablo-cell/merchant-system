# Generated migration for bidding app
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('listings', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Bid',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('active', 'Active'), ('outbid', 'Outbid'), ('winning', 'Winning'), ('won', 'Won'), ('cancelled', 'Cancelled'), ('pending_cancel', 'Pending Cancel')], default='active', max_length=20)),
                ('is_auto_bid', models.BooleanField(default=False, help_text='Whether this was an automatic proxy bid')),
                ('personal_increment', models.DecimalField(blank=True, decimal_places=2, help_text="Bidder's preferred increment for this listing", max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bidder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to=settings.AUTH_USER_MODEL)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bids', to='listings.listing')),
            ],
            options={
                'verbose_name': 'Bid',
                'verbose_name_plural': 'Bids',
                'db_table': 'bids',
                'ordering': ['-amount', '-created_at'],
                'indexes': [
                    models.Index(fields=['listing', 'status'], name='bids_listing_status_idx'),
                    models.Index(fields=['bidder', 'status'], name='bids_bidder_status_idx'),
                    models.Index(fields=['listing', '-amount'], name='bids_listing_amount_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='MaxBidCap',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('is_active', models.BooleanField(default=True)),
                ('personal_increment', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('bidder', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='max_bid_caps', to=settings.AUTH_USER_MODEL)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='max_bid_caps', to='listings.listing')),
            ],
            options={
                'verbose_name': 'Max Bid Cap',
                'verbose_name_plural': 'Max Bid Caps',
                'db_table': 'max_bid_caps',
                'unique_together': {('listing', 'bidder')},
                'indexes': [
                    models.Index(fields=['listing', 'is_active'], name='maxbidcaps_listing_active_idx'),
                    models.Index(fields=['bidder', 'is_active'], name='maxbidcaps_bidder_active_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='BidCancellationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('reason', models.TextField()),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('approved', 'Approved'), ('denied', 'Denied')], default='pending', max_length=20)),
                ('admin_notes', models.TextField(blank=True)),
                ('reviewed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('bid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cancellation_requests', to='bidding.bid')),
                ('reviewed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='reviewed_cancellations', to=settings.AUTH_USER_MODEL)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bid_cancellation_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Bid Cancellation Request',
                'verbose_name_plural': 'Bid Cancellation Requests',
                'db_table': 'bid_cancellation_requests',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='AuctionExtension',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('previous_end', models.DateTimeField()),
                ('new_end', models.DateTimeField()),
                ('extension_seconds', models.IntegerField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auction_extensions', to='listings.listing')),
                ('triggered_by_bid', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='bidding.bid')),
            ],
            options={
                'verbose_name': 'Auction Extension',
                'verbose_name_plural': 'Auction Extensions',
                'db_table': 'auction_extensions',
                'ordering': ['-created_at'],
            },
        ),
    ]
