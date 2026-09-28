from django.urls import path
from . import views

urlpatterns = [
    path('place/<slug:slug>/', views.place_bid, name='place_bid'),
    path('max-cap/<slug:slug>/', views.set_max_bid_cap, name='set_max_bid_cap'),
    path('history/<slug:slug>/', views.bid_history, name='bid_history'),
    path('cancel/<int:bid_id>/', views.request_bid_cancellation, name='request_bid_cancellation'),
    path('my-bids/', views.my_bids, name='my_bids'),
]
