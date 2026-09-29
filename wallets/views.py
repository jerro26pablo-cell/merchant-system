from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Wallet, WalletTransaction


@login_required
def wallet_detail(request):
    """View wallet details and transaction history"""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    transactions = wallet.transactions.all().order_by('-created_at')
    
    return render(request, 'wallets/wallet_detail.html', {
        'wallet': wallet,
        'transactions': transactions
    })


@login_required
def add_funds(request):
    """Add funds to wallet"""
    wallet, _ = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount', 0))
        description = request.POST.get('description', '')
        
        try:
            wallet.add_funds(amount, description)
            messages.success(request, f'${amount:.2f} added to your wallet!')
            return redirect('wallet_detail')
        except ValueError as e:
            messages.error(request, str(e))
    
    return render(request, 'wallets/add_funds.html', {'wallet': wallet})