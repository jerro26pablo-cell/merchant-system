from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from listings.models import Listing

User = get_user_model()

class Order(models.Model):
    ORDER_TYPE_CHOICES = [
        ('buy_now', _('Buy Now')),
        ('auction_win', _('Auction Win')),
        ('second_chance', _('Second Chance Offer')),
    ]
    
    ORDER_STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('paid', _('Paid')),
        ('processing', _('Processing')),
        ('rider_assigned', _('Rider Assigned')),
        ('rider_accepted', _('Rider Accepted')),
        ('picked_up', _('Picked Up')),
        ('in_transit', _('In Transit')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('disputed', _('Disputed')),
    ]
    
    PAYMENT_METHOD_CHOICES = [
        ('online', _('Online Payment')),
        ('cod', _('Cash on Delivery')),
    ]
    
    buyer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    listing = models.ForeignKey(Listing, on_delete=models.CASCADE, related_name='orders')
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    
    # Order details
    order_number = models.CharField(max_length=50, unique=True)
    quantity = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='online')
    is_paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Shipping
    shipping_address = models.TextField()
    tracking_number = models.CharField(max_length=100, blank=True)
    carrier = models.CharField(max_length=100, blank=True)
    
    # Rider
    rider = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_orders')
    
    # Second chance offer reference (using string to avoid circular import)
    second_chance_offer = models.ForeignKey('bidding.SecondChanceOffer', on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    
    # Escrow
    escrow_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    escrow_released = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        verbose_name = _('Order')
        verbose_name_plural = _('Orders')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['buyer', 'status']),
            models.Index(fields=['listing', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['rider', 'status']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.buyer.email}"
    
    def save(self, *args, **kwargs):
        if not self.order_number:
            # Generate unique order number
            import random
            import string
            while True:
                order_number = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
                if not Order.objects.filter(order_number=order_number).exists():
                    self.order_number = order_number
                    break
        super().save(*args, **kwargs)
    
    @property
    def can_be_cancelled(self):
        return self.status in ['pending', 'paid']
    
    def mark_as_paid(self):
        self.status = 'paid'
        self.is_paid = True
        self.paid_at = timezone.now()
        
        # Set up escrow
        self.escrow_amount = self.total_amount
        self.save()
        
        # Create wallet transaction
        from wallets.models import Wallet, WalletTransaction
        buyer_wallet, _ = Wallet.objects.get_or_create(user=self.buyer)
        WalletTransaction.objects.create(
            wallet=buyer_wallet,
            transaction_type='payment',
            amount=-self.total_amount,
            description=f'Payment for order {self.order_number}',
            related_order=self
        )
    
    def release_escrow(self):
        if self.escrow_amount and not self.escrow_released:
            # Release funds to seller
            from wallets.models import Wallet, WalletTransaction
            seller_wallet, _ = Wallet.objects.get_or_create(user=self.listing.seller)
            
            WalletTransaction.objects.create(
                wallet=seller_wallet,
                transaction_type='sale',
                amount=self.escrow_amount,
                description=f'Escrow release for order {self.order_number}',
                related_order=self
            )
            
            self.escrow_released = True
            self.save()