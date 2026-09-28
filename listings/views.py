from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Listing, ListingImage, ListingAttribute, InventoryLog
from .forms import ListingForm, ListingImageFormSet

def listing_catalog(request):
    """Catalog-style view of all active listings"""
    listings = Listing.objects.filter(
        status='active'
    ).select_related('seller', 'category').prefetch_related('images').order_by('-created_at')
    
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
    
    # Price range filter
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        listings = listings.filter(current_price__gte=min_price)
    if max_price:
        listings = listings.filter(current_price__lte=max_price)
    
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
    }
    
    return render(request, 'listings/catalog.html', context)

def listing_detail(request, slug):
    listing = get_object_or_404(Listing, slug=slug, status='active')
    
    # Track view
    listing.add_view(
        user=request.user if request.user.is_authenticated else None,
        ip_address=request.META.get('REMOTE_ADDR')
    )
    
    # Get similar listings
    similar_listings = Listing.objects.filter(
        category=listing.category,
        status='active'
    ).exclude(id=listing.id)[:4]
    
    context = {
        'listing': listing,
        'similar_listings': similar_listings,
    }
    
    return render(request, 'listings/detail.html', context)

@login_required
def create_listing(request):
    if not request.user.is_seller:
        messages.error(request, 'You need to enable seller mode to create listings.')
        return redirect('enable_seller_mode')
    
    if request.method == 'POST':
        form = ListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.seller = request.user
            listing.save()
            
            # Handle images
            image_formset = ListingImageFormSet(request.POST, request.FILES, instance=listing)
            if image_formset.is_valid():
                image_formset.save()
            
            # Log inventory
            InventoryLog.objects.create(
                listing=listing,
                change_type='restock',
                quantity_before=0,
                quantity_after=listing.quantity,
                notes='Initial listing creation'
            )
            
            messages.success(request, 'Listing created successfully!')
            return redirect('listing_detail', slug=listing.slug)
    else:
        form = ListingForm()
        image_formset = ListingImageFormSet()
    
    return render(request, 'listings/create.html', {'form': form, 'image_formset': image_formset})

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
