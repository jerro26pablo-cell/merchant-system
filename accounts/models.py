from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    USER_STATUS_CHOICES = [
        ('active', _('Active')),
        ('suspended', _('Suspended')),
        ('pending', _('Pending')),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    seller_enabled = models.BooleanField(default=False, help_text=_('Whether user has enabled seller mode'))
    status = models.CharField(max_length=20, choices=USER_STATUS_CHOICES, default='pending')
    email_verified = models.BooleanField(default=False)
    phone = models.CharField(max_length=20, blank=True)
    province = models.CharField(max_length=100, blank=True, help_text=_('Province'))
    municipality = models.CharField(max_length=100, blank=True, help_text=_('Municipality/City'))
    address = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = 'users'
        verbose_name = _('User')
        verbose_name_plural = _('Users')
    
    def __str__(self):
        return self.email
    
    @property
    def is_seller(self):
        return self.seller_enabled and self.status == 'active'
    
    @property
    def is_buyer(self):
        return self.status == 'active'
    
    def enable_seller_mode(self):
        if not self.seller_enabled:
            self.seller_enabled = True
            self.save()
            # SellerProfile creation is handled in the view to avoid circular import
    
    def disable_seller_mode(self):
        if self.seller_enabled:
            self.seller_enabled = False
            self.save()

class SellerProfile(models.Model):
    VERIFICATION_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('verified', _('Verified')),
        ('rejected', _('Rejected')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='seller_profile')
    business_name = models.CharField(max_length=200, blank=True)
    business_address = models.TextField(blank=True)
    business_description = models.TextField(blank=True)
    verification_status = models.CharField(max_length=20, choices=VERIFICATION_STATUS_CHOICES, default='pending')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_sales = models.IntegerField(default=0)
    total_reviews = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'seller_profiles'
        verbose_name = _('Seller Profile')
        verbose_name_plural = _('Seller Profiles')
    
    def __str__(self):
        return f"{self.user.email} - {self.business_name or 'No Business Name'}"

class BuyerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='buyer_profile')
    shipping_address = models.TextField(blank=True)
    billing_address = models.TextField(blank=True)
    total_purchases = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'buyer_profiles'
        verbose_name = _('Buyer Profile')
        verbose_name_plural = _('Buyer Profiles')
    
    def __str__(self):
        return f"{self.user.email} - Buyer Profile"

class RiderProfile(models.Model):
    AVAILABILITY_STATUS_CHOICES = [
        ('available', _('Available')),
        ('busy', _('Busy')),
        ('offline', _('Offline')),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rider_profile')
    vehicle_type = models.CharField(max_length=50, blank=True)
    vehicle_plate = models.CharField(max_length=20, blank=True)
    availability_status = models.CharField(max_length=20, choices=AVAILABILITY_STATUS_CHOICES, default='offline')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_deliveries = models.IntegerField(default=0)
    current_location_lat = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    current_location_lng = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'rider_profiles'
        verbose_name = _('Rider Profile')
        verbose_name_plural = _('Rider Profiles')
    
    def __str__(self):
        return f"{self.user.email} - Rider Profile"
