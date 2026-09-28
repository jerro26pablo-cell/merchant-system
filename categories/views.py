from django.shortcuts import render, get_object_or_404
from .models import Category

def category_list(request):
    main_categories = Category.objects.filter(category_type='main', is_active=True).order_by('sort_order')
    return render(request, 'categories/category_list.html', {'categories': main_categories})

def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug, is_active=True)
    subcategories = category.children.filter(is_active=True).order_by('sort_order')
    return render(request, 'categories/category_detail.html', {'category': category, 'subcategories': subcategories})
