from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Case, When, F, DecimalField
from django.core.paginator import Paginator
from django.db.models.functions import Coalesce
from decimal import Decimal, InvalidOperation
from django.http import JsonResponse
from .models import Listing, ListingImage, ListingAttribute, InventoryLog
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
        # Allow viewing any listing that the user owns or is active/official
        listing = get_object_or_404(Listing, slug=slug)
        
        # If not the seller, only show active/official listings
        if request.user != listing.seller and listing.status not in ['active', 'official']:
            messages.error(request, 'This listing is not currently available.')
            return redirect('catalog')
        
        # Track view
        listing.add_view(
            user=request.user if request.user.is_authenticated else None,
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        # Get similar listings
        similar_listings = Listing.objects.filter(
            category=listing.category,
            status__in=['active', 'official']
        ).exclude(id=listing.id)[:4]
        
        context = {
            'listing': listing,
            'similar_listings': similar_listings,
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
def make_listing_official(request, slug):
    """Make a draft listing official (visible in store)"""
    try:
        if not request.user.is_seller:
            messages.error(request, 'You need to enable seller mode first.')
            return redirect('enable_seller_mode')
        
        listing = get_object_or_404(Listing, slug=slug, seller=request.user, status='draft')
        
        if request.method == 'POST':
            listing.status = 'active'
            listing.save()
            messages.success(request, 'Listing is now official and visible in the store!')
            return redirect('seller_dashboard')
        
        return render(request, 'listings/make_official.html', {'listing': listing})
    except Exception as e:
        logger.error(f"Error in make_listing_official: {e}", exc_info=True)
        messages.error(request, 'An error occurred while making the listing official.')
        return redirect('seller_dashboard')

@login_required
def make_draft(request, slug):
    """Make an official listing return to draft (not visible in store)"""
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
        
    except Exception as e:
        logger.error(f"Error in adjust_quantity: {e}", exc_info=True)
        return JsonResponse({'success': False, 'message': 'An error occurred while adjusting quantity.'}, status=500)

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
