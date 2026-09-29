from django.urls import path
from . import views

urlpatterns = [
    path('my-wallet/', views.wallet_detail, name='wallet_detail'),
    path('add-funds/', views.add_funds, name='add_funds'),
]