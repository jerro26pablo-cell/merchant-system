from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('buyer-dashboard/', views.buyer_dashboard, name='buyer_dashboard'),
    path('enable-seller/', views.enable_seller_mode, name='enable_seller_mode'),
    path('seller-profile/', views.seller_profile, name='seller_profile'),
    path('seller-dashboard/', views.seller_dashboard, name='seller_dashboard'),
]
