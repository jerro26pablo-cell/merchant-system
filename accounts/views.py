from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .forms import UserRegistrationForm, UserLoginForm, SellerProfileForm
from .models import User, SellerProfile, BuyerProfile

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            BuyerProfile.objects.get_or_create(user=user)
            login(request, user)
            messages.success(request, 'Registration successful! You are now a buyer.')
            return redirect('home')
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
    return render(request, 'accounts/profile.html')

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
    
    return render(request, 'accounts/seller_dashboard.html', {'listings': listings})
