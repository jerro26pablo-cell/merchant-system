from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.static import serve
from listings.views import seed_categories_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('categories/', include('categories.urls')),
    path('listings/', include('listings.urls')),
    path('bidding/', include('bidding.urls')),
    path('notifications/', include('notifications.urls')),
    path('orders/', include('orders.urls')),
    path('wallets/', include('wallets.urls')),
    path('riders/', include('riders.urls')),
    path('api/', include('rest_framework.urls')),
    path('seed-categories/', seed_categories_view, name='seed_categories'),
    path('', TemplateView.as_view(template_name='index.html'), name='home'),
]

# Serve media files in both development and production
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
