from django.urls import path
from . import views

urlpatterns = [
    path('', views.listing_catalog, name='catalog'),
    path('create/', views.create_listing, name='create_listing'),
    path('<slug:slug>/', views.listing_detail, name='listing_detail'),
    path('<slug:slug>/edit/', views.edit_listing, name='edit_listing'),
    path('<slug:slug>/delete/', views.delete_listing, name='delete_listing'),
    path('<slug:slug>/convert-to-auction/', views.convert_to_auction, name='convert_to_auction'),
]
