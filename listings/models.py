from django.db import models
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from categories.models import Category, SizeSpecification

User = get_user_model()

class Listing(models.Model):
    LISTING_TYPE_CHOICES = [
        ('auction', _('Auction')),
        ('buy_now', _('Buy Now')),
        ('both', _('Both (Auction + Buy Now)')),
    ]
    
    LISTING_STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('active', _('Active')),
        ('ended', _('Ended')),
        ('sold', _('Sold')),
        ('cancelled', _('Cancelled')),
        ('relisted', _('Relisted')),
    ]
    
    CONDITION_CHOICES = [
        ('new', _('New')),
        ('like_new', _('Like New')),
        ('good', _('Good')),
        ('fair', _('Fair')),
        ('for_parts', _('For Parts')),
    ]
    
    seller = models.ForeignKey(User, on_delete=models.CASCADE, related_name='listings')
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='listings')
    
    listing_type = models.CharField(max_length=20, choices=LISTING_TYPE_CHOICES, default='buy_now')
    status = models.CharField(max_length=20, choices=LISTING_STATUS_CHOICES, default='draft')
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='good')
    
    # Quantity management - CRITICAL FIELDS
    quantity = models.IntegerField(default=1, help_text=_('Total original quantity'))
    available_stock = models.IntegerField(default=1, help_text=_('Available for buy-now purchases'))
    auction_quantity = models.IntegerField(default=0, help_text=_('Quantity allocated to auction'))
    quantity_sold = models.IntegerField(default=0, help_text=_('Total quantity sold'))
    
    # Pricing
    starting_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    buy_now_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    reserve_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    display_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    minimum_increment = models.DecimalField(max_digits=10, decimal_places=2, default=1.00)
    
    # Auction timing
    auction_start = models.DateTimeField(null=True, blank=True)
    auction_end = models.DateTimeField(null=True, blank=True)
    anti_snipe_seconds = models.IntegerField(default=300, help_text=_('Seconds to extend if bid placed near end'))
    auto_relist = models.BooleanField(default=False)
    
    # Size specification
    size = models.ForeignKey(SizeSpecification, on_delete=models.SET_NULL, null=True, blank=True, related_name='listings')
    
    # Shipping
    shipping_address = models.TextField(blank=True, help_text=_('Shipping address for this listing'))
    
    # Tracking
    view_count = models.IntegerField(default=0)
    original_listing = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='relistings')
    inventory_source = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='auction_conversions', help_text=_('Original buy-now listing if this is an auction created from inventory'))
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'listings'
        verbose_name = _('Listing')
        verbose_name_plural = _('Listings')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'listing_type']),
            models.Index(fields=['category']),
            models.Index(fields=['seller']),
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Ensure unique slug
            counter = 1
            original_slug = self.slug
            while Listing.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('listing_detail', kwargs={'slug': self.slug})
    
    @property
    def is_auction(self):
        return self.listing_type in ['auction', 'both']
    
    @property
    def is_buy_now(self):
        return self.listing_type in ['buy_now', 'both']
    
    @property
    def current_price(self):
        if self.is_auction and self.current_bid:
            return self.current_bid
        return self.buy_now_price
    
    @property
    def is_available(self):
        if self.is_buy_now and self.available_stock > 0:
            return True
        if self.is_auction and self.status == 'active':
            return True
        return False
    
    @property
    def time_remaining(self):
        if self.auction_end and self.status == 'active':
            return self.auction_end - timezone.now()
        return None
    
    @property
    def primary_image(self):
        return self.images.filter(is_primary=True).first() or self.images.first()
    
    def add_view(self, user=None, ip_address=None):
        self.view_count += 1
        self.save()
        ListingView.objects.create(listing=self, user=user, ip_address=ip_address)

class ListingImage(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='listings/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    sort_order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listing_images'
        verbose_name = _('Listing Image')
        verbose_name_plural = _('Listing Images')
        ordering = ['sort_order']
    
    def __str__(self):
        return f"{self.listing.title} - Image {self.sort_order}"

class ListingAttribute(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='attributes')
    attribute = models.ForeignKey('categories.CategoryAttribute', on_delete=models.CASCADE)
    value = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listing_attributes'
        verbose_name = _('Listing Attribute')
        verbose_name_plural = _('Listing Attributes')
        unique_together = ['listing', 'attribute']
    
    def __str__(self):
        return f"{self.listing.title} - {self.attribute.name}: {self.value}"

class ListingView(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'listing_views'
        verbose_name = _('Listing View')
        verbose_name_plural = _('Listing Views')
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.listing.title} - View at {self.viewed_at}"

class InventoryLog(models.Model):
    INVENTORY_CHANGE_TYPES = [
        ('restock', _('Restock')),
        ('sale', _('Sale')),
        ('adjustment', _('Adjustment')),
        ('return', _('Return')),
        ('relist', _('Relist')),
        ('auction_conversion', _('Auction Conversion')),
    ]
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='inventory_logs')
    change_type = models.CharField(max_length=30, choices=INVENTORY_CHANGE_TYPES)
    quantity_before = models.IntegerField()
    quantity_after = models.IntegerField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'inventory_logs'
        verbose_name = _('Inventory Log')
        verbose_name_plural = _('Inventory Logs')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.listing.title} - {self.change_type}: {self.quantity_before} → {self.quantity_after}"
