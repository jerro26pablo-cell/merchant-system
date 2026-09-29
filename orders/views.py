from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from .models import Order
from listings.models import Listing
import logging

logger = logging.getLogger(__name__)


@login_required
def add_to_cart(request, slug):
    """Create an order for buy-now purchase"""
    try:
        listing = get_object_or_404(Listing, slug=slug)
        
        # Prevent seller from buying their own items
        if request.user == listing.seller:
            messages.error(request, 'You cannot purchase your own listing.')
            return redirect('listing_detail', slug=slug)
        
        # Check if listing is buy-now and has stock
        if not listing.is_buy_now:
            messages.error(request, 'This listing is not available for buy-now purchase.')
            return redirect('listing_detail', slug=slug)
        
        if listing.available_stock <= 0:
            messages.error(request, 'This item is out of stock.')
            return redirect('listing_detail', slug=slug)
        
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity < 1:
            messages.error(request, 'Quantity must be at least 1.')
            return redirect('listing_detail', slug=slug)
        
        if quantity > listing.available_stock:
            messages.error(request, f'Only {listing.available_stock} items available.')
            return redirect('listing_detail', slug=slug)
        
        total_amount = listing.buy_now_price * quantity
        
        with transaction.atomic():
            # Create order
            order = Order.objects.create(
                buyer=request.user,
                listing=listing,
                order_type='buy_now',
                quantity=quantity,
                total_amount=total_amount,
                shipping_address=request.user.profile.address if hasattr(request.user, 'profile') else '',
                status='pending'
            )
            
            # Reduce stock
            listing.available_stock -= quantity
            listing.quantity_sold += quantity
            listing.save()
            
            # Log inventory change
            from listings.models import InventoryLog
            InventoryLog.objects.create(
                listing=listing,
                change_type='sale',
                quantity_before=listing.available_stock + quantity,
                quantity_after=listing.available_stock,
                notes=f'Buy Now order {order.order_number}: {quantity} items'
            )
        
        logger.info(f"Order {order.order_number} created for listing {listing.slug} by user {request.user.id}")
        messages.success(request, f'Order {order.order_number} created successfully! Please complete payment.')
        return redirect('order_detail', order_number=order.order_number)
        
    except Exception as e:
        logger.error(f"Error in add_to_cart: {e}", exc_info=True)
        messages.error(request, 'An error occurred while creating your order.')
        return redirect('listing_detail', slug=slug)


@login_required
def order_list(request):
    """View all orders for the current user"""
    orders = Order.objects.filter(buyer=request.user).order_by('-created_at')
    return render(request, 'orders/order_list.html', {'orders': orders})


@login_required
def order_detail(request, order_number):
    """View details of a specific order"""
    order = get_object_or_404(Order, order_number=order_number, buyer=request.user)
    return render(request, 'orders/order_detail.html', {'order': order})