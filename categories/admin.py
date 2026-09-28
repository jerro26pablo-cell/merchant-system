from django.contrib import admin
from .models import Category, SizeSystem, SizeSpecification, CategoryAttribute, AttributeValue

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'parent', 'is_active', 'sort_order']
    list_filter = ['category_type', 'is_active']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['sort_order', 'name']

@admin.register(SizeSystem)
class SizeSystemAdmin(admin.ModelAdmin):
    list_display = ['name', 'system_type', 'is_active']
    list_filter = ['system_type', 'is_active']
    filter_horizontal = ['categories']

@admin.register(SizeSpecification)
class SizeSpecificationAdmin(admin.ModelAdmin):
    list_display = ['size_system', 'size_value', 'display_name', 'sort_order']
    list_filter = ['size_system', 'is_active']
    ordering = ['size_system', 'sort_order', 'size_value']

@admin.register(CategoryAttribute)
class CategoryAttributeAdmin(admin.ModelAdmin):
    list_display = ['category', 'name', 'attribute_type', 'is_required', 'sort_order']
    list_filter = ['attribute_type', 'is_required', 'is_active']
    ordering = ['category', 'sort_order', 'name']

@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute', 'value', 'sort_order']
    list_filter = ['attribute__category', 'is_active']
    ordering = ['attribute', 'sort_order', 'value']
