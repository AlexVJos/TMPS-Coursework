from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.admin.views.decorators import staff_member_required

from services.order_facade import OrderPlacementFacade
from .models import Order
from .forms import OrderCreateForm
from cart.cart import Cart

from services.order_builder import OrderBuilder
from services.notification_service import get_order_notifier
from services.order_state_machine import OrderContext
from services.discount_strategies import (
    DefaultOrderDiscountAllocator,
    PromoCodeDiscountAllocator,
    NoDiscountStrategy
)


def order_create(request):
    cart = Cart(request)
    if not cart and request.method == 'GET':
        return redirect('catalog:product_list')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            facade = OrderPlacementFacade(request)
            order, errors = facade.place_order(form.cleaned_data)

            if order:
                request.session['order_id'] = order.id
                return redirect(reverse('orders:order_created_success'))
            else:
                if errors:
                    for error_msg in errors:
                        form.add_error(None, error_msg)
    else:
        form = OrderCreateForm()

    context = {
        'cart': cart,
        'form': form
    }
    return render(request, 'orders/order/create.html', context)

def order_created_success(request):
    order_id = request.session.get('order_id')
    if not order_id:
        return redirect('catalog:product_list')

    try:
        order = Order.objects.get(id=order_id)
    except Order.DoesNotExist:
        return redirect('catalog:product_list')

    return render(request, 'orders/order/created.html', {'order': order})


@staff_member_required
def admin_order_detail_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_context = OrderContext(order)

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'process_next':
            order_context.process_next_step()
        elif action == 'cancel':
            order_context.cancel_order()
        return redirect('orders:admin_order_detail', order_id=order.id)

    context = {
        'order': order,
        'order_context': order_context
    }
    return render(request, 'orders/admin/order_detail.html', context)

@staff_member_required
def admin_order_list(request):
    orders = Order.objects.all().order_by('-created_at')
    return render(request, 'orders/admin/order_list.html', {'orders': orders})