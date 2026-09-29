from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'buyer', 'listing', 'status', 'total_amount', 'created_at']
    list_filter = ['status', 'order_type', 'payment_method', 'created_at']
    search_fields = ['order_number', 'buyer__email', 'listing__title']
    readonly_fields = ['order_number', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'