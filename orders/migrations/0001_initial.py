# Generated migration for orders app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
        ('listings', '0001_initial'),
        ('bidding', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Order',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_type', models.CharField(choices=[('buy_now', 'Buy Now'), ('auction_win', 'Auction Win'), ('second_chance', 'Second Chance Offer')], max_length=20)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('paid', 'Paid'), ('processing', 'Processing'), ('rider_assigned', 'Rider Assigned'), ('rider_accepted', 'Rider Accepted'), ('picked_up', 'Picked Up'), ('in_transit', 'In Transit'), ('shipped', 'Shipped'), ('delivered', 'Delivered'), ('cancelled', 'Cancelled'), ('disputed', 'Disputed')], default='pending', max_length=20)),
                ('order_number', models.CharField(max_length=50, unique=True)),
                ('quantity', models.IntegerField(default=1)),
                ('total_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_method', models.CharField(choices=[('online', 'Online Payment'), ('cod', 'Cash on Delivery')], default='online', max_length=20)),
                ('is_paid', models.BooleanField(default=False)),
                ('paid_at', models.DateTimeField(blank=True, null=True)),
                ('shipping_address', models.TextField()),
                ('tracking_number', models.CharField(blank=True, max_length=100)),
                ('carrier', models.CharField(blank=True, max_length=100)),
                ('escrow_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('escrow_released', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='accounts.user')),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orders', to='listings.listing')),
                ('rider', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='assigned_orders', to='accounts.user')),
                ('second_chance_offer', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='orders', to='bidding.secondchanceoffer')),
            ],
            options={
                'db_table': 'orders',
                'verbose_name': 'Order',
                'verbose_name_plural': 'Orders',
                'ordering': ['-created_at'],
            },
        ),
    ]