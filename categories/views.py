from django.shortcuts import render, get_object_or_404
from .models import Category
import logging

logger = logging.getLogger(__name__)

def category_list(request):
    try:
        main_categories = Category.objects.filter(category_type='main', is_active=True).order_by('sort_order')
    except Exception as e:
        logger.error(f"Error fetching categories: {e}")
        main_categories = Category.objects.none()
    return render(request, 'categories/category_list.html', {'categories': main_categories})

def category_detail(request, slug):
    try:
        category = get_object_or_404(Category, slug=slug, is_active=True)
        subcategories = category.children.filter(is_active=True).order_by('sort_order')
    except Exception as e:
        logger.error(f"Error fetching category detail: {e}")
        raise  # Re-raise since get_object_or_404 should handle 404s
    return render(request, 'categories/category_detail.html', {'category': category, 'subcategories': subcategories})
