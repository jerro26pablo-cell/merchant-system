# Generated migration for riders app

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='RiderLocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('latitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('longitude', models.DecimalField(decimal_places=6, max_digits=9)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('rider', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='rider_locations', to='accounts.user')),
            ],
            options={
                'db_table': 'rider_locations',
                'verbose_name': 'Rider Location',
                'verbose_name_plural': 'Rider Locations',
                'ordering': ['-timestamp'],
            },
        ),
    ]