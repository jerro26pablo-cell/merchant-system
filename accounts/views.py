from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import UserRegistrationForm, UserLoginForm, SellerProfileForm, UserProfileForm, BuyerProfileForm
from .models import User, SellerProfile, BuyerProfile

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            BuyerProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Registration successful! You are now a buyer.')
            return redirect('buyer_dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, 'Login successful!')
            return redirect('home')
    else:
        form = UserLoginForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def user_logout(request):
    logout(request)
    messages.success(request, 'You have been logged out.')
    return redirect('home')

@login_required
def profile(request):
    """User profile page with edit functionality"""
    user = request.user
    
    # Get or create profiles
    buyer_profile, _ = BuyerProfile.objects.get_or_create(user=user)
    seller_profile = None
    if user.seller_enabled:
        seller_profile, _ = SellerProfile.objects.get_or_create(user=user)
    
    if request.method == 'POST':
        user_form = UserProfileForm(request.POST, instance=user)
        buyer_form = BuyerProfileForm(request.POST, instance=buyer_profile)
        
        if user_form.is_valid() and buyer_form.is_valid():
            user_form.save()
            buyer_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        user_form = UserProfileForm(instance=user)
        buyer_form = BuyerProfileForm(instance=buyer_profile)
    
    context = {
        'user_form': user_form,
        'buyer_form': buyer_form,
        'seller_profile': seller_profile,
    }
    
    return render(request, 'accounts/profile.html', context)

@login_required
def buyer_dashboard(request):
    """Buyer dashboard - shows purchase history and saved items"""
    buyer_profile, created = BuyerProfile.objects.get_or_create(user=request.user)
    
    from listings.models import Listing
    # Can add recent listings viewed, purchased items, etc.
    recent_listings = Listing.objects.filter(status='active').order_by('-created_at')[:8]
    
    return render(request, 'accounts/buyer_dashboard.html', {
        'buyer_profile': buyer_profile,
        'recent_listings': recent_listings
    })

@login_required
@transaction.atomic
def enable_seller_mode(request):
    user = request.user
    if not user.seller_enabled:
        user.enable_seller_mode()
        messages.success(request, 'Seller mode enabled! Please complete your seller profile.')
        return redirect('seller_profile')
    return redirect('profile')

@login_required
def seller_profile(request):
    profile, created = SellerProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        form = SellerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Seller profile updated successfully!')
            return redirect('seller_dashboard')
    else:
        form = SellerProfileForm(instance=profile)
    
    return render(request, 'accounts/seller_profile.html', {'form': form, 'profile': profile})

@login_required
def seller_dashboard(request):
    if not request.user.is_seller:
        messages.error(request, 'You need to enable seller mode first.')
        return redirect('enable_seller_mode')
    
    from listings.models import Listing
    listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
    
    # Calculate statistics
    active_listings = listings.filter(status='active').count()
    buy_now_listings = listings.filter(listing_type='buy_now').count()
    auction_listings = listings.filter(listing_type='auction').count()
    
    context = {
        'listings': listings,
        'active_listings': active_listings,
        'buy_now_listings': buy_now_listings,
        'auction_listings': auction_listings,
    }
    
    return render(request, 'accounts/seller_dashboard.html', context)
