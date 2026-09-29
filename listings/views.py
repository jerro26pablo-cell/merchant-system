from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, F, DecimalField
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from django.db import transaction
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from .models import Listing, ListingImage, ListingAttribute, InventoryLog, Wishlist, Conversation, Message
from .forms import ListingForm, ListingImageFormSet
import logging

logger = logging.getLogger(__name__)

def listing_catalog(request):
    """Catalog-style view of all active listings"""
    try:
        listings = Listing.objects.filter(
            status='active'
        ).select_related('seller', 'category').prefetch_related('images').order_by('-created_at')
        logger.info(f"Fetched {listings.count()} active listings")
        
        # Get categories for filter
        from categories.models import Category
        categories = Category.objects.filter(is_active=True).order_by('name')
    except Exception as e:
        # Handle database errors gracefully
        logger.error(f"Error fetching listings: {e}", exc_info=True)
        listings = Listing.objects.none()
        categories = Category.objects.none()
    
    try:
        # Search functionality
        search_query = request.GET.get('search', '')
        if search_query:
            listings = listings.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        
        # Category filter
        category_slug = request.GET.get('category')
        if category_slug:
            listings = listings.filter(category__slug=category_slug)
        
        # Listing type filter
        listing_type = request.GET.get('type')
        if listing_type:
            listings = listings.filter(listing_type=listing_type)
        
        # Condition filter
        condition = request.GET.get('condition')
        if condition:
            listings = listings.filter(condition=condition)
        
        # Price range filter - annotate with calculated price
        # For auctions: use current_bid if available, otherwise starting_bid
        # For buy-now: use buy_now_price
        listings = listings.annotate(
            calculated_price=Case(
                When(
                    listing_type__in=['auction', 'both'],
                    then=Coalesce(F('current_bid'), F('starting_bid'))
                ),
                default=F('buy_now_price'),
                output_field=DecimalField()
            )
        )
        
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        if min_price:
            try:
                min_price_decimal = Decimal(min_price)
                listings = listings.filter(calculated_price__gte=min_price_decimal)
            except (ValueError, InvalidOperation, TypeError):
                logger.warning(f"Invalid min_price value: {min_price}")
        if max_price:
            try:
                max_price_decimal = Decimal(max_price)
                listings = listings.filter(calculated_price__lte=max_price_decimal)
            except (ValueError, InvalidOperation, TypeError):
                logger.warning(f"Invalid max_price value: {max_price}")
        
        # Pagination
        paginator = Paginator(listings, 12)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'category_slug': category_slug,
            'listing_type': listing_type,
            'condition': condition,
            'min_price': min_price,
            'max_price': max_price,
            'categories': categories,
        }
        
        return render(request, 'listings/catalog.html', context)
    except Exception as e:
        logger.error(f"Error in listing catalog processing: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the catalog.')
        return render(request, 'listings/catalog.html', {
            'page_obj': Paginator(Listing.objects.none(), 12).get_page(1),
            'search_query': '',
            'category_slug': '',
            'listing_type': '',
            'condition': '',
            'min_price': '',
            'max_price': '',
            'categories': Category.objects.none(),
        })

def listing_detail(request, slug):
    try:
        # Allow viewing any listing that the user owns or is active
        listing = get_object_or_404(Listing, slug=slug)

        # If not the seller, only show active listings
        if request.user.is_authenticated and request.user != listing.seller and listing.status != 'active':
            messages.error(request, 'This listing is not currently available.')
            return redirect('catalog')

        # Track view
        try:
            listing.add_view(
                user=request.user if request.user.is_authenticated else None,
                ip_address=request.META.get('REMOTE_ADDR')
            )
        except Exception as view_error:
            logger.warning(f"Could not track view: {view_error}")

        # Get similar listings (by price, same category)
        similar_listings = Listing.objects.filter(
            category=listing.category,
            status='active'
        ).exclude(id=listing.id).order_by('buy_now_price')[:4]

        # Get category price stats
        from django.db.models import Avg, Min, Max, Count
        category_stats = Listing.objects.filter(
            category=listing.category,
            status='active'
        ).aggregate(
            min_price=Min('buy_now_price'),
            avg_price=Avg('buy_now_price'),
            max_price=Max('buy_now_price'),
            count=Count('id')
        )

        # Check if wishlisted
        is_wishlisted = False
        my_increment = None
        my_cap = None
        if request.user.is_authenticated:
            is_wishlisted = Wishlist.objects.filter(
                user=request.user,
                listing=listing
            ).exists()

            # Get user's bidder increment preference
            from accounts.models import BuyerProfile
            buyer_profile, _ = BuyerProfile.objects.get_or_create(user=request.user)
            my_increment = buyer_profile.bidder_increment

            # Get user's max bid cap for this listing
            from bidding.models import MaxBidCap
            my_cap = MaxBidCap.objects.filter(
                listing=listing,
                bidder=request.user,
                is_active=True
            ).first()

        context = {
            'listing': listing,
            'similar_listings': similar_listings,
            'category_stats': category_stats,
            'is_wishlisted': is_wishlisted,
            'my_increment': my_increment,
            'my_cap': my_cap,
        }

        return render(request, 'listings/detail.html', context)
    except Exception as e:
        logger.error(f"Error in listing detail: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the listing details.')
        return redirect('catalog')

@login_required
def create_listing(request):
    try:
        logger.info(f"Create listing request - Method: {request.method}, User: {request.user}, Is seller: {request.user.is_seller}")
        
        if not request.user.is_seller:
            messages.error(request, 'You need to enable seller mode to create listings.')
            return redirect('enable_seller_mode')
        
        if request.method == 'POST':
            logger.info(f"POST data: {request.POST}")
            logger.info(f"FILES data: {request.FILES}")
            
            form = ListingForm(request.POST, request.FILES)
            image_formset = ListingImageFormSet(request.POST, request.FILES)
            save_as_draft = request.POST.get('save_as_draft') == 'true'
            
            logger.info(f"Form valid: {form.is_valid()}, save_as_draft: {save_as_draft}")
            
            if not form.is_valid():
                logger.error(f"Form errors: {form.errors}")
                messages.error(request, 'Please correct the errors below.')
                return render(request, 'listings/create.html', {'form': form, 'image_formset': image_formset})
            
            listing = form.save(commit=False)
            listing.seller = request.user
            if save_as_draft:
                listing.status = 'draft'
            else:
                listing.status = 'active'
            listing.save()
            
            logger.info(f"Listing created: {listing.id}, status: {listing.status}, quantity: {listing.quantity}")
            
            # Handle images
            image_formset = ListingImageFormSet(request.POST, request.FILES, instance=listing)
            if image_formset.is_valid():
                image_formset.save()
                logger.info(f"Images saved for listing {listing.id}")
            else:
                logger.error(f"Image formset errors: {image_formset.errors}")
                messages.error(request, 'There were errors with the images. Please check and try again.')
            
            # Log inventory
            InventoryLog.objects.create(
                listing=listing,
                change_type='restock',
                quantity_before=0,
                quantity_after=listing.quantity,
                notes='Initial listing creation'
            )
            
            logger.info(f"Inventory log created for listing {listing.id}")
            
            if save_as_draft:
                messages.success(request, 'Draft listing created successfully!')
                return redirect('inventory_management')
            else:
                messages.success(request, 'Listing created successfully!')
                return redirect('listing_detail', slug=listing.slug)
        else:
            form = ListingForm()
            image_formset = ListingImageFormSet()
        
        return render(request, 'listings/create.html', {'form': form, 'image_formset': image_formset})
    except Exception as e:
        logger.error(f"Error in create listing: {e}", exc_info=True)
        messages.error(request, 'An error occurred while creating the listing.')
        return render(request, 'listings/create.html', {'form': ListingForm(), 'image_formset': ListingImageFormSet()})

@login_required
def edit_listing(request, slug):
    listing = get_object_or_404(Listing, slug=slug, seller=request.user)
    
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            
            image_formset = ListingImageFormSet(request.POST, request.FILES, instance=listing)
            if image_formset.is_valid():
                image_formset.save()
            
            messages.success(request, 'Listing updated successfully!')
            # Redirect to inventory if it's a draft, otherwise to detail page
            if listing.status == 'draft':
                return redirect('inventory_management')
            else:
                return redirect('listing_detail', slug=listing.slug)
    else:
        form = ListingForm(instance=listing)
        image_formset = ListingImageFormSet(instance=listing)
    
    return render(request, 'listings/edit.html', {'form': form, 'image_formset': image_formset, 'listing': listing})

@login_required
def delete_listing(request, slug):
    listing = get_object_or_404(Listing, slug=slug, seller=request.user)
    
    if request.method == 'POST':
        listing.status = 'cancelled'
        listing.save()
        messages.success(request, 'Listing cancelled successfully.')
        return redirect('seller_dashboard')
    
    return render(request, 'listings/delete.html', {'listing': listing})

@login_required
def convert_to_auction(request, slug):
    """Convert buy-now inventory to auction listing"""
    if not request.user.is_seller:
        messages.error(request, 'You need to enable seller mode.')
        return redirect('enable_seller_mode')
    
    original_listing = get_object_or_404(Listing, slug=slug, seller=request.user, listing_type='buy_now')
    
    if request.method == 'POST':
        auction_quantity = int(request.POST.get('auction_quantity', 1))
        
        if auction_quantity <= 0:
            messages.error(request, 'Auction quantity must be at least 1.')
            return redirect('listing_detail', slug=slug)
        
        if auction_quantity > original_listing.available_stock:
            messages.error(request, 'Not enough available stock.')
            return redirect('listing_detail', slug=slug)
        
        # Create new auction listing
        auction_listing = Listing.objects.create(
            seller=request.user,
            title=original_listing.title,
            description=original_listing.description,
            category=original_listing.category,
            listing_type='auction',
            status='draft',
            condition=original_listing.condition,
            quantity=auction_quantity,
            available_stock=0,
            auction_quantity=auction_quantity,
            quantity_sold=0,
            starting_bid=request.POST.get('starting_bid'),
            reserve_price=request.POST.get('reserve_price'),
            minimum_increment=original_listing.minimum_increment,
            auction_start=request.POST.get('auction_start'),
            auction_end=request.POST.get('auction_end'),
            size=original_listing.size,
            inventory_source=original_listing,
            anti_snipe_seconds=original_listing.anti_snipe_seconds,
        )
        
        # Copy images
        for image in original_listing.images.all():
            ListingImage.objects.create(
                listing=auction_listing,
                image=image.image,
                alt_text=image.alt_text,
                is_primary=image.is_primary,
                sort_order=image.sort_order
            )
        
        # Copy attributes
        for attr in original_listing.attributes.all():
            ListingAttribute.objects.create(
                listing=auction_listing,
                attribute=attr.attribute,
                value=attr.value
            )
        
        # Update original listing
        original_listing.available_stock -= auction_quantity
        original_listing.save()
        
        # Log inventory changes
        InventoryLog.objects.create(
            listing=original_listing,
            change_type='auction_conversion',
            quantity_before=original_listing.available_stock + auction_quantity,
            quantity_after=original_listing.available_stock,
            notes=f'Converted {auction_quantity} items to auction'
        )
        
        InventoryLog.objects.create(
            listing=auction_listing,
            change_type='auction_conversion',
            quantity_before=0,
            quantity_after=auction_quantity,
            notes='Created from buy-now inventory'
        )
        
        messages.success(request, f'Successfully converted {auction_quantity} items to auction!')
        return redirect('listing_detail', slug=auction_listing.slug)
    
    return render(request, 'listings/convert_to_auction.html', {'listing': original_listing})

@login_required
def inventory_management(request):
    """Inventory management dashboard for sellers"""
    try:
        if not request.user.is_seller:
            messages.error(request, 'You need to enable seller mode first.')
            return redirect('enable_seller_mode')
        
        listings = Listing.objects.filter(seller=request.user).order_by('-created_at')
        draft_listings = listings.filter(status='draft')
        active_listings = listings.filter(status='active')
        
        # Calculate inventory statistics
        total_stock = sum(listing.available_stock for listing in listings if listing.is_buy_now)
        total_sold = sum(listing.quantity_sold for listing in listings)
        low_stock_items = listings.filter(available_stock__lt=5, listing_type='buy_now', status='active')
        
        context = {
            'listings': listings,
            'draft_listings': draft_listings,
            'active_listings': active_listings,
            'total_stock': total_stock,
            'total_sold': total_sold,
            'low_stock_items': low_stock_items,
        }
        
        return render(request, 'listings/inventory_management.html', context)
    except Exception as e:
        logger.error(f"Error in inventory management: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading your inventory.')
        return redirect('seller_dashboard')

@login_required
def adjust_inventory(request, slug):
    """Adjust inventory levels for a listing"""
    if not request.user.is_seller:
        messages.error(request, 'You need to enable seller mode first.')
        return redirect('enable_seller_mode')
    
    listing = get_object_or_404(Listing, slug=slug, seller=request.user)
    
    if request.method == 'POST':
        change_type = request.POST.get('change_type')
        quantity_change = int(request.POST.get('quantity_change', 0))
        notes = request.POST.get('notes', '')
        
        if quantity_change == 0:
            messages.error(request, 'Quantity change cannot be zero.')
            return redirect('inventory_management')
        
        quantity_before = listing.available_stock
        quantity_after = quantity_before
        
        if change_type == 'restock':
            listing.available_stock += quantity_change
            listing.quantity += quantity_change
            quantity_after = listing.available_stock
        elif change_type == 'sale':
            if quantity_change > listing.available_stock:
                messages.error(request, 'Not enough stock available.')
                return redirect('inventory_management')
            listing.available_stock -= quantity_change
            listing.quantity_sold += quantity_change
            quantity_after = listing.available_stock
        elif change_type == 'adjustment':
            if quantity_change < 0 and abs(quantity_change) > listing.available_stock:
                messages.error(request, 'Cannot reduce stock below zero.')
                return redirect('inventory_management')
            listing.available_stock += quantity_change
            listing.quantity += quantity_change
            quantity_after = listing.available_stock
        elif change_type == 'return':
            listing.available_stock += quantity_change
            listing.quantity_sold -= quantity_change
            quantity_after = listing.available_stock
        
        listing.save()
        
        # Log the inventory change
        InventoryLog.objects.create(
            listing=listing,
            change_type=change_type,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            notes=notes or f'{change_type} of {quantity_change} items'
        )
        
        messages.success(request, f'Inventory adjusted successfully. {quantity_before} → {quantity_after}')
        return redirect('inventory_management')
    
    return render(request, 'listings/adjust_inventory.html', {'listing': listing})

@login_required
def inventory_logs(request, slug):
    """View inventory logs for a specific listing"""
    if not request.user.is_seller:
        messages.error(request, 'You need to enable seller mode first.')
        return redirect('enable_seller_mode')
    
    listing = get_object_or_404(Listing, slug=slug, seller=request.user)
    logs = listing.inventory_logs.all().order_by('-created_at')
    
    return render(request, 'listings/inventory_logs.html', {'listing': listing, 'logs': logs})

@login_required
def make_listing_active(request, slug):
    """Make a draft listing active (visible in store)"""
    try:
        if not request.user.is_seller:
            messages.error(request, 'You need to enable seller mode first.')
            return redirect('enable_seller_mode')

        listing = get_object_or_404(Listing, slug=slug, seller=request.user, status='draft')

        if request.method == 'POST':
            listing.status = 'active'
            listing.save()
            messages.success(request, 'Listing is now active and visible in the store!')
            return redirect('seller_dashboard')

        return render(request, 'listings/make_active.html', {'listing': listing})
    except Exception as e:
        logger.error(f"Error in make_listing_active: {e}", exc_info=True)
        messages.error(request, 'An error occurred while making the listing active.')
        return redirect('seller_dashboard')

@login_required
def make_draft(request, slug):
    """Make an active listing return to draft (not visible in store)"""
    try:
        if not request.user.is_seller:
            messages.error(request, 'You need to enable seller mode first.')
            return redirect('enable_seller_mode')
        
        listing = get_object_or_404(Listing, slug=slug, seller=request.user, status='active')
        
        if request.method == 'POST':
            listing.status = 'draft'
            listing.save()
            messages.success(request, 'Listing is now a draft and not visible in the store.')
            return redirect('seller_dashboard')
        
        return render(request, 'listings/make_draft.html', {'listing': listing})
    except Exception as e:
        logger.error(f"Error in make_draft: {e}", exc_info=True)
        messages.error(request, 'An error occurred while making the listing a draft.')
        return redirect('seller_dashboard')

@login_required
def bulk_inventory_operation(request):
    """Perform bulk inventory operations on multiple listings"""
    try:
        if not request.user.is_seller:
            messages.error(request, 'You need to enable seller mode first.')
            return redirect('enable_seller_mode')
        
        if request.method == 'POST':
            operation_type = request.POST.get('operation_type')
            quantity = int(request.POST.get('quantity', 0))
            listing_ids = request.POST.getlist('listings')
            
            if not operation_type or quantity <= 0 or not listing_ids:
                messages.error(request, 'Invalid operation parameters.')
                return redirect('seller_dashboard')
            
            listings = Listing.objects.filter(id__in=listing_ids, seller=request.user)
            updated_count = 0
            
            for listing in listings:
                quantity_before = listing.available_stock
                
                if operation_type == 'add':
                    listing.available_stock += quantity
                    listing.quantity += quantity
                    change_type = 'restock'
                elif operation_type == 'remove':
                    if listing.available_stock < quantity:
                        messages.warning(request, f'Cannot remove {quantity} from {listing.title}. Only {listing.available_stock} available.')
                        continue
                    listing.available_stock -= quantity
                    listing.quantity -= quantity
                    change_type = 'sale'
                elif operation_type == 'putqty':
                    listing.available_stock = quantity
                    listing.quantity = quantity
                    change_type = 'adjustment'
                
                listing.save()
                
                # Log the inventory change
                InventoryLog.objects.create(
                    listing=listing,
                    change_type=change_type,
                    quantity_before=quantity_before,
                    quantity_after=listing.available_stock,
                    notes=f'Bulk {operation_type} operation: {quantity} items'
                )
                
                updated_count += 1
            
            messages.success(request, f'Successfully updated {updated_count} listings.')
            return redirect('seller_dashboard')
        
        return redirect('seller_dashboard')
    except Exception as e:
        logger.error(f"Error in bulk inventory operation: {e}", exc_info=True)
        messages.error(request, 'An error occurred during bulk operation.')
        return redirect('seller_dashboard')

@login_required
def adjust_quantity(request):
    """Handle individual quantity adjustments via AJAX"""
    try:
        if not request.user.is_seller:
            return JsonResponse({'success': False, 'message': 'You need to enable seller mode first.'}, status=403)
        
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=405)
        
        listing_id = request.POST.get('listing_id')
        change = int(request.POST.get('change', 0))
        
        if not listing_id or change == 0:
            return JsonResponse({'success': False, 'message': 'Invalid parameters.'}, status=400)
        
        listing = get_object_or_404(Listing, id=listing_id, seller=request.user)
        
        if not listing.is_buy_now:
            return JsonResponse({'success': False, 'message': 'Only buy-now listings can have quantity adjustments.'}, status=400)
        
        quantity_before = listing.available_stock
        new_stock = quantity_before + change
        
        if new_stock < 0:
            return JsonResponse({'success': False, 'message': 'Cannot reduce stock below 0.'}, status=400)
        
        listing.available_stock = new_stock
        listing.quantity = new_stock
        listing.save()
        
        # Log the inventory change
        change_type = 'restock' if change > 0 else 'sale'
        InventoryLog.objects.create(
            listing=listing,
            change_type=change_type,
            quantity_before=quantity_before,
            quantity_after=new_stock,
            notes=f'Quick adjustment: {change:+d} items'
        )
        
        logger.info(f"User {request.user.id} adjusted quantity for listing {listing.id} by {change}")
        
        return JsonResponse({
            'success': True,
            'new_stock': new_stock,
            'message': f'Stock updated to {new_stock}'
        })
        
    except Listing.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Listing not found.'}, status=404)
    except ValueError:
        return JsonResponse({'success': False, 'message': 'Invalid quantity value.'}, status=400)
    except Exception as e:
        logger.error(f"Error in adjust_quantity: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'An error occurred while adjusting quantity.'}, status=500)

@login_required
def add_to_wishlist(request, slug):
    """Add listing to wishlist (acts as add-to-cart)"""
    try:
        listing = get_object_or_404(Listing, slug=slug)

        # Prevent seller from adding their own items
        if request.user == listing.seller:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'You cannot add your own listing to wishlist.'}, status=400)
            messages.error(request, 'You cannot add your own listing to wishlist.')
            return redirect('listing_detail', slug=slug)

        # Only buy-now items can be added to wishlist
        if not listing.is_buy_now:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'Only buy-now items can be added to wishlist.'}, status=400)
            messages.error(request, 'Only buy-now items can be added to wishlist.')
            return redirect('listing_detail', slug=slug)
        
        if listing.available_stock <= 0:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'This item is out of stock.'}, status=400)
            messages.error(request, 'This item is out of stock.')
            return redirect('listing_detail', slug=slug)

        # Get quantity from POST or default to 1
        quantity = int(request.POST.get('quantity', 1))

        if quantity < 1:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': 'Quantity must be at least 1.'}, status=400)
            messages.error(request, 'Quantity must be at least 1.')
            return redirect('listing_detail', slug=slug)

        if quantity > listing.available_stock:
            if request.headers.get('Content-Type') == 'application/json':
                return JsonResponse({'success': False, 'message': f'Only {listing.available_stock} items available.'}, status=400)
            messages.error(request, f'Only {listing.available_stock} items available.')
            return redirect('listing_detail', slug=slug)

        # Add or update wishlist item
        wishlist_item, created = Wishlist.objects.get_or_create(
            user=request.user,
            listing=listing,
            defaults={'quantity': quantity}
        )

        if not created:
            # Update quantity if already in wishlist
            new_total = wishlist_item.quantity + quantity
            if new_total > listing.available_stock:
                if request.headers.get('Content-Type') == 'application/json':
                    return JsonResponse({'success': False, 'message': f'Cannot add more than {listing.available_stock} items total.'}, status=400)
                messages.error(request, f'Cannot add more than {listing.available_stock} items total.')
                return redirect('listing_detail', slug=slug)
            wishlist_item.quantity = new_total
            wishlist_item.save()

        logger.info(f"User {request.user.id} added {listing.slug} to wishlist (qty: {quantity})")

        if request.headers.get('Content-Type') == 'application/json':
            return JsonResponse({'success': True, 'quantity': wishlist_item.quantity})

        messages.success(request, f'Added to wishlist! Total: {wishlist_item.quantity} items')
        return redirect('wishlist')

    except Exception as e:
        logger.error(f"Error in add_to_wishlist: {e}", exc_info=True)
        messages.error(request, 'An error occurred while adding to wishlist.')
        return redirect('listing_detail', slug=slug)

