from django.db import models
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from orders.models import Order

User = get_user_model()

class RiderLocation(models.Model):
    rider = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rider_locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'rider_locations'
        verbose_name = _('Rider Location')
        verbose_name_plural = _('Rider Locations')
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.rider.email} - {self.latitude}, {self.longitude}"