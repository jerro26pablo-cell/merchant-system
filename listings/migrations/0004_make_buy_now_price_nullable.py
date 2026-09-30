# Generated migration to make buy_now_price nullable
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0003_add_wishlist_conversation_message'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='buy_now_price',
            field=models.DecimalField(blank=True, max_digits=10, decimal_places=2, null=True),
        ),
    ]
