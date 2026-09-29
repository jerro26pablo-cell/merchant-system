from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from django.db import transaction

User = get_user_model()

class Wallet(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'wallets'
        verbose_name = _('Wallet')
        verbose_name_plural = _('Wallets')
    
    def __str__(self):
        return f"{self.user.email} - ${self.balance:.2f}"
    
    @transaction.atomic
    def add_funds(self, amount, description=''):
        """Add funds to wallet"""
        if amount <= 0:
            raise ValueError('Amount must be positive')
        
        self.balance += amount
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='deposit',
            amount=amount,
            description=description or 'Deposit'
        )
    
    @transaction.atomic
    def deduct_funds(self, amount, description=''):
        """Deduct funds from wallet"""
        if amount <= 0:
            raise ValueError('Amount must be positive')
        
        if self.balance < amount:
            raise ValueError('Insufficient funds')
        
        self.balance -= amount
        self.save()
        
        WalletTransaction.objects.create(
            wallet=self,
            transaction_type='withdrawal',
            amount=-amount,
            description=description or 'Withdrawal'
        )

class WalletTransaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', _('Deposit')),
        ('withdrawal', _('Withdrawal')),
        ('payment', _('Payment')),
        ('refund', _('Refund')),
        ('escrow_hold', _('Escrow Hold')),
        ('escrow_release', _('Escrow Release')),
        ('sale', _('Sale')),
    ]
    
    wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(blank=True)
    related_order = models.ForeignKey('orders.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='wallet_transactions')
    balance_after = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'wallet_transactions'
        verbose_name = _('Wallet Transaction')
        verbose_name_plural = _('Wallet Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['wallet', 'created_at']),
            models.Index(fields=['transaction_type']),
            models.Index(fields=['related_order']),
        ]
    
    def __str__(self):
        return f"{self.wallet.user.email} - {self.transaction_type}: ${self.amount:.2f}"
    
    def save(self, *args, **kwargs):
        # Store balance after transaction
        if not self.balance_after:
            self.balance_after = self.wallet.balance + self.amount
        super().save(*args, **kwargs)