from django.db import models
from django.contrib.auth import get_user_model
from listings.models import Listing

User = get_user_model()

class Notification(models.Model):
    NOTIFICATION_TYPE_CHOICES = [
        ('outbid', _('Outbid')),
        ('bid_status', _('Bid Status Update')),
        ('price_drop', _('Price Drop')),
        ('saved_search', _('Saved Search Match')),
        ('order_update', _('Order Update')),
        ('chat_message', _('Chat Message')),
        ('auto_bid', _('Auto Bid')),
        ('auction_ended', _('Auction Ended')),
        ('won_auction', _('Won Auction')),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_listing = models.ForeignKey(Listing, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'notifications'
        verbose_name = _('Notification')
        verbose_name_plural = _('Notifications')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'is_read']),
            models.Index(fields=['notification_type']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.title}"
    
    def mark_as_read(self):
        self.is_read = True
        self.save()

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_preferences')
    outbid_notifications = models.BooleanField(default=True)
    bid_status_notifications = models.BooleanField(default=True)
    price_drop_notifications = models.BooleanField(default=True)
    saved_search_notifications = models.BooleanField(default=True)
    order_update_notifications = models.BooleanField(default=True)
    chat_message_notifications = models.BooleanField(default=True)
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    in_app_notifications = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = _('Notification Preference')
        verbose_name_plural = _('Notification Preferences')
    
    def __str__(self):
        return f"{self.user.email} - Preferences"
