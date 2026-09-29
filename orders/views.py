from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Order


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