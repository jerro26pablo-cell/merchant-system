# Generated migration for categories app
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('slug', models.SlugField(max_length=250, unique=True)),
                ('category_type', models.CharField(choices=[('main', 'Main Category'), ('item_type', 'Item Type'), ('sub_type', 'Sub Type')], default='main', max_length=20)),
                ('description', models.TextField(blank=True)),
                ('image', models.ImageField(blank=True, null=True, upload_to='categories/')),
                ('sort_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='categories.category')),
            ],
            options={
                'verbose_name': 'Category',
                'verbose_name_plural': 'Categories',
                'db_table': 'categories',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='SizeSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('system_type', models.CharField(choices=[('alpha', 'Alpha (S, M, L, XL)'), ('numeric_waist_length', 'Numeric Waist/Length'), ('chest', 'Chest Sizing'), ('shoe_us', 'Shoe US'), ('shoe_eu', 'Shoe EU'), ('shoe_uk', 'Shoe UK'), ('none', 'No Size System')], max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Size System',
                'verbose_name_plural': 'Size Systems',
                'db_table': 'size_systems',
            },
        ),
        migrations.CreateModel(
            name='SizeSpecification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('size_value', models.CharField(max_length=50)),
                ('display_name', models.CharField(max_length=100)),
                ('sort_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('size_system', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='specifications', to='categories.sizesystem')),
            ],
            options={
                'verbose_name': 'Size Specification',
                'verbose_name_plural': 'Size Specifications',
                'db_table': 'size_specifications',
                'ordering': ['sort_order', 'size_value'],
            },
        ),
        migrations.CreateModel(
            name='CategoryAttribute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('attribute_type', models.CharField(choices=[('select', 'Select'), ('text', 'Text'), ('number', 'Number'), ('boolean', 'Boolean')], default='text', max_length=20)),
                ('is_required', models.BooleanField(default=False)),
                ('sort_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='attributes', to='categories.category')),
            ],
            options={
                'verbose_name': 'Category Attribute',
                'verbose_name_plural': 'Category Attributes',
                'db_table': 'category_attributes',
                'ordering': ['sort_order', 'name'],
            },
        ),
        migrations.CreateModel(
            name='AttributeValue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('value', models.CharField(max_length=200)),
                ('sort_order', models.IntegerField(default=0)),
                ('is_active', models.BooleanField(default=True)),
                ('attribute', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='values', to='categories.categoryattribute')),
            ],
            options={
                'verbose_name': 'Attribute Value',
                'verbose_name_plural': 'Attribute Values',
                'db_table': 'attribute_values',
                'ordering': ['sort_order', 'value'],
            },
        ),
        migrations.AddField(
            model_name='sizesystem',
            name='categories',
            field=models.ManyToManyField(blank=True, related_name='size_systems', to='categories.category'),
        ),
        migrations.AlterUniqueTogether(
            name='sizespecification',
            unique_together={('size_system', 'size_value')},
        ),
        migrations.AlterUniqueTogether(
            name='attributevalue',
            unique_together={('attribute', 'value')},
        ),
    ]
