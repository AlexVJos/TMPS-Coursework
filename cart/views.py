from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from catalog.models import Product
from .cart import Cart
from .forms import CartAddProductForm  # Мы создадим эту форму далее


@require_POST  # Этот декоратор разрешает только POST-запросы
def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    form = CartAddProductForm(request.POST)
    if form.is_valid():
        cd = form.cleaned_data
        cart.add(product=product,
                 quantity=cd['quantity'],
                 update_quantity=cd['update_quantity'])
    # Если AJAX, можно вернуть JSON-ответ. Пока просто редирект.
    return redirect('cart:cart_detail')


@require_POST
def cart_remove(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    # Добавляем формы обновления количества для каждого товара в корзине
    for item in cart:
        item['update_quantity_form'] = CartAddProductForm(
            initial={'quantity': item['quantity'], 'update_quantity': True}
        )

    # Потенциальное место для применения паттерна Стратегия (для скидок)
    # total_price_before_discount = cart.get_total_price()
    # discount_amount = 0 # Рассчитать скидку с помощью стратегии
    # final_total_price = total_price_before_discount - discount_amount

    context = {
        'cart': cart,
        # 'discount_amount': discount_amount,
        # 'final_total_price': final_total_price,
    }
    return render(request, 'cart/detail.html', context)