from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.rider_dashboard, name='rider_dashboard'),
]