@login_required
@transaction.atomic
def buy_now(request, slug):
    """Direct buy now purchase"""
    try:
        listing = get_object_or_404(Listing, slug=slug)

        # Prevent seller from buying their own items
        if request.user == listing.seller:
            messages.error(request, 'You cannot buy your own listing.')
            return redirect('listing_detail', slug=slug)

        # Only buy-now items can be purchased
        if not listing.is_buy_now:
            messages.error(request, 'This item is not available for buy now.')
            return redirect('listing_detail', slug=slug)

        if listing.available_stock <= 0:
            messages.error(request, 'This item is out of stock.')
            return redirect('listing_detail', slug=slug)

        if request.method == 'POST':
            quantity = int(request.POST.get('quantity', 1))

            if quantity < 1:
                messages.error(request, 'Quantity must be at least 1.')
                return redirect('listing_detail', slug=slug)

            if quantity > listing.available_stock:
                messages.error(request, f'Only {listing.available_stock} items available.')
                return redirect('listing_detail', slug=slug)

            # Create order
            from orders.models import Order
            from wallets.models import Wallet, WalletTransaction

            # Check wallet balance
            wallet, _ = Wallet.objects.get_or_create(user=request.user)
            total_amount = listing.buy_now_price * quantity

            if wallet.balance < total_amount:
                messages.error(request, f'Insufficient wallet balance. You need ₱{total_amount} but have ₱{wallet.balance}.')
                return redirect('listing_detail', slug=slug)

            # Create order
            order = Order.objects.create(
                buyer=request.user,
                listing=listing,
                order_type='buy_now',
                quantity=quantity,
                total_amount=total_amount,
                shipping_address=request.user.buyer_profile.shipping_address if hasattr(request.user, 'buyer_profile') else request.user.address if request.user.address else 'No address provided',
                status='pending'
            )

            # Deduct from wallet
            wallet.balance -= total_amount
            wallet.save()

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='payment',
                amount=-total_amount,
                description=f'Payment for order {order.order_number}',
                related_order=order
            )

            # Reduce stock
            listing.available_stock -= quantity
            listing.quantity_sold += quantity
            listing.save()

            # Log inventory change
            InventoryLog.objects.create(
                listing=listing,
                change_type='sale',
                quantity_before=listing.available_stock + quantity,
                quantity_after=listing.available_stock,
                notes=f'Buy now order {order.order_number}: {quantity} items'
            )

            logger.info(f"User {request.user.id} bought {listing.slug} (qty: {quantity})")
            messages.success(request, f'Purchase successful! Order {order.order_number}.')
            return redirect('order_list')

        return redirect('listing_detail', slug=slug)

    except Exception as e:
        logger.error(f"Error in buy_now: {e}", exc_info=True)
        messages.error(request, 'An error occurred while processing your purchase.')
        return redirect('listing_detail', slug=slug)

