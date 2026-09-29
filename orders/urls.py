from django.urls import path
from . import views

urlpatterns = [
    path('my-orders/', views.order_list, name='order_list'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
]