from django.db import models
from django.utils.translation import gettext_lazy as _

class Category(models.Model):
    CATEGORY_TYPE_CHOICES = [
        ('main', _('Main Category')),
        ('item_type', _('Item Type')),
        ('sub_type', _('Sub Type')),
    ]
    
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPE_CHOICES, default='main')
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('category_detail', kwargs={'slug': self.slug})
    
    @property
    def has_children(self):
        return self.children.exists()
    
    def get_size_systems(self):
        return self.size_systems.filter(is_active=True)

class SizeSystem(models.Model):
    SIZE_SYSTEM_CHOICES = [
        ('alpha', _('Alpha (S, M, L, XL)')),
        ('numeric_waist_length', _('Numeric Waist/Length')),
        ('chest', _('Chest Sizing')),
        ('shoe_us', _('Shoe US')),
        ('shoe_eu', _('Shoe EU')),
        ('shoe_uk', _('Shoe UK')),
        ('none', _('No Size System')),
    ]
    
    name = models.CharField(max_length=100)
    system_type = models.CharField(max_length=30, choices=SIZE_SYSTEM_CHOICES)
    categories = models.ManyToManyField(Category, related_name='size_systems', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'size_systems'
        verbose_name = _('Size System')
        verbose_name_plural = _('Size Systems')
    
    def __str__(self):
        return self.name

class SizeSpecification(models.Model):
    size_system = models.ForeignKey(SizeSystem, on_delete=models.CASCADE, related_name='specifications')
    size_value = models.CharField(max_length=50)
    display_name = models.CharField(max_length=100)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'size_specifications'
        verbose_name = _('Size Specification')
        verbose_name_plural = _('Size Specifications')
        ordering = ['sort_order', 'size_value']
        unique_together = ['size_system', 'size_value']
    
    def __str__(self):
        return f"{self.size_system.name} - {self.display_name}"

class CategoryAttribute(models.Model):
    ATTRIBUTE_TYPE_CHOICES = [
        ('select', _('Select')),
        ('text', _('Text')),
        ('number', _('Number')),
        ('boolean', _('Boolean')),
    ]
    
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='attributes')
    name = models.CharField(max_length=100)
    attribute_type = models.CharField(max_length=20, choices=ATTRIBUTE_TYPE_CHOICES, default='text')
    is_required = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'category_attributes'
        verbose_name = _('Category Attribute')
        verbose_name_plural = _('Category Attributes')
        ordering = ['sort_order', 'name']
    
    def __str__(self):
        return f"{self.category.name} - {self.name}"

class AttributeValue(models.Model):
    attribute = models.ForeignKey(CategoryAttribute, on_delete=models.CASCADE, related_name='values')
    value = models.CharField(max_length=200)
    sort_order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'attribute_values'
        verbose_name = _('Attribute Value')
        verbose_name_plural = _('Attribute Values')
        ordering = ['sort_order', 'value']
        unique_together = ['attribute', 'value']
    
    def __str__(self):
        return f"{self.attribute.name} - {self.value}"
