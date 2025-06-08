from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from catalog.models import Product
from services.commands import AddToCartCommand
from .cart import Cart
from .forms import CartAddProductForm

@require_POST
def cart_add(request, product_id):
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data

        command = AddToCartCommand(
            request=request,
            product_id=product_id,
            quantity=cd['quantity'],
            update_quantity=cd['update_quantity']
        )

        try:
            success = command.execute()
            if not success:
                pass
        except Exception as e:
            print(f"Error executing AddToCartCommand: {str(e)}")
            pass
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'update_quantity': True}
        )

    context = {
        'cart': cart,
    }
    return render(request, 'cart/detail.html', context)