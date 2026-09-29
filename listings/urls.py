from django.urls import path
from . import views

urlpatterns = [
    path('', views.listing_catalog, name='catalog'),
    path('create/', views.create_listing, name='create_listing'),
    path('<slug:slug>/', views.listing_detail, name='listing_detail'),
    path('<slug:slug>/edit/', views.edit_listing, name='edit_listing'),
    path('<slug:slug>/delete/', views.delete_listing, name='delete_listing'),
    path('<slug:slug>/convert-to-auction/', views.convert_to_auction, name='convert_to_auction'),
    path('inventory/', views.inventory_management, name='inventory_management'),
    path('<slug:slug>/adjust-inventory/', views.adjust_inventory, name='adjust_inventory'),
    path('<slug:slug>/inventory-logs/', views.inventory_logs, name='inventory_logs'),
    path('<slug:slug>/make-active/', views.make_listing_active, name='make_listing_active'),
    path('<slug:slug>/make-draft/', views.make_draft, name='make_draft'),
    path('bulk-operation/', views.bulk_inventory_operation, name='bulk_inventory_operation'),
    path('adjust-quantity/', views.adjust_quantity, name='adjust_quantity'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('wishlist/add/<slug:slug>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('wishlist/update/<int:item_id>/', views.update_wishlist_quantity, name='update_wishlist_quantity'),
    path('wishlist/remove/<int:item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('wishlist/checkout/', views.checkout_wishlist, name='checkout_wishlist'),
    path('conversations/', views.conversation_list, name='conversation_list'),
    path('conversations/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('conversations/start/<slug:slug>/', views.start_conversation, name='start_conversation'),
]
