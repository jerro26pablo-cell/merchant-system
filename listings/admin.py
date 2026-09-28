from django.contrib import admin
from .models import Listing, ListingImage, ListingAttribute, ListingView, InventoryLog

class ListingImageInline(admin.TabularInline):
    model = ListingImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']

class ListingAttributeInline(admin.TabularInline):
    model = ListingAttribute
    extra = 1

@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['title', 'seller', 'listing_type', 'status', 'current_price', 'quantity', 'available_stock', 'created_at']
    list_filter = ['listing_type', 'status', 'condition', 'category', 'is_active']
    search_fields = ['title', 'slug', 'seller__email', 'description']
    prepopulated_fields = {'slug': ('title',)}
    readonly_fields = ['view_count', 'created_at', 'updated_at']
    inlines = [ListingImageInline, ListingAttributeInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('seller', 'title', 'slug', 'description', 'category', 'condition')
        }),
        ('Listing Type & Status', {
            'fields': ('listing_type', 'status', 'is_active')
        }),
        ('Quantity Management', {
            'fields': ('quantity', 'available_stock', 'auction_quantity', 'quantity_sold')
        }),
        ('Pricing', {
            'fields': ('starting_bid', 'current_bid', 'buy_now_price', 'reserve_price', 'display_price', 'minimum_increment')
        }),
        ('Auction Settings', {
            'fields': ('auction_start', 'auction_end', 'anti_snipe_seconds', 'auto_relist')
        }),
        ('Size', {
            'fields': ('size',)
        }),
        ('Tracking', {
            'fields': ('view_count', 'original_listing', 'inventory_source')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(ListingImage)
class ListingImageAdmin(admin.ModelAdmin):
    list_display = ['listing', 'is_primary', 'sort_order', 'created_at']
    list_filter = ['is_primary']
    search_fields = ['listing__title', 'alt_text']

@admin.register(ListingAttribute)
class ListingAttributeAdmin(admin.ModelAdmin):
    list_display = ['listing', 'attribute', 'value']
    search_fields = ['listing__title', 'attribute__name', 'value']

@admin.register(ListingView)
class ListingViewAdmin(admin.ModelAdmin):
    list_display = ['listing', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['listing__title', 'user__email']
    readonly_fields = ['viewed_at']

@admin.register(InventoryLog)
class InventoryLogAdmin(admin.ModelAdmin):
    list_display = ['listing', 'change_type', 'quantity_before', 'quantity_after', 'created_at']
    list_filter = ['change_type', 'created_at']
    search_fields = ['listing__title']
    readonly_fields = ['created_at']
