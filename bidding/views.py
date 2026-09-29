from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from .models import Bid, MaxBidCap, BidCancellationRequest
from listings.models import Listing
import logging

logger = logging.getLogger(__name__)

@login_required
def place_bid(request, slug):
    try:
        listing = get_object_or_404(Listing, slug=slug, status='active')

        if request.method == 'POST':
            amount = float(request.POST.get('amount'))
            bidder_increment = request.POST.get('bidder_increment')
            max_cap = request.POST.get('max_cap')

            try:
                # Save bidder increment preference
                if bidder_increment:
                    from accounts.models import BuyerProfile
                    buyer_profile, _ = BuyerProfile.objects.get_or_create(user=request.user)
                    buyer_profile.bidder_increment = float(bidder_increment)
                    buyer_profile.save()

                # Place bid with increment preference
                bid = Bid.place_bid(listing, request.user, amount, is_auto_bid=False)

                # Save bidder increment to the bid
                if bidder_increment:
                    bid.personal_increment = float(bidder_increment)
                    bid.save()

                # Set max bid cap if provided
                if max_cap:
                    max_cap_obj, created = MaxBidCap.objects.update_or_create(
                        listing=listing,
                        bidder=request.user,
                        defaults={
                            'max_amount': float(max_cap),
                            'personal_increment': float(bidder_increment) if bidder_increment else None,
                            'is_active': True
                        }
                    )

                # Check if AJAX request
                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

                if is_ajax:
                    return JsonResponse({
                        'success': True,
                        'bid_amount': str(bid.amount),
                        'current_bid': str(listing.current_bid),
                        'status': bid.status
                    })

                messages.success(request, f'Bid of ₱{amount:.2f} placed successfully!')
                return redirect('listing_detail', slug=listing.slug)

            except Exception as e:
                logger.error(f"Error placing bid: {e}", exc_info=True)

                is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

                if is_ajax:
                    return JsonResponse({'success': False, 'error': str(e)}, status=400)

                messages.error(request, str(e))
                return redirect('listing_detail', slug=listing.slug)

        return redirect('listing_detail', slug=listing.slug)
    except Exception as e:
        logger.error(f"Error in place_bid view: {e}", exc_info=True)
        messages.error(request, 'An error occurred while processing your bid.')
        return redirect('catalog')

@login_required
def set_max_bid_cap(request, slug):
    try:
        listing = get_object_or_404(Listing, slug=slug, status='active')
        
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
                    logger.error(f"Error processing proxy bidding: {e}", exc_info=True)
                    messages.warning(request, f'Could not process auto-bids: {str(e)}')
            
            return redirect('listing_detail', slug=listing.slug)
        
        return redirect('listing_detail', slug=listing.slug)
    except Exception as e:
        logger.error(f"Error in set_max_bid_cap: {e}", exc_info=True)
        messages.error(request, 'An error occurred while setting your max bid cap.')
        return redirect('listing_detail', slug=slug)

@login_required
def bid_history(request, slug):
    try:
        listing = get_object_or_404(Listing, slug=slug, status='active')
        bids = listing.bids.all().order_by('-created_at')
        
        context = {
            'listing': listing,
            'bids': bids,
        }
        
        return render(request, 'bidding/bid_history.html', context)
    except Exception as e:
        logger.error(f"Error in bid_history: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading bid history.')
        return redirect('listing_detail', slug=slug)

@login_required
def request_bid_cancellation(request, bid_id):
    try:
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
    except Exception as e:
        logger.error(f"Error in request_bid_cancellation: {e}", exc_info=True)
        messages.error(request, 'An error occurred while processing your cancellation request.')
        return redirect('my_bids')

@login_required
def my_bids(request):
    try:
        from django.utils import timezone

        all_bids = Bid.objects.filter(bidder=request.user).select_related('listing').order_by('-created_at')

        # Separate into active and past bids
        active_bids = []
        past_bids = []
        now = timezone.now()

        for bid in all_bids:
            is_active = (bid.listing.status == 'active' and
                        bid.listing.auction_end and
                        bid.listing.auction_end > now)

            if is_active:
                active_bids.append(bid)
            else:
                past_bids.append(bid)

        context = {
            'bids': all_bids,
            'active_bids': active_bids,
            'past_bids': past_bids,
        }

        return render(request, 'bidding/my_bids.html', context)
    except Exception as e:
        logger.error(f"Error in my_bids: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading your bids.')
        return render(request, 'bidding/my_bids.html', {'bids': Bid.objects.none()})
