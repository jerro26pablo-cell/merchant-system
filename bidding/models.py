from django.db import models
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from listings.models import Listing

User = get_user_model()

class Bid(models.Model):
    BID_STATUS_CHOICES = [
        ('active', _('Active')),
        ('outbid', _('Outbid')),
        ('winning', _('Winning')),
        ('won', _('Won')),
        ('cancelled', _('Cancelled')),
        ('pending_cancel', _('Pending Cancel')),
    ]
    
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=BID_STATUS_CHOICES, default='active')
    is_auto_bid = models.BooleanField(default=False, help_text=_('Whether this was an automatic proxy bid'))
    personal_increment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text=_('Bidder\'s preferred increment for this listing'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'bids'
        verbose_name = _('Bid')
        verbose_name_plural = _('Bids')
        ordering = ['-amount', '-created_at']
        indexes = [
            models.Index(fields=['listing', 'status']),
            models.Index(fields=['bidder', 'status']),
            models.Index(fields=['listing', '-amount']),
        ]
    
    def __str__(self):
        return f"{self.bidder.email} - ${self.amount} on {self.listing.title}"
    
    @classmethod
    @transaction.atomic
    def place_bid(cls, listing, bidder, amount, is_auto_bid=False):
        """Place a bid with all validation and automatic increment logic"""
        from django.core.exceptions import ValidationError
        
        # Lock the listing for update
        listing = Listing.objects.select_for_update().get(id=listing.id)
        
        # Validate auction status
        if not listing.is_auction:
            raise ValidationError('This is not an auction listing.')
        
        if listing.status != 'active':
            raise ValidationError('This auction is not active.')
        
        if not listing.auction_start or not listing.auction_end:
            raise ValidationError('Auction times are not set.')
        
        now = timezone.now()
        if now < listing.auction_start:
            raise ValidationError('Auction has not started yet.')
        
        if now > listing.auction_end:
            raise ValidationError('Auction has already ended.')
        
        # Validate bidder
        if bidder == listing.seller:
            raise ValidationError('Sellers cannot bid on their own listings.')
        
        # Calculate minimum bid
        min_bid = listing.current_bid + listing.minimum_increment if listing.current_bid else listing.starting_bid
        
        if amount < min_bid:
            raise ValidationError(f'Bid must be at least ${min_bid:.2f}')
        
        # Check against user's max bid cap
        max_bid_cap = MaxBidCap.objects.filter(
            listing=listing,
            bidder=bidder,
            is_active=True
        ).first()
        
        if max_bid_cap and amount > max_bid_cap.max_amount:
            raise ValidationError(f'Bid exceeds your maximum bid cap of ${max_bid_cap.max_amount:.2f}')
        
        # Check for anti-snipe
        time_remaining = (listing.auction_end - now).total_seconds()
        if time_remaining <= listing.anti_snipe_seconds:
            # Extend auction
            extension_seconds = listing.anti_snipe_seconds
            listing.auction_end = listing.auction_end + timezone.timedelta(seconds=extension_seconds)
            listing.save()
            
            AuctionExtension.objects.create(
                listing=listing,
                previous_end=listing.auction_end - timezone.timedelta(seconds=extension_seconds),
                new_end=listing.auction_end,
                extension_seconds=extension_seconds
            )
        
        # Create the bid
        bid = cls.objects.create(
            listing=listing,
            bidder=bidder,
            amount=amount,
            status='active',
            is_auto_bid=is_auto_bid
        )
        
        # Update listing current bid
        listing.current_bid = amount
        listing.save()
        
        # Update other bids to outbid
        cls.objects.filter(
            listing=listing,
            status='active'
        ).exclude(id=bid.id).update(status='outbid')
        
        # Set this bid as winning
        bid.status = 'winning'
        bid.save()
        
        # Process proxy bidding for other users
        cls._process_proxy_bidding(listing, amount, bidder)
        
        # Create notifications for outbid users
        from notifications.models import Notification
        outbid_bids = cls.objects.filter(listing=listing, status='outbid')
        for outbid_bid in outbid_bids:
            if outbid_bid.bidder != bidder:
                Notification.objects.create(
                    user=outbid_bid.bidder,
                    notification_type='outbid',
                    title='You have been outbid',
                    message=f'You have been outbid on {listing.title}. Current bid: ${amount:.2f}',
                    related_listing=listing
                )
        
        return bid
    
    @classmethod
    def _process_proxy_bidding(cls, listing, new_bid_amount, new_bidder):
        """Process automatic proxy bidding for users with max bid caps"""
        # Get all active max bid caps for this listing (excluding the new bidder)
        max_bid_caps = MaxBidCap.objects.filter(
            listing=listing,
            is_active=True
        ).exclude(bidder=new_bidder).order_by('-max_amount')
        
        for cap in max_bid_caps:
            # If the new bid is below this user's max cap, auto-bid
            if new_bid_amount < cap.max_amount:
                # Calculate auto-bid amount (minimum increment above new bid)
                auto_bid_amount = new_bid_amount + listing.minimum_increment
                
                # Don't exceed max cap
                if auto_bid_amount > cap.max_amount:
                    auto_bid_amount = cap.max_amount
                
                # Place auto bid
                try:
                    auto_bid = cls.place_bid(
                        listing=listing,
                        bidder=cap.bidder,
                        amount=auto_bid_amount,
                        is_auto_bid=True
                    )
                    
                    # Update listing current bid
                    listing.current_bid = auto_bid_amount
                    listing.save()
                    
                    # Notify the auto-bidder
                    from notifications.models import Notification
                    Notification.objects.create(
                        user=cap.bidder,
                        notification_type='auto_bid',
                        title='Automatic bid placed',
                        message=f'An automatic bid of ${auto_bid_amount:.2f} was placed on your behalf for {listing.title}',
                        related_listing=listing
                    )
                    
                    # Update new bid amount for next iteration
                    new_bid_amount = auto_bid_amount
                    new_bidder = cap.bidder
                    
                except Exception:
                    # If auto-bid fails, continue to next cap
                    continue

class MaxBidCap(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='max_bid_caps')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='max_bid_caps')
    max_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    personal_increment = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'max_bid_caps'
        verbose_name = _('Max Bid Cap')
        verbose_name_plural = _('Max Bid Caps')
        unique_together = ['listing', 'bidder']
        indexes = [
            models.Index(fields=['listing', 'is_active']),
            models.Index(fields=['bidder', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.bidder.email} - Max: ${self.max_amount:.2f} on {self.listing.title}"

class BidCancellationRequest(models.Model):
    REQUEST_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('denied', _('Denied')),
    ]
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='cancellation_requests')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bid_cancellation_requests')
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=REQUEST_STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_cancellations')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'bid_cancellation_requests'
        verbose_name = _('Bid Cancellation Request')
        verbose_name_plural = _('Bid Cancellation Requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Cancellation request for bid ${self.bid.amount} by {self.user.email}"

class AuctionExtension(models.Model):
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='auction_extensions')
    previous_end = models.DateTimeField()
    new_end = models.DateTimeField()
    extension_seconds = models.IntegerField()
    triggered_by_bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'auction_extensions'
        verbose_name = _('Auction Extension')
        verbose_name_plural = _('Auction Extensions')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.listing.title} extended by {self.extension_seconds}s"
