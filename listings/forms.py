from django import forms
from django.core.exceptions import ValidationError
from .models import Listing, ListingImage, ListingAttribute
from categories.models import Category, SizeSpecification

class ListingForm(forms.ModelForm):
    class Meta:
        model = Listing
        fields = [
            'title', 'description', 'category', 'listing_type', 'condition',
            'quantity', 'available_stock', 'auction_quantity',
            'starting_bid', 'buy_now_price', 'reserve_price', 'minimum_increment',
            'auction_start', 'auction_end', 'anti_snipe_seconds', 'auto_relist',
            'size'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
            'auction_start': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'auction_end': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        self.fields['size'].queryset = SizeSpecification.objects.filter(is_active=True)
    
    def clean(self):
        cleaned_data = super().clean()
        listing_type = cleaned_data.get('listing_type')
        starting_bid = cleaned_data.get('starting_bid')
        buy_now_price = cleaned_data.get('buy_now_price')
        reserve_price = cleaned_data.get('reserve_price')
        auction_start = cleaned_data.get('auction_start')
        auction_end = cleaned_data.get('auction_end')
        quantity = cleaned_data.get('quantity')
        available_stock = cleaned_data.get('available_stock')
        auction_quantity = cleaned_data.get('auction_quantity')
        
        # Validate auction requirements
        if listing_type in ['auction', 'both']:
            if not starting_bid:
                raise ValidationError('Starting bid is required for auction listings.')
            if not auction_start or not auction_end:
                raise ValidationError('Auction start and end times are required for auction listings.')
            if auction_end <= auction_start:
                raise ValidationError('Auction end time must be after start time.')
        
        # Validate buy-now requirements
        if listing_type in ['buy_now', 'both']:
            if not buy_now_price:
                raise ValidationError('Buy now price is required for buy-now listings.')
        
        # Validate pricing logic
        if reserve_price and starting_bid and reserve_price <= starting_bid:
            raise ValidationError('Reserve price must be higher than starting bid.')
        
        if buy_now_price and starting_bid and buy_now_price <= starting_bid:
            raise ValidationError('Buy now price must be higher than starting bid.')
        
        # Validate quantity logic
        if listing_type == 'buy_now':
            if available_stock > quantity:
                raise ValidationError('Available stock cannot exceed total quantity.')
            cleaned_data['auction_quantity'] = 0
        elif listing_type == 'auction':
            if auction_quantity > quantity:
                raise ValidationError('Auction quantity cannot exceed total quantity.')
            cleaned_data['available_stock'] = 0
        elif listing_type == 'both':
            if available_stock + auction_quantity > quantity:
                raise ValidationError('Sum of available stock and auction quantity cannot exceed total quantity.')
        
        return cleaned_data

class ListingImageForm(forms.ModelForm):
    class Meta:
        model = ListingImage
        fields = ['image', 'alt_text', 'is_primary', 'sort_order']

ListingImageFormSet = forms.inlineformset_factory(
    Listing,
    ListingImage,
    form=ListingImageForm,
    extra=3,
    can_delete=True
)
