from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from .models import Bid, MaxBidCap, BidCancellationRequest
from listings.models import Listing

@login_required
def place_bid(request, slug):
    listing = get_object_or_404(Listing, slug=slug, is_active=True)
    
    if request.method == 'POST':
        amount = float(request.POST.get('amount'))
        
        try:
            bid = Bid.place_bid(listing, request.user, amount)
            messages.success(request, f'Bid of ${amount:.2f} placed successfully!')
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({
                    'success': True,
                    'bid_amount': str(bid.amount),
                    'current_bid': str(listing.current_bid),
                    'status': bid.status
                })
            
            return redirect('listing_detail', slug=listing.slug)
            
        except Exception as e:
            messages.error(request, str(e))
            
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'error': str(e)}, status=400)
            
            return redirect('listing_detail', slug=listing.slug)
    
    return redirect('listing_detail', slug=listing.slug)

@login_required
def set_max_bid_cap(request, slug):
    listing = get_object_or_404(Listing, slug=slug, is_active=True)
    
    if request.method == 'POST':
        max_amount = float(request.POST.get('max_amount'))
        personal_increment = request.POST.get('personal_increment')
        
        # Validate max amount
        if max_amount <= (listing.current_bid or listing.starting_bid):
            messages.error(request, 'Max bid must be higher than current bid.')
            return redirect('listing_detail', slug=listing.slug)
        
        # Create or update max bid cap
        cap, created = MaxBidCap.objects.update_or_create(
            listing=listing,
            bidder=request.user,
            defaults={
                'max_amount': max_amount,
                'personal_increment': float(personal_increment) if personal_increment else None,
                'is_active': True
            }
        )
        
        messages.success(request, f'Max bid cap set to ${max_amount:.2f}!')
        
        # Trigger immediate proxy bidding if needed
        if listing.current_bid and listing.current_bid < max_amount:
            try:
                Bid._process_proxy_bidding(listing, listing.current_bid, request.user)
                listing.refresh_from_db()
            except Exception as e:
                messages.warning(request, f'Could not process auto-bids: {str(e)}')
        
        return redirect('listing_detail', slug=listing.slug)
    
    return redirect('listing_detail', slug=listing.slug)

@login_required
def bid_history(request, slug):
    listing = get_object_or_404(Listing, slug=slug, is_active=True)
    bids = listing.bids.all().order_by('-created_at')
    
    context = {
        'listing': listing,
        'bids': bids,
    }
    
    return render(request, 'bidding/bid_history.html', context)

@login_required
def request_bid_cancellation(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id, bidder=request.user)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        
        # Check if there's already a pending request
        if BidCancellationRequest.objects.filter(bid=bid, status='pending').exists():
            messages.error(request, 'You already have a pending cancellation request for this bid.')
            return redirect('listing_detail', slug=bid.listing.slug)
        
        BidCancellationRequest.objects.create(
            bid=bid,
            user=request.user,
            reason=reason
        )
        
        messages.success(request, 'Bid cancellation request submitted for admin review.')
        return redirect('listing_detail', slug=bid.listing.slug)
    
    return render(request, 'bidding/request_cancellation.html', {'bid': bid})

@login_required
def my_bids(request):
    bids = Bid.objects.filter(bidder=request.user).select_related('listing').order_by('-created_at')
    
    context = {
        'bids': bids,
    }
    
    return render(request, 'bidding/my_bids.html', context)
