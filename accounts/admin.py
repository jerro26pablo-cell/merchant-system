from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, SellerProfile, BuyerProfile, RiderProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'username', 'seller_enabled', 'status', 'email_verified', 'is_staff', 'created_at']
    list_filter = ['seller_enabled', 'status', 'email_verified', 'is_staff', 'is_superuser']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('seller_enabled', 'status', 'email_verified', 'phone', 'address')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('email', 'seller_enabled', 'status', 'phone', 'address')}),
    )

@admin.register(SellerProfile)
class SellerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'business_name', 'verification_status', 'rating', 'total_sales']
    list_filter = ['verification_status']
    search_fields = ['user__email', 'business_name']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(BuyerProfile)
class BuyerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'total_purchases', 'total_spent']
    search_fields = ['user__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(RiderProfile)
class RiderProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'vehicle_type', 'availability_status', 'rating', 'total_deliveries']
    list_filter = ['availability_status']
    search_fields = ['user__email', 'vehicle_plate']
    readonly_fields = ['created_at', 'updated_at']
