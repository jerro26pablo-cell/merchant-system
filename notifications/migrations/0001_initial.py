# Generated migration for notifications app
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
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('outbid', 'Outbid'), ('bid_status', 'Bid Status Update'), ('price_drop', 'Price Drop'), ('saved_search', 'Saved Search Match'), ('order_update', 'Order Update'), ('chat_message', 'Chat Message'), ('auto_bid', 'Auto Bid'), ('auction_ended', 'Auction Ended'), ('won_auction', 'Won Auction')], max_length=30)),
                ('title', models.CharField(max_length=200)),
                ('message', models.TextField()),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('related_listing', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='listings.listing')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification',
                'verbose_name_plural': 'Notifications',
                'db_table': 'notifications',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['user', 'is_read'], name='notifications_user_read_idx'),
                    models.Index(fields=['notification_type'], name='notifications_type_idx'),
                ],
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('outbid_notifications', models.BooleanField(default=True)),
                ('bid_status_notifications', models.BooleanField(default=True)),
                ('price_drop_notifications', models.BooleanField(default=True)),
                ('saved_search_notifications', models.BooleanField(default=True)),
                ('order_update_notifications', models.BooleanField(default=True)),
                ('chat_message_notifications', models.BooleanField(default=True)),
                ('email_notifications', models.BooleanField(default=True)),
                ('push_notifications', models.BooleanField(default=True)),
                ('in_app_notifications', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Notification Preference',
                'verbose_name_plural': 'Notification Preferences',
                'db_table': 'notification_preferences',
            },
        ),
    ]
