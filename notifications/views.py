from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Notification, NotificationPreference
import logging

logger = logging.getLogger(__name__)

@login_required
def notification_list(request):
    try:
        from .models import Notification
        notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
        
        context = {
            'notifications': notifications,
        }
        
        return render(request, 'notifications/list.html', context)
    except Exception as e:
        logger.error(f"Error in notification_list: {e}", exc_info=True)
        messages.error(request, 'An error occurred while loading your notifications.')
        return render(request, 'notifications/list.html', {'notifications': []})

@login_required
def mark_notification_read(request, notification_id):
    try:
        notification = get_object_or_404(Notification, id=notification_id, user=request.user)
        notification.mark_as_read()
        messages.success(request, 'Notification marked as read.')
        return redirect('notification_list')
    except Exception as e:
        logger.error(f"Error in mark_notification_read: {e}", exc_info=True)
        messages.error(request, 'An error occurred while marking the notification as read.')
        return redirect('notification_list')

@login_required
def notification_preferences(request):
    try:
        preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
        
        if request.method == 'POST':
            # Update preferences
            preferences.outbid_notifications = request.POST.get('outbid_notifications') == 'on'
            preferences.bid_status_notifications = request.POST.get('bid_status_notifications') == 'on'
            preferences.price_drop_notifications = request.POST.get('price_drop_notifications') == 'on'
            preferences.saved_search_notifications = request.POST.get('saved_search_notifications') == 'on'
            preferences.order_update_notifications = request.POST.get('order_update_notifications') == 'on'
            preferences.chat_message_notifications = request.POST.get('chat_message_notifications') == 'on'
            preferences.email_notifications = request.POST.get('email_notifications') == 'on'
            preferences.push_notifications = request.POST.get('push_notifications') == 'on'
            preferences.in_app_notifications = request.POST.get('in_app_notifications') == 'on'
            preferences.save()
            messages.success(request, 'Notification preferences updated successfully!')
        
        return render(request, 'notifications/preferences.html', {'preferences': preferences})
    except Exception as e:
        logger.error(f"Error in notification_preferences: {e}", exc_info=True)
        messages.error(request, 'An error occurred while updating your notification preferences.')
        return redirect('notification_list')
