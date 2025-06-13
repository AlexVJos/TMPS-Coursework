from django.shortcuts import render, get_object_or_404

from cart.forms import CartAddProductForm
from .models import Category, Product


def product_list(request, category_slug=None):
    current_category = None
    categories = Category.objects.filter(
        parent__isnull=True)

    products = Product.objects.filter(available=True)

    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        category_ids_to_filter = [current_category.id]

        def get_all_children_ids(category):
            ids = []
            for child in category.children.all():
                ids.append(child.id)
                ids.extend(get_all_children_ids(child))
            return ids

        category_ids_to_filter.extend(get_all_children_ids(current_category))

        products = products.filter(category_id__in=category_ids_to_filter)

    context = {
        'current_category': current_category,
        'categories': Category.objects.all(),
        'products': products
    }
    return render(request, 'catalog/product/list.html', context)


def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug, available=True)
    categories = Category.objects.all()
    cart_add_form = CartAddProductForm()

    context = {
        'product': product,
        'categories': categories,
        'cart_add_form': cart_add_form,
    }
    return render(request, 'catalog/product/detail.html', context)