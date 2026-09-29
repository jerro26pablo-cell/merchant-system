from django.urls import path
from . import views

urlpatterns = [
    path('add-to-cart/<slug:slug>/', views.add_to_cart, name='add_to_cart'),
    path('my-orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
]