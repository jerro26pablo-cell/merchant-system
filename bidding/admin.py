from django.contrib import admin
from django.utils import timezone
from .models import Bid, MaxBidCap, BidCancellationRequest, AuctionExtension

@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ['listing', 'bidder', 'amount', 'status', 'is_auto_bid', 'created_at']
    list_filter = ['status', 'is_auto_bid', 'created_at']
    search_fields = ['listing__title', 'bidder__email']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'

@admin.register(MaxBidCap)
class MaxBidCapAdmin(admin.ModelAdmin):
    list_display = ['listing', 'bidder', 'max_amount', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['listing__title', 'bidder__email']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(BidCancellationRequest)
class BidCancellationRequestAdmin(admin.ModelAdmin):
    list_display = ['bid', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['bid__listing__title', 'user__email']
    readonly_fields = ['created_at', 'reviewed_at']
    actions = ['approve_requests', 'deny_requests']
    
    def approve_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='approved', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{updated} request(s) approved.')
    approve_requests.short_description = 'Approve selected requests'
    
    def deny_requests(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='denied', reviewed_by=request.user, reviewed_at=timezone.now())
        self.message_user(request, f'{updated} request(s) denied.')
    deny_requests.short_description = 'Deny selected requests'

@admin.register(AuctionExtension)
class AuctionExtensionAdmin(admin.ModelAdmin):
    list_display = ['listing', 'extension_seconds', 'previous_end', 'new_end', 'created_at']
    list_filter = ['created_at']
    search_fields = ['listing__title']
    readonly_fields = ['created_at']
