from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import RiderLocation


@login_required
def rider_dashboard(request):
    """Rider dashboard for managing deliveries"""
    if not hasattr(request.user, 'rider_profile'):
        return render(request, 'riders/no_profile.html')
    
    locations = request.user.rider_locations.all().order_by('-timestamp')[:10]
    
    return render(request, 'riders/dashboard.html', {
        'locations': locations
    })