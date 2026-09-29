# Generated migration to add shipping_address field
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='shipping_address',
            field=models.TextField(blank=True, help_text='Shipping address for this listing'),
        ),
    ]
