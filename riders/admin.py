from django.contrib import admin
from .models import RiderLocation


@admin.register(RiderLocation)
class RiderLocationAdmin(admin.ModelAdmin):
    list_display = ['rider', 'latitude', 'longitude', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['rider__email']
    readonly_fields = ['timestamp']