@login_required
def wishlist(request):
    """View wishlist (acts as shopping cart)"""
    try:
        wishlist_items = Wishlist.objects.filter(user=request.user).select_related('listing', 'listing__seller', 'listing__category')
        
        total_amount = sum(item.total_price for item in wishlist_items)
        total_items = sum(item.quantity for item in wishlist_items)
        
        context = {
            'wishlist_items': wishlist_items,
            'total_amount': total_amount,
            'total_items': total_items,
        }
        
        return render(request, 'listings/wishlist.html', context)
    except Exception as e:
        logger.error(f"Error in wishlist: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading your wishlist.')
        return redirect('catalog')

@login_required
def update_wishlist_quantity(request, item_id):
    """Update quantity of wishlist item via AJAX"""
    try:
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        new_quantity = int(request.POST.get('quantity', 1))
        
        if new_quantity < 1:
            wishlist_item.delete()
            return JsonResponse({'success': True, 'deleted': True})
        
        if new_quantity > wishlist_item.listing.available_stock:
            return JsonResponse({
                'success': False,
                'message': f'Cannot add more than {wishlist_item.listing.available_stock} items'
            }, status=400)
        
        wishlist_item.update_quantity(new_quantity)
        
        return JsonResponse({
            'success': True,
            'new_quantity': wishlist_item.quantity,
            'new_total': wishlist_item.total_price
        })
        
    except Exception as e:
        logger.error(f"Error in update_wishlist_quantity: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'An error occurred.'}, status=500)

@login_required
def remove_from_wishlist_by_listing(request, listing_id):
    """Remove item from wishlist by listing_id (for toggle functionality)"""
    try:
        wishlist_item = Wishlist.objects.get(listing_id=listing_id, user=request.user)
        wishlist_item.delete()
        return JsonResponse({'success': True})
    except Wishlist.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Item not in wishlist'}, status=404)
    except Exception as e:
        logger.error(f"Error in remove_from_wishlist_by_listing: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'An error occurred.'}, status=500)

@login_required
def remove_from_wishlist(request, item_id):
    """Remove item from wishlist"""
    try:
        wishlist_item = get_object_or_404(Wishlist, id=item_id, user=request.user)
        wishlist_item.delete()
        messages.success(request, 'Item removed from wishlist.')
        return redirect('wishlist')
    except Exception as e:
        logger.error(f"Error in remove_from_wishlist: {e}", exc_info=True)
        messages.error(request, 'An error occurred while removing item.')
        return redirect('wishlist')

@login_required
@transaction.atomic
def checkout_wishlist(request):
    """Checkout all items in wishlist"""
    try:
        wishlist_items = Wishlist.objects.filter(user=request.user)
        
        if not wishlist_items.exists():
            messages.error(request, 'Your wishlist is empty.')
            return redirect('wishlist')
        
        # Create orders for each item
        from orders.models import Order
        from wallets.models import Wallet, WalletTransaction

        orders_created = []
        total_deduction = 0

        for wishlist_item in wishlist_items:
            listing = wishlist_item.listing

            # Check stock again
            if listing.available_stock < wishlist_item.quantity:
                messages.error(request, f'{listing.title} no longer has enough stock.')
                continue

            # Check wallet balance for this item
            wallet, _ = Wallet.objects.get_or_create(user=request.user)

            if wallet.balance < wishlist_item.total_price:
                messages.error(request, f'Insufficient wallet balance for {listing.title}. Need ₱{wishlist_item.total_price} but have ₱{wallet.balance}.')
                continue

            # Create order
            order = Order.objects.create(
                buyer=request.user,
                listing=listing,
                order_type='buy_now',
                quantity=wishlist_item.quantity,
                total_amount=wishlist_item.total_price,
                shipping_address=request.user.buyer_profile.shipping_address if hasattr(request.user, 'buyer_profile') else request.user.address if request.user.address else 'No address provided',
                status='pending'
            )

            total_deduction += wishlist_item.total_price

            WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='payment',
                amount=-wishlist_item.total_price,
                description=f'Payment for order {order.order_number}',
                related_order=order
            )

            # Reduce stock
            listing.available_stock -= wishlist_item.quantity
            listing.quantity_sold += wishlist_item.quantity
            listing.save()

            # Log inventory change
            InventoryLog.objects.create(
                listing=listing,
                change_type='sale',
                quantity_before=listing.available_stock + wishlist_item.quantity,
                quantity_after=listing.available_stock,
                notes=f'Wishlist checkout order {order.order_number}: {wishlist_item.quantity} items'
            )

            orders_created.append(order)
            wishlist_item.delete()

        # Deduct total from wallet once
        if total_deduction > 0:
            wallet.balance -= total_deduction
            wallet.save()

        if orders_created:
            messages.success(request, f'Successfully created {len(orders_created)} order(s)!')
            return redirect('order_list')
        else:
            messages.error(request, 'No orders were created. Please check stock availability.')
            return redirect('wishlist')
            
    except Exception as e:
        logger.error(f"Error in checkout_wishlist: {e}", exc_info=True)
        messages.error(request, 'An error occurred during checkout.')
        return redirect('wishlist')

@login_required
def conversation_list(request):
    """View all conversations for the current user"""
    try:
        # Get conversations where user is either buyer or seller
        conversations = Conversation.objects.filter(
            Q(buyer=request.user) | Q(seller=request.user)
        ).select_related('listing', 'buyer', 'seller').prefetch_related('messages').order_by('-updated_at')
        
        context = {
            'conversations': conversations,
        }
        
        return render(request, 'listings/conversations.html', context)
    except Exception as e:
        logger.error(f"Error in conversation_list: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading conversations.')
        return redirect('catalog')

@login_required
def conversation_detail(request, conversation_id):
    """View and send messages in a conversation"""
    try:
        conversation = get_object_or_404(
            Conversation.objects.filter(Q(buyer=request.user) | Q(seller=request.user)),
            id=conversation_id
        )
        
        # Mark messages as read
        if request.user == conversation.seller:
            conversation.messages.filter(sender=conversation.buyer, is_read=False).update(is_read=True)
        else:
            conversation.messages.filter(sender=conversation.seller, is_read=False).update(is_read=True)
        
        if request.method == 'POST':
            content = request.POST.get('content', '').strip()
            if content:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content
                )
                conversation.updated_at = timezone.now()
                conversation.save()
                messages.success(request, 'Message sent!')
                return redirect('conversation_detail', conversation_id=conversation.id)
            else:
                messages.error(request, 'Message cannot be empty.')
        
        context = {
            'conversation': conversation,
            'messages': conversation.messages.all().order_by('created_at'),
        }
        
        return render(request, 'listings/conversation_detail.html', context)
    except Exception as e:
        logger.error(f"Error in conversation_detail: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the conversation.')
        return redirect('conversation_list')

@login_required
def start_conversation(request, slug):
    """Start a new conversation about a listing"""
    try:
        listing = get_object_or_404(Listing, slug=slug)
        
        # Prevent conversation with yourself
        if request.user == listing.seller:
            messages.error(request, 'You cannot start a conversation with yourself.')
            return redirect('listing_detail', slug=slug)
        
        # Check if conversation already exists
        conversation = Conversation.objects.filter(
            listing=listing,
            buyer=request.user,
            seller=listing.seller
        ).first()
        
        if not conversation:
            conversation = Conversation.objects.create(
                listing=listing,
                buyer=request.user,
                seller=listing.seller
            )
            messages.success(request, 'Conversation started!')
        else:
            messages.info(request, 'Conversation already exists.')
        
        return redirect('conversation_detail', conversation_id=conversation.id)
    except Exception as e:
        logger.error(f"Error in start_conversation: {e}", exc_info=True)
        messages.error(request, 'An error occurred while starting the conversation.')
        return redirect('listing_detail', slug=slug)

@login_required
def seller_store(request, seller_id):
    """View seller's store page"""
    try:
        seller = get_object_or_404(User, id=seller_id, seller_enabled=True)

        # Get seller's active listings
        listings = Listing.objects.filter(
            seller=seller,
            status='active'
        ).select_related('category').prefetch_related('images').order_by('-created_at')

        # Get seller stats
        active_count = listings.count()
        sold_count = Listing.objects.filter(
            seller=seller,
            status='sold'
        ).count()

        context = {
            'seller': seller,
            'listings': listings,
            'active_count': active_count,
            'sold_count': sold_count,
        }

        return render(request, 'listings/seller_store.html', context)
    except Exception as e:
        logger.error(f"Error in seller_store: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading the store.')
        return redirect('catalog')

def seed_categories_view(request):
    """Simple view to seed categories - accessible via URL for Render free tier"""
    try:
        from categories.models import Category, SizeSystem, SizeSpecification
        
        categories_data = [
            {'name': 'Electronics', 'slug': 'electronics', 'category_type': 'main', 'description': 'Electronic devices and accessories'},
            {'name': 'Clothing', 'slug': 'clothing', 'category_type': 'main', 'description': 'Clothing and apparel'},
            {'name': 'Home & Garden', 'slug': 'home-garden', 'category_type': 'main', 'description': 'Home and garden items'},
            {'name': 'Sports', 'slug': 'sports', 'category_type': 'main', 'description': 'Sports equipment and accessories'},
            {'name': 'Books', 'slug': 'books', 'category_type': 'main', 'description': 'Books and publications'},
        ]
        
        created_count = 0
        existing_count = 0
        
        for cat_data in categories_data:
            category, created = Category.objects.get_or_create(
                slug=cat_data['slug'],
                defaults=cat_data
            )
            if created:
                created_count += 1
            else:
                existing_count += 1
        
        # Create size system for clothing
        size_system, created = SizeSystem.objects.get_or_create(
            name='Clothing Sizes',
            system_type='alpha',
            defaults={'name': 'Clothing Sizes', 'system_type': 'alpha'}
        )
        
        if created:
            sizes = [
                {'size_value': 'S', 'display_name': 'Small'},
                {'size_value': 'M', 'display_name': 'Medium'},
                {'size_value': 'L', 'display_name': 'Large'},
                {'size_value': 'XL', 'display_name': 'Extra Large'},
            ]
            for size_data in sizes:
                SizeSpecification.objects.get_or_create(
                    size_system=size_system,
                    size_value=size_data['size_value'],
                    defaults=size_data
                )
        
        return JsonResponse({
            'success': True,
            'message': f'Categories seeded: {created_count} created, {existing_count} already existed',
            'total_categories': Category.objects.count()
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
