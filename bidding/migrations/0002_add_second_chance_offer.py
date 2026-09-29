# Generated migration for SecondChanceOffer model

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bidding', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='SecondChanceOffer',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('offer_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('declined', 'Declined'), ('expired', 'Expired')], default='pending', max_length=20)),
                ('expires_at', models.DateTimeField()),
                ('accepted_at', models.DateTimeField(blank=True, null=True)),
                ('declined_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='second_chance_offers', to='accounts.user')),
                ('listing', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='second_chance_offers', to='listings.listing')),
                ('original_bid', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='second_chance_offers', to='bidding.bid')),
            ],
            options={
                'db_table': 'second_chance_offers',
                'verbose_name': 'Second Chance Offer',
                'verbose_name_plural': 'Second Chance Offers',
                'ordering': ['-created_at'],
            },
        ),
    